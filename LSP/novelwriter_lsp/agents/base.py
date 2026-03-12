"""
NovelWriter LSP - Base Agent Class

Simplified base agent class for ValidatorAgent and UpdaterAgent.
Removes Writer project-specific dependencies while maintaining core functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

try:
    from typing import override
except ImportError:
    from typing_extensions import override


class AgentState(str, Enum):
    """Possible states for an agent."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Result from an agent execution."""

    success: bool
    data: dict[str, object] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Abstract base class for all NovelWriter LSP agents.

    All specialized agents (ValidatorAgent, UpdaterAgent, etc.) should
    inherit from this class and implement the execute() method.
    """

    name: str
    state: AgentState
    _execution_count: int

    def __init__(self, name: str) -> None:
        """Initialize the agent.

        Args:
            name: Human-readable name for the agent
        """
        self.name = name
        self.state = AgentState.IDLE
        self._execution_count = 0

    @abstractmethod
    async def execute(self, input_data: dict[str, object]) -> AgentResult:
        """Execute the agent's main task.

        Args:
            input_data: Input data for the agent's task

        Returns:
            AgentResult with success status and output data
        """
        pass

    def update_state(self, new_state: AgentState) -> None:
        """Update the agent's state.

        Args:
            new_state: New state to set
        """
        self.state = new_state

    async def run(self, input_data: dict[str, object]) -> AgentResult:
        """Run the agent with state management.

        This method wraps execute() with state tracking and error handling.

        Args:
            input_data: Input data for the agent's task

        Returns:
            AgentResult with success status and output data
        """
        self.update_state(AgentState.RUNNING)
        self._execution_count += 1

        try:
            result = await self.execute(input_data)
            self.update_state(AgentState.COMPLETED if result.success else AgentState.FAILED)
            return result
        except Exception as e:
            self.update_state(AgentState.FAILED)
            return AgentResult(
                success=False,
                data={},
                errors=[str(e)],
            )

    @property
    def execution_count(self) -> int:
        """Number of times this agent has been executed."""
        return self._execution_count

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, state={self.state.value})"
