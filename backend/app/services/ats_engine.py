"""
ATS Engine Module.
Handles section detection and ATS scoring using NLP and rule-based approaches.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import spacy

logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


class SectionType(str, Enum):
    """Resume section types."""
    NAME = "name"
    CONTACT = "contact"
    SUMMARY = "summary"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    UNKNOWN = "unknown"


@dataclass
class Section:
    """Represents a detected resume section."""
    type: SectionType
    title: str
    content: str
    start_line: int
    end_line: int


@dataclass
class ATSScore:
    """ATS scoring result."""
    total_score: int
    breakdown: Dict[str, int]
    issues: List[str]
    suggestions: List[str]


# Section heading patterns
SECTION_PATTERNS = {
    SectionType.SUMMARY: [
        r'\b(professional\s+)?summary\b',
        r'\b(career\s+)?objective\b',
        r'\bprofile\b',
        r'\babout\s+me\b',
    ],
    SectionType.SKILLS: [
        r'\b(technical\s+)?skills\b',
        r'\bcore\s+competencies\b',
        r'\bexpertise\b',
        r'\bproficiencies\b',
    ],
    SectionType.EXPERIENCE: [
        r'\b(work\s+)?experience\b',
        r'\bemployment(\s+history)?\b',
        r'\bprofessional\s+experience\b',
        r'\bwork\s+history\b',
    ],
    SectionType.EDUCATION: [
        r'\beducation(al)?\s*(background)?\b',
        r'\bacademic\s+(background|qualifications)\b',
        r'\bqualifications\b',
    ],
    SectionType.PROJECTS: [
        r'\bprojects?\b',
        r'\bportfolio\b',
        r'\bkey\s+projects\b',
    ],
    SectionType.CERTIFICATIONS: [
        r'\bcertification(s)?\b',
        r'\blicense(s)?\b',
        r'\baccreditation(s)?\b',
        r'\btraining\b',
    ],
    SectionType.CONTACT: [
        r'\bcontact(\s+information)?\b',
        r'\bcontact\s+details\b',
    ],
}

# Standard ATS-friendly headings
STANDARD_HEADINGS = {
    SectionType.SUMMARY: "Professional Summary",
    SectionType.SKILLS: "Skills",
    SectionType.EXPERIENCE: "Work Experience",
    SectionType.EDUCATION: "Education",
    SectionType.PROJECTS: "Projects",
    SectionType.CERTIFICATIONS: "Certifications",
    SectionType.CONTACT: "Contact Information",
}

# Common skill keywords for keyword density check
COMMON_SKILLS = [
    "python", "java", "javascript", "sql", "html", "css", "react", "node",
    "aws", "docker", "kubernetes", "git", "agile", "scrum", "leadership",
    "communication", "problem-solving", "teamwork", "management", "analysis",
    "excel", "powerpoint", "word", "project management", "data analysis",
]


def detect_name(text: str) -> Optional[str]:
    """
    Detect the person's name from the resume text.
    Usually the first line or uses NLP entity recognition.
    """
    lines = text.strip().split('\n')
    
    # First, try NLP-based detection
    if nlp:
        doc = nlp(text[:500])  # Check first 500 chars
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
    
    # Fallback: assume first non-empty line is name
    for line in lines[:5]:
        line = line.strip()
        # Skip lines that look like headers or contact info
        if line and not re.search(r'[@|:•\-–—]', line) and len(line.split()) <= 4:
            return line
    
    return None


def detect_contact(text: str) -> Dict[str, str]:
    """
    Detect contact information from resume text.
    """
    contact = {}
    
    # Email pattern
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        contact['email'] = email_match.group()
    
    # Phone pattern (various formats)
    phone_match = re.search(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{3,4}', text)
    if phone_match:
        contact['phone'] = phone_match.group()
    
    # LinkedIn pattern
    linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    if linkedin_match:
        contact['linkedin'] = linkedin_match.group()
    
    # GitHub pattern
    github_match = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
    if github_match:
        contact['github'] = github_match.group()
    
    return contact


def detect_sections(text: str) -> Dict[str, Section]:
    """
    Detect and extract resume sections using regex patterns and NLP.
    
    Args:
        text: Full resume text
        
    Returns:
        Dictionary mapping section types to Section objects
    """
    sections = {}
    lines = text.split('\n')
    
    # Track section boundaries
    section_starts = []
    
    # Find section headings
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        
        for section_type, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_clean):
                    section_starts.append((i, section_type, line.strip()))
                    break
    
    # Sort by line number
    section_starts.sort(key=lambda x: x[0])
    
    # Extract section contents
    for idx, (start_line, section_type, title) in enumerate(section_starts):
        # End line is either next section or end of document
        if idx + 1 < len(section_starts):
            end_line = section_starts[idx + 1][0] - 1
        else:
            end_line = len(lines) - 1
        
        # Extract content
        content = '\n'.join(lines[start_line + 1:end_line + 1]).strip()
        
        sections[section_type.value] = Section(
            type=section_type,
            title=title,
            content=content,
            start_line=start_line,
            end_line=end_line
        )
    
    # Detect name (usually before first section)
    name = detect_name(text)
    if name:
        sections['name'] = Section(
            type=SectionType.NAME,
            title="Name",
            content=name,
            start_line=0,
            end_line=0
        )
    
    # Detect contact info
    contact = detect_contact(text)
    if contact:
        sections['contact'] = Section(
            type=SectionType.CONTACT,
            title="Contact",
            content=str(contact),
            start_line=0,
            end_line=5
        )
    
    return sections


def check_bullet_formatting(text: str) -> Tuple[int, List[str]]:
    """
    Check bullet point formatting quality.
    
    Returns:
        Tuple of (score out of 20, list of issues)
    """
    issues = []
    score = 20
    
    lines = text.split('\n')
    bullet_lines = [l for l in lines if re.match(r'^\s*[•\-\*\→>]\s*', l)]
    
    if len(bullet_lines) < 5:
        issues.append("Too few bullet points. Use bullets to highlight achievements.")
        score -= 5
    
    # Check for action verbs at start of bullets
    action_verbs = [
        'achieved', 'accomplished', 'built', 'created', 'delivered', 'developed',
        'designed', 'established', 'generated', 'implemented', 'improved', 'increased',
        'launched', 'led', 'managed', 'optimized', 'reduced', 'resolved', 'streamlined'
    ]
    
    weak_starts = 0
    for bullet in bullet_lines:
        # Remove bullet character and get first word
        clean = re.sub(r'^[\s•\-\*\→>]+', '', bullet).strip()
        first_word = clean.split()[0].lower() if clean.split() else ""
        
        if first_word and first_word not in action_verbs:
            weak_starts += 1
    
    if weak_starts > len(bullet_lines) * 0.5 and bullet_lines:
        issues.append("Start bullet points with strong action verbs (e.g., 'Developed', 'Led', 'Achieved').")
        score -= 5
    
    # Check for quantifiable metrics
    metrics_pattern = r'\d+[%\$]?|\$\d+'
    bullets_with_metrics = sum(1 for b in bullet_lines if re.search(metrics_pattern, b))
    
    if bullets_with_metrics < len(bullet_lines) * 0.3 and bullet_lines:
        issues.append("Add quantifiable metrics to more bullet points (e.g., 'Increased sales by 25%').")
        score -= 5
    
    return max(0, score), issues


def check_keyword_density(text: str) -> Tuple[int, List[str]]:
    """
    Check keyword density and relevance.
    
    Returns:
        Tuple of (score out of 20, list of issues)
    """
    issues = []
    score = 20
    text_lower = text.lower()
    
    # Count skill keywords found
    found_skills = [skill for skill in COMMON_SKILLS if skill in text_lower]
    
    if len(found_skills) < 5:
        issues.append("Low keyword density. Include more relevant industry keywords and skills.")
        score -= 10
    elif len(found_skills) < 10:
        issues.append("Consider adding more technical and soft skills keywords.")
        score -= 5
    
    return max(0, score), issues


def check_formatting_issues(text: str) -> Tuple[int, List[str]]:
    """
    Check for ATS-unfriendly formatting issues.
    
    Returns:
        Tuple of (score out of 20, list of issues)
    """
    issues = []
    score = 20
    
    # Check for potential tables (detected by pipe characters or tab-separated content)
    if text.count('|') > 5 or text.count('\t') > 10:
        issues.append("Detected potential tables. ATS may not parse tables correctly. Use simple formatting.")
        score -= 10
    
    # Check for special characters that might be icons
    icon_patterns = [r'[★☆●○◆◇■□▪▫►▻]', r'[\u2600-\u26FF]', r'[\u2700-\u27BF]']
    for pattern in icon_patterns:
        if re.search(pattern, text):
            issues.append("Detected special characters/icons. Use standard bullet points (•, -, *).")
            score -= 5
            break
    
    # Check for very short lines (might indicate multiple columns)
    lines = text.split('\n')
    short_lines = sum(1 for l in lines if 0 < len(l.strip()) < 30)
    if short_lines > len(lines) * 0.4 and len(lines) > 20:
        issues.append("Many short lines detected. Avoid multi-column layouts for better ATS parsing.")
        score -= 5
    
    return max(0, score), issues


def check_section_presence(sections: Dict[str, Section]) -> Tuple[int, List[str]]:
    """
    Check presence of essential resume sections.
    
    Returns:
        Tuple of (score out of 25, list of issues)
    """
    issues = []
    score = 25
    
    essential_sections = ['experience', 'education', 'skills']
    recommended_sections = ['summary', 'contact']
    
    for section in essential_sections:
        if section not in sections:
            issues.append(f"Missing essential section: {section.title()}. Add this section for better ATS parsing.")
            score -= 7
    
    for section in recommended_sections:
        if section not in sections:
            issues.append(f"Missing recommended section: {section.title()}.")
            score -= 3
    
    return max(0, score), issues


def check_heading_standards(sections: Dict[str, Section]) -> Tuple[int, List[str]]:
    """
    Check if section headings follow ATS-friendly standards.
    
    Returns:
        Tuple of (score out of 15, list of issues)
    """
    issues = []
    score = 15
    
    for section_key, section in sections.items():
        if section.type in STANDARD_HEADINGS:
            standard = STANDARD_HEADINGS[section.type]
            if section.title.lower() != standard.lower():
                # Non-standard but acceptable variations don't penalize much
                score -= 1
    
    # Check for creative/non-standard headings
    creative_patterns = [
        r'what\s+i\s+do',
        r'my\s+journey',
        r'where\s+i\'ve\s+been',
        r'things\s+i\s+know',
    ]
    
    full_text = ' '.join(s.title.lower() for s in sections.values())
    for pattern in creative_patterns:
        if re.search(pattern, full_text):
            issues.append("Use standard section headings (e.g., 'Work Experience' instead of creative alternatives).")
            score -= 5
            break
    
    return max(0, score), issues


def calculate_ats_score(text: str) -> ATSScore:
    """
    Calculate comprehensive ATS score for a resume.
    
    Args:
        text: Full resume text
        
    Returns:
        ATSScore object with total score, breakdown, issues, and suggestions
    """
    all_issues = []
    all_suggestions = []
    breakdown = {}
    
    # 1. Detect sections
    sections = detect_sections(text)
    
    # 2. Check section presence (25 points)
    section_score, section_issues = check_section_presence(sections)
    breakdown['section_presence'] = section_score
    all_issues.extend(section_issues)
    
    # 3. Check heading standards (15 points)
    heading_score, heading_issues = check_heading_standards(sections)
    breakdown['heading_standards'] = heading_score
    all_issues.extend(heading_issues)
    
    # 4. Check keyword density (20 points)
    keyword_score, keyword_issues = check_keyword_density(text)
    breakdown['keyword_density'] = keyword_score
    all_issues.extend(keyword_issues)
    
    # 5. Check bullet formatting (20 points)
    bullet_score, bullet_issues = check_bullet_formatting(text)
    breakdown['bullet_formatting'] = bullet_score
    all_issues.extend(bullet_issues)
    
    # 6. Check formatting issues (20 points)
    format_score, format_issues = check_formatting_issues(text)
    breakdown['formatting'] = format_score
    all_issues.extend(format_issues)
    
    # Calculate total score
    total_score = sum(breakdown.values())
    
    # Generate suggestions based on score
    if total_score < 50:
        all_suggestions.append("Your resume needs significant improvements for ATS compatibility.")
    elif total_score < 70:
        all_suggestions.append("Your resume is moderately ATS-friendly. Focus on the issues listed above.")
    elif total_score < 85:
        all_suggestions.append("Good job! Your resume is fairly ATS-compatible. Minor tweaks can help further.")
    else:
        all_suggestions.append("Excellent! Your resume is well-optimized for ATS systems.")
    
    return ATSScore(
        total_score=total_score,
        breakdown=breakdown,
        issues=all_issues,
        suggestions=all_suggestions
    )


def get_structured_resume(text: str) -> Dict:
    """
    Parse resume text into structured JSON format.
    
    Args:
        text: Full resume text
        
    Returns:
        Dictionary with structured resume data
    """
    sections = detect_sections(text)
    name = detect_name(text)
    contact = detect_contact(text)
    
    structured = {
        "name": name,
        "contact": contact,
        "sections": {}
    }
    
    for key, section in sections.items():
        if key not in ['name', 'contact']:
            structured["sections"][key] = {
                "title": section.title,
                "content": section.content
            }
    
    return structured
