"""
Resume Routes Module.
Handles all resume-related API endpoints.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import UPLOAD_DIR, GENERATED_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS
from app.services import parser, ats_engine, ai_service, resume_builder

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models ==============

class UploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str
    filename: str
    message: str


class AnalysisResponse(BaseModel):
    """Response model for resume analysis."""
    file_id: str
    ats_score: int
    score_breakdown: dict
    issues: list
    suggestions: list
    detected_sections: list
    structured_resume: dict


class GenerateResponse(BaseModel):
    """Response model for ATS resume generation."""
    file_id: str
    download_url: str
    message: str


class JobMatchRequest(BaseModel):
    """Request model for job description matching."""
    file_id: str
    job_description: str


class JobMatchResponse(BaseModel):
    """Response model for job matching."""
    match_percentage: int
    matching_keywords: list
    missing_keywords: list
    suggestions: list


# ============== Helper Functions ==============

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    extension = Path(file.filename).suffix.lower().lstrip('.')
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: .{extension}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def save_upload(file: UploadFile) -> tuple[str, Path]:
    """Save uploaded file and return file_id and path."""
    file_id = str(uuid.uuid4())[:8]
    extension = Path(file.filename).suffix.lower()
    saved_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / saved_filename
    
    # Read and save file
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    return file_id, file_path


def get_uploaded_file(file_id: str) -> Path:
    """Get path to uploaded file by file_id."""
    for ext in ALLOWED_EXTENSIONS:
        file_path = UPLOAD_DIR / f"{file_id}.{ext}"
        if file_path.exists():
            return file_path
    
    raise HTTPException(status_code=404, detail=f"File not found: {file_id}")


# ============== API Endpoints ==============

@router.post("/upload_resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF or DOCX).
    
    - **file**: Resume file to upload
    
    Returns file_id for subsequent operations.
    """
    try:
        validate_file(file)
        file_id, file_path = await save_upload(file)
        
        logger.info(f"Uploaded resume: {file_id} ({file.filename})")
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            message="Resume uploaded successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze_resume", response_model=AnalysisResponse)
async def analyze_resume(file_id: str = Form(...)):
    """
    Analyze an uploaded resume.
    
    - **file_id**: ID from upload_resume response
    
    Returns ATS score, issues, suggestions, and detected sections.
    """
    try:
        # Get uploaded file
        file_path = get_uploaded_file(file_id)
        
        # Extract text from resume
        resume_text = parser.extract_text(file_path)
        resume_text = parser.clean_text(resume_text)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from resume")
        
        # Calculate ATS score
        ats_result = ats_engine.calculate_ats_score(resume_text)
        
        # Get structured resume
        structured = ats_engine.get_structured_resume(resume_text)
        
        # Detect sections
        sections = ats_engine.detect_sections(resume_text)
        detected_section_names = list(sections.keys())
        
        # Get AI-powered suggestions (if API key configured)
        try:
            ai_suggestions = ai_service.get_improvement_suggestions(resume_text, ats_result.total_score)
            all_suggestions = ats_result.suggestions + ai_suggestions
        except Exception as e:
            logger.warning(f"AI suggestions failed: {e}")
            all_suggestions = ats_result.suggestions
        
        logger.info(f"Analyzed resume {file_id}: Score {ats_result.total_score}")
        
        return AnalysisResponse(
            file_id=file_id,
            ats_score=ats_result.total_score,
            score_breakdown=ats_result.breakdown,
            issues=ats_result.issues,
            suggestions=all_suggestions,
            detected_sections=detected_section_names,
            structured_resume=structured
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/generate_ats_resume", response_model=GenerateResponse)
async def generate_ats_resume(file_id: str = Form(...)):
    """
    Generate an ATS-optimized resume from an uploaded file.
    
    - **file_id**: ID from upload_resume response
    
    Returns download URL for the generated resume.
    """
    try:
        # Get uploaded file
        file_path = get_uploaded_file(file_id)
        
        # Extract text
        resume_text = parser.extract_text(file_path)
        resume_text = parser.clean_text(resume_text)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from resume")
        
        # Get structured data
        structured = ats_engine.get_structured_resume(resume_text)
        
        # Try AI rewrite first
        try:
            rewritten = ai_service.rewrite_resume_ats_style(resume_text)
            generated_filename = f"ats_resume_{file_id}.docx"
            output_path = resume_builder.generate_from_ai_rewrite(
                rewritten, 
                structured, 
                generated_filename
            )
        except Exception as e:
            logger.warning(f"AI rewrite failed, using rule-based: {e}")
            # Fallback to rule-based generation
            sections = ats_engine.detect_sections(resume_text)
            resume_data = {
                "name": structured.get("name"),
                "contact": structured.get("contact", {}),
                "sections": {
                    k: {"type": k, "title": v.title, "content": v.content}
                    for k, v in sections.items()
                    if k not in ['name', 'contact']
                }
            }
            generated_filename = f"ats_resume_{file_id}.docx"
            output_path = resume_builder.create_ats_friendly_docx(resume_data, generated_filename)
        
        logger.info(f"Generated ATS resume for {file_id}: {output_path}")
        
        return GenerateResponse(
            file_id=file_id,
            download_url=f"/download/{generated_filename}",
            message="ATS-optimized resume generated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/match_job_description", response_model=JobMatchResponse)
async def match_job_description(request: JobMatchRequest):
    """
    Match resume against a job description.
    
    - **file_id**: ID from upload_resume response
    - **job_description**: Job description text to match against
    
    Returns match percentage and keyword analysis.
    """
    try:
        # Get uploaded file
        file_path = get_uploaded_file(request.file_id)
        
        # Extract text
        resume_text = parser.extract_text(file_path)
        resume_text = parser.clean_text(resume_text)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from resume")
        
        if not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Job description is required")
        
        # Match using AI
        result = ai_service.match_job_description(resume_text, request.job_description)
        
        logger.info(f"Job matching for {request.file_id}: {result['match_percentage']}%")
        
        return JobMatchResponse(
            match_percentage=result['match_percentage'],
            matching_keywords=result['matching_keywords'],
            missing_keywords=result['missing_keywords'],
            suggestions=result['suggestions']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job matching error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job matching failed: {str(e)}")


@router.get("/download/{filename}")
async def download_resume(filename: str):
    """
    Download a generated resume file.
    
    - **filename**: Filename of the generated resume
    
    Returns the DOCX file.
    """
    try:
        file_path = GENERATED_DIR / filename
        
        if not file_path.exists():
            # Try to find by file_id
            file_path = resume_builder.get_download_path(filename)
            if not file_path:
                raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Download requested: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/tips")
async def get_resume_tips():
    """
    Get general resume improvement tips.
    
    Returns a list of actionable tips for ATS optimization.
    """
    try:
        tips = ai_service.generate_resume_tips()
        return {"tips": tips}
    except Exception as e:
        logger.warning(f"Tips generation failed: {e}")
        return {
            "tips": [
                "Use standard section headings like 'Work Experience' and 'Education'",
                "Start bullet points with strong action verbs",
                "Include quantifiable achievements (numbers, percentages, dollar amounts)",
                "Avoid tables, graphics, and special characters",
                "Tailor your resume to each job description",
                "Use a clean, single-column format",
                "Include relevant keywords from the job posting",
                "Keep your resume to 1-2 pages",
                "Proofread carefully for errors",
                "Use a professional email address"
            ]
        }
