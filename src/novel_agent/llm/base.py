# src/llm/base.py
"""Base class for LLM integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.novel_agent.monitoring import async_trace, async_track_errors, timer


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    tokens_used: int
    model: str
    finish_reason: str = "stop"
    metadata: dict[str, Any] | None = None


class BaseLLM(ABC):
    """Abstract base class for LLM integrations.

    All LLM implementations (DeepSeek, OpenAI, Claude, etc.) should inherit
    from this class and implement the required methods.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the LLM client.

        Args:
            api_key: API key for the LLM service
            model: Model identifier to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._total_tokens_used = 0

    @timer("llm.generate")
    @async_trace("llm.generate")
    @async_track_errors()
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt for the LLM
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    def generate_sync(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Synchronous wrapper for generate().

        Args:
            prompt: Input prompt for the LLM
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        import asyncio

        return asyncio.run(self.generate(prompt, temperature, max_tokens, **kwargs))

    @timer("llm.generate_with_system")
    @async_trace("llm.generate_with_system")
    @async_track_errors()
    @abstractmethod
    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text with separate system and user prompts.

        Args:
            system_prompt: System message for context/behavior
            user_prompt: User message with the actual request
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @property
    def total_tokens_used(self) -> int:
        """Total tokens used across all calls."""
        return self._total_tokens_used

    def reset_token_count(self) -> None:
        """Reset the token counter."""
        self._total_tokens_used = 0
