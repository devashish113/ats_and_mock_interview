"""
Mock Interview Service Module.
Provides AI-powered mock interview functionality using Groq API.
Voice features use browser Web Speech API (handled in frontend).
"""

import logging
import uuid
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Initialize Groq client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    logger.warning("GROQ_API_KEY not set. Mock interview features will be disabled.")


# ============== Data Classes ==============

@dataclass
class QuestionEvaluation:
    """Stores evaluation for a single answer."""
    question: str
    answer: str
    score: int
    strengths: List[str]
    missing_points: List[str]
    improvement_tip: str


@dataclass
class InterviewSession:
    """Stores interview session state."""
    session_id: str
    file_id: str
    role: str
    resume_summary: str
    questions: List[str] = field(default_factory=list)
    current_index: int = 0
    evaluations: List[QuestionEvaluation] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, completed
    created_at: datetime = field(default_factory=datetime.now)


# In-memory session storage
INTERVIEW_SESSIONS: Dict[str, InterviewSession] = {}


# ============== Helper Functions ==============

def _call_groq(messages: List[Dict], max_tokens: int = 1500) -> Optional[str]:
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
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        raise ValueError(f"AI service error: {str(e)}")


def _parse_json_response(response: str) -> dict:
    """Parse JSON from AI response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0]
    elif "```" in response:
        response = response.split("```")[1].split("```")[0]
    
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON: {response[:200]}")
        return {}


# ============== Core Functions ==============

def generate_questions(resume_text: str, role: str, count: int = 5) -> List[str]:
    """
    Generate interview questions based on resume and target role.
    
    Args:
        resume_text: Extracted text from resume
        role: Target role (any role provided by user)
        count: Number of questions to generate
        
    Returns:
        List of interview questions (guaranteed to be strings)
    """
    # Use the role as provided by user (no restriction)
    if not role or not role.strip():
        role = "General IT"
    
    prompt = f"""You are a senior technical interviewer conducting a {role} interview.

CANDIDATE RESUME:
{resume_text[:3000]}

Generate exactly {count} technical interview questions for this {role} position.

REQUIREMENTS:
1. Base questions on the candidate's actual skills and experience from their resume
2. Include a mix of:
   - Technical knowledge questions
   - Problem-solving scenarios
   - Experience-based behavioral questions
3. Start with easier questions, gradually increase difficulty
4. Make questions specific to {role} role
5. Questions should be answerable in 1-2 minutes verbally

CRITICAL: Output ONLY a JSON object with an array of question STRINGS. Each question must be a plain text string, NOT an object.

