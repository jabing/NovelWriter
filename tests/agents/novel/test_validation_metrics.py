"""Tests for ValidationMetrics performance monitoring."""

import json
from datetime import datetime

import pytest

from src.novel_agent.novel.validation_metrics import (
    FixRecord,
    ValidationMetrics,
    ValidationRecord,
)


class TestValidationRecord:
    """Tests for ValidationRecord dataclass."""

    def test_creation(self) -> None:
        """Test creating a validation record."""
        timestamp = datetime.now()
        record = ValidationRecord(
            chapter=1,
            timestamp=timestamp,
            duration_ms=100.5,
            issues_count=3,
            validator="character",
        )
        assert record.chapter == 1
        assert record.timestamp == timestamp
        assert record.duration_ms == 100.5
        assert record.issues_count == 3
        assert record.validator == "character"


class TestFixRecord:
    """Tests for FixRecord dataclass."""

    def test_creation(self) -> None:
        """Test creating a fix record."""
        timestamp = datetime.now()
        record = FixRecord(
            chapter=2,
            timestamp=timestamp,
            duration_ms=50.0,
            success=True,
        )
        assert record.chapter == 2
        assert record.timestamp == timestamp
        assert record.duration_ms == 50.0
        assert record.success is True


class TestValidationMetrics:
    """Tests for ValidationMetrics class."""

    @pytest.fixture
    def metrics(self) -> ValidationMetrics:
        """Create a fresh ValidationMetrics instance."""
        return ValidationMetrics()

    def test_initial_state(self, metrics: ValidationMetrics) -> None:
        """Test initial state of metrics."""
        assert metrics.validations == []
        assert metrics.fixes == []
        assert metrics.max_records == 10000

    def test_record_validation(self, metrics: ValidationMetrics) -> None:
        """Test recording a validation."""
        metrics.record_validation(
            chapter=1,
            duration_ms=150.0,
            issues_count=5,
            validator="character",
        )

        assert len(metrics.validations) == 1
        record = metrics.validations[0]
        assert record.chapter == 1
        assert record.duration_ms == 150.0
        assert record.issues_count == 5
        assert record.validator == "character"
        assert isinstance(record.timestamp, datetime)

    def test_record_multiple_validations(self, metrics: ValidationMetrics) -> None:
        """Test recording multiple validations."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_validation(
            chapter=1, duration_ms=150.0, issues_count=3, validator="reference"
        )
        metrics.record_validation(
            chapter=2, duration_ms=200.0, issues_count=1, validator="timeline"
        )

        assert len(metrics.validations) == 3

    def test_record_fix(self, metrics: ValidationMetrics) -> None:
        """Test recording a fix."""
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)

        assert len(metrics.fixes) == 1
        record = metrics.fixes[0]
        assert record.chapter == 1
        assert record.duration_ms == 50.0
        assert record.success is True
        assert isinstance(record.timestamp, datetime)

    def test_record_multiple_fixes(self, metrics: ValidationMetrics) -> None:
        """Test recording multiple fixes."""
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        metrics.record_fix(chapter=1, duration_ms=75.0, success=False)
        metrics.record_fix(chapter=2, duration_ms=100.0, success=True)

        assert len(metrics.fixes) == 3

    def test_get_chapter_metrics_empty(self, metrics: ValidationMetrics) -> None:
        """Test getting metrics for a chapter with no data."""
        result = metrics.get_chapter_metrics(chapter=1)

        assert result["chapter"] == 1
        assert result["validations_count"] == 0
        assert result["total_issues"] == 0
        assert result["avg_validation_time_ms"] == 0.0
        assert result["fixes_count"] == 0
        assert result["fix_success_rate"] == 0.0
        assert result["validators_used"] == []

    def test_get_chapter_metrics_with_data(self, metrics: ValidationMetrics) -> None:
        """Test getting metrics for a chapter with data."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_validation(
            chapter=1, duration_ms=200.0, issues_count=4, validator="reference"
        )
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        metrics.record_fix(chapter=1, duration_ms=75.0, success=False)

        result = metrics.get_chapter_metrics(chapter=1)

        assert result["chapter"] == 1
        assert result["validations_count"] == 2
        assert result["total_issues"] == 6
        assert result["avg_validation_time_ms"] == 150.0
        assert result["fixes_count"] == 2
        assert result["fix_success_rate"] == 0.5
        assert set(result["validators_used"]) == {"character", "reference"}

    def test_get_summary_empty(self, metrics: ValidationMetrics) -> None:
        """Test getting summary with no data."""
        result = metrics.get_summary()

        assert result["total_validations"] == 0
        assert result["total_fixes"] == 0
        assert result["total_issues_found"] == 0
        assert result["avg_validation_time_ms"] == 0.0
        assert result["avg_fix_time_ms"] == 0.0
        assert result["fix_success_rate"] == 0.0
        assert result["chapters_validated"] == 0
        assert result["validator_stats"] == {}

    def test_get_summary_with_data(self, metrics: ValidationMetrics) -> None:
        """Test getting summary with data."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_validation(
            chapter=2, duration_ms=200.0, issues_count=3, validator="reference"
        )
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        metrics.record_fix(chapter=2, duration_ms=100.0, success=False)

        result = metrics.get_summary()

        assert result["total_validations"] == 2
        assert result["total_fixes"] == 2
        assert result["total_issues_found"] == 5
        assert result["avg_validation_time_ms"] == 150.0
        assert result["avg_fix_time_ms"] == 75.0
        assert result["fix_success_rate"] == 0.5
        assert result["chapters_validated"] == 2
        assert "character" in result["validator_stats"]
        assert "reference" in result["validator_stats"]

    def test_validator_stats(self, metrics: ValidationMetrics) -> None:
        """Test per-validator statistics."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_validation(
            chapter=1, duration_ms=200.0, issues_count=4, validator="character"
        )
        metrics.record_validation(
            chapter=2, duration_ms=150.0, issues_count=3, validator="reference"
        )

        stats = metrics._compute_validator_stats()

        assert stats["character"]["count"] == 2
        assert stats["character"]["total_issues"] == 6
        assert stats["character"]["avg_time_ms"] == 150.0
        assert stats["character"]["avg_issues_per_validation"] == 3.0

        assert stats["reference"]["count"] == 1
        assert stats["reference"]["total_issues"] == 3

    def test_generate_text_report(self, metrics: ValidationMetrics) -> None:
        """Test generating text report."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)

        report = metrics.generate_report(format="text")

        assert "VALIDATION METRICS REPORT" in report
        assert "Total Validations: 1" in report
        assert "Total Fixes: 1" in report
        assert "character" in report

    def test_generate_json_report(self, metrics: ValidationMetrics) -> None:
        """Test generating JSON report."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)

        report = metrics.generate_report(format="json")

        data = json.loads(report)
        assert "summary" in data
        assert data["summary"]["total_validations"] == 1
        assert data["summary"]["total_fixes"] == 1
        assert "recent_validations" in data
        assert "recent_fixes" in data

    def test_reset(self, metrics: ValidationMetrics) -> None:
        """Test resetting metrics."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)

        assert len(metrics.validations) == 1
        assert len(metrics.fixes) == 1

        metrics.reset()

        assert len(metrics.validations) == 0
        assert len(metrics.fixes) == 0

    def test_max_records_limit(self) -> None:
        """Test that max_records limit is enforced."""
        metrics = ValidationMetrics(max_records=5)

        for i in range(10):
            metrics.record_validation(
                chapter=i,
                duration_ms=float(i),
                issues_count=i,
                validator="test",
            )

        assert len(metrics.validations) == 5
        assert metrics.validations[0].chapter == 5
        assert metrics.validations[-1].chapter == 9

    def test_max_records_limit_fixes(self) -> None:
        """Test that max_records limit is enforced for fixes."""
        metrics = ValidationMetrics(max_records=3)

        for i in range(5):
            metrics.record_fix(chapter=i, duration_ms=float(i), success=True)

        assert len(metrics.fixes) == 3
        assert metrics.fixes[0].chapter == 2
        assert metrics.fixes[-1].chapter == 4

    def test_get_validator_performance(self, metrics: ValidationMetrics) -> None:
        """Test getting performance for a specific validator."""
        metrics.record_validation(
            chapter=1, duration_ms=100.0, issues_count=2, validator="character"
        )
        metrics.record_validation(
            chapter=2, duration_ms=200.0, issues_count=4, validator="character"
        )
        metrics.record_validation(
            chapter=1, duration_ms=150.0, issues_count=3, validator="reference"
        )

        char_stats = metrics.get_validator_performance("character")

        assert char_stats["validator"] == "character"
        assert char_stats["count"] == 2
        assert char_stats["total_issues"] == 6
        assert char_stats["avg_time_ms"] == 150.0

    def test_get_validator_performance_nonexistent(self, metrics: ValidationMetrics) -> None:
        """Test getting performance for a non-existent validator."""
        stats = metrics.get_validator_performance("nonexistent")

        assert stats["validator"] == "nonexistent"
        assert stats["count"] == 0
        assert stats["total_issues"] == 0
        assert stats["avg_time_ms"] == 0.0

    def test_fix_success_rate_calculation(self, metrics: ValidationMetrics) -> None:
        """Test fix success rate calculation."""
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        metrics.record_fix(chapter=1, duration_ms=50.0, success=False)

        summary = metrics.get_summary()
        assert summary["fix_success_rate"] == pytest.approx(0.67, rel=0.1)

    def test_multiple_chapters_metrics(self, metrics: ValidationMetrics) -> None:
        """Test metrics across multiple chapters."""
        for chapter in range(1, 4):
            metrics.record_validation(
                chapter=chapter,
                duration_ms=100.0 * chapter,
                issues_count=chapter,
                validator="test",
            )

        summary = metrics.get_summary()
        assert summary["chapters_validated"] == 3
        assert summary["total_issues_found"] == 6
        assert summary["avg_validation_time_ms"] == 200.0
