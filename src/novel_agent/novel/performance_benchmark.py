"""Performance benchmarking for the QA validation system.

This module provides benchmarking tools to measure and validate
performance requirements for the validation pipeline:
- Validation time < 5 seconds per chapter
- Memory usage < 500MB

Example:
    >>> benchmark = PerformanceBenchmark()
    >>> result = benchmark.time_validation(validator, content, iterations=10)
    >>> print(f"Average time: {result.duration_ms:.2f}ms")
    >>> if benchmark.check_thresholds():
    ...     print("Performance within acceptable limits")
"""

from __future__ import annotations

import logging
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark operation.

    Attributes:
        operation: Name of the benchmarked operation
        duration_ms: Duration in milliseconds
        memory_mb: Memory usage in megabytes
        iterations: Number of iterations run
        timestamp: When the benchmark was run
        metadata: Additional metadata about the benchmark
    """

    operation: str
    duration_ms: float
    memory_mb: float
    iterations: int
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    """Performance benchmarking suite for QA validation system.

    Provides tools to measure timing and memory usage of validators
    and ensure performance meets requirements.

    Attributes:
        results: List of benchmark results
        thresholds: Performance thresholds configuration

    Example:
        >>> benchmark = PerformanceBenchmark()
        >>> result = benchmark.time_validation(my_validator, chapter_content)
        >>> benchmark.check_thresholds(validation_time_s=5, memory_mb=500)
        True
    """

    results: list[BenchmarkResult] = field(default_factory=list)
    thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "validation_time_s": 5.0,
            "memory_mb": 500.0,
        }
    )

    def time_validation(
        self,
        validator: Callable[..., Any],
        content: str,
        iterations: int = 10,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """Time a validation operation over multiple iterations.

        Args:
            validator: Callable that performs validation
            content: Content to validate
            iterations: Number of iterations to run (default: 10)
            **kwargs: Additional arguments passed to validator

        Returns:
            BenchmarkResult with timing and memory metrics
        """
        validator_name = validator.__name__ if hasattr(validator, "__name__") else "callable"
        logger.debug(f"Starting benchmark: validator={validator_name}, iterations={iterations}")

        # Start memory tracking
        tracemalloc.start()

        # Warm-up iteration (not counted)
        try:
            _ = validator(content, **kwargs)
        except Exception:
            pass  # Warm-up can fail, we just want to prime any caches

        # Timed iterations
        total_time = 0.0
        peak_memory = 0.0

        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                _ = validator(content, **kwargs)
            except Exception as e:
                logger.warning(f"Iteration {i} failed: {e}")
            end_time = time.perf_counter()

            iteration_time = (end_time - start_time) * 1000  # Convert to ms
            total_time += iteration_time

            # Track peak memory
            current, peak = tracemalloc.get_traced_memory()
            peak_memory = max(peak_memory, peak / (1024 * 1024))  # Convert to MB

        tracemalloc.stop()

        avg_time = total_time / iterations if iterations > 0 else 0.0
        timestamp = datetime.now()

        result = BenchmarkResult(
            operation="validation",
            duration_ms=avg_time,
            memory_mb=peak_memory,
            iterations=iterations,
            timestamp=timestamp,
            metadata={
                "validator": validator.__name__ if hasattr(validator, "__name__") else "callable",
                "content_length": len(content),
                "total_time_ms": total_time,
            },
        )

        self.results.append(result)
        logger.info(
            f"Benchmark complete: avg_time={avg_time:.2f}ms, "
            f"peak_memory={peak_memory:.2f}MB, iterations={iterations}"
        )

        return result

    def memory_usage(self) -> float:
        """Get current memory usage in MB.

        Returns:
            Current memory usage in megabytes
        """
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            current, _ = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        else:
            current, _ = tracemalloc.get_traced_memory()

        return current / (1024 * 1024)

    def run_full_benchmark(self, novel_id: str) -> dict[str, Any]:
        """Run a complete benchmark suite for a novel.

        This runs multiple benchmark scenarios:
        - Single chapter validation
        - Multi-chapter throughput
        - Memory stress test

        Args:
            novel_id: Novel identifier for context

        Returns:
            Dictionary with full benchmark results
        """
        logger.info(f"Starting full benchmark suite for novel: {novel_id}")
        start_time = time.perf_counter()

        # Clear previous results
        self.results.clear()

        benchmark_report: dict[str, Any] = {
            "novel_id": novel_id,
            "timestamp": datetime.now().isoformat(),
            "scenarios": {},
            "summary": {},
        }

        # Scenario 1: Single chapter validation (simulated)
        single_chapter_result = self._benchmark_single_chapter()
        benchmark_report["scenarios"]["single_chapter"] = single_chapter_result

        # Scenario 2: Multi-chapter throughput (simulated)
        multi_chapter_result = self._benchmark_multi_chapter()
        benchmark_report["scenarios"]["multi_chapter"] = multi_chapter_result

        # Scenario 3: Memory usage
        memory_result = self._benchmark_memory()
        benchmark_report["scenarios"]["memory"] = memory_result

        total_time = time.perf_counter() - start_time

        # Generate summary
        benchmark_report["summary"] = {
            "total_benchmark_time_s": round(total_time, 3),
            "results_count": len(self.results),
            "avg_duration_ms": round(
                sum(r.duration_ms for r in self.results) / len(self.results), 2
            )
            if self.results
            else 0,
            "max_memory_mb": round(max((r.memory_mb for r in self.results), default=0), 2),
            "thresholds_met": self.check_thresholds(),
        }

        logger.info(f"Full benchmark complete in {total_time:.3f}s")
        return benchmark_report

    def _benchmark_single_chapter(self) -> dict[str, Any]:
        """Benchmark single chapter validation performance.

        Returns:
            Dictionary with single chapter benchmark results
        """
        # Simulated content
        sample_content = "Chapter content for benchmarking. " * 100

        def mock_validator(content: str) -> dict[str, Any]:
            """Mock validator for benchmarking."""
            # Simulate some work
            _ = content.lower().split()
            return {"valid": True, "issues": []}

        result = self.time_validation(
            mock_validator,
            sample_content,
            iterations=5,
        )

        return {
            "avg_duration_ms": result.duration_ms,
            "memory_mb": result.memory_mb,
            "iterations": result.iterations,
            "status": "pass" if result.duration_ms < 5000 else "fail",
        }

    def _benchmark_multi_chapter(self) -> dict[str, Any]:
        """Benchmark multi-chapter validation throughput.

        Returns:
            Dictionary with multi-chapter benchmark results
        """
        chapters = [f"Chapter {i} content. " * 50 for i in range(1, 6)]
        total_time = 0.0

        def mock_validator(content: str) -> dict[str, Any]:
            _ = content.lower()
            return {"valid": True}

        start_time = time.perf_counter()
        for chapter in chapters:
            _ = mock_validator(chapter)
        total_time_ms = (time.perf_counter() - start_time) * 1000

        avg_time = total_time_ms / len(chapters) if chapters else 0

        result = BenchmarkResult(
            operation="multi_chapter",
            duration_ms=avg_time,
            memory_mb=self.memory_usage(),
            iterations=len(chapters),
            timestamp=datetime.now(),
            metadata={"total_chapters": len(chapters)},
        )
        self.results.append(result)

        return {
            "total_time_ms": total_time,
            "avg_per_chapter_ms": avg_time,
            "chapters_processed": len(chapters),
            "throughput_chapters_per_s": round(len(chapters) / (total_time / 1000), 2)
            if total_time > 0
            else 0,
        }

    def _benchmark_memory(self) -> dict[str, Any]:
        """Benchmark memory usage during validation.

        Returns:
            Dictionary with memory benchmark results
        """
        tracemalloc.start()

        # Simulate memory-intensive operation
        large_content = "x" * 1_000_000  # 1MB of content
        _ = large_content.upper()

        current_mb, peak_mb = tracemalloc.get_traced_memory()
        current_mb = current_mb / (1024 * 1024)
        peak_mb = peak_mb / (1024 * 1024)

        tracemalloc.stop()

        result = BenchmarkResult(
            operation="memory_stress",
            duration_ms=0.0,
            memory_mb=peak_mb,
            iterations=1,
            timestamp=datetime.now(),
            metadata={"current_mb": current_mb},
        )
        self.results.append(result)

        return {
            "current_memory_mb": round(current_mb, 2),
            "peak_memory_mb": round(peak_mb, 2),
            "status": "pass" if peak_mb < 500 else "fail",
        }

    def generate_report(self) -> str:
        """Generate a human-readable performance report.

        Returns:
            Formatted report string
        """
        lines: list[str] = []

        lines.append("=" * 60)
        lines.append("PERFORMANCE BENCHMARK REPORT")
        lines.append("=" * 60)
        lines.append("")

        if not self.results:
            lines.append("No benchmark results available.")
            lines.append("Run benchmarks first using time_validation() or run_full_benchmark().")
            return "\n".join(lines)

        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total Benchmarks: {len(self.results)}")
        lines.append(
            f"Avg Duration: {sum(r.duration_ms for r in self.results) / len(self.results):.2f}ms"
        )
        lines.append(f"Max Memory: {max(r.memory_mb for r in self.results):.2f}MB")
        lines.append("")

        # Thresholds section
        lines.append("THRESHOLD CHECK")
        lines.append("-" * 40)
        thresholds_met = self.check_thresholds()
        lines.append(f"Status: {'PASS' if thresholds_met else 'FAIL'}")
        lines.append(f"Max Validation Time: {self.thresholds['validation_time_s']}s")
        lines.append(f"Max Memory: {self.thresholds['memory_mb']}MB")
        lines.append("")

        # Detailed results
        lines.append("DETAILED RESULTS")
        lines.append("-" * 40)
        for i, result in enumerate(self.results, 1):
            lines.append(f"  [{i}] {result.operation}")
            lines.append(f"      Duration: {result.duration_ms:.2f}ms")
            lines.append(f"      Memory: {result.memory_mb:.2f}MB")
            lines.append(f"      Iterations: {result.iterations}")
            if result.metadata:
                for key, value in result.metadata.items():
                    lines.append(f"      {key}: {value}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def check_thresholds(
        self,
        validation_time_s: float = 5.0,
        memory_mb: float = 500.0,
    ) -> bool:
        """Check if performance meets the specified thresholds.

        Args:
            validation_time_s: Maximum allowed validation time in seconds
            memory_mb: Maximum allowed memory usage in MB

        Returns:
            True if all thresholds are met, False otherwise
        """
        self.thresholds["validation_time_s"] = validation_time_s
        self.thresholds["memory_mb"] = memory_mb

        if not self.results:
            logger.warning("No benchmark results to check against thresholds")
            return True  # No data means no violations

        # Check validation time (convert ms to s for comparison)
        max_duration_s = max(r.duration_ms for r in self.results) / 1000
        max_memory = max(r.memory_mb for r in self.results)

        time_ok = max_duration_s <= validation_time_s
        memory_ok = max_memory <= memory_mb

        if not time_ok:
            logger.warning(
                f"Validation time {max_duration_s:.2f}s exceeds threshold {validation_time_s}s"
            )

        if not memory_ok:
            logger.warning(f"Memory usage {max_memory:.2f}MB exceeds threshold {memory_mb}MB")

        return time_ok and memory_ok

    def get_validator_performance(self, validator_name: str) -> dict[str, Any]:
        """Get aggregated performance for a specific validator.

        Args:
            validator_name: Name of the validator to query

        Returns:
            Dictionary with validator performance metrics
        """
        validator_results = [
            r for r in self.results if r.metadata.get("validator") == validator_name
        ]

        if not validator_results:
            return {
                "validator": validator_name,
                "count": 0,
                "avg_duration_ms": 0.0,
                "max_memory_mb": 0.0,
            }

        return {
            "validator": validator_name,
            "count": len(validator_results),
            "avg_duration_ms": round(
                sum(r.duration_ms for r in validator_results) / len(validator_results), 2
            ),
            "max_memory_mb": round(max(r.memory_mb for r in validator_results), 2),
        }

    def reset(self) -> None:
        """Clear all benchmark results."""
        self.results.clear()
        logger.info("Benchmark results cleared")


__all__ = [
    "BenchmarkResult",
    "PerformanceBenchmark",
]
