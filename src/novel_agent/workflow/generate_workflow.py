"""Workflow generation module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.novel_agent.workflow.state import WorkflowState


@dataclass
class GenerateWorkflow(ABC):
    """Base class for workflow generation."""

    name: str
    description: str = ""

    @abstractmethod
    async def generate_content(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Generate content based on workflow plan."""
        pass

    @abstractmethod
    async def validate_output(self, output: dict[str, Any]) -> bool:
        """Validate generated output."""
        pass

    @abstractmethod
    async def finalize(self, output: dict[str, Any]) -> WorkflowState:
        """Finalize workflow and produce final output."""
        pass
