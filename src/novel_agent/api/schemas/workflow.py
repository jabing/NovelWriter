"""Workflow-related Pydantic schemas for the API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow/Task status values."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    current_step: str | None = Field(None, description="Current step description")
    errors: list[str] = Field(default_factory=list, description="List of errors if any")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")


class TaskListResponse(BaseModel):
    tasks: list[TaskStatusResponse] = Field(..., description="List of tasks")
    total_count: int = Field(..., ge=0, description="Total number of tasks")
    queued_count: int = Field(..., ge=0, description="Number of queued tasks")
    running_count: int = Field(..., ge=0, description="Number of running tasks")
    completed_count: int = Field(..., ge=0, description="Number of completed tasks")
    failed_count: int = Field(..., ge=0, description="Number of failed tasks")
    cancelled_count: int = Field(..., ge=0, description="Number of cancelled tasks")


class TaskUpdateRequest(BaseModel):
    status: WorkflowStatus = Field(..., description="New status for the task")
    progress: int | None = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    current_step: str | None = Field(None, description="Current step description")
    errors: list[str] = Field(default_factory=list, description="List of errors if any")


class InitializeRequest(BaseModel):
    pass


class InitializeResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Initial status: queued")
    message: str = Field(default="Initialization queued successfully")


class WorkflowResult(BaseModel):
    success: bool = Field(..., description="Whether the workflow succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: list[str] = Field(default_factory=list, description="Any warnings")


class WorkflowTaskListResponse(BaseModel):
    """Alias for TaskListResponse for backward compatibility."""


class WorkflowTaskResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")


# Export all classes
__all__ = [
    "WorkflowStatus",
    "TaskStatusResponse",
    "TaskListResponse",
    "TaskUpdateRequest",
    "InitializeRequest",
    "InitializeResponse",
    "WorkflowResult",
    "WorkflowTaskListResponse",
    "WorkflowTaskResponse",
]
