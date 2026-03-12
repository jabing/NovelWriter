# src/monitoring/metrics.py
"""Performance metrics collection system."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from statistics import mean, median, quantiles
from threading import Lock
from typing import Any, Callable, Generic, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def _serialize_labels(labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Serialize labels to a hashable tuple.

    Args:
        labels: Dictionary of label key-value pairs

    Returns:
        Sorted tuple of label key-value pairs
    """
    return tuple(sorted(labels.items()))


class Counter:
    """Counter metric for accumulating values."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize counter.

        Args:
            name: Metric name
            description: Metric description
        """
        self.name = name
        self.description = description
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = Lock()

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment counter.

        Args:
            value: Value to add (default: 1.0)
            labels: Optional labels dictionary
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            self._values[label_key] += value

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get current counter value.

        Args:
            labels: Optional labels dictionary

        Returns:
            Current counter value
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            return self._values.get(label_key, 0.0)

    def reset(self, labels: dict[str, str] | None = None) -> None:
        """Reset counter.

        Args:
            labels: Optional labels dictionary (resets all if None)
        """
        with self._lock:
            if labels is None:
                self._values.clear()
            else:
                label_key = _serialize_labels(labels)
                self._values.pop(label_key, None)

    def collect(self) -> dict[str, Any]:
        """Collect all metric data.

        Returns:
            Dictionary of metric data
        """
        with self._lock:
            return {
                "name": self.name,
                "type": "counter",
                "description": self.description,
                "values": [
                    {"labels": dict(labels), "value": value}
                    for labels, value in self._values.items()
                ],
            }


