"""Workflow planning module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.novel_agent.workflow.state import WorkflowState


@dataclass
class PlanWorkflow(ABC):
    """Base class for workflow planning."""

    name: str
    description: str = ""

    @abstractmethod
    async def create_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Create a workflow plan from input data."""
        pass

    @abstractmethod
    async def validate_plan(self, plan: dict[str, Any]) -> bool:
        """Validate a workflow plan."""
        pass

    @abstractmethod
    async def execute_plan(self, plan: dict[str, Any]) -> WorkflowState:
        """Execute a workflow plan."""
        pass
