import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Job, EvaluationResult
from ..schemas import JobCreate, JobUpdate, JobResponse
from ..embeddings.embedding_model import generate_embedding, serialize_embedding

router = APIRouter(prefix="/api/jobs", tags=["Job DB"])

PRESET_TEMPLATES = [
    {
        "title": "Senior AI / Machine Learning Engineer",
        "department": "AI & Research",
        "description": "We are seeking a Senior AI/ML Engineer to build transformer models, LLM pipelines, RAG systems, and deploy scalable inference architectures. Strong experience with PyTorch, HuggingFace, FastAPI, and vector databases required.",
        "required_skills": ["python", "pytorch", "transformers", "machine learning", "deep learning", "fastapi", "docker"],
        "preferred_skills": ["llms", "langchain", "vector databases", "kubernetes", "aws", "ci/cd"],
        "min_experience": 3.0,
        "threshold": 60.0,
        "weight_semantic": 0.40,
        "weight_skills": 0.35,
        "weight_experience": 0.15,
        "weight_keywords": 0.10
    },
    {
        "title": "Full Stack Developer (React & Node/Python)",
        "department": "Engineering",
        "description": "Looking for a high-performing Full Stack Developer to design responsive web applications and robust REST APIs. Proficiency in React, TypeScript, Node.js or Python, PostgreSQL, and modern cloud deployment is essential.",
        "required_skills": ["javascript", "typescript", "react", "node.js", "python", "postgresql", "rest api", "git"],
        "preferred_skills": ["next.js", "docker", "tailwind css", "redis", "aws"],
        "min_experience": 2.0,
        "threshold": 55.0,
        "weight_semantic": 0.35,
        "weight_skills": 0.40,
        "weight_experience": 0.15,
        "weight_keywords": 0.10
    },
    {
        "title": "Cloud DevOps & Infrastructure Engineer",
        "department": "Platform Operations",
        "description": "Seeking an experienced DevOps Engineer to manage Kubernetes clusters, CI/CD pipelines, Terraform IaC, and cloud security across AWS and GCP environments.",
        "required_skills": ["docker", "kubernetes", "aws", "terraform", "ci/cd", "linux", "bash", "git"],
        "preferred_skills": ["ansible", "gcp", "python", "nginx", "security"],
        "min_experience": 3.0,
        "threshold": 60.0,
        "weight_semantic": 0.35,
        "weight_skills": 0.40,
        "weight_experience": 0.15,
        "weight_keywords": 0.10
    },
    {
        "title": "Data Analyst & Business Intelligence Specialist",
        "department": "Data Analytics",
        "description": "Seeking a Data Analyst to extract business insights, build interactive Tableau/Power BI dashboards, write complex SQL queries, and perform statistical modeling with Python and Pandas.",
        "required_skills": ["sql", "python", "pandas", "data analysis", "tableau", "power bi"],
        "preferred_skills": ["snowflake", "dbt", "r", "machine learning"],
        "min_experience": 1.5,
        "threshold": 50.0,
        "weight_semantic": 0.35,
        "weight_skills": 0.40,
        "weight_experience": 0.15,
        "weight_keywords": 0.10
    }
]

@router.get("/templates")
def get_job_templates():
    """Get pre-configured industry job requirement templates."""
    return PRESET_TEMPLATES

@router.get("", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    """List all created job openings with candidate counts."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    results = []
    for job in jobs:
        total = db.query(EvaluationResult).filter(EvaluationResult.job_id == job.id).count()
        shortlisted = db.query(EvaluationResult).filter(
            EvaluationResult.job_id == job.id,
            EvaluationResult.status == "SHORTLISTED"
        ).count()
        
        results.append(JobResponse(
            id=job.id,
            title=job.title,
            department=job.department or "General",
            description=job.description,
            required_skills=job.get_required_skills_list(),
            preferred_skills=job.get_preferred_skills_list(),
            min_experience=job.min_experience,
            threshold=job.threshold,
            weight_semantic=job.weight_semantic,
            weight_skills=job.weight_skills,
            weight_experience=job.weight_experience,
            weight_keywords=job.weight_keywords,
            created_at=job.created_at,
            updated_at=job.updated_at,
            total_candidates=total,
            shortlisted_count=shortlisted
        ))
    return results

@router.post("", response_model=JobResponse)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    """Create a new job posting and pre-calculate its semantic vector embedding."""
    # Pre-calculate semantic embedding for the job
    job_embed_text = f"{job_in.title} {job_in.description} Required Skills: {', '.join(job_in.required_skills)}"
    embedding_vec = generate_embedding(job_embed_text)

    job = Job(
        title=job_in.title,
        department=job_in.department,
        description=job_in.description,
        required_skills=json.dumps(job_in.required_skills),
        preferred_skills=json.dumps(job_in.preferred_skills),
        min_experience=job_in.min_experience,
        threshold=job_in.threshold,
        weight_semantic=job_in.weight_semantic,
        weight_skills=job_in.weight_skills,
        weight_experience=job_in.weight_experience,
        weight_keywords=job_in.weight_keywords,
        embedding=serialize_embedding(embedding_vec)
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobResponse(
        id=job.id,
        title=job.title,
        department=job.department,
        description=job.description,
        required_skills=job.get_required_skills_list(),
        preferred_skills=job.get_preferred_skills_list(),
        min_experience=job.min_experience,
        threshold=job.threshold,
        weight_semantic=job.weight_semantic,
        weight_skills=job.weight_skills,
        weight_experience=job.weight_experience,
        weight_keywords=job.weight_keywords,
        created_at=job.created_at,
        updated_at=job.updated_at,
        total_candidates=0,
        shortlisted_count=0
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get single job details."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    total = db.query(EvaluationResult).filter(EvaluationResult.job_id == job.id).count()
    shortlisted = db.query(EvaluationResult).filter(
        EvaluationResult.job_id == job.id,
        EvaluationResult.status == "SHORTLISTED"
    ).count()

    return JobResponse(
        id=job.id,
        title=job.title,
        department=job.department,
        description=job.description,
        required_skills=job.get_required_skills_list(),
        preferred_skills=job.get_preferred_skills_list(),
        min_experience=job.min_experience,
        threshold=job.threshold,
        weight_semantic=job.weight_semantic,
        weight_skills=job.weight_skills,
        weight_experience=job.weight_experience,
        weight_keywords=job.weight_keywords,
        created_at=job.created_at,
        updated_at=job.updated_at,
        total_candidates=total,
        shortlisted_count=shortlisted
    )

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job and its associated evaluations."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}