OUTPUT FORMAT (JSON only, no markdown):
{{"questions": ["What is your experience with X?", "How would you handle Y?", "Describe a time when Z", "Explain the difference between A and B", "What approach would you take for C?"]}}
"""

    messages = [
        {"role": "system", "content": "You are a technical interviewer. Output valid JSON only. Questions must be plain text strings."},
        {"role": "user", "content": prompt}
    ]
    
    response = _call_groq(messages, max_tokens=800)
    
    if response:
        parsed = _parse_json_response(response)
        questions = parsed.get("questions", [])
        
        # Ensure all questions are strings (not dicts or other types)
        valid_questions = []
        for q in questions:
            if isinstance(q, str) and q.strip():
                valid_questions.append(q.strip())
            elif isinstance(q, dict):
                # If AI returned a dict, try to extract text from common keys
                text = q.get("question") or q.get("text") or q.get("content") or str(q)
                if isinstance(text, str) and text.strip():
                    valid_questions.append(text.strip())
        
        if len(valid_questions) >= count:
            return valid_questions[:count]
    
    # Fallback questions based on role keywords
    role_lower = role.lower()
    
    if any(kw in role_lower for kw in ["devops", "sre", "infrastructure", "platform"]):
        fallback = [
            "Walk me through your experience with CI/CD pipelines.",
            "How would you handle a production deployment issue?",
            "Describe your containerization experience with Docker or Kubernetes.",
            "How do you approach infrastructure as code?",
            "Tell me about a challenging DevOps problem you solved."
        ]
    elif any(kw in role_lower for kw in ["backend", "server", "api", "python", "java", "node"]):
        fallback = [
            "Describe your experience with backend frameworks and databases.",
            "How do you ensure API security and performance?",
            "Walk me through your approach to database design.",
            "How do you handle error handling and logging?",
            "Tell me about a complex backend feature you implemented."
        ]
    elif any(kw in role_lower for kw in ["cloud", "aws", "azure", "gcp"]):
        fallback = [
            "Describe your experience with cloud platforms like AWS, Azure, or GCP.",
            "How would you design a scalable cloud architecture?",
            "Explain your approach to cloud security and compliance.",
            "How do you optimize cloud costs?",
            "Tell me about a cloud migration project you worked on."
        ]
    elif any(kw in role_lower for kw in ["frontend", "react", "angular", "vue", "javascript", "ui", "ux"]):
        fallback = [
            "Tell me about your experience with modern frontend frameworks.",
            "How do you approach responsive design and cross-browser compatibility?",
            "Describe your experience with state management in applications.",
            "How do you optimize frontend performance?",
            "Tell me about a challenging UI feature you implemented."
        ]
    elif any(kw in role_lower for kw in ["data", "machine learning", "ml", "ai", "analytics"]):
        fallback = [
            "Describe your experience with data processing and analysis.",
            "How do you approach feature engineering for ML models?",
            "Walk me through a machine learning project you've worked on.",
            "How do you handle data quality and validation?",
            "Tell me about your experience with model deployment."
        ]
    else:
        fallback = [
            f"Tell me about your technical background relevant to {role}.",
            "How do you approach learning new technologies?",
            "Describe a challenging technical problem you solved.",
            "How do you collaborate with team members on technical projects?",
            f"What specific skills make you a good fit for a {role} position?"
        ]
    
    return fallback[:count]


def evaluate_answer(question: str, answer: str) -> QuestionEvaluation:
    """
    Evaluate candidate's answer to an interview question.
    
    Args:
        question: The interview question asked
        answer: Candidate's verbal answer (transcribed)
        
    Returns:
        QuestionEvaluation with score, strengths, missing points, and tip
    """
    if not answer or len(answer.strip()) < 10:
        return QuestionEvaluation(
            question=question,
            answer=answer,
            score=2,
            strengths=["Attempted to answer"],
            missing_points=["Answer was too brief", "Needs more detail and examples"],
            improvement_tip="Provide more detailed responses with specific examples from your experience."
        )
    
    prompt = f"""Evaluate this interview answer:

QUESTION: {question}

CANDIDATE'S ANSWER: {answer}

Evaluate the answer and provide:
1. Score (1-10 where 1=poor, 5=average, 10=excellent)
2. 2-3 strengths (what candidate did well)
3. 2-3 missing points (what could be improved)
4. One specific improvement tip

