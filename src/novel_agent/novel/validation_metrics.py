"""Performance monitoring for the QA validation system.

This module provides metrics tracking for validation operations including
timing, issue counts, fix success rates, and per-validator performance.

Example:
    >>> metrics = ValidationMetrics()
    >>> metrics.record_validation(chapter=1, duration_ms=150.5, issues_count=3, validator="character")
    >>> metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
    >>> summary = metrics.get_summary()
    >>> report = metrics.generate_report(format="text")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationRecord:
    """Record of a single validation operation.

    Attributes:
        chapter: Chapter number that was validated
        timestamp: When the validation occurred
        duration_ms: Duration of validation in milliseconds
        issues_count: Number of issues found
        validator: Name of the validator that ran
    """

    chapter: int
    timestamp: datetime
    duration_ms: float
    issues_count: int
    validator: str


@dataclass
class FixRecord:
    """Record of a single fix attempt.

    Attributes:
        chapter: Chapter number that was fixed
        timestamp: When the fix was attempted
        duration_ms: Duration of fix attempt in milliseconds
        success: Whether the fix was successful
    """

    chapter: int
    timestamp: datetime
    duration_ms: float
    success: bool


@dataclass
class ValidationMetrics:
    """Tracks performance metrics for the validation system.

    This class provides in-memory storage for validation and fix records,
    with methods to record operations, query metrics, and generate reports.

    Attributes:
        validations: List of validation records
        fixes: List of fix records
        max_records: Maximum number of records to store (prevents memory issues)

    Example:
        >>> metrics = ValidationMetrics()
        >>> metrics.record_validation(chapter=1, duration_ms=100.0, issues_count=2, validator="character")
        >>> metrics.record_fix(chapter=1, duration_ms=50.0, success=True)
        >>> print(metrics.get_summary())
    """

    validations: list[ValidationRecord] = field(default_factory=list)
    fixes: list[FixRecord] = field(default_factory=list)
    max_records: int = 10000

    def record_validation(
        self,
        chapter: int,
        duration_ms: float,
        issues_count: int,
        validator: str,
    ) -> None:
        """Record a validation operation.

        Args:
            chapter: Chapter number that was validated
            duration_ms: Duration of validation in milliseconds
            issues_count: Number of issues found
            validator: Name of the validator (e.g., "character", "reference")
        """
        record = ValidationRecord(
            chapter=chapter,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            issues_count=issues_count,
            validator=validator,
        )
        self.validations.append(record)

        # Trim if exceeding max records
        if len(self.validations) > self.max_records:
            self.validations = self.validations[-self.max_records :]

        logger.debug(
            f"Recorded validation: chapter={chapter}, validator={validator}, "
            f"duration={duration_ms:.1f}ms, issues={issues_count}"
        )

    def record_fix(
        self,
        chapter: int,
        duration_ms: float,
        success: bool,
    ) -> None:
        """Record a fix attempt.

        Args:
            chapter: Chapter number that was fixed
            duration_ms: Duration of fix attempt in milliseconds
            success: Whether the fix was successful
        """
        record = FixRecord(
            chapter=chapter,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
        )
        self.fixes.append(record)

        # Trim if exceeding max records
        if len(self.fixes) > self.max_records:
            self.fixes = self.fixes[-self.max_records :]

        logger.debug(
            f"Recorded fix: chapter={chapter}, duration={duration_ms:.1f}ms, success={success}"
        )

    def get_chapter_metrics(self, chapter: int) -> dict[str, Any]:
        """Get metrics for a specific chapter.

        Args:
            chapter: Chapter number to get metrics for

        Returns:
            Dictionary with chapter-specific metrics:
            - validations_count: Number of validations
            - total_issues: Total issues found
            - avg_validation_time_ms: Average validation time
            - fixes_count: Number of fix attempts
            - fix_success_rate: Success rate of fixes (0.0-1.0)
            - validators_used: List of validators used
        """
        chapter_validations = [v for v in self.validations if v.chapter == chapter]
        chapter_fixes = [f for f in self.fixes if f.chapter == chapter]

        validations_count = len(chapter_validations)
        total_issues = sum(v.issues_count for v in chapter_validations)

        avg_validation_time = 0.0
        if chapter_validations:
            avg_validation_time = sum(v.duration_ms for v in chapter_validations) / len(
                chapter_validations
            )

        fixes_count = len(chapter_fixes)
        fix_success_rate = 0.0
        if chapter_fixes:
            successful = sum(1 for f in chapter_fixes if f.success)
            fix_success_rate = successful / len(chapter_fixes)

        validators_used = list({v.validator for v in chapter_validations})

        return {
            "chapter": chapter,
            "validations_count": validations_count,
            "total_issues": total_issues,
            "avg_validation_time_ms": round(avg_validation_time, 2),
            "fixes_count": fixes_count,
            "fix_success_rate": round(fix_success_rate, 2),
            "validators_used": validators_used,
        }

    def get_summary(self) -> dict[str, Any]:
        """Get aggregate statistics across all chapters.

        Returns:
            Dictionary with aggregate metrics:
            - total_validations: Total validation count
            - total_fixes: Total fix count
            - total_issues_found: Total issues found
            - avg_validation_time_ms: Average validation time
            - avg_fix_time_ms: Average fix time
            - fix_success_rate: Overall fix success rate
            - chapters_validated: Number of unique chapters validated
            - validator_stats: Per-validator performance metrics
        """
        total_validations = len(self.validations)
        total_fixes = len(self.fixes)
        total_issues_found = sum(v.issues_count for v in self.validations)

        avg_validation_time = 0.0
        if self.validations:
            avg_validation_time = sum(v.duration_ms for v in self.validations) / len(
                self.validations
            )

        avg_fix_time = 0.0
        if self.fixes:
            avg_fix_time = sum(f.duration_ms for f in self.fixes) / len(self.fixes)

        fix_success_rate = 0.0
        if self.fixes:
            successful = sum(1 for f in self.fixes if f.success)
            fix_success_rate = successful / len(self.fixes)

        chapters_validated = len({v.chapter for v in self.validations})

        validator_stats = self._compute_validator_stats()

        return {
            "total_validations": total_validations,
            "total_fixes": total_fixes,
            "total_issues_found": total_issues_found,
            "avg_validation_time_ms": round(avg_validation_time, 2),
            "avg_fix_time_ms": round(avg_fix_time, 2),
            "fix_success_rate": round(fix_success_rate, 2),
            "chapters_validated": chapters_validated,
            "validator_stats": validator_stats,
        }

    def _compute_validator_stats(self) -> dict[str, dict[str, Any]]:
        """Compute per-validator performance metrics.

        Returns:
            Dictionary mapping validator names to their metrics
        """
        stats: dict[str, dict[str, Any]] = {}

        by_validator: dict[str, list[ValidationRecord]] = {}
        for v in self.validations:
            if v.validator not in by_validator:
                by_validator[v.validator] = []
            by_validator[v.validator].append(v)

        for validator, records in by_validator.items():
            count = len(records)
            total_issues = sum(r.issues_count for r in records)
            avg_time = sum(r.duration_ms for r in records) / count if count > 0 else 0

            stats[validator] = {
                "count": count,
                "total_issues": total_issues,
                "avg_time_ms": round(avg_time, 2),
                "avg_issues_per_validation": round(total_issues / count, 2) if count > 0 else 0,
            }

        return stats

    def generate_report(self, format: str = "text") -> str:
        """Generate a metrics report.

        Args:
            format: Output format - "text" or "json"

        Returns:
            Formatted report string
        """
        if format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """Generate a human-readable text report.

        Returns:
            Text formatted report
        """
        summary = self.get_summary()
        lines: list[str] = []

        lines.append("=" * 60)
        lines.append("VALIDATION METRICS REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Overall stats
        lines.append("OVERALL STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total Validations: {summary['total_validations']}")
        lines.append(f"Total Fixes: {summary['total_fixes']}")
        lines.append(f"Total Issues Found: {summary['total_issues_found']}")
        lines.append(f"Chapters Validated: {summary['chapters_validated']}")
        lines.append("")

        # Performance stats
        lines.append("PERFORMANCE")
        lines.append("-" * 40)
        lines.append(f"Avg Validation Time: {summary['avg_validation_time_ms']:.2f}ms")
        lines.append(f"Avg Fix Time: {summary['avg_fix_time_ms']:.2f}ms")
        lines.append(f"Fix Success Rate: {summary['fix_success_rate'] * 100:.1f}%")
        lines.append("")

        if summary["validator_stats"]:
            lines.append("PER-VALIDATOR STATISTICS")
            lines.append("-" * 40)
            for validator, stats in summary["validator_stats"].items():
                lines.append(f"  {validator}:")
                lines.append(f"    Validations: {stats['count']}")
                lines.append(f"    Total Issues: {stats['total_issues']}")
                lines.append(f"    Avg Time: {stats['avg_time_ms']:.2f}ms")
                lines.append(f"    Avg Issues/Validation: {stats['avg_issues_per_validation']:.2f}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_json_report(self) -> str:
        """Generate a JSON formatted report.

        Returns:
            JSON formatted report string
        """
        summary = self.get_summary()

        # Add recent records for context
        recent_validations = [
            {
                "chapter": v.chapter,
                "timestamp": v.timestamp.isoformat(),
                "duration_ms": v.duration_ms,
                "issues_count": v.issues_count,
                "validator": v.validator,
            }
            for v in self.validations[-10:]  # Last 10 validations
        ]

        recent_fixes = [
            {
                "chapter": f.chapter,
                "timestamp": f.timestamp.isoformat(),
                "duration_ms": f.duration_ms,
                "success": f.success,
            }
            for f in self.fixes[-10:]  # Last 10 fixes
        ]

        report = {
            "summary": summary,
            "recent_validations": recent_validations,
            "recent_fixes": recent_fixes,
        }

        return json.dumps(report, indent=2)

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self.validations.clear()
        self.fixes.clear()
        logger.info("Validation metrics reset")

    def get_validator_performance(self, validator: str) -> dict[str, Any]:
        """Get performance metrics for a specific validator.

        Args:
            validator: Validator name to get metrics for

        Returns:
            Dictionary with validator-specific metrics
        """
        records = [v for v in self.validations if v.validator == validator]

        if not records:
            return {
                "validator": validator,
                "count": 0,
                "total_issues": 0,
                "avg_time_ms": 0.0,
                "avg_issues_per_validation": 0.0,
            }

        count = len(records)
        total_issues = sum(r.issues_count for r in records)
        avg_time = sum(r.duration_ms for r in records) / count

        return {
            "validator": validator,
            "count": count,
            "total_issues": total_issues,
            "avg_time_ms": round(avg_time, 2),
            "avg_issues_per_validation": round(total_issues / count, 2),
        }


__all__ = [
    "ValidationRecord",
    "FixRecord",
    "ValidationMetrics",
]
