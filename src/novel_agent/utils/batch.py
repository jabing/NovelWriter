# src/utils/batch.py
"""Batch processing utilities for performance optimization."""

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchResult(Generic[T]):
    """Result of batch processing."""

    success: bool
    results: list[T]
    errors: list[dict[str, Any]]
    total_time: float
    batch_count: int


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    batch_size: int = 10
    max_concurrent: int = 5
    delay_between_batches: float = 0.1  # seconds
    retry_failed: bool = True
    max_retries: int = 2


class BatchProcessor(Generic[T, R]):
    """Process items in batches with concurrency control."""

    def __init__(
        self,
        processor: Callable[[list[T]], Coroutine[Any, Any, list[R]]],
        config: BatchConfig | None = None,
    ) -> None:
        """Initialize batch processor.

        Args:
            processor: Async function to process a batch of items
            config: Batch processing configuration
        """
        self.processor = processor
        self.config = config or BatchConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)

    async def process(self, items: list[T]) -> BatchResult[R]:
        """Process all items in batches.

        Args:
            items: Items to process

        Returns:
            BatchResult with processed results
        """
        start_time = time.time()
        results: list[R] = []
        errors: list[dict[str, Any]] = []

        # Split into batches
        batches = [
            items[i : i + self.config.batch_size]
            for i in range(0, len(items), self.config.batch_size)
        ]

        # Process batches with concurrency control
        async def process_batch(
            batch: list[T], batch_idx: int
        ) -> tuple[list[R], dict[str, Any] | None]:
            """Process a single batch with retry logic."""
            async with self._semaphore:
                for attempt in range(self.config.max_retries + 1):
                    try:
                        batch_results = await self.processor(batch)
                        return batch_results, None
                    except Exception as e:
                        if attempt == self.config.max_retries:
                            return [], {
                                "batch_index": batch_idx,
                                "error": str(e),
                                "item_count": len(batch),
                            }
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

                return [], {"batch_index": batch_idx, "error": "Max retries exceeded"}

        # Process all batches concurrently (limited by semaphore)
        tasks = [process_batch(batch, idx) for idx, batch in enumerate(batches)]

        batch_results = await asyncio.gather(*tasks)

        # Collect results
        for batch_result, error in batch_results:
            results.extend(batch_result)
            if error:
                errors.append(error)

        total_time = time.time() - start_time

        return BatchResult(
            success=len(errors) == 0,
            results=results,
            errors=errors,
            total_time=total_time,
            batch_count=len(batches),
        )


class AsyncQueue:
    """Async queue for background processing."""

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize async queue.

        Args:
            max_size: Maximum queue size
        """
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._processed = 0
        self._errors = 0

    async def put(self, item: Any) -> bool:
        """Add item to queue.

        Args:
            item: Item to add

        Returns:
            True if added successfully
        """
        try:
            self._queue.put_nowait(item)
            return True
        except asyncio.QueueFull:
            return False

    async def get(self) -> Any:
        """Get item from queue.

        Returns:
            Next item from queue
        """
        return await self._queue.get()

    def task_done(self) -> None:
        """Mark task as done."""
        self._queue.task_done()
        self._processed += 1

    def mark_error(self) -> None:
        """Mark an error occurred."""
        self._errors += 1

    @property
    def size(self) -> int:
        """Current queue size."""
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    async def join(self) -> None:
        """Wait for all items to be processed."""
        await self._queue.join()

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        return {
            "current_size": self.size,
            "processed": self._processed,
            "errors": self._errors,
        }


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(
        self,
        calls_per_second: float = 10,
        burst_size: int = 20,
    ) -> None:
        """Initialize rate limiter.

        Args:
            calls_per_second: Maximum calls per second
            burst_size: Maximum burst size
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size
        self._tokens: float = float(burst_size)
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update

            # Replenish tokens
            self._tokens = min(self.burst_size, self._tokens + elapsed * self.calls_per_second)
            self._last_update = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    async def wait_and_acquire(self, tokens: int = 1) -> None:
        """Wait until tokens are available and acquire.

        Args:
            tokens: Number of tokens to acquire
        """
        while not await self.acquire(tokens):
            wait_time = (tokens - self._tokens) / self.calls_per_second
            await asyncio.sleep(max(0.01, wait_time))


async def process_in_parallel(
    items: list[T],
    processor: Callable[[T], Coroutine[Any, Any, R]],
    max_concurrent: int = 10,
) -> list[tuple[T, R | Exception]]:
    """Process items in parallel with concurrency limit.

    Args:
        items: Items to process
        processor: Async function to process each item
        max_concurrent: Maximum concurrent operations

    Returns:
        List of (item, result) tuples
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[tuple[T, R | Exception]] = []

    async def process_with_semaphore(item: T) -> tuple[T, R | Exception]:
        async with semaphore:
            try:
                result = await processor(item)
                return (item, result)
            except Exception as e:
                return (item, e)

    tasks = [process_with_semaphore(item) for item in items]
    results = await asyncio.gather(*tasks)

    return results


async def chunk_and_process(
    items: list[T],
    processor: Callable[[list[T]], Coroutine[Any, Any, list[R]]],
    chunk_size: int = 10,
) -> list[R]:
    """Process items in chunks.

    Args:
        items: Items to process
        processor: Async function to process a chunk
        chunk_size: Size of each chunk

    Returns:
        Flattened list of results
    """
    if not items:
        return []

    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    results = await asyncio.gather(*[processor(chunk) for chunk in chunks])

    # Flatten results
    return [item for sublist in results for item in sublist]
