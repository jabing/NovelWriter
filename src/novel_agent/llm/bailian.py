# src/llm/bailian.py
"""Bailian (Alibaba Cloud) LLM integration - Anthropic-compatible API.

Supports:
- Qwen3.5 Plus, Qwen3 Max, Qwen3 Coder series
- Thinking mode with budget_tokens
- Multimodal input (text + images)
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


class BailianLLM(BaseLLM):
    """Bailian (Alibaba Cloud) LLM client using Anthropic-compatible API.

    Supports thinking mode with budget_tokens parameter.
    """

    BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"

    MODELS = {
        "qwen3.5-plus": "Qwen3.5 Plus - Balanced reasoning model",
        "qwen3-max-2026-01-23": "Qwen3 Max - Best reasoning model",
        "qwen3-coder-next": "Qwen3 Coder Next - Optimized for system novels",
        "qwen3-coder-plus": "Qwen3 Coder Plus - High volume coding",
        "glm-5": "GLM-5 - Zhipu's latest model",
        "glm-4.7": "GLM 4.7 - Balanced model",
        "kimi-k2.5": "Kimi K2.5 - Moonshot's latest",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "qwen3.5-plus",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        budget_tokens: int | None = None,
        max_retries: int = 3,
        base_url: str | None = None,
    ) -> None:
        """Initialize Bailian client.

        Args:
            api_key: Bailian API key (defaults to BAILIAN_API_KEY env var)
            model: Model to use (qwen3.5-plus, qwen3-max-2026-01-23, etc.)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            budget_tokens: Tokens reserved for thinking (default: max_tokens)
            max_retries: Maximum retry attempts
            base_url: API base URL (defaults to Bailian endpoint)
        """
        api_key = api_key or os.getenv("BAILIAN_API_KEY")
        if not api_key:
            raise ValueError(
                "Bailian API key required. Set BAILIAN_API_KEY or pass api_key parameter."
            )

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )
        self._client = None
        self._max_retries = max_retries
        self._base_url = base_url or os.getenv("BAILIAN_BASE_URL", self.BASE_URL)
        self._budget_tokens = budget_tokens or max_tokens

    def _get_client(self) -> Any:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )

            self._client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self._base_url,
            )
        return self._client

    @timer("llm.generate.bailian")
    @async_trace("llm.generate.bailian")
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

    @timer("llm.generate_with_system.bailian")
    @async_trace("llm.generate_with_system.bailian")
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

        Supports thinking mode via budget_tokens parameter.
        """
        # Use instance defaults if not specified
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        budget_tokens = budget_tokens or self._budget_tokens

        async def _call_api() -> Any:
            client = self._get_client()

            # Build message with optional thinking
            extra_headers: dict[str, Any] = {}
            if budget_tokens:
                # Enable thinking mode
                extra_headers["anthropic-beta"] = "thinking-2025-03-06"

            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                extra_headers=extra_headers if budget_tokens else None,
                **kwargs,
            )

            return response

        response = await _retry_with_backoff(_call_api, max_retries=self._max_retries)

        # Extract content and thinking
        content = ""
        thinking_content = ""

        if hasattr(response, "content") and response.content:
            for block in response.content:
                if hasattr(block, "type"):
                    if block.type == "text":
                        content += block.text
                    elif block.type == "thinking":
                        thinking_content = getattr(block, "thinking", "")

        tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, "usage") else 0

        self._total_tokens_used += tokens_used

        return LLMResponse(
            content=content,
            tokens_used=tokens_used,
            model=self.model,
            finish_reason=response.stop_reason if hasattr(response, "stop_reason") else "stop",
            metadata={
                "prompt_tokens": response.usage.input_tokens if hasattr(response, "usage") else 0,
                "completion_tokens": response.usage.output_tokens if hasattr(response, "usage") else 0,
                "thinking_tokens": response.usage.cache_read_input_tokens if hasattr(response, "usage") else 0,
                "thinking_content": thinking_content,
            },
        )
