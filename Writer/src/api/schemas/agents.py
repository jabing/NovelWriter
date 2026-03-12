"""Agent and Task-related Pydantic schemas for the API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(..., min_length=1, max_length=200)
    task_type: str = Field(..., description="Type: write, review, publish, research")
    novel_id: str | None = None
    chapter_number: int | None = None
    scheduled_time: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Schema for task response data."""

    id: str
    title: str
    task_type: str
    status: str
    novel_id: str | None
    chapter_number: int | None
    scheduled_time: str | None
    completed_time: str | None
    details: dict[str, Any]


class TaskListResponse(BaseModel):
    """Schema for list of tasks."""

    tasks: list[TaskResponse]
    total_count: int
    pending_count: int
    in_progress_count: int
    completed_count: int
    failed_count: int


class AgentStatusResponse(BaseModel):
    """Schema for agent status response."""

    agent_id: str
    agent_name: str
    agent_type: str
    status: str
    current_task: str | None = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_activity: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
