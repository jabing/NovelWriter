"""Task tracking router for workflow status monitoring."""

import threading
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from src.novel_agent.api.schemas.workflow import (
    TaskListResponse,
    TaskStatusResponse,
    TaskUpdateRequest,
    WorkflowStatus,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"], redirect_slashes=False)


class TaskStore:
    """Thread-safe in-memory task store for tracking workflow status."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_task(
        self,
        task_id: str | None = None,
        status: WorkflowStatus = WorkflowStatus.QUEUED,
        progress: int = 0,
        current_step: str | None = None,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new task and return its ID."""
        task_id = task_id or str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "status": status.value,
            "progress": progress,
            "current_step": current_step,
            "errors": errors or [],
            "metadata": metadata or {},
            "created_at": self._get_timestamp(),
        }
        with self._lock:
            self._tasks[task_id] = task_data
        return task_id

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: WorkflowStatus | None = None,
        progress: int | None = None,
        current_step: str | None = None,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Update task status. Returns True if task exists."""
        with self._lock:
            if task_id not in self._tasks:
                return False
            task = self._tasks[task_id]
            if status is not None:
                task["status"] = status.value
            if progress is not None:
                task["progress"] = progress
            if current_step is not None:
                task["current_step"] = current_step
            if errors is not None:
                task["errors"] = errors
            if metadata is not None:
                task["metadata"].update(metadata)
            task["updated_at"] = self._get_timestamp()
            return True

    def get_all_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks."""
        with self._lock:
            return list(self._tasks.values())

    def delete_task(self, task_id: str) -> bool:
        """Delete a task. Returns True if task existed."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()


_task_store = TaskStore()


def get_task_store() -> TaskStore:
    """Get the global task store instance."""
    return _task_store


@router.get("/", response_model=TaskListResponse)
async def list_tasks():
    """
    GET /api/tasks
    Return a list of all tasks for dashboard.
    """
    tasks = get_task_store().get_all_tasks()

    total = len(tasks)
    queued = sum(1 for t in tasks if t["status"] == WorkflowStatus.QUEUED.value)
    running = sum(1 for t in tasks if t["status"] == WorkflowStatus.RUNNING.value)
    completed = sum(1 for t in tasks if t["status"] == WorkflowStatus.COMPLETED.value)
    failed = sum(1 for t in tasks if t["status"] == WorkflowStatus.FAILED.value)
    cancelled = sum(1 for t in tasks if t["status"] == WorkflowStatus.CANCELLED.value)

    task_responses = [
        TaskStatusResponse(
            task_id=t["task_id"],
            status=t["status"],
            progress=t["progress"],
            current_step=t["current_step"],
            errors=t["errors"],
            metadata=t["metadata"],
        )
        for t in tasks
    ]

    return TaskListResponse(
        tasks=task_responses,
        total_count=total,
        queued_count=queued,
        running_count=running,
        completed_count=completed,
        failed_count=failed,
        cancelled_count=cancelled,
    )


@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    GET /api/tasks/{task_id}/status
    Return the current status of a specific task.
    """
    task = get_task_store().get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        current_step=task["current_step"],
        errors=task["errors"],
        metadata=task["metadata"],
    )


@router.patch("/{task_id}")
async def update_task(task_id: str, update: TaskUpdateRequest):
    """
    PATCH /api/tasks/{task_id}
    Update task status and progress.
    """
    success = get_task_store().update_task(
        task_id=task_id,
        status=update.status,
        progress=update.progress,
        current_step=update.current_step,
        errors=update.errors,
    )

    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    task = get_task_store().get_task(task_id)

    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        current_step=task["current_step"],
        errors=task["errors"],
        metadata=task["metadata"],
    )
