import os
import json
import asyncio
import logging
from typing import Optional
from pathlib import Path

from ..database import SessionLocal
from ..models import Job, Candidate, EvaluationResult
from ..queue.task_queue import resume_queue
from ..extraction.text_extractor import extract_resume_content
from ..nlp.nlp_processor import process_resume_nlp
from ..embeddings.embedding_model import generate_embedding, serialize_embedding, deserialize_embedding
from ..engine.similarity_engine import evaluate_candidate_match

logger = logging.getLogger(__name__)

class ProcessingWorker:
    """
    Background worker that continuously consumes items from the Resume Queue,
    executes the processing pipeline, and persists candidate and evaluation results.
    """
    def __init__(self):
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._process_loop())
            logger.info("Processing Worker started.")

    async def stop(self):
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Processing Worker stopped.")

    async def _process_loop(self):
        """Worker main consumption loop."""
        while self._is_running:
            try:
                task_data = await resume_queue.get_next_task()
                task_id = task_data["id"]
                try:
                    await self._process_single_task(task_data)
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
                    await resume_queue.update_status(
                        task_id=task_id,
                        status="FAILED",
                        progress=100,
                        step_message="Processing failed",
                        error_message=str(e)
                    )
                finally:
                    resume_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_single_task(self, task_data: dict):
        task_id = task_data["id"]
        job_id = task_data["job_id"]
        file_path = task_data["file_path"]
        filename = task_data["filename"]
        file_type = task_data["file_type"]
        file_size = task_data["file_size_bytes"]

        logger.info(f"Worker processing task {task_id} for file: {filename}")

        # Step 1: Text Extraction & OCR
        await resume_queue.update_status(
            task_id=task_id,
            status="EXTRACTING",
            progress=20,
            step_message=f"Extracting text from {filename}..."
        )
        
        # Read file bytes
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found on disk: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Run extraction in thread pool to avoid blocking asyncio event loop
        loop = asyncio.get_event_loop()
        extraction_res = await loop.run_in_executor(
            None, extract_resume_content, file_bytes, filename, file_type
        )

        if not extraction_res.get("success") or not extraction_res.get("text", "").strip():
            err = extraction_res.get("error", "No readable text could be extracted from document.")
            raise ValueError(f"Text extraction failed: {err}")

        raw_text = extraction_res["text"]
        is_ocr_used = extraction_res.get("is_ocr", False)
        ocr_confidence = extraction_res.get("ocr_confidence")

        if is_ocr_used:
            await resume_queue.update_status(
                task_id=task_id,
                status="OCR",
                progress=35,
                step_message="Scanned document detected. Optical Character Recognition (OCR) applied."
            )
            await asyncio.sleep(0.3)

        # Step 2: NLP Processing
        await resume_queue.update_status(
            task_id=task_id,
            status="NLP_PROCESSING",
            progress=50,
            step_message="Analyzing skills, experience timeline, and contact information..."
        )

        nlp_res = await loop.run_in_executor(
            None, process_resume_nlp, raw_text, filename
        )

        # Step 3: Embedding Model
        await resume_queue.update_status(
            task_id=task_id,
            status="EMBEDDING",
            progress=70,
            step_message="Generating dense transformer semantic embeddings..."
        )

        # Combine clean text + key skills for a rich dense semantic vector
        embedding_text = f"{nlp_res['clean_text']} Skills: {', '.join(nlp_res['skills'])}"
        candidate_embedding = await loop.run_in_executor(
            None, generate_embedding, embedding_text
        )

        # Step 4: Similarity Engine & Scoring
        await resume_queue.update_status(
            task_id=task_id,
            status="SCORING",
            progress=85,
            step_message="Executing multi-factor similarity matching against job requirements..."
        )

        # Retrieve Job and Job Embedding from DB
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job ID {job_id} not found in database.")

            job_req_skills = job.get_required_skills_list()
            job_pref_skills = job.get_preferred_skills_list()

            # Ensure job has an embedding
            job_embedding = deserialize_embedding(job.embedding)
            if not job_embedding:
                job_embed_text = f"{job.title} {job.description} Required Skills: {', '.join(job_req_skills)}"
                job_embedding = await loop.run_in_executor(None, generate_embedding, job_embed_text)
                job.embedding = serialize_embedding(job_embedding)
                db.commit()

            job_data = {
                "title": job.title,
                "description": job.description,
                "required_skills": job_req_skills,
                "preferred_skills": job_pref_skills,
                "min_experience": job.min_experience,
                "threshold": job.threshold,
                "weight_semantic": job.weight_semantic,
                "weight_skills": job.weight_skills,
                "weight_experience": job.weight_experience,
                "weight_keywords": job.weight_keywords
            }

            candidate_data = {
                "extracted_skills": nlp_res["skills"],
                "total_experience_years": nlp_res["experience_years"],
                "clean_text": nlp_res["clean_text"]
            }

            eval_res = evaluate_candidate_match(
                candidate_data=candidate_data,
                candidate_embedding=candidate_embedding,
                job_data=job_data,
                job_embedding=job_embedding
            )

            # Step 5: Persist Candidate & Evaluation in DB
            candidate = Candidate(
                name=nlp_res["candidate_name"],
                email=nlp_res["email"],
                phone=nlp_res["phone"],
                total_experience_years=nlp_res["experience_years"],
                extracted_skills=json.dumps(nlp_res["skills"]),
                education=json.dumps(nlp_res["education"]),
                work_history=json.dumps(nlp_res.get("sections", {}).get("experience", "")),
                raw_text=raw_text,
                clean_text=nlp_res["clean_text"],
                is_ocr_used=is_ocr_used,
                ocr_confidence=ocr_confidence,
                file_path=file_path,
                original_filename=filename,
                file_type=file_type,
                file_size_bytes=file_size,
                embedding=serialize_embedding(candidate_embedding)
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

            evaluation = EvaluationResult(
                job_id=job.id,
                candidate_id=candidate.id,
                overall_score=eval_res["overall_score"],
                semantic_score=eval_res["semantic_score"],
                skill_score=eval_res["skill_score"],
                experience_score=eval_res["experience_score"],
                keyword_score=eval_res["keyword_score"],
                matched_skills=json.dumps(eval_res["matched_skills"]),
                missing_skills=json.dumps(eval_res["missing_skills"]),
                extra_skills=json.dumps(eval_res["extra_skills"]),
                status=eval_res["status"],
                explanation=json.dumps(eval_res["explanation"])
            )
            db.add(evaluation)
            db.commit()

            # Mark Completed
            await resume_queue.update_status(
                task_id=task_id,
                status="COMPLETED",
                progress=100,
                step_message=f"Candidate evaluated: {candidate.name} ({eval_res['overall_score']}% match - {eval_res['status']})",
                candidate_id=candidate.id
            )
            logger.info(f"Task {task_id} completed successfully for candidate {candidate.name} (ID: {candidate.id})")
        finally:
            db.close()

# Worker Singleton instance
processing_worker = ProcessingWorker()
