# src/llm/deepseek.py
"""DeepSeek LLM integration."""

import asyncio
import logging
import os
from typing import Any

from src.novel_agent.llm.base import BaseLLM, LLMResponse
from src.novel_agent.monitoring import async_trace, async_track_errors, timer

logger = logging.getLogger(__name__)


async def _retry_with_backoff(
    func: Any,
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs: Any,
) -> Any:
    """Execute async function with retry and exponential backoff.

    Args:
        func: Async function to execute
        *args: Positional arguments
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        **kwargs: Keyword arguments

    Returns:
        Result of the function

    Raises:
        Last exception if all retries fail
    """
    delay = base_delay
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)

    # All retries exhausted
    logger.error(f"All {max_retries} attempts failed")
    if last_exception:
        raise last_exception
    raise RuntimeError("Unknown error in retry logic")


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM client using OpenAI-compatible API.

    DeepSeek provides an OpenAI-compatible API endpoint, so we use
    the openai library for integration.
    """

    # DeepSeek API base URL
    BASE_URL = "https://api.deepseek.com/v1"

    # Available models
    MODELS = {
        "deepseek-chat": "General purpose chat model",
        "deepseek-coder": "Code-specialized model",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> None:
        """Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)
            model: Model to use (deepseek-chat or deepseek-coder)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts for API calls
        """
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DeepSeek API key required. Set DEEPSEEK_API_KEY or pass api_key parameter."
            )

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )
        self._client = None
        self._max_retries = max_retries

    def _get_client(self) -> Any:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL,
            )
        return self._client

    @timer("llm.generate.deepseek")
    @async_trace("llm.generate.deepseek")
    @async_track_errors()
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content
        """
        return await self.generate_with_system(
            system_prompt="You are a creative fiction writer.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @timer("llm.generate_with_system.deepseek")
    @async_trace("llm.generate_with_system.deepseek")
    @async_track_errors()
    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text with system and user prompts.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content
        """

        async def _call_api() -> Any:
            client = self._get_client()
            return await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs,
            )

        response = await _retry_with_backoff(_call_api, max_retries=self._max_retries)

        # Extract response data
        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Update token counter
        self._total_tokens_used += tokens_used

        return LLMResponse(
            content=content,
            tokens_used=tokens_used,
            model=self.model,
            finish_reason=response.choices[0].finish_reason,
            metadata={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )
