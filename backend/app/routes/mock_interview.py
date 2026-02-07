"""
Mock Interview Routes Module.
Handles API endpoints for voice-based mock interview feature.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import parser, ats_engine, mock_interview
from app.routes.resume import get_uploaded_file

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models ==============

class StartInterviewRequest(BaseModel):
    """Request model for starting an interview."""
    file_id: str
    role: str  # DevOps, Backend, Cloud, General IT


class StartInterviewResponse(BaseModel):
    """Response model for starting an interview."""
    session_id: str
    question: str
    question_index: int
    total_questions: int
    role: str


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    session_id: str
    answer_text: str


class SubmitAnswerResponse(BaseModel):
    """Response model for answer submission."""
    feedback: str
    score: int
    strengths: list
    missing_points: list
    improvement_tip: str
    next_question: Optional[str]
    question_index: int
    is_complete: bool


class InterviewReportResponse(BaseModel):
    """Response model for interview report."""
    session_id: str
    role: str
    status: str
    final_score: float
    performance_level: str
    summary: str
    questions_answered: int
    qa_history: list


# ============== API Endpoints ==============

@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new mock interview session.
    
    - **file_id**: ID of uploaded resume (from /upload_resume)
    - **role**: Target role (DevOps, Backend, Cloud, General IT)
    
    Returns session_id and first interview question.
    """
    try:
        # Validate role
        if request.role not in mock_interview.SUPPORTED_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Supported: {', '.join(mock_interview.SUPPORTED_ROLES)}"
            )
        
        # Get uploaded resume
        file_path = get_uploaded_file(request.file_id)
        
        # Extract text from resume
        resume_text = parser.extract_text(file_path)
        resume_text = parser.clean_text(resume_text)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from resume")
        
        # Create interview session
        session = mock_interview.create_session(
            file_id=request.file_id,
            role=request.role,
            resume_text=resume_text
        )
        
        logger.info(f"Started interview session {session.session_id} for role {request.role}")
        
        return StartInterviewResponse(
            session_id=session.session_id,
            question=session.questions[0],
            question_index=0,
            total_questions=len(session.questions),
            role=session.role
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@router.post("/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer for the current interview question.
    
    - **session_id**: Interview session ID from /mock/start
    - **answer_text**: Transcribed answer from speech or typed input
    
    Returns feedback, score, and next question (if any).
    """
    try:
        # Validate session exists
        session = mock_interview.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status == "completed":
            raise HTTPException(status_code=400, detail="Interview already completed")
        
        # Submit answer and get evaluation
        result = mock_interview.submit_answer(
            session_id=request.session_id,
            answer_text=request.answer_text
        )
        
        logger.info(f"Answer submitted for session {request.session_id}, score: {result['score']}")
        
        return SubmitAnswerResponse(
            feedback=result["feedback"],
            score=result["score"],
            strengths=result["strengths"],
            missing_points=result["missing_points"],
            improvement_tip=result["improvement_tip"],
            next_question=result["next_question"],
            question_index=result["question_index"],
            is_complete=result["is_complete"]
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")


@router.get("/report", response_model=InterviewReportResponse)
async def get_interview_report(session_id: str):
    """
    Get the complete interview report.
    
    - **session_id**: Interview session ID
    
    Returns full interview summary with scores and Q&A history.
    """
    try:
        # Validate session exists
        session = mock_interview.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get full report
        report = mock_interview.get_report(session_id)
        
        logger.info(f"Report requested for session {session_id}")
        
        return InterviewReportResponse(**report)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/roles")
async def get_supported_roles():
    """Get list of supported interview roles."""
    return {"roles": mock_interview.SUPPORTED_ROLES}
