"""Tasks API router for CRUD operations."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.novel_agent.api.dependencies import get_state
from src.novel_agent.api.schemas.agents import TaskCreate, TaskListResponse, TaskResponse
from src.novel_agent.studio.core.state import StudioState, Task, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"], redirect_slashes=False)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    state: Annotated[StudioState, Depends(get_state)],
    novel_id: str | None = Query(None, description="Filter by novel ID"),
    status_filter: TaskStatus | None = Query(None, alias="status", description="Filter by status"),
) -> TaskListResponse:
    """Get all tasks with optional filtering."""
    tasks = state.get_tasks(novel_id=novel_id)
    
    # Apply status filter if provided
    if status_filter:
        tasks = [t for t in tasks if t.status == status_filter]
    
    # Convert to response format
    task_responses = [_task_to_response(t) for t in tasks]
    
    # Calculate counts
    pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    in_progress_count = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    completed_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed_count = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    
    return TaskListResponse(
        tasks=task_responses,
        total_count=len(tasks),
        pending_count=pending_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        failed_count=failed_count,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    state: Annotated[StudioState, Depends(get_state)],
) -> TaskResponse:
    """Create a new task."""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    task = Task(
        id=task_id,
        title=task_data.title,
        task_type=task_data.task_type,
        status=TaskStatus.PENDING,
        novel_id=task_data.novel_id,
        chapter_number=task_data.chapter_number,
        scheduled_time=task_data.scheduled_time,
        details=task_data.details,
    )
    
    state.add_task(task)
    return _task_to_response(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> TaskResponse:
    """Get a specific task by ID."""
    tasks = state.get_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return _task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: dict,
    state: Annotated[StudioState, Depends(get_state)],
) -> TaskResponse:
    """Update an existing task."""
    tasks = state.get_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Update fields
    update_data = {k: v for k, v in task_data.items() if v is not None}
    
    if "title" in update_data:
        task.title = update_data["title"]
    if "task_type" in update_data:
        task.task_type = update_data["task_type"]
    if "status" in update_data:
        task.status = TaskStatus(update_data["status"])
    if "novel_id" in update_data:
        task.novel_id = update_data["novel_id"]
    if "chapter_number" in update_data:
        task.chapter_number = update_data["chapter_number"]
    if "scheduled_time" in update_data:
        task.scheduled_time = update_data["scheduled_time"]
    if "details" in update_data:
        task.details.update(update_data["details"])
    
    state.update_task(task)
    return _task_to_response(task)


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> TaskResponse:
    """Mark a task as completed."""
    if not state.complete_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Get the updated task
    tasks = state.get_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    return _task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> None:
    """Delete a task."""
    tasks = state.get_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Remove from state
    del state._tasks[task_id]
    state._save_state()


def _task_to_response(task: Task) -> TaskResponse:
    """Convert a Task to a TaskResponse."""
    return TaskResponse(
        id=task.id,
        title=task.title,
        task_type=task.task_type,
        status=task.status.value,
        novel_id=task.novel_id,
        chapter_number=task.chapter_number,
        scheduled_time=task.scheduled_time,
        completed_time=task.completed_time,
        details=task.details,
    )
