"""Retry handler with exponential backoff for robust LLM operations.

This module provides retry logic with configurable exponential backoff
for handling transient failures during chapter generation.
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Error that can be retried."""

    pass


class NonRetryableError(Exception):
    """Error that should not be retried."""

    pass


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts
        base_delay_seconds: Initial delay before first retry
        max_delay_seconds: Maximum delay cap
        exponential_base: Multiplier for exponential backoff
        jitter: Whether to add randomness to delays
        retryable_errors: List of error types that should be retried
    """

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: list[str] = field(
        default_factory=lambda: [
            "rate_limit",
            "timeout",
            "temporary_failure",
            "content_too_short",
            "validation_failed",
            "service_unavailable",
        ]
    )


@dataclass
class RetryResult:
    """Result of a retry operation.

    Attributes:
        success: Whether the operation ultimately succeeded
        attempts: Number of attempts made
        final_content: The successful content (if any)
        last_error: The last error encountered
        total_delay_seconds: Total time spent in delays
    """

    success: bool
    attempts: int
    final_content: str | None
    last_error: str | None
    total_delay_seconds: float


class RetryHandler:
    """Handles retry logic with exponential backoff.

    This class provides robust retry capabilities for operations that
    may fail transiently, such as LLM API calls.

    Features:
    - Exponential backoff with configurable parameters
    - Optional jitter to prevent thundering herd
    - Configurable retryable error types
    - Comprehensive logging

    Example:
        >>> handler = RetryHandler()
        >>> result = await handler.execute_with_retry(
        ...     operation=lambda: llm.generate(prompt),
        ...     validator=lambda content: len(content) > 100,
        ... )
        >>> if result.success:
        ...     print(f"Generated: {result.final_content[:100]}")
    """

    def __init__(self, config: RetryConfig | None = None):
        """Initialize the retry handler.

        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[str]],
        validator: Callable[[str], bool] | None = None,
        on_retry: Callable[[int, Exception], None] | None = None,
    ) -> RetryResult:
        """Execute an operation with retry logic.

        Args:
            operation: Async function that generates content
            validator: Optional function to validate result
            on_retry: Optional callback called before each retry

        Returns:
            RetryResult with the outcome
        """
        attempts = 0
        total_delay = 0.0
        last_error: str | None = None
        content: str | None = None

        while attempts < self.config.max_attempts:
            attempts += 1

            try:
                # Execute the operation
                content = await operation()

                # Validate if validator provided
                if validator is not None:
                    if not validator(content):
                        raise RetryableError("Validation failed - content did not meet criteria")

                # Success!
                logger.info(f"Operation succeeded on attempt {attempts}")
                return RetryResult(
                    success=True,
                    attempts=attempts,
                    final_content=content,
                    last_error=None,
                    total_delay_seconds=total_delay,
                )

            except RetryableError as e:
                last_error = str(e)
                error_type = self._classify_error(e)

                if error_type not in self.config.retryable_errors:
                    logger.warning(f"Non-retryable error: {e}")
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        final_content=content,
                        last_error=last_error,
                        total_delay_seconds=total_delay,
                    )

                if attempts < self.config.max_attempts:
                    delay = self._calculate_delay(attempts)
                    total_delay += delay

                    logger.warning(
                        f"Attempt {attempts}/{self.config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempts, e)

                    await asyncio.sleep(delay)

            except NonRetryableError as e:
                # Don't retry non-retryable errors
                last_error = str(e)
                logger.error(f"Non-retryable error: {e}")
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    final_content=content,
                    last_error=last_error,
                    total_delay_seconds=total_delay,
                )

            except Exception as e:
                # Unexpected error - classify it
                last_error = str(e)
                error_type = self._classify_error(e)

                if error_type in self.config.retryable_errors:
                    if attempts < self.config.max_attempts:
                        delay = self._calculate_delay(attempts)
                        total_delay += delay
                        logger.warning(
                            f"Attempt {attempts}/{self.config.max_attempts} failed with unexpected error: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                else:
                    logger.error(f"Unexpected non-retryable error: {e}")
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        final_content=content,
                        last_error=last_error,
                        total_delay_seconds=total_delay,
                    )

        # All attempts exhausted
        logger.error(f"All {attempts} attempts failed. Last error: {last_error}")
        return RetryResult(
            success=False,
            attempts=attempts,
            final_content=content,
            last_error=last_error,
            total_delay_seconds=total_delay,
        )

    def execute_sync_with_retry(
        self,
        operation: Callable[[], str],
        validator: Callable[[str], bool] | None = None,
    ) -> RetryResult:
        """Synchronous version of execute_with_retry.

        Args:
            operation: Sync function that generates content
            validator: Optional function to validate result

        Returns:
            RetryResult with the outcome
        """
        import time

        attempts = 0
        total_delay = 0.0
        last_error: str | None = None
        content: str | None = None

        while attempts < self.config.max_attempts:
            attempts += 1

            try:
                content = operation()

                if validator is not None and not validator(content):
                    raise RetryableError("Validation failed")

                return RetryResult(
                    success=True,
                    attempts=attempts,
                    final_content=content,
                    last_error=None,
                    total_delay_seconds=total_delay,
                )

            except RetryableError as e:
                last_error = str(e)

                if attempts < self.config.max_attempts:
                    delay = self._calculate_delay(attempts)
                    total_delay += delay
                    logger.warning(f"Attempt {attempts} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)

            except NonRetryableError as e:
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    final_content=content,
                    last_error=str(e),
                    total_delay_seconds=total_delay,
                )

            except Exception as e:
                last_error = str(e)
                if attempts < self.config.max_attempts:
                    delay = self._calculate_delay(attempts)
                    total_delay += delay
                    time.sleep(delay)

        return RetryResult(
            success=False,
            attempts=attempts,
            final_content=content,
            last_error=last_error,
            total_delay_seconds=total_delay,
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.config.base_delay_seconds * (self.config.exponential_base ** (attempt - 1))

        # Cap at maximum
        delay = min(delay, self.config.max_delay_seconds)

        # Add jitter if enabled
        if self.config.jitter:
            # Add up to 25% randomness
            delay *= 1 + 0.25 * random.random()

        return delay

    def _classify_error(self, error: Exception) -> str:
        """Classify an error into a type.

        Args:
            error: The exception that occurred

        Returns:
            Error type string
        """
        error_str = str(error).lower()

        # Rate limiting
        if any(term in error_str for term in ["rate limit", "429", "too many requests"]):
            return "rate_limit"

        # Timeout
        if any(term in error_str for term in ["timeout", "timed out", "deadline"]):
            return "timeout"

        # Service unavailable
        if any(term in error_str for term in ["503", "service unavailable", "overloaded"]):
            return "service_unavailable"

        # Content issues
        if any(term in error_str for term in ["too short", "empty", "no content"]):
            return "content_too_short"

        # Validation
        if "validation" in error_str:
            return "validation_failed"

        # Default to temporary
        return "temporary_failure"