OUTPUT FORMAT (JSON only):
{{
  "score": 7,
  "strengths": ["strength 1", "strength 2"],
  "missing_points": ["missing 1", "missing 2"],
  "improvement_tip": "specific actionable tip"
}}
"""

    messages = [
        {"role": "system", "content": "You are a fair technical interviewer. Evaluate answers objectively. Output valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = _call_groq(messages, max_tokens=500)
    
    if response:
        parsed = _parse_json_response(response)
        if parsed:
            return QuestionEvaluation(
                question=question,
                answer=answer,
                score=min(10, max(1, parsed.get("score", 5))),
                strengths=parsed.get("strengths", ["Answered the question"])[:3],
                missing_points=parsed.get("missing_points", [])[:3],
                improvement_tip=parsed.get("improvement_tip", "Keep practicing your interview skills.")
            )
    
    # Fallback evaluation
    return QuestionEvaluation(
        question=question,
        answer=answer,
        score=5,
        strengths=["Provided a response"],
        missing_points=["Could add more specific examples"],
        improvement_tip="Try to include concrete examples from your experience."
    )


def generate_feedback(evaluation: QuestionEvaluation) -> str:
    """
    Generate spoken feedback from evaluation (for TTS).
    
    Args:
        evaluation: The question evaluation
        
    Returns:
        Natural-sounding feedback text for speech synthesis
    """
    score = evaluation.score
    
    if score >= 8:
        intro = "Excellent answer!"
    elif score >= 6:
        intro = "Good answer."
    elif score >= 4:
        intro = "Okay answer, but there's room for improvement."
    else:
        intro = "This answer needs more work."
    
    # Build feedback
    strengths_text = ""
    if evaluation.strengths:
        strengths_text = f" You did well on: {', '.join(evaluation.strengths[:2])}."
    
    tip_text = f" Tip: {evaluation.improvement_tip}" if evaluation.improvement_tip else ""
    
    return f"{intro} Your score is {score} out of 10.{strengths_text}{tip_text}"


def compute_final_score(evaluations: List[QuestionEvaluation]) -> dict:
    """
    Compute overall interview score and summary.
    
    Args:
        evaluations: List of all question evaluations
        
    Returns:
        Dict with final_score, performance_level, and summary
    """
    if not evaluations:
        return {
            "final_score": 0,
            "performance_level": "Not Completed",
            "summary": "No questions were answered."
        }
    
    total_score = sum(e.score for e in evaluations)
    final_score = round(total_score / len(evaluations), 1)
    
    # Determine performance level
    if final_score >= 8:
        level = "Excellent"
        summary = "Outstanding interview performance! You demonstrated strong technical knowledge and communication skills."
    elif final_score >= 6:
        level = "Good"
        summary = "Good interview performance. You showed solid understanding with some areas for improvement."
    elif final_score >= 4:
        level = "Average"
        summary = "Average performance. Focus on providing more specific examples and technical depth."
    else:
        level = "Needs Improvement"
        summary = "More preparation needed. Practice explaining your experience clearly with concrete examples."
    
    return {
        "final_score": final_score,
        "performance_level": level,
        "summary": summary,
        "questions_answered": len(evaluations),
        "average_score": final_score
    }


# ============== Session Management ==============

def create_session(file_id: str, role: str, resume_text: str) -> InterviewSession:
    """Create a new interview session."""
    session_id = str(uuid.uuid4())[:12]
    
    # Generate questions for this session
    questions = generate_questions(resume_text, role)
    
    session = InterviewSession(
        session_id=session_id,
        file_id=file_id,
        role=role,
        resume_summary=resume_text[:500],
        questions=questions,
        current_index=0,
        evaluations=[],
        status="in_progress"
    )
    
    INTERVIEW_SESSIONS[session_id] = session
    logger.info(f"Created interview session {session_id} for role {role}")
    
    return session


def get_session(session_id: str) -> Optional[InterviewSession]:
    """Get an existing interview session."""
    return INTERVIEW_SESSIONS.get(session_id)


def submit_answer(session_id: str, answer_text: str) -> dict:
    """
    Submit an answer for the current question.
    
    Returns dict with evaluation, feedback, and next question (if any).
    """
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    
    if session.status == "completed":
        raise ValueError("Interview already completed")
    
    current_question = session.questions[session.current_index]
    
    # Evaluate the answer
    evaluation = evaluate_answer(current_question, answer_text)
    session.evaluations.append(evaluation)
    
    # Generate spoken feedback
    feedback = generate_feedback(evaluation)
    
    # Move to next question
    session.current_index += 1
    
    # Check if interview is complete
    is_complete = session.current_index >= len(session.questions)
    next_question = None
    
    if is_complete:
        session.status = "completed"
    else:
        next_question = session.questions[session.current_index]
    
    return {
        "feedback": feedback,
        "score": evaluation.score,
        "strengths": evaluation.strengths,
        "missing_points": evaluation.missing_points,
        "improvement_tip": evaluation.improvement_tip,
        "next_question": next_question,
        "question_index": session.current_index,
        "is_complete": is_complete
    }


def get_report(session_id: str) -> dict:
    """Get the full interview report."""
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    
    final_result = compute_final_score(session.evaluations)
    
    # Build detailed Q&A history
    qa_history = []
    for eval in session.evaluations:
        qa_history.append({
            "question": eval.question,
            "answer": eval.answer,
            "score": eval.score,
            "strengths": eval.strengths,
            "missing_points": eval.missing_points,
            "improvement_tip": eval.improvement_tip
        })
    
    return {
        "session_id": session_id,
        "role": session.role,
        "status": session.status,
        "final_score": final_result["final_score"],
        "performance_level": final_result["performance_level"],
        "summary": final_result["summary"],
        "questions_answered": final_result["questions_answered"],
        "qa_history": qa_history
    }
