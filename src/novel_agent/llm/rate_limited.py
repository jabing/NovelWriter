"""Rate-limited LLM wrapper for API call management.

This module provides a wrapper class that adds rate limiting capabilities
to any LLM implementation, preventing API rate limit errors and ensuring
stable throughput.
"""

import asyncio
import logging
import time
from typing import Any

from src.novel_agent.llm.base import BaseLLM, LLMResponse
from src.novel_agent.utils.batch import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitedLLM(BaseLLM):
    """Rate-limited wrapper for LLM implementations.

    This class wraps any BaseLLM implementation and adds rate limiting
    to prevent API rate limit errors. It uses a token bucket algorithm
    to control request rate.

    Example:
        >>> base_llm = DeepSeekLLM(api_key="...")
        >>> rate_limited = RateLimitedLLM(
        ...     base_llm,
        ...     calls_per_second=2.0,  # 2 calls per second
        ...     burst_size=5  # Allow burst of 5 calls
        ... )
        >>> response = await rate_limited.generate("Hello, world!")
    """

    def __init__(
        self,
        base_llm: BaseLLM,
        calls_per_second: float = 2.0,
        burst_size: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        """Initialize rate-limited LLM wrapper.

        Args:
            base_llm: The underlying LLM implementation to wrap.
            calls_per_second: Maximum API calls per second.
            burst_size: Maximum burst size for token bucket.
            max_retries: Maximum retry attempts on rate limit errors.
            retry_delay: Base delay for retries (exponential backoff).
            max_delay: Maximum delay between retries.
        """
        # Initialize BaseLLM with same parameters as base_llm
        super().__init__(
            api_key=base_llm.api_key,
            model=base_llm.model,
            temperature=base_llm.temperature,
            max_tokens=base_llm.max_tokens,
        )

        self._base_llm = base_llm
        self._rate_limiter = RateLimiter(
            calls_per_second=calls_per_second,
            burst_size=burst_size,
        )
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._max_delay = max_delay

        # Statistics
        self._total_calls = 0
        self._rate_limited_count = 0
        self._total_wait_time = 0.0

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from a prompt with rate limiting.

        Args:
            prompt: Input prompt for the LLM.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with generated content.
        """
        return await self._execute_with_rate_limit(
            lambda: self._base_llm.generate(prompt, temperature, max_tokens, **kwargs)
        )

    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text with system and user prompts with rate limiting.

        Args:
            system_prompt: System message for context/behavior.
            user_prompt: User message with the actual request.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with generated content.
        """
        return await self._execute_with_rate_limit(
            lambda: self._base_llm.generate_with_system(
                system_prompt, user_prompt, temperature, max_tokens, **kwargs
            )
        )

    async def _execute_with_rate_limit(
        self,
        operation: Any,
    ) -> LLMResponse:
        """Execute an LLM operation with rate limiting and retries.

        Args:
            operation: Callable that returns a coroutine for the LLM operation.

        Returns:
            LLMResponse from the operation.

        Raises:
            Exception: If all retries fail.
        """
        self._total_calls += 1
        delay = self._retry_delay
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            # Wait for rate limiter
            wait_start = time.time()
            await self._rate_limiter.wait_and_acquire()
            wait_time = time.time() - wait_start
            self._total_wait_time += wait_time

            if wait_time > 0.1:
                logger.debug(f"Rate limiter wait: {wait_time:.2f}s")

            try:
                response = await operation()
                # Update token count from base LLM
                self._total_tokens_used = self._base_llm.total_tokens_used
                return response

            except Exception as e:
                last_exception = e
                str(e).lower()

                # Check if it's a rate limit error
                if self._is_rate_limit_error(e):
                    self._rate_limited_count += 1
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{self._max_retries + 1}): {e}"
                    )

                    if attempt < self._max_retries:
                        # Exponential backoff
                        logger.info(f"Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, self._max_delay)
                        continue
                else:
                    # Non-rate-limit error, don't retry
                    raise

        # All retries exhausted
        logger.error(f"All {self._max_retries + 1} attempts failed")
        if last_exception:
            raise last_exception
        raise RuntimeError("Unknown error in rate-limited execution")

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if an error is a rate limit error.

        Args:
            error: Exception to check.

        Returns:
            True if it's a rate limit error.
        """
        error_str = str(error).lower()

        # Common rate limit indicators
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
            "throttl",
            "slow down",
            "limit exceeded",
            "requests per",
        ]

        return any(indicator in error_str for indicator in rate_limit_indicators)

    @property
    def stats(self) -> dict[str, Any]:
        """Get rate limiting statistics.

        Returns:
            Dictionary with statistics including:
            - total_calls: Total number of API calls
            - rate_limited_count: Number of rate limit errors encountered
            - total_wait_time: Total time spent waiting for rate limiter
            - base_llm_model: Model name of underlying LLM
        """
        return {
            "total_calls": self._total_calls,
            "rate_limited_count": self._rate_limited_count,
            "total_wait_time": self._total_wait_time,
            "base_llm_model": self._base_llm.model,
            "base_llm_tokens": self._base_llm.total_tokens_used,
        }

    def reset_stats(self) -> None:
        """Reset rate limiting statistics."""
        self._total_calls = 0
        self._rate_limited_count = 0
        self._total_wait_time = 0.0


def create_rate_limited_llm(
    base_llm: BaseLLM,
    calls_per_second: float = 2.0,
    burst_size: int = 5,
) -> RateLimitedLLM:
    """Factory function to create a rate-limited LLM.

    Args:
        base_llm: The underlying LLM implementation.
        calls_per_second: Maximum API calls per second.
        burst_size: Maximum burst size.

    Returns:
        RateLimitedLLM wrapping the base LLM.
    """
    return RateLimitedLLM(
        base_llm=base_llm,
        calls_per_second=calls_per_second,
        burst_size=burst_size,
    )