class Gauge:
    """Gauge metric for tracking current values."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize gauge.

        Args:
            name: Metric name
            description: Metric description
        """
        self.name = name
        self.description = description
        self._values: dict[tuple[tuple[str, str], ...], float] = {}
        self._lock = Lock()

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set gauge value.

        Args:
            value: Value to set
            labels: Optional labels dictionary
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment gauge.

        Args:
            value: Value to add
            labels: Optional labels dictionary
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            self._values[label_key] = self._values.get(label_key, 0.0) + value

    def dec(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Decrement gauge.

        Args:
            value: Value to subtract
            labels: Optional labels dictionary
        """
        self.inc(-value, labels)

    def get(self, labels: dict[str, str] | None = None) -> float | None:
        """Get current gauge value.

        Args:
            labels: Optional labels dictionary

        Returns:
            Current gauge value or None
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            return self._values.get(label_key)

    def collect(self) -> dict[str, Any]:
        """Collect all metric data.

        Returns:
            Dictionary of metric data
        """
        with self._lock:
            return {
                "name": self.name,
                "type": "gauge",
                "description": self.description,
                "values": [
                    {"labels": dict(labels), "value": value}
                    for labels, value in self._values.items()
                ],
            }


@dataclass
class HistogramData:
    """Data container for histogram observations."""

    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = -float("inf")
    values: list[float] = field(default_factory=list)
    buckets: dict[float, int] = field(default_factory=dict)


class Histogram:
    """Histogram metric for tracking value distributions."""

    DEFAULT_BUCKETS = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Metric name
            description: Metric description
            buckets: Bucket boundaries
        """
        self.name = name
        self.description = description
        self.buckets = tuple(sorted(buckets))
        self._data: dict[tuple[tuple[str, str], ...], HistogramData] = defaultdict(HistogramData)
        self._lock = Lock()

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe a value.

        Args:
            value: Value to observe
            labels: Optional labels dictionary
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            data = self._data[label_key]
            data.count += 1
            data.sum += value
            data.min = min(data.min, value)
            data.max = max(data.max, value)
            data.values.append(value)

            # Update buckets
            for bucket in self.buckets:
                if value <= bucket:
                    data.buckets[bucket] = data.buckets.get(bucket, 0) + 1

    def collect(self) -> dict[str, Any]:
        """Collect all metric data.

        Returns:
            Dictionary of metric data
        """
        with self._lock:
            result = {
                "name": self.name,
                "type": "histogram",
                "description": self.description,
                "buckets": list(self.buckets),
                "values": [],
            }

            for labels, data in self._data.items():
                value_data = {
                    "labels": dict(labels),
                    "count": data.count,
                    "sum": data.sum,
                    "min": data.min if data.count > 0 else None,
                    "max": data.max if data.count > 0 else None,
                    "mean": mean(data.values) if data.count > 0 else None,
                    "median": median(data.values) if data.count > 0 else None,
                    "buckets": [
                        {"le": bucket, "count": data.buckets.get(bucket, 0)}
                        for bucket in self.buckets
                    ],
                }

                if data.count >= 4:
                    try:
                        qs = quantiles(data.values, n=4)
                        value_data["p25"] = qs[0]
                        value_data["p50"] = qs[1]
                        value_data["p75"] = qs[2]
                    except Exception:
                        pass

                result["values"].append(value_data)

            return result


class Summary:
    """Summary metric for tracking percentiles."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize summary.

        Args:
            name: Metric name
            description: Metric description
        """
        self.name = name
        self.description = description
        self._data: dict[tuple[tuple[str, str], ...], HistogramData] = defaultdict(HistogramData)
        self._lock = Lock()

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe a value.

        Args:
            value: Value to observe
            labels: Optional labels dictionary
        """
        label_key = _serialize_labels(labels or {})
        with self._lock:
            data = self._data[label_key]
            data.count += 1
            data.sum += value
            data.min = min(data.min, value)
            data.max = max(data.max, value)
            data.values.append(value)

    def collect(self) -> dict[str, Any]:
        """Collect all metric data.

        Returns:
            Dictionary of metric data
        """
        with self._lock:
            result = {
                "name": self.name,
                "type": "summary",
                "description": self.description,
                "values": [],
            }

            for labels, data in self._data.items():
                value_data = {
                    "labels": dict(labels),
                    "count": data.count,
                    "sum": data.sum,
                    "min": data.min if data.count > 0 else None,
                    "max": data.max if data.count > 0 else None,
                    "mean": mean(data.values) if data.count > 0 else None,
                }

                if data.count >= 4:
                    try:
                        qs = quantiles(data.values, n=4)
                        value_data["p25"] = qs[0]
                        value_data["p50"] = qs[1]
                        value_data["p75"] = qs[2]
                    except Exception:
                        pass

                result["values"].append(value_data)

            return result


class MetricsCollector:
    """Central metrics collector."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._summaries: dict[str, Summary] = {}
        self._lock = Lock()

    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter.

        Args:
            name: Metric name
            description: Metric description

        Returns:
            Counter instance
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge.

        Args:
            name: Metric name
            description: Metric description

        Returns:
            Gauge instance
        """
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        buckets: tuple[float, ...] = Histogram.DEFAULT_BUCKETS,
    ) -> Histogram:
        """Get or create a histogram.

        Args:
            name: Metric name
            description: Metric description
            buckets: Bucket boundaries

        Returns:
            Histogram instance
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets)
            return self._histograms[name]

    def summary(self, name: str, description: str = "") -> Summary:
        """Get or create a summary.

        Args:
            name: Metric name
            description: Metric description

        Returns:
            Summary instance
        """
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, description)
            return self._summaries[name]

    def timeit(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator to measure function execution time.

        Args:
            name: Histogram name
            labels: Optional labels

        Returns:
            Decorator function
        """
        histogram = self.histogram(name, f"Execution time for {name}")

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                start_time = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start_time
                    histogram.observe(elapsed, labels)

            return wrapper

        return decorator

    def async_timeit(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
        """Decorator to measure async function execution time.

        Args:
            name: Histogram name
            labels: Optional labels

        Returns:
            Decorator function
        """
        histogram = self.histogram(name, f"Execution time for {name}")

        def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                start_time = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start_time
                    histogram.observe(elapsed, labels)

            return wrapper

        return decorator

    def collect_all(self) -> dict[str, Any]:
        """Collect all metrics.

        Returns:
            Dictionary of all metrics
        """
        with self._lock:
            return {
                "counters": [c.collect() for c in self._counters.values()],
                "gauges": [g.collect() for g in self._gauges.values()],
                "histograms": [h.collect() for h in self._histograms.values()],
                "summaries": [s.collect() for s in self._summaries.values()],
            }

    def reset_all(self) -> None:
        """Reset all metrics."""
        with self._lock:
            for counter in self._counters.values():
                counter.reset()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector.

    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
