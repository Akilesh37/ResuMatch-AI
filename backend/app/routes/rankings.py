import io
import csv
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import Job, Candidate, EvaluationResult
from ..schemas import EvaluationResponse, CandidateResponse, EvaluationStatusUpdate

router = APIRouter(tags=["Ranking DB & Results"])

@router.get("/api/jobs/{job_id}/rankings", response_model=List[EvaluationResponse])
def get_job_rankings(
    job_id: int,
    status: Optional[str] = Query(None, description="Filter by status: SHORTLISTED, ELIGIBLE, UNDER_REVIEW, REJECTED"),
    min_score: Optional[float] = Query(None, description="Minimum overall score filter"),
    db: Session = Depends(get_db)
):
    """
    Retrieve ranked candidate list for a specific job, ordered by highest overall score.
    """
    query = db.query(EvaluationResult, Candidate).join(
        Candidate, EvaluationResult.candidate_id == Candidate.id
    ).filter(EvaluationResult.job_id == job_id)

    if status:
        query = query.filter(EvaluationResult.status == status.upper())
    if min_score is not None:
        query = query.filter(EvaluationResult.overall_score >= min_score)

    eval_tuples = query.order_by(desc(EvaluationResult.overall_score)).all()

    results = []
    for evaluation, candidate in eval_tuples:
        results.append(EvaluationResponse(
            id=evaluation.id,
            job_id=evaluation.job_id,
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            candidate_phone=candidate.phone,
            candidate_experience=candidate.total_experience_years,
            original_filename=candidate.original_filename,
            file_type=candidate.file_type,
            is_ocr_used=candidate.is_ocr_used,
            overall_score=evaluation.overall_score,
            semantic_score=evaluation.semantic_score,
            skill_score=evaluation.skill_score,
            experience_score=evaluation.experience_score,
            keyword_score=evaluation.keyword_score,
            matched_skills=evaluation.get_matched_skills_list(),
            missing_skills=evaluation.get_missing_skills_list(),
            extra_skills=json.loads(evaluation.extra_skills) if evaluation.extra_skills else [],
            status=evaluation.status,
            explanation=evaluation.get_explanation_dict(),
            created_at=evaluation.created_at
        ))

    return results

@router.get("/api/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate_details(candidate_id: int, db: Session = Depends(get_db)):
    """Retrieve deep dive details of a candidate, including extracted raw text and OCR status."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        total_experience_years=candidate.total_experience_years,
        extracted_skills=candidate.get_skills_list(),
        education=candidate.get_education_list(),
        raw_text=candidate.raw_text,
        clean_text=candidate.clean_text,
        is_ocr_used=candidate.is_ocr_used,
        ocr_confidence=candidate.ocr_confidence,
        original_filename=candidate.original_filename,
        file_type=candidate.file_type,
        file_size_bytes=candidate.file_size_bytes,
        created_at=candidate.created_at
    )

@router.patch("/api/evaluations/{evaluation_id}/status")
def update_evaluation_status(
    evaluation_id: int,
    status_update: EvaluationStatusUpdate,
    db: Session = Depends(get_db)
):
    """Allow recruiter to manually update candidate shortlisting status."""
    evaluation = db.query(EvaluationResult).filter(EvaluationResult.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation result not found")

    evaluation.status = status_update.status.upper()
    db.commit()
    return {"message": "Status updated successfully", "new_status": evaluation.status}

@router.get("/api/jobs/{job_id}/export")
def export_job_rankings(
    job_id: int,
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Export evaluated candidate rankings as CSV or JSON report."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    eval_tuples = db.query(EvaluationResult, Candidate).join(
        Candidate, EvaluationResult.candidate_id == Candidate.id
    ).filter(EvaluationResult.job_id == job_id).order_by(desc(EvaluationResult.overall_score)).all()

    if format == "json":
        export_data = []
        for evaluation, candidate in eval_tuples:
            export_data.append({
                "rank": len(export_data) + 1,
                "candidate_name": candidate.name,
                "email": candidate.email,
                "phone": candidate.phone,
                "total_experience_years": candidate.total_experience_years,
                "overall_score": evaluation.overall_score,
                "semantic_score": evaluation.semantic_score,
                "skill_score": evaluation.skill_score,
                "experience_score": evaluation.experience_score,
                "keyword_score": evaluation.keyword_score,
                "status": evaluation.status,
                "matched_skills": evaluation.get_matched_skills_list(),
                "missing_skills": evaluation.get_missing_skills_list(),
                "is_ocr_used": candidate.is_ocr_used,
                "filename": candidate.original_filename
            })
        return export_data

    # CSV export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Candidate Name", "Email", "Phone", "Experience (Years)",
        "Overall Score (%)", "Semantic Score (%)", "Skill Score (%)", "Experience Score (%)",
        "Status", "Matched Skills", "Missing Skills", "OCR Used", "Original File"
    ])

    for i, (evaluation, candidate) in enumerate(eval_tuples, start=1):
        writer.writerow([
            i,
            candidate.name,
            candidate.email or "N/A",
            candidate.phone or "N/A",
            candidate.total_experience_years,
            evaluation.overall_score,
            evaluation.semantic_score,
            evaluation.skill_score,
            evaluation.experience_score,
            evaluation.status,
            ", ".join(evaluation.get_matched_skills_list()),
            ", ".join(evaluation.get_missing_skills_list()),
            "Yes" if candidate.is_ocr_used else "No",
            candidate.original_filename
        ])

    csv_content = output.getvalue()
    filename = f"rankings_job_{job_id}_{job.title.replace(' ', '_')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
