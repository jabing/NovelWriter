# src/llm/infini.py
"""Infini AI (Kimi K2.5) LLM integration - OpenAI Compatible."""

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
    """Execute async function with retry and exponential backoff."""
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

    logger.error(f"All {max_retries} attempts failed")
    if last_exception:
        raise last_exception
    raise RuntimeError("Unknown error in retry logic")


class InfiniAILLM(BaseLLM):
    """Infini AI (Kimi K2.5) LLM client using OpenAI-compatible API.

    Note: Kimi K2.5 requires temperature=1.0 and doesn't support custom temperature.
    """

    BASE_URL = "https://cloud.infini-ai.com/maas/coding/v1"

    MODELS = {
        "kimi-k2.5": "Kimi K2.5 - Advanced reasoning model",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "kimi-k2.5",
        temperature: float = 1.0,  # Kimi requires exactly 1.0
        max_tokens: int = 4096,
        max_retries: int = 3,
        base_url: str | None = None,
    ) -> None:
        """Initialize Infini AI client.

        Args:
            api_key: Infini API key (defaults to INFINI_API_KEY env var)
            model: Model to use (kimi-k2.5)
            temperature: Must be 1.0 for Kimi K2.5
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts
            base_url: API base URL (defaults to Infini AI endpoint)
        """
        api_key = api_key or os.getenv("INFINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Infini API key required. Set INFINI_API_KEY or pass api_key parameter."
            )

        # Kimi K2.5 requires temperature=1.0
        if temperature != 1.0:
            logger.warning(f"Kimi K2.5 requires temperature=1.0, ignoring {temperature}")
            temperature = 1.0

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )
        self._client = None
        self._max_retries = max_retries
        self._base_url = base_url or os.getenv("INFINI_BASE_URL", self.BASE_URL)

    def _get_client(self) -> Any:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self._base_url,
            )
        return self._client

    @timer("llm.generate.infini")
    @async_trace("llm.generate.infini")
    @async_track_errors()
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt."""
        return await self.generate_with_system(
            system_prompt="You are a creative fiction writer specializing in fantasy novels.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @timer("llm.generate_with_system.infini")
    @async_trace("llm.generate_with_system.infini")
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

        Note: Kimi K2.5 requires temperature=1.0, this parameter is fixed.
        """

        # Remove temperature from kwargs if present - Kimi requires 1.0
        if "temperature" in kwargs:
            del kwargs["temperature"]

        async def _call_api() -> Any:
            client = self._get_client()
            return await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=1.0,  # Kimi K2.5 requires exactly 1.0
                max_tokens=max_tokens or self.max_tokens,
                **kwargs,
            )

        response = await _retry_with_backoff(_call_api, max_retries=self._max_retries)

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

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
