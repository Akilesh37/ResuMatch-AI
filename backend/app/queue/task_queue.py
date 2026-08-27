import asyncio
import uuid
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeQueueManager:
    """
    Asynchronous in-memory and persistent queue coordinator with event broadcasting.
    """
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def enqueue(
        self,
        job_id: int,
        file_path: str,
        filename: str,
        file_type: str,
        file_size_bytes: int
    ) -> Dict[str, Any]:
        """Enqueue a new resume file for processing."""
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "job_id": job_id,
            "filename": filename,
            "file_path": file_path,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "status": "QUEUED",
            "progress": 0,
            "step_message": "Resume enqueued in processing queue",
            "candidate_id": None,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        async with self._lock:
            self._tasks[task_id] = task_data

        await self._queue.put(task_data)
        await self._broadcast({
            "event": "TASK_ENQUEUED",
            "task": task_data
        })
        logger.info(f"Enqueued task {task_id} for file {filename}")
        return task_data

    async def get_next_task(self) -> Dict[str, Any]:
        """Worker method to fetch the next queued item."""
        return await self._queue.get()

    def task_done(self):
        """Acknowledge task completion in asyncio.Queue."""
        self._queue.task_done()

    async def update_status(
        self,
        task_id: str,
        status: str,
        progress: int,
        step_message: str,
        candidate_id: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update task progress and broadcast live update."""
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = status
                self._tasks[task_id]["progress"] = progress
                self._tasks[task_id]["step_message"] = step_message
                self._tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
                if candidate_id is not None:
                    self._tasks[task_id]["candidate_id"] = candidate_id
                if error_message is not None:
                    self._tasks[task_id]["error_message"] = error_message
                
                updated_task = dict(self._tasks[task_id])
            else:
                return

        await self._broadcast({
            "event": "TASK_PROGRESS",
            "task": updated_task
        })

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return list(self._tasks.values())

    def get_job_tasks(self, job_id: int) -> List[Dict[str, Any]]:
        return [t for t in self._tasks.values() if t.get("job_id") == job_id]

    def get_queue_stats(self) -> Dict[str, Any]:
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "queued": sum(1 for t in tasks if t["status"] == "QUEUED"),
            "processing": sum(1 for t in tasks if t["status"] not in ["QUEUED", "COMPLETED", "FAILED"]),
            "completed": sum(1 for t in tasks if t["status"] == "COMPLETED"),
            "failed": sum(1 for t in tasks if t["status"] == "FAILED")
        }

    async def subscribe(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to real-time event updates via async generator (for SSE)."""
        subscriber_queue = asyncio.Queue()
        self._subscribers.append(subscriber_queue)
        try:
            while True:
                data = await subscriber_queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            if subscriber_queue in self._subscribers:
                self._subscribers.remove(subscriber_queue)

    async def _broadcast(self, event_data: Dict[str, Any]):
        """Publish event to all active SSE subscribers."""
        dead_subscribers = []
        for sub in self._subscribers:
            try:
                sub.put_nowait(event_data)
            except Exception:
                dead_subscribers.append(sub)
        for dead in dead_subscribers:
            if dead in self._subscribers:
                self._subscribers.remove(dead)

# Global queue singleton
resume_queue = ResumeQueueManager()
