# src/novel_agent/novel/retry_policy.py
"""Intelligent retry policy with exponential backoff for robust operations.

This module provides a configurable retry mechanism with exponential backoff
for handling transient failures during operations like LLM calls or API requests.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts (not including initial attempt).
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Multiplier for exponential backoff calculation.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed).

        Uses exponential backoff formula:
            delay = min(base_delay * (exponential_base ** attempt), max_delay)

        Args:
            attempt: The attempt number (0 for first retry, 1 for second, etc.)

        Returns:
            Delay in seconds, capped at max_delay.
        """
        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


@dataclass
class RetryResult:
    """Result of a retry operation.

    Attributes:
        success: Whether the operation ultimately succeeded.
        result: The return value from the successful operation.
        error: The last exception that occurred (if failed).
        attempts: Total number of attempts made (including initial attempt).
        last_error: The last exception encountered (same as error for compatibility).
    """

    success: bool
    result: Any = None
    error: Exception | None = None
    attempts: int = 0
    last_error: Exception | None = None


class RetryManager:
    """Manages retry logic for operations with configurable exponential backoff.

    This class provides robust retry capabilities for operations that may fail
    transiently. It tracks retry counts across all operations and logs retry
    attempts with detailed context.

    Example:
        >>> policy = RetryPolicy(max_retries=3, base_delay=1.0)
        >>> manager = RetryManager(policy)
        >>>
        >>> async def fetch_data():
        ...     # Operation that may fail
        ...     return await api.call()
        >>>
        >>> result = await manager.execute_with_retry(fetch_data)
        >>> if result.success:
        ...     print(f"Got: {result.result}")
        ... else:
        ...     print(f"Failed after {result.attempts} attempts: {result.error}")
    """

    def __init__(self, policy: RetryPolicy | None = None) -> None:
        """Initialize the retry manager.

        Args:
            policy: Retry policy configuration. Uses defaults if None.
        """
        self.policy = policy or RetryPolicy()
        self._retry_count = 0

    async def execute_with_retry(
        self,
        operation: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult:
        """Execute an async operation with retry on failure.

        Retries the operation up to max_retries times using exponential backoff
        delays. Logs each retry attempt with the reason for failure.

        Args:
            operation: Async function to execute.
            *args: Positional arguments to pass to the operation.
            **kwargs: Keyword arguments to pass to the operation.

        Returns:
            RetryResult containing success status, result (if successful),
            error details (if failed), and attempt count.
        """
        attempts = 0
        last_error: Exception | None = None
        max_attempts = self.policy.max_retries + 1  # +1 for initial attempt

        while attempts < max_attempts:
            attempts += 1

            try:
                result = await operation(*args, **kwargs)
                logger.debug(f"Operation succeeded on attempt {attempts}/{max_attempts}")
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    last_error=None,
                )

            except Exception as e:
                last_error = e
                self._retry_count += 1

                if attempts < max_attempts:
                    # Calculate delay for this retry (0-indexed attempt)
                    delay = self.policy.calculate_delay(attempts - 1)

                    logger.warning(
                        f"Attempt {attempts}/{max_attempts} failed: "
                        f"{type(e).__name__}: {e}. "
                        f"Retrying in {delay:.1f}s... (retry #{self._retry_count})"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {attempts} attempts exhausted. Last error: {type(e).__name__}: {e}"
                    )

        return RetryResult(
            success=False,
            result=None,
            error=last_error,
            attempts=attempts,
            last_error=last_error,
        )

    def get_retry_count(self) -> int:
        """Return total retries across all operations.

        Returns:
            Total number of retry attempts made across all execute_with_retry calls.
        """
        return self._retry_count

    def reset_retry_count(self) -> None:
        """Reset the total retry counter to zero."""
        self._retry_count = 0
