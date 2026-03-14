"""Workflow state management for novel generation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class WorkflowState:
    """State of the workflow execution."""

    planning_complete: bool = False
    last_generated_chapter: int = 0
    validation_enabled: bool = True
    volume_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow state to dictionary for serialization."""
        return {
            "planning_complete": self.planning_complete,
            "last_generated_chapter": self.last_generated_chapter,
            "validation_enabled": self.validation_enabled,
            "volume_count": self.volume_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create WorkflowState from dictionary."""
        return cls(
            planning_complete=data.get("planning_complete", False),
            last_generated_chapter=data.get("last_generated_chapter", 0),
            validation_enabled=data.get("validation_enabled", True),
            volume_count=data.get("volume_count", 0),
        )


@dataclass
class WorkflowCheckpoint:
    """A checkpoint capturing workflow state at a specific point."""

    chapter_number: int
    content: str
    timestamp: str
    project_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "chapter_number": self.chapter_number,
            "content": self.content,
            "timestamp": self.timestamp,
            "project_id": self.project_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowCheckpoint":
        """Create WorkflowCheckpoint from dictionary."""
        return cls(
            chapter_number=data["chapter_number"],
            content=data["content"],
            timestamp=data["timestamp"],
            project_id=data["project_id"],
        )


def create_checkpoint(
    chapter_number: int,
    content: str,
    project_id: str,
) -> WorkflowCheckpoint:
    return WorkflowCheckpoint(
        chapter_number=chapter_number,
        content=content,
        timestamp=datetime.now().isoformat(),
        project_id=project_id,
    )


__all__ = [
    "WorkflowState",
    "WorkflowCheckpoint",
    "create_checkpoint",
]
