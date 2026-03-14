"""Tests for PerformanceBenchmark benchmarking system."""

from datetime import datetime

import pytest

from src.novel_agent.novel.performance_benchmark import (
    BenchmarkResult,
    PerformanceBenchmark,
)


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_creation(self) -> None:
        """Test creating a benchmark result."""
        timestamp = datetime.now()
        result = BenchmarkResult(
            operation="validation",
            duration_ms=100.5,
            memory_mb=50.2,
            iterations=10,
            timestamp=timestamp,
        )
        assert result.operation == "validation"
        assert result.duration_ms == 100.5
        assert result.memory_mb == 50.2
        assert result.iterations == 10
        assert result.timestamp == timestamp
        assert result.metadata == {}

    def test_creation_with_metadata(self) -> None:
        """Test creating a benchmark result with metadata."""
        result = BenchmarkResult(
            operation="test",
            duration_ms=50.0,
            memory_mb=25.0,
            iterations=5,
            timestamp=datetime.now(),
            metadata={"key": "value", "count": 10},
        )
        assert result.metadata["key"] == "value"
        assert result.metadata["count"] == 10


class TestPerformanceBenchmark:
    """Tests for PerformanceBenchmark class."""

    @pytest.fixture
    def benchmark(self) -> PerformanceBenchmark:
        """Create a fresh PerformanceBenchmark instance."""
        return PerformanceBenchmark()

    def test_initial_state(self, benchmark: PerformanceBenchmark) -> None:
        """Test initial state of benchmark."""
        assert benchmark.results == []
        assert "validation_time_s" in benchmark.thresholds
        assert "memory_mb" in benchmark.thresholds

    def test_time_validation(self, benchmark: PerformanceBenchmark) -> None:
        """Test timing a validation operation."""

        def sample_validator(content: str) -> dict[str, bool]:
            return {"valid": len(content) > 0}

        content = "Test content for validation."
        result = benchmark.time_validation(sample_validator, content, iterations=5)

        assert result.operation == "validation"
        assert result.duration_ms >= 0
        assert result.memory_mb >= 0
        assert result.iterations == 5
        assert len(benchmark.results) == 1

    def test_time_validation_with_kwargs(self, benchmark: PerformanceBenchmark) -> None:
        """Test timing validation with additional kwargs."""

        def validator_with_args(content: str, strict: bool = False) -> bool:
            return len(content) > 0 if strict else True

        result = benchmark.time_validation(
            validator_with_args,
            "content",
            iterations=3,
            strict=True,
        )

        assert result.iterations == 3
        assert result.metadata.get("strict") is None

    def test_time_validation_exception_handling(self, benchmark: PerformanceBenchmark) -> None:
        """Test that exceptions in validator don't crash benchmark."""

        def failing_validator(content: str) -> None:
            raise ValueError("Intentional failure")

        result = benchmark.time_validation(
            failing_validator,
            "content",
            iterations=3,
        )

        assert result.iterations == 3
        assert len(benchmark.results) == 1

    def test_memory_usage(self, benchmark: PerformanceBenchmark) -> None:
        """Test getting current memory usage."""
        memory = benchmark.memory_usage()
        assert memory >= 0
        assert isinstance(memory, float)

    def test_run_full_benchmark(self, benchmark: PerformanceBenchmark) -> None:
        """Test running full benchmark suite."""
        report = benchmark.run_full_benchmark("test_novel")

        assert report["novel_id"] == "test_novel"
        assert "timestamp" in report
        assert "scenarios" in report
        assert "summary" in report
        assert "single_chapter" in report["scenarios"]
        assert "multi_chapter" in report["scenarios"]
        assert "memory" in report["scenarios"]
        assert len(benchmark.results) > 0

    def test_run_full_benchmark_summary(self, benchmark: PerformanceBenchmark) -> None:
        """Test full benchmark summary contains expected fields."""
        report = benchmark.run_full_benchmark("test_novel")

        summary = report["summary"]
        assert "total_benchmark_time_s" in summary
        assert "results_count" in summary
        assert "avg_duration_ms" in summary
        assert "max_memory_mb" in summary
        assert "thresholds_met" in summary

    def test_generate_report_empty(self, benchmark: PerformanceBenchmark) -> None:
        """Test generating report with no results."""
        report = benchmark.generate_report()

        assert "PERFORMANCE BENCHMARK REPORT" in report
        assert "No benchmark results available" in report

    def test_generate_report_with_results(self, benchmark: PerformanceBenchmark) -> None:
        """Test generating report with results."""

        def dummy_validator(content: str) -> bool:
            return True

        benchmark.time_validation(dummy_validator, "test", iterations=2)
        report = benchmark.generate_report()

        assert "PERFORMANCE BENCHMARK REPORT" in report
        assert "SUMMARY" in report
        assert "THRESHOLD CHECK" in report
        assert "DETAILED RESULTS" in report
        assert "validation" in report

    def test_check_thresholds_empty(self, benchmark: PerformanceBenchmark) -> None:
        """Test threshold check with no results returns True."""
        result = benchmark.check_thresholds()
        assert result is True

    def test_check_thresholds_pass(self, benchmark: PerformanceBenchmark) -> None:
        """Test threshold check when thresholds are met."""

        def fast_validator(content: str) -> bool:
            return True

        benchmark.time_validation(fast_validator, "test", iterations=10)
        result = benchmark.check_thresholds(validation_time_s=10.0, memory_mb=1000.0)

        assert result is True

    def test_check_thresholds_fail_time(self, benchmark: PerformanceBenchmark) -> None:
        """Test threshold check fails when time exceeded."""

        def slow_validator(content: str) -> bool:
            import time

            time.sleep(0.01)
            return True

        benchmark.time_validation(slow_validator, "test", iterations=1)
        result = benchmark.check_thresholds(validation_time_s=0.001, memory_mb=1000.0)

        assert result is False

    def test_check_thresholds_updates_stored(self, benchmark: PerformanceBenchmark) -> None:
        """Test that check_thresholds updates stored thresholds."""
        benchmark.check_thresholds(validation_time_s=3.0, memory_mb=300.0)

        assert benchmark.thresholds["validation_time_s"] == 3.0
        assert benchmark.thresholds["memory_mb"] == 300.0

    def test_get_validator_performance(self, benchmark: PerformanceBenchmark) -> None:
        """Test getting performance for a specific validator."""

        def my_validator(content: str) -> bool:
            return len(content) > 0

        benchmark.time_validation(my_validator, "test content", iterations=5)
        perf = benchmark.get_validator_performance("my_validator")

        assert perf["validator"] == "my_validator"
        assert perf["count"] == 1
        assert perf["avg_duration_ms"] >= 0

    def test_get_validator_performance_nonexistent(self, benchmark: PerformanceBenchmark) -> None:
        """Test getting performance for non-existent validator."""
        perf = benchmark.get_validator_performance("nonexistent")

        assert perf["validator"] == "nonexistent"
        assert perf["count"] == 0
        assert perf["avg_duration_ms"] == 0.0
        assert perf["max_memory_mb"] == 0.0

    def test_reset(self, benchmark: PerformanceBenchmark) -> None:
        """Test resetting benchmark results."""

        def validator(content: str) -> bool:
            return True

        benchmark.time_validation(validator, "test", iterations=2)
        assert len(benchmark.results) == 1

        benchmark.reset()
        assert len(benchmark.results) == 0

    def test_multiple_validations(self, benchmark: PerformanceBenchmark) -> None:
        """Test recording multiple validations."""

        def validator1(content: str) -> bool:
            return True

        def validator2(content: str) -> bool:
            return len(content) > 0

        benchmark.time_validation(validator1, "test1", iterations=2)
        benchmark.time_validation(validator2, "test2", iterations=3)

        assert len(benchmark.results) == 2

    def test_benchmark_result_metadata(self, benchmark: PerformanceBenchmark) -> None:
        """Test that benchmark results include expected metadata."""

        def test_val(content: str) -> bool:
            return True

        result = benchmark.time_validation(test_val, "sample content", iterations=5)

        assert result.metadata["validator"] == "test_val"
        assert result.metadata["content_length"] == len("sample content")
        assert result.metadata["total_time_ms"] >= 0

    def test_multi_chapter_throughput(self, benchmark: PerformanceBenchmark) -> None:
        """Test multi-chapter benchmark includes throughput."""
        report = benchmark.run_full_benchmark("test_novel")

        multi = report["scenarios"]["multi_chapter"]
        assert "throughput_chapters_per_s" in multi
        assert multi["throughput_chapters_per_s"] >= 0

    def test_default_thresholds(self, benchmark: PerformanceBenchmark) -> None:
        """Test default threshold values."""
        assert benchmark.thresholds["validation_time_s"] == 5.0
        assert benchmark.thresholds["memory_mb"] == 500.0

    def test_custom_thresholds(self) -> None:
        """Test creating benchmark with custom thresholds."""
        custom_thresholds = {
            "validation_time_s": 3.0,
            "memory_mb": 250.0,
        }
        benchmark = PerformanceBenchmark(thresholds=custom_thresholds)

        assert benchmark.thresholds["validation_time_s"] == 3.0
        assert benchmark.thresholds["memory_mb"] == 250.0
