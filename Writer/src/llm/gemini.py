# src/llm/gemini.py
"""Gemini LLM integration via OpenAI-compatible API.

Provides access to Google's Gemini models with 1M+ token context windows,
ideal for long-form novel generation (50+ chapters).
"""

import logging
import os
from typing import Any

from src.llm.base import BaseLLM, LLMResponse
from src.monitoring import async_trace, async_track_errors, timer

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """Gemini LLM client using OpenAI-compatible API.

    Gemini models support up to 1M token context windows, making them
    ideal for long-form content generation like novels.

    Available models:
    - gemini-2.5-pro: Best quality, 1M context, multimodal
    - gemini-2.5-flash: Fast, 1M context, cost-efficient
    """

    # Default API base URL (laozhang proxy)
    DEFAULT_BASE_URL = "https://api.laozhang.ai/v1"

    # Available models with their characteristics
    MODELS = {
        "gemini-2.5-pro": {
            "context_window": 1_000_000,
            "description": "Best quality, multimodal, long context",
        },
        "gemini-2.5-flash": {
            "context_window": 1_000_000,
            "description": "Fast, cost-efficient, long context",
        },
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        base_url: str | None = None,
    ) -> None:
        """Initialize Gemini client.

        Args:
            api_key: API key (defaults to GEMINI_API_KEY or LAOZHANG_API_KEY env var)
            model: Model to use (gemini-2.5-pro or gemini-2.5-flash)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            base_url: API base URL (defaults to laozhang proxy)
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LAOZHANG_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY or LAOZHANG_API_KEY "
                "environment variable, or pass api_key parameter."
            )

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self._client = None

        logger.info(f"Initialized GeminiLLM with model={model}, base_url={self.base_url}")

    def _get_client(self) -> Any:
        """Get or create OpenAI client lazily.

        Returns:
            OpenAI client instance
        """
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")

            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        return self._client

    @timer("llm.generate.gemini")
    @async_trace("llm.generate.gemini")
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
            prompt: Input prompt for the LLM
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional parameters (passed to API)

        Returns:
            LLMResponse with generated content and metadata
        """
        client = self._get_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        logger.debug(
            f"Generating with Gemini: model={self.model}, temp={temp}, max_tokens={tokens}"
        )

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=tokens,
                **kwargs,
            )

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            self._total_tokens_used += tokens_used

            logger.debug(f"Gemini response: {len(content)} chars, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self.model,
                finish_reason=response.choices[0].finish_reason or "stop",
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    @timer("llm.generate_with_system.gemini")
    @async_trace("llm.generate_with_system.gemini")
    @async_track_errors()
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
            **kwargs: Additional parameters (passed to API)

        Returns:
            LLMResponse with generated content and metadata
        """
        client = self._get_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        logger.debug(
            f"Generating with Gemini (system+user): model={self.model}, "
            f"temp={temp}, max_tokens={tokens}"
        )

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temp,
                max_tokens=tokens,
                **kwargs,
            )

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            self._total_tokens_used += tokens_used

            logger.debug(f"Gemini response: {len(content)} chars, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                model=self.model,
                finish_reason=response.choices[0].finish_reason or "stop",
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "system_prompt_length": len(system_prompt),
                },
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    @property
    def context_window(self) -> int:
        """Get the context window size for the current model.

        Returns:
            Context window size in tokens
        """
        model_info = self.MODELS.get(self.model, {})
        return model_info.get("context_window", 1_000_000)

    def __repr__(self) -> str:
        return f"GeminiLLM(model={self.model}, context_window={self.context_window})"
