"""
AI Service Module.
Integrates with Groq API for AI-powered resume improvements.
Outputs clean text without markdown formatting.
Optimized for concise, action-verb-driven content.
"""

import re
import logging
from typing import Dict, List, Optional

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Initialize Groq client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    logger.warning("GROQ_API_KEY not set. AI features will be disabled.")

# Strong action verbs for prompts
ACTION_VERBS = [
    'Achieved', 'Architected', 'Automated', 'Built', 'Collaborated',
    'Configured', 'Created', 'Delivered', 'Deployed', 'Designed',
    'Developed', 'Drove', 'Enhanced', 'Established', 'Executed',
    'Implemented', 'Improved', 'Increased', 'Integrated', 'Launched',
    'Led', 'Managed', 'Mentored', 'Migrated', 'Optimized',
    'Orchestrated', 'Reduced', 'Refactored', 'Resolved', 'Scaled',
    'Spearheaded', 'Streamlined', 'Transformed', 'Upgraded'
]


def clean_ai_output(text: str) -> str:
    """Remove markdown formatting from AI output."""
    if not text:
        return ""
    
    # Remove bold/italic markdown
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```\w*\n?', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def _call_groq(messages: List[Dict], max_tokens: int = 2000) -> Optional[str]:
    """Make a call to Groq API."""
    if not client:
        raise ValueError("Groq API key not configured. Set GROQ_API_KEY in .env file.")
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        result = response.choices[0].message.content
        return clean_ai_output(result)
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        raise ValueError(f"AI service error: {str(e)}")


def improve_bullet_points(bullet_points: List[str]) -> List[str]:
    """Improve bullet points with strong action verbs and metrics."""
    if not bullet_points:
        return []
    
    bullets_text = "\n".join([f"- {bp}" for bp in bullet_points])
    
    prompt = f"""Improve these resume bullet points for maximum ATS impact:

{bullets_text}

STRICT RULES:
1. Start EVERY bullet with one of these action verbs: {', '.join(ACTION_VERBS[:15])}
2. Include metrics (%, numbers, $) wherever possible
3. Keep each bullet to ONE line (max 15 words)
4. Focus on ACHIEVEMENTS, not responsibilities
5. Maximum 4 bullets total - pick the strongest ones

OUTPUT FORMAT:
- [improved bullet 1]
- [improved bullet 2]
- [improved bullet 3]
- [improved bullet 4]

NO markdown. NO explanations. Just the improved bullets."""

    messages = [
        {"role": "system", "content": "You are an expert resume writer. Output plain text only. Be extremely concise."},
        {"role": "user", "content": prompt}
    ]
    
    response = _call_groq(messages)
    
    if response:
        improved = []
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                clean_line = line.lstrip('-•').strip()
                if clean_line and len(improved) < 4:
                    improved.append(clean_line)
        return improved if improved else bullet_points[:4]
    
    return bullet_points[:4]


def rewrite_resume_ats_style(resume_text: str) -> str:
    """Rewrite resume in ATS-friendly format optimized for 1-2 pages."""
    
    prompt = f"""Rewrite this resume for ATS systems. Make it CONCISE - must fit 1-2 pages.

ORIGINAL RESUME:
{resume_text}

STRICT REQUIREMENTS:

1. SECTIONS (in this order):
   - Professional Summary (2-3 sentences MAX)
   - Skills (group as: Technical Skills: ..., Soft Skills: ...)
   - Work Experience (max 4 bullets per role)
   - Education (one line per degree, NO coursework)
   - Projects (max 4 bullets per project)
   - Certifications (if any, NO coursework)

2. FORMATTING:
   - Experience format: Job Title | Company | Location | Dates
   - Every bullet MUST start with: {', '.join(ACTION_VERBS[:10])}
   - Include metrics in 50%+ of bullets
   - Maximum 4 bullets per role/project
   - NO duplicate content between Experience and Projects

3. CONTENT:
   - Remove ALL coursework
   - Merge similar skills
   - Technical Skills: programming, tools, technologies
   - Soft Skills: communication, leadership, teamwork

OUTPUT RULES:
- Plain text ONLY (no **, no ##, no markdown)
- Simple dashes (-) for bullets
- Keep it SHORT and IMPACTFUL"""

    messages = [
        {"role": "system", "content": "You are a senior resume writer. Create concise, ATS-optimized resumes. Plain text only. No markdown ever."},
        {"role": "user", "content": prompt}
    ]
    
    return _call_groq(messages, max_tokens=2500)


def get_improvement_suggestions(resume_text: str, ats_score: int) -> List[str]:
    """Generate concise improvement suggestions."""
    
    prompt = f"""Resume ATS score: {ats_score}/100

{resume_text}

Give exactly 5 specific improvement suggestions. Be brief.

FORMAT (plain text, no markdown):
- suggestion 1
- suggestion 2
- suggestion 3
- suggestion 4
- suggestion 5"""

    messages = [
        {"role": "system", "content": "Expert career coach. Brief, actionable advice. No markdown."},
        {"role": "user", "content": prompt}
    ]
    
    response = _call_groq(messages, max_tokens=500)
    
    if response:
        suggestions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                clean_line = line.lstrip('-•*0123456789. ').strip()
                if clean_line and len(suggestions) < 5:
                    suggestions.append(clean_line)
        return suggestions
    
    return []


def match_job_description(resume_text: str, job_description: str) -> Dict:
    """Match resume against job description."""
    
    prompt = f"""RESUME:
{resume_text[:2000]}

JOB:
{job_description[:1500]}

Analyze match. Output EXACTLY this format:

MATCH_PERCENTAGE: [0-100]
MATCHING_KEYWORDS: [keyword1, keyword2, keyword3]
MISSING_KEYWORDS: [keyword1, keyword2, keyword3]
SUGGESTIONS:
- suggestion 1
- suggestion 2
- suggestion 3

No markdown. Keep keywords to top 5-8 each."""

    messages = [
        {"role": "system", "content": "ATS analyst. Concise output. No markdown."},
        {"role": "user", "content": prompt}
    ]
    
    response = _call_groq(messages, max_tokens=600)
    
    if response:
        result = {
            "match_percentage": 0,
            "matching_keywords": [],
            "missing_keywords": [],
            "suggestions": []
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('MATCH_PERCENTAGE:'):
                try:
                    pct = line.split(':')[1].strip()
                    result['match_percentage'] = int(''.join(filter(str.isdigit, pct[:3])))
                except:
                    pass
            elif line.startswith('MATCHING_KEYWORDS:'):
                kw = line.split(':', 1)[1].strip() if ':' in line else ''
                result['matching_keywords'] = [k.strip() for k in kw.split(',') if k.strip()][:8]
            elif line.startswith('MISSING_KEYWORDS:'):
                kw = line.split(':', 1)[1].strip() if ':' in line else ''
                result['missing_keywords'] = [k.strip() for k in kw.split(',') if k.strip()][:8]
            elif line.startswith('SUGGESTIONS:'):
                current_section = 'suggestions'
            elif current_section == 'suggestions' and line.startswith('-'):
                result['suggestions'].append(line.lstrip('- ').strip())
        
        return result
    
    return {
        "match_percentage": 0,
        "matching_keywords": [],
        "missing_keywords": [],
        "suggestions": ["Analysis failed. Please try again."]
    }


def generate_resume_tips() -> List[str]:
    """Generate resume tips."""
    return [
        "Start every bullet point with a strong action verb (Led, Developed, Achieved)",
        "Include quantifiable metrics in at least 50% of your bullets",
        "Keep your resume to 1-2 pages maximum",
        "Use standard section headings: Work Experience, Education, Skills",
        "Group skills into Technical Skills and Soft Skills categories",
        "Remove coursework unless you're a recent graduate",
        "Limit to 3-4 bullet points per role for readability",
        "Avoid tables, graphics, and multi-column layouts",
        "Tailor keywords to match the job description",
        "Use a clean, simple format with consistent spacing"
    ]
