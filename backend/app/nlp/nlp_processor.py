import re
import datetime
from typing import Dict, Any, List, Optional
from .skill_matcher import extract_skills_from_text

# Regex patterns for contact information
EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(?:(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4})'

# Section Header keywords
SECTION_HEADERS = {
    "experience": ["work experience", "experience", "employment history", "professional experience", "work history"],
    "education": ["education", "academic background", "qualifications", "academic credentials"],
    "skills": ["skills", "technical skills", "technologies", "core competencies", "skills & tools", "proficiencies"],
    "projects": ["projects", "personal projects", "academic projects", "key projects"],
    "certifications": ["certifications", "certificates", "licenses", "courses"],
    "summary": ["summary", "professional summary", "about me", "profile", "objective"]
}

# Degree keywords
DEGREE_PATTERNS = [
    r"\bph\.?d\.?\b",
    r"\bdoctor(?:ate)?\b",
    r"\bm\.?s\.?\b",
    r"\bm\.?tech\b",
    r"\bm\.?b\.?a\.?\b",
    r"\bmaster(?:'s)?\b",
    r"\bb\.?s\.?\b",
    r"\bb\.?tech\b",
    r"\bb\.?e\.?\b",
    r"\bbachelor(?:'s)?\b",
    r"\bassociate(?:'s)?\b",
    r"\bdiploma\b"
]

def clean_text(raw_text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not raw_text:
        return ""
    # Replace non-breaking spaces and irregular whitespace
    text = re.sub(r'[\r\t\f\v]', ' ', raw_text)
    # Remove null bytes or control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_email(text: str) -> Optional[str]:
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    match = re.search(PHONE_REGEX, text)
    if match:
        phone = match.group(0).strip()
        # Ensure it has at least 7 digits to avoid matching random dates or numbers
        if len(re.findall(r'\d', phone)) >= 7:
            return phone
    return None

def extract_candidate_name(text: str, filename: str = "") -> str:
    """
    Heuristic candidate name extractor:
    1. Check top lines of the resume before contacts
    2. Check filename if text is inconclusive
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    skip_keywords = ["resume", "curriculum vitae", "cv", "page", "summary", "profile", "objective", "experience", "education", "skills", "contact"]
    
    for line in lines[:6]:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        # Ignore lines with email, phone, or section headers
        if re.search(EMAIL_REGEX, line_clean) or re.search(PHONE_REGEX, line_clean):
            continue
        if any(h in line_lower for h in skip_keywords):
            continue
            
        words = line_clean.split()
        if 1 <= len(words) <= 4:
            # Check if all words are letters or valid name punctuation (e.g. Dr., St., O'Connor, etc.)
            clean_words = [w.replace('.', '').replace("'", '').replace('-', '') for w in words]
            if all(w.isalpha() for w in clean_words):
                return line_clean.title()

    # Fallback to filename
    clean_fn = re.sub(r'[-_]', ' ', filename.rsplit('.', 1)[0])
    clean_fn = re.sub(r'(?i)\b(resume|cv|updated|profile|final|sample)\b', '', clean_fn).strip()
    if clean_fn:
        return clean_fn.title()

    return "Anonymous Candidate"

    return "Anonymous Candidate"

def extract_experience_years(text: str) -> float:
    """
    Compute total years of experience using:
    1. Explicit mentions (e.g., '5+ years of experience', '3.5 years in software')
    2. Date range timeline parsing (e.g. '2018 - 2023', 'Jan 2020 - Present')
    """
    current_year = datetime.datetime.now().year
    
    # 1. Direct regex for explicit experience statements
    explicit_patterns = [
        r'(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience',
        r'experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)',
        r'over\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)',
    ]
    for pattern in explicit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0.0 < val <= 40.0:
                    return round(val, 1)
            except Exception:
                pass

    # 2. Date ranges scanning
    # Matches formats like: 2018 - 2022, 2019 - Present, Jan 2021 to Current, 06/2017 - 08/2021
    date_range_pattern = r'\b(19\d\d|20\d\d)\s*(?:[-–—]|to)\s*(19\d\d|20\d\d|present|current|now)\b'
    matches = re.findall(date_range_pattern, text, re.IGNORECASE)
    
    ranges = []
    for start_str, end_str in matches:
        try:
            start = int(start_str)
            if end_str.lower() in ["present", "current", "now"]:
                end = current_year
            else:
                end = int(end_str)
            
            if 1970 <= start <= current_year and start <= end <= current_year + 1:
                ranges.append((start, end))
        except Exception:
            continue

    if ranges:
        # Merge overlapping intervals
        ranges.sort(key=lambda x: x[0])
        merged = [ranges[0]]
        for current in ranges[1:]:
            prev_start, prev_end = merged[-1]
            if current[0] <= prev_end:
                merged[-1] = (prev_start, max(prev_end, current[1]))
            else:
                merged.append(current)
                
        total_span = sum(end - start for start, end in merged)
        if 0 < total_span <= 40:
            return float(total_span)

    return 0.0

def extract_education(text: str) -> List[str]:
    """Identify education degrees and credentials."""
    found_degrees = []
    for pattern in DEGREE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            found_degrees.append(match.group(0).upper())
    return list(set(found_degrees))

def segment_sections(text: str) -> Dict[str, str]:
    """Segment resume into major sections."""
    lines = text.split('\n')
    sections = {sec: [] for sec in SECTION_HEADERS}
    sections["general"] = []
    
    current_sec = "general"
    for line in lines:
        l_lower = line.strip().lower()
        matched_header = False
        for sec, keywords in SECTION_HEADERS.items():
            if any(l_lower == kw or l_lower.startswith(f"{kw}:") or l_lower == f"## {kw}" for kw in keywords):
                current_sec = sec
                matched_header = True
                break
        if not matched_header:
            sections[current_sec].append(line)
            
    return {k: "\n".join(v).strip() for k, v in sections.items() if v}

def process_resume_nlp(raw_text: str, filename: str = "") -> Dict[str, Any]:
    """
    Main NLP processing pipeline for extracted resume text.
    """
    clean = clean_text(raw_text)
    email = extract_email(clean)
    phone = extract_phone(clean)
    name = extract_candidate_name(clean, filename)
    experience_years = extract_experience_years(clean)
    skills = extract_skills_from_text(clean)
    education = extract_education(clean)
    sections = segment_sections(clean)

    return {
        "candidate_name": name,
        "email": email,
        "phone": phone,
        "experience_years": experience_years,
        "skills": skills,
        "education": education,
        "sections": sections,
        "clean_text": clean
    }
