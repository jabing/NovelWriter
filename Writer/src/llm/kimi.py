# src/llm/kimi.py
"""Kimi LLM integration - Moonshot AI's K2.5 model."""

import os
from typing import Any

from src.llm.base import BaseLLM, LLMResponse
from src.monitoring import async_trace, async_track_errors, timer


class KimiLLM(BaseLLM):
    """Kimi K2.5 LLM client using OpenAI-compatible API.

    Kimi K2.5 is currently the best open-source model for Chinese creative writing,
    with 1T total parameters and strong emotional nuance.

    Supports both:
    - Official Moonshot API (platform.moonshot.cn)
    - Third-party proxies (Infini AI, etc.) via OpenAI-compatible endpoints
    """

    # API base URLs
    OFFICIAL_BASE_URL = "https://api.moonshot.cn/v1"

    # Available models
    MODELS = {
        "kimi-k2.5": "Kimi K2.5 - 1T params, best for creative writing",
        "kimi-k2": "Kimi K2 - Previous version",
        "kimi-latest": "Always points to latest model",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "kimi-k2.5",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        base_url: str | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize Kimi client.

        Args:
            api_key: Kimi API key (defaults to MOONSHOT_API_KEY or KIMI_API_KEY env var)
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            base_url: Custom base URL for third-party proxies (e.g., Infini AI)
            max_retries: Maximum retry attempts
        """
        api_key = api_key or os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError(
                "Kimi API key required. Set MOONSHOT_API_KEY or KIMI_API_KEY env var, "
                "or pass api_key parameter."
            )

        super().__init__(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
        )

        # Use custom base URL if provided (for Infini AI, etc.)
        self.base_url = base_url or self.OFFICIAL_BASE_URL
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
                base_url=self.base_url,  # Can be official or third-party
            )
        return self._client

    @timer("llm.generate.kimi")
    @async_trace("llm.generate.kimi")
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
            system_prompt="You are a creative fiction writer specializing in web novels.",
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @timer("llm.generate_with_system.kimi")
    @async_trace("llm.generate_with_system.kimi")
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

        Note: When using Infini AI or other proxies, some advanced features
        like Agent Swarm may not be available.
        """
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )

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
                "provider": "moonshot" if "moonshot" in self.base_url else "third_party",
                "base_url": self.base_url,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    @property
    def is_using_proxy(self) -> bool:
        """Check if using third-party proxy instead of official API."""
        return self.base_url != self.OFFICIAL_BASE_URL

    def get_proxy_warnings(self) -> list[str]:
        """Get warnings about third-party proxy limitations."""
        if not self.is_using_proxy:
            return []

        warnings = [
            "Using third-party proxy API instead of official Moonshot API",
            "Some advanced features may not be available:",
            "  - Agent Swarm (multi-agent parallelism)",
            "  - Native multimodal features (image/video)",
            "  - Real-time streaming optimizations",
            "  - Official rate limits and quotas",
        ]

        # Infini AI specific
        if "infini" in self.base_url.lower():
            warnings.extend(
                [
                    "\nInfini AI specific notes:",
                    "  - Verify token pricing differs from official",
                    "  - Check if context window is limited vs official 256K",
                    "  - Confirm availability of k2.5 vs k2 model",
                ]
            )

        return warnings
