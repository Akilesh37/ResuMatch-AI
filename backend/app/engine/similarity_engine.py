import re
import numpy as np
from typing import Dict, Any, List, Optional
from ..nlp.skill_matcher import match_skills

def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vector embeddings."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    cos_sim = float(np.dot(a, b) / (norm_a * norm_b))
    # Bound to [0.0, 1.0] and scale to 100%
    return max(0.0, min(1.0, cos_sim)) * 100.0

def compute_experience_score(candidate_exp: float, required_exp: float) -> float:
    """
    Calculate experience match score (0-100).
    - If candidate meets or exceeds requirement: 100
    - If required is 0: 100
    - If candidate has less experience: graded penalty
    """
    if required_exp <= 0.0:
        return 100.0 if candidate_exp > 0 else 85.0

    if candidate_exp >= required_exp:
        # Bonus for extra experience capped at 100
        return 100.0

    # Graded ratio
    ratio = candidate_exp / required_exp
    return round(ratio * 100.0, 2)

def compute_keyword_score(candidate_text: str, job_text: str) -> float:
    """
    Evaluate domain keyword strength, action verbs, and relevant impact terms.
    """
    high_impact_keywords = [
        "led", "developed", "architected", "built", "implemented", "scaled",
        "optimized", "designed", "deployed", "managed", "collaborated",
        "production", "performance", "pipeline", "automated", "infrastructure"
    ]
    
    cand_lower = candidate_text.lower()
    hits = sum(1 for kw in high_impact_keywords if re.search(rf'\b{kw}\b', cand_lower))
    
    base_score = min(hits * 7.0, 70.0)
    
    # Check overlap with key words in job description
    job_words = set(re.findall(r'\b[a-z]{4,}\b', job_text.lower()))
    stop_words = {"with", "that", "this", "from", "have", "will", "your", "must", "work", "team", "year", "more"}
    meaningful_job_words = job_words - stop_words
    
    if meaningful_job_words:
        overlap = sum(1 for w in meaningful_job_words if re.search(rf'\b{w}\b', cand_lower))
        overlap_score = min((overlap / max(len(meaningful_job_words) * 0.3, 1)) * 30.0, 30.0)
    else:
        overlap_score = 25.0
        
    return round(min(base_score + overlap_score, 100.0), 2)

def evaluate_candidate_match(
    candidate_data: Dict[str, Any],
    candidate_embedding: List[float],
    job_data: Dict[str, Any],
    job_embedding: List[float]
) -> Dict[str, Any]:
    """
    Multi-factor evaluation engine combining semantic, skill, experience, and keyword scores.
    """
    # 1. Semantic Similarity Score
    semantic_score = round(compute_cosine_similarity(candidate_embedding, job_embedding), 2)
    
    # 2. Skill Match Score
    req_skills = job_data.get("required_skills", [])
    pref_skills = job_data.get("preferred_skills", [])
    cand_skills = candidate_data.get("extracted_skills", [])
    
    matched_skills, missing_skills, extra_skills, skill_score = match_skills(
        req_skills, pref_skills, cand_skills
    )
    
    # 3. Experience Score
    cand_exp = float(candidate_data.get("total_experience_years", 0.0))
    req_exp = float(job_data.get("min_experience", 0.0))
    experience_score = round(compute_experience_score(cand_exp, req_exp), 2)
    
    # 4. Keyword & Context Score
    cand_text = candidate_data.get("clean_text", "")
    job_text = job_data.get("description", "")
    keyword_score = round(compute_keyword_score(cand_text, job_text), 2)
    
    # Weights configuration
    w_sem = float(job_data.get("weight_semantic", 0.40))
    w_skl = float(job_data.get("weight_skills", 0.35))
    w_exp = float(job_data.get("weight_experience", 0.15))
    w_kw = float(job_data.get("weight_keywords", 0.10))
    
    # Normalize weights if sum != 1.0
    total_w = w_sem + w_skl + w_exp + w_kw
    if total_w > 0:
        w_sem /= total_w
        w_skl /= total_w
        w_exp /= total_w
        w_kw /= total_w
        
    overall_score = round(
        (semantic_score * w_sem) +
        (skill_score * w_skl) +
        (experience_score * w_exp) +
        (keyword_score * w_kw),
        2
    )
    
    # Status Assignment
    threshold = float(job_data.get("threshold", 50.0))
    if overall_score >= threshold:
        if overall_score >= 80.0 and len(missing_skills) == 0:
            status = "SHORTLISTED"
        else:
            status = "ELIGIBLE"
    elif overall_score >= max(threshold - 15.0, 20.0):
        status = "UNDER_REVIEW"
    else:
        status = "REJECTED"
        
    # Generate human-readable AI explanation
    strengths = []
    weaknesses = []
    
    if semantic_score >= 75.0:
        strengths.append("Strong semantic context alignment with job requirements.")
    if skill_score >= 70.0:
        strengths.append(f"Matched {len(matched_skills)} core technical skills.")
    if cand_exp >= req_exp and req_exp > 0:
        strengths.append(f"Meets experience criteria ({cand_exp} yrs vs {req_exp} yrs required).")
        
    if missing_skills:
        weaknesses.append(f"Missing required skills: {', '.join(missing_skills[:4])}.")
    if cand_exp < req_exp and req_exp > 0:
        weaknesses.append(f"Experience gap: {cand_exp} yrs vs {req_exp} yrs required.")
    if semantic_score < 50.0:
        weaknesses.append("Low overall semantic similarity to the job description.")
        
    explanation = {
        "summary": f"Candidate scored {overall_score}/100 based on hybrid semantic and skill analysis.",
        "strengths": strengths or ["General profile match."],
        "weaknesses": weaknesses or ["No significant gaps identified."],
        "breakdown": {
            "semantic_score": semantic_score,
            "skill_score": skill_score,
            "experience_score": experience_score,
            "keyword_score": keyword_score,
            "weights": {
                "semantic": round(w_sem, 2),
                "skills": round(w_skl, 2),
                "experience": round(w_exp, 2),
                "keywords": round(w_kw, 2)
            }
        },
        "radar_metrics": {
            "Semantic Fit": semantic_score,
            "Skill Coverage": skill_score,
            "Experience Alignment": experience_score,
            "Action & Keywords": keyword_score,
            "Overall Match": overall_score
        }
    }
    
    return {
        "overall_score": overall_score,
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "keyword_score": keyword_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "status": status,
        "explanation": explanation
    }
