# src/agents/base.py
"""Base class for all agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.llm.base import BaseLLM
from src.memory.base import BaseMemory
from src.monitoring import async_trace, async_track_errors, timer


class AgentState(str, Enum):
    """Possible states for an agent."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class AgentResult:
    """Result from an agent execution."""

    success: bool
    data: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all novel writing agents.

    All specialized agents (Plot, Character, Writer, Editor, etc.) should
    inherit from this class and implement the execute() method.
    """

    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        memory: BaseMemory | None = None,
        constitution_validator: Any | None = None,
        glossary: Any | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            name: Human-readable name for the agent
            llm: LLM instance for text generation
            memory: Memory system for context storage (optional)
            constitution_validator: Constitutional rules validator (optional)
            glossary: Glossary manager for terminology consistency (optional)
        """
        self.name = name
        self.llm = llm
        self.memory = memory
        self.constitution_validator = constitution_validator
        self.glossary = glossary
        self.state = AgentState.IDLE
        self._execution_count = 0

    @timer("agent.execute")
    @async_trace("agent.execute")
    @async_track_errors()
    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the agent's main task.

        Args:
            input_data: Input data for the agent's task

        Returns:
            AgentResult with success status and output data
        """
        pass

    async def validate_with_constitution(
        self, domain: str, data: Any
    ) -> list[tuple[str, bool, str]]:
        """Validate data against constitutional rules for a domain.

        Args:
            domain: Rule domain (character, plot, world, style, consistency, ethical)
            data: Data to validate

        Returns:
            List of (rule_id, is_valid, error_message) tuples
        """
        if self.constitution_validator is None:
            return []
        # Assume constitution_validator has validate_domain method
        try:
            from src.novel.constitution import RuleDomain

            domain_enum = RuleDomain(domain.lower())
            return self.constitution_validator.validate_domain(domain_enum, data)
        except (ImportError, ValueError):
            # Fallback: treat domain as string
            return self.constitution_validator.validate_domain(domain, data)

    async def register_with_glossary(
        self, term: str, term_type: str, definition: str, **kwargs
    ) -> bool:
        """Register a term with the glossary.

        Args:
            term: Term name
            term_type: Type of term (character, location, etc.)
            definition: Definition of term
            **kwargs: Additional metadata

        Returns:
            True if registered successfully, False otherwise
        """
        if self.glossary is None:
            return False
        try:
            from src.novel.glossary import GlossaryTerm, TermStatus, TermType

            term_type_enum = TermType(term_type.lower())
            glossary_term = GlossaryTerm(
                term=term,
                type=term_type_enum,
                definition=definition,
                status=TermStatus.APPROVED,
                **kwargs,
            )
            await self.glossary.store_term(glossary_term)
            return True
        except (ImportError, ValueError, Exception):
            # Fallback: store as dictionary
            await self.glossary.store(
                f"terms/{term}",
                {"term": term, "type": term_type, "definition": definition, **kwargs},
            )
            return True

    def update_state(self, new_state: AgentState) -> None:
        """Update the agent's state.

        Args:
            new_state: New state to set
        """
        self.state = new_state

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, state={self.state.value})"
