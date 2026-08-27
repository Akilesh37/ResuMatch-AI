import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import UPLOAD_DIR
from ..database import get_db
from ..models import Job
from ..schemas import BatchUploadResponse, QueueTaskResponse
from ..queue.task_queue import resume_queue

router = APIRouter(prefix="/api/resumes", tags=["Resume Ingestion"])

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".rtf",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"
}

@router.post("/upload", response_model=BatchUploadResponse)
async def upload_resumes(
    job_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Batch resume upload endpoint.
    Saves uploaded files and pushes them onto the async Resume Queue for worker processing.
    """
    # Verify Job exists in Job DB
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    enqueued_tasks: List[QueueTaskResponse] = []

    for upload_file in files:
        filename = upload_file.filename or "resume"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            # Skip invalid extension or handle
            continue

        # Save to disk with unique token prefix
        unique_prefix = uuid.uuid4().hex[:8]
        safe_filename = f"{unique_prefix}_{os.path.basename(filename)}"
        save_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Read file contents and compute size
        content = await upload_file.read()
        file_size = len(content)

        with open(save_path, "wb") as f:
            f.write(content)

        # Enqueue task
        task_data = await resume_queue.enqueue(
            job_id=job.id,
            file_path=save_path,
            filename=filename,
            file_type=upload_file.content_type or ext,
            file_size_bytes=file_size
        )

        enqueued_tasks.append(QueueTaskResponse(
            id=task_data["id"],
            job_id=task_data["job_id"],
            candidate_id=task_data["candidate_id"],
            filename=task_data["filename"],
            file_type=task_data["file_type"],
            status=task_data["status"],
            progress=task_data["progress"],
            step_message=task_data["step_message"],
            error_message=task_data["error_message"],
            created_at=datetime.fromisoformat(task_data["created_at"])
        ))

    return BatchUploadResponse(
        job_id=job.id,
        enqueued_count=len(enqueued_tasks),
        tasks=enqueued_tasks,
        message=f"Successfully enqueued {len(enqueued_tasks)} resume(s) for evaluation against '{job.title}'."
    )
