import json
import asyncio
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional

from ..queue.task_queue import resume_queue

router = APIRouter(prefix="/api/queue", tags=["Resume Queue Monitor"])

@router.get("/status")
def get_queue_status(job_id: Optional[int] = Query(None)):
    """Get active tasks in the queue and overall processing stats."""
    stats = resume_queue.get_queue_stats()
    if job_id:
        tasks = resume_queue.get_job_tasks(job_id)
    else:
        tasks = resume_queue.get_all_tasks()
    return {
        "stats": stats,
        "tasks": tasks
    }

@router.get("/tasks/{task_id}")
def get_single_task(task_id: str):
    """Get status of a specific task."""
    task = resume_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in queue")
    return task

@router.get("/stream")
async def stream_queue_events():
    """
    Server-Sent Events (SSE) real-time streaming endpoint for queue events.
    Pushes instantaneous updates to the browser as resumes move through extraction, OCR, NLP, embedding, and ranking.
    """
    async def event_generator():
        # Send initial snapshot
        initial_payload = {
            "event": "INITIAL_STATE",
            "stats": resume_queue.get_queue_stats(),
            "tasks": resume_queue.get_all_tasks()
        }
        yield f"data: {json.dumps(initial_payload)}\n\n"
        
        async for event in resume_queue.subscribe():
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
