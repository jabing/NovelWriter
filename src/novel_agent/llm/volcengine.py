# src/llm/volcengine.py
"""Volcengine Ark LLM integration - OpenAI-compatible API.

Supports:
- Doubao Seed 2.0 series (Code/Pro/Lite)
- Thinking mode with budget_tokens
- MiniMax, DeepSeek, GLM, Kimi models
"""

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


class VolcengineLLM(BaseLLM):
    """Volcengine Ark LLM client using OpenAI-compatible API.

    Supports Doubao Seed 2.0 series with thinking mode.
    """

    BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"

    MODELS = {
        "doubao-seed-2.0-code": "Doubao Seed 2.0 Code - Coding specialist",
        "doubao-seed-2.0-pro": "Doubao Seed 2.0 Pro - Best reasoning",
        "doubao-seed-2.0-lite": "Doubao Seed 2.0 Lite - Fast & cheap",
        "doubao-seed-code": "Doubao Seed Code - Coding model",
        "minimax-m2.5": "MiniMax M2.5 - Long context",
        "kimi-k2.5": "Kimi K2.5 - Moonshot model",
        "glm-4.7": "GLM 4.7 - Zhipu model",
        "deepseek-v3.2": "DeepSeek V3.2 - Cost effective",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "doubao-seed-2.0-pro",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        budget_tokens: int | None = None,
        max_retries: int = 3,
        base_url: str | None = None,
    ) -> None:
        """Initialize Volcengine client.

        Args:
            api_key: Volcengine API key (defaults to VOLCENGINE_API_KEY env var)
            model: Model to use (doubao-seed-2.0-pro, etc.)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            budget_tokens: Tokens reserved for thinking (default: max_tokens)
            max_retries: Maximum retry attempts
            base_url: API base URL (defaults to Volcengine endpoint)
        """
        api_key = api_key or os.getenv("VOLCENGINE_API_KEY")
        if not api_key:
            raise ValueError(
                "Volcengine API key required. Set VOLCENGINE_API_KEY or pass api_key parameter."
            )

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )
        self._client = None
        self._max_retries = max_retries
        self._base_url = base_url or os.getenv("VOLCENGINE_BASE_URL", self.BASE_URL)
        self._budget_tokens = budget_tokens or max_tokens

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

    @timer("llm.generate.volcengine")
    @async_trace("llm.generate.volcengine")
    @async_track_errors()
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        budget_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt."""
        return await self.generate_with_system(
            system_prompt="You are a creative fiction writer specializing in Chinese web novels.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            budget_tokens=budget_tokens,
            **kwargs,
        )

    @timer("llm.generate_with_system.volcengine")
    @async_trace("llm.generate_with_system.volcengine")
    @async_track_errors()
    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        budget_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text with system and user prompts.

        Supports thinking mode via extra_body parameter.
        """
        # Use instance defaults if not specified
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        budget_tokens = budget_tokens or self._budget_tokens

        async def _call_api() -> Any:
            client = self._get_client()

            # Build extra_body for thinking mode
            extra_body: dict[str, Any] = {}
            if budget_tokens:
                # Enable thinking mode for Doubao models
                extra_body["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": budget_tokens,
                }

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body=extra_body if budget_tokens else None,
                **kwargs,
            )

            return response

        response = await _retry_with_backoff(_call_api, max_retries=self._max_retries)

        # Extract content and thinking
        choice = response.choices[0]
        content = choice.message.content or ""
        reasoning_content = getattr(choice.message, "reasoning_content", "")

        tokens_used = response.usage.total_tokens if response.usage else 0

        self._total_tokens_used += tokens_used

        return LLMResponse(
            content=content,
            tokens_used=tokens_used,
            model=self.model,
            finish_reason=choice.finish_reason,
            metadata={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "reasoning_content": reasoning_content,
                "has_thinking": bool(reasoning_content),
            },
        )
