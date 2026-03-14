# src/utils/performance.py
"""Performance monitoring and metrics collection."""

import time
from collections import defaultdict
from collections.abc import Callable, Coroutine
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: float
    value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class TimingStats:
    """Statistics for timing measurements."""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    last_time: float = 0.0

    def update(self, elapsed: float) -> None:
        """Update statistics with new measurement."""
        self.count += 1
        self.total_time += elapsed
        self.last_time = elapsed
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.avg_time = self.total_time / self.count


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""

    def __init__(self, name: str = "default") -> None:
        """Initialize performance monitor.

        Args:
            name: Monitor name for identification
        """
        self.name = name
        self._timings: dict[str, TimingStats] = defaultdict(TimingStats)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.time()

    @contextmanager
    def measure(self, operation: str) -> Any:
        """Context manager to measure operation time.

        Args:
            operation: Operation name

        Yields:
            TimingStats for the operation
        """
        start = time.time()
        try:
            yield self._timings[operation]
        finally:
            elapsed = time.time() - start
            self._timings[operation].update(elapsed)

    def start_timer(self, operation: str) -> float:
        """Start a timer for an operation.

        Args:
            operation: Operation name

        Returns:
            Start time
        """
        return time.time()

    def stop_timer(self, operation: str, start_time: float) -> None:
        """Stop timer and record elapsed time.

        Args:
            operation: Operation name
            start_time: Start time from start_timer
        """
        elapsed = time.time() - start_time
        self._timings[operation].update(elapsed)

    async def measure_async_op(self, operation: str, coro: Coroutine[Any, Any, T]) -> T:
        """Measure an async operation.

        Args:
            operation: Operation name
            coro: Coroutine to measure

        Returns:
            Result of the coroutine
        """
        start = time.time()
        try:
            result = await coro
            return result
        finally:
            elapsed = time.time() - start
            self._timings[operation].update(elapsed)

    def increment(self, counter: str, amount: int = 1) -> None:
        """Increment a counter.

        Args:
            counter: Counter name
            amount: Amount to increment
        """
        self._counters[counter] += amount

    def set_gauge(self, gauge: str, value: float) -> None:
        """Set a gauge value.

        Args:
            gauge: Gauge name
            value: Gauge value
        """
        self._gauges[gauge] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record a value in a histogram.

        Args:
            name: Histogram name
            value: Value to record
        """
        self._histograms[name].append(value)
        # Keep only last 1000 values
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def get_timing(self, operation: str) -> TimingStats | None:
        """Get timing statistics for an operation.

        Args:
            operation: Operation name

        Returns:
            TimingStats or None if not measured
        """
        return self._timings.get(operation)

    def get_counter(self, counter: str) -> int:
        """Get counter value.

        Args:
            counter: Counter name

        Returns:
            Counter value
        """
        return self._counters.get(counter, 0)

    def get_gauge(self, gauge: str) -> float | None:
        """Get gauge value.

        Args:
            gauge: Gauge name

        Returns:
            Gauge value or None
        """
        return self._gauges.get(gauge)

    def get_histogram_percentile(self, name: str, percentile: float) -> float | None:
        """Get percentile value from histogram.

        Args:
            name: Histogram name
            percentile: Percentile (0-100)

        Returns:
            Percentile value or None
        """
        values = self._histograms.get(name, [])
        if not values:
            return None

        sorted_values = sorted(values)
        idx = int(len(sorted_values) * percentile / 100)
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]

    def get_all_stats(self) -> dict[str, Any]:
        """Get all statistics.

        Returns:
            Dictionary of all metrics
        """
        uptime = time.time() - self._start_time

        return {
            "name": self.name,
            "uptime_seconds": round(uptime, 2),
            "timings": {
                op: {
                    "count": stats.count,
                    "total_time": round(stats.total_time, 4),
                    "avg_time": round(stats.avg_time, 4),
                    "min_time": round(stats.min_time, 4) if stats.min_time != float("inf") else 0,
                    "max_time": round(stats.max_time, 4),
                    "last_time": round(stats.last_time, 4),
                }
                for op, stats in self._timings.items()
            },
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "p50": self.get_histogram_percentile(name, 50),
                    "p90": self.get_histogram_percentile(name, 90),
                    "p99": self.get_histogram_percentile(name, 99),
                }
                for name, values in self._histograms.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._timings.clear()
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_time = time.time()


def timed(monitor: PerformanceMonitor, operation: str | None = None) -> Callable:
    """Decorator to time function execution.

    Args:
        monitor: PerformanceMonitor instance
        operation: Operation name (uses function name if None)

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with monitor.measure(op_name):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def async_timed(monitor: PerformanceMonitor, operation: str | None = None) -> Callable:
    """Decorator to time async function execution.

    Args:
        monitor: PerformanceMonitor instance
        operation: Operation name (uses function name if None)

    Returns:
        Decorated async function
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        op_name = operation or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await monitor.measure_async_op(op_name, func(*args, **kwargs))

        return wrapper
    return decorator


class TokenTracker:
    """Track LLM token usage and costs."""

    # Approximate costs per 1K tokens (as of 2024)
    COSTS = {
        "deepseek": {"input": 0.001, "output": 0.002},
        "openai": {"input": 0.03, "output": 0.06},
        "anthropic": {"input": 0.015, "output": 0.075},
    }

    def __init__(self, provider: str = "deepseek") -> None:
        """Initialize token tracker.

        Args:
            provider: LLM provider name
        """
        self.provider = provider
        self._input_tokens = 0
        self._output_tokens = 0
        self._request_count = 0
        self._costs = self.COSTS.get(provider, {"input": 0, "output": 0})

    def record(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._request_count += 1

    def get_usage(self) -> dict[str, Any]:
        """Get token usage statistics.

        Returns:
            Usage statistics
        """
        input_cost = (self._input_tokens / 1000) * self._costs["input"]
        output_cost = (self._output_tokens / 1000) * self._costs["output"]

        return {
            "provider": self.provider,
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "total_tokens": self._input_tokens + self._output_tokens,
            "request_count": self._request_count,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(input_cost + output_cost, 4),
        }

    def reset(self) -> None:
        """Reset token counts."""
        self._input_tokens = 0
        self._output_tokens = 0
        self._request_count = 0


class MemoryTracker:
    """Track memory usage for operations."""

    def __init__(self) -> None:
        """Initialize memory tracker."""
        self._operations: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def record(self, operation: str, size_bytes: int) -> None:
        """Record memory usage for an operation.

        Args:
            operation: Operation name
            size_bytes: Memory size in bytes
        """
        self._operations[operation].append({
            "timestamp": datetime.now().isoformat(),
            "size_bytes": size_bytes,
        })

    def get_stats(self) -> dict[str, Any]:
        """Get memory usage statistics.

        Returns:
            Memory statistics
        """
        stats = {}
        for op, records in self._operations.items():
            sizes = [r["size_bytes"] for r in records]
            if sizes:
                stats[op] = {
                    "count": len(sizes),
                    "total_bytes": sum(sizes),
                    "avg_bytes": sum(sizes) / len(sizes),
                    "min_bytes": min(sizes),
                    "max_bytes": max(sizes),
                }
        return stats


# Global monitors
_default_monitor = PerformanceMonitor(name="novel_agent")
_token_tracker = TokenTracker(provider="deepseek")
_memory_tracker = MemoryTracker()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _default_monitor


def get_token_tracker() -> TokenTracker:
    """Get global token tracker."""
    return _token_tracker


def get_memory_tracker() -> MemoryTracker:
    """Get global memory tracker."""
    return _memory_tracker
