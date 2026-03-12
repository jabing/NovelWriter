"""Persistent storage for repair history tracking.

This module provides a thread-safe store for managing repair histories
across multiple chapters with JSON-based persistence and backup rotation.
"""

import json
import logging
import os
import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.novel.auto_fixer import RepairAttempt, RepairHistory

logger = logging.getLogger(__name__)


@dataclass
class RepairHistoryStore:
    """Thread-safe store for managing repair histories with persistence.

    Attributes:
        histories: Dictionary mapping chapter numbers to repair histories
        max_stored: Maximum number of histories to keep in memory
        auto_save: Whether to automatically save after each modification
        save_path: Default path for saving/loading history files
        backup_count: Number of backup files to keep
        _lock: Thread lock for thread-safe operations
    """

    histories: dict[int, RepairHistory] = field(default_factory=dict)
    max_stored: int = 1000
    auto_save: bool = True
    save_path: str = "data/repair_history.json"
    backup_count: int = 5

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_history(self, history: RepairHistory) -> None:
        """Add a repair history to the store.

        If a history for the same chapter already exists, it will be replaced.

        Args:
            history: The RepairHistory to add
        """
        with self._lock:
            # Enforce max_stored limit
            if len(self.histories) >= self.max_stored:
                # Remove oldest history by started_at timestamp
                if history.chapter_number not in self.histories:
                    oldest_key = min(
                        self.histories.keys(),
                        key=lambda k: self.histories[k].started_at,
                    )
                    del self.histories[oldest_key]
                    logger.info(
                        f"Removed oldest history (chapter {oldest_key}) to stay within limit"
                    )

            self.histories[history.chapter_number] = history
            logger.info(f"Added repair history for chapter {history.chapter_number}")

            if self.auto_save:
                self._auto_save()

    def get_history(self, chapter_number: int) -> RepairHistory | None:
        """Get repair history for a specific chapter.

        Args:
            chapter_number: The chapter number to retrieve

        Returns:
            RepairHistory if found, None otherwise
        """
        with self._lock:
            return self.histories.get(chapter_number)

    def get_all_histories(self) -> dict[int, RepairHistory]:
        """Get all stored repair histories.

        Returns:
            Dictionary of chapter numbers to repair histories
        """
        with self._lock:
            return dict(self.histories)

    def get_statistics(self) -> dict[str, Any]:
        """Calculate aggregate statistics across all histories.

        Returns:
            Dictionary containing:
                - total_chapters: Total number of chapters with history
                - total_attempts: Total repair attempts across all chapters
                - successful_repairs: Count of successful repairs
                - failed_repairs: Count of failed repairs
                - partial_repairs: Count of partial repairs
                - manual_reviews: Count requiring manual review
                - success_rate: Overall success rate (0.0-1.0)
                - average_iterations: Average number of attempts per repair
                - total_issues_found: Total issues found across all chapters
                - total_issues_fixed: Total issues successfully fixed
                - total_issues_remaining: Total unresolved issues
                - fix_rate: Overall issue fix rate (0.0-1.0)
                - validator_usage: Count of times each validator was used
                - most_common_issues: Top 5 most common issue types
        """
        with self._lock:
            if not self.histories:
                return self._empty_statistics()

            total_attempts = sum(len(h.attempts) for h in self.histories.values())
            successful = sum(1 for h in self.histories.values() if h.final_status == "success")
            failed = sum(1 for h in self.histories.values() if h.final_status == "failed")
            partial = sum(1 for h in self.histories.values() if h.final_status == "partial")
            manual = sum(1 for h in self.histories.values() if h.final_status == "manual_review")

            total_issues_found = sum(h.total_issues_found for h in self.histories.values())
            total_issues_fixed = sum(h.issues_fixed for h in self.histories.values())
            total_issues_remaining = sum(h.issues_remaining for h in self.histories.values())

            # Count validator usage
            validator_counts: dict[str, int] = {}
            for history in self.histories.values():
                for validator in history.validators_used:
                    validator_counts[validator] = validator_counts.get(validator, 0) + 1

            # Calculate most common issue types from attempts
            issue_type_counts: dict[str, int] = {}
            for history in self.histories.values():
                for attempt in history.attempts:
                    for issue in attempt.issues_before:
                        issue_type = issue.get("inconsistency_type", "unknown")
                        if hasattr(issue_type, "value"):
                            issue_type = issue_type.value
                        issue_type_counts[str(issue_type)] = (
                            issue_type_counts.get(str(issue_type), 0) + 1
                        )

            # Get top 5 most common issues
            most_common = sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "total_chapters": len(self.histories),
                "total_attempts": total_attempts,
                "successful_repairs": successful,
                "failed_repairs": failed,
                "partial_repairs": partial,
                "manual_reviews": manual,
                "success_rate": successful / len(self.histories) if self.histories else 0,
                "average_iterations": total_attempts / len(self.histories) if self.histories else 0,
                "total_issues_found": total_issues_found,
                "total_issues_fixed": total_issues_fixed,
                "total_issues_remaining": total_issues_remaining,
                "fix_rate": total_issues_fixed / total_issues_found
                if total_issues_found > 0
                else 0,
                "validator_usage": validator_counts,
                "most_common_issues": dict(most_common),
            }

    def save_to_file(self, path: str | None = None) -> None:
        """Save all histories to a JSON file with atomic write.

        Uses atomic write (write to temp file, then rename) to prevent
        corruption from partial writes.

        Args:
            path: Path to save file (uses save_path if None)

        Raises:
            IOError: If save fails
        """
        save_path = path or self.save_path
        save_path_obj = Path(save_path)

        # Ensure directory exists
        save_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "histories": {
                    str(chapter): history.to_dict() for chapter, history in self.histories.items()
                },
            }

            # Atomic write: write to temp file first
            temp_fd = None
            temp_path = None
            try:
                # Create temp file in same directory for atomic rename
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=save_path_obj.parent,
                    prefix=".tmp_repair_history_",
                    suffix=".json",
                )

                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                temp_fd = None  # Already closed by fdopen

                # Atomic rename
                shutil.move(temp_path, save_path)
                temp_path = None  # Successfully moved

                logger.info(f"Saved {len(self.histories)} repair histories to {save_path}")

            finally:
                # Cleanup temp file if it still exists
                if temp_fd is not None:
                    try:
                        os.close(temp_fd)
                    except Exception:
                        pass
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

    def load_from_file(self, path: str | None = None) -> None:
        """Load histories from a JSON file.

        Creates backup of existing data before loading.

        Args:
            path: Path to load file from (uses save_path if None)

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        load_path = path or self.save_path

        if not os.path.exists(load_path):
            logger.warning(f"No history file found at {load_path}")
            return

        with self._lock:
            # Create backup of current data
            if self.histories:
                self._create_backup(load_path)

            with open(load_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse histories
            loaded_histories: dict[int, RepairHistory] = {}
            for chapter_str, history_dict in data.get("histories", {}).items():
                try:
                    chapter_num = int(chapter_str)
                    history = self._dict_to_history(history_dict)
                    loaded_histories[chapter_num] = history
                except (ValueError, KeyError) as e:
                    logger.error(f"Failed to parse history for chapter {chapter_str}: {e}")

            self.histories = loaded_histories
            logger.info(f"Loaded {len(self.histories)} repair histories from {load_path}")

    def clear(self) -> None:
        """Clear all histories from the store."""
        with self._lock:
            count = len(self.histories)
            self.histories.clear()
            logger.info(f"Cleared {count} repair histories")

            if self.auto_save and os.path.exists(self.save_path):
                self.save_to_file()

    def get_chapters_by_status(self, status: str) -> list[int]:
        """Get list of chapters with a specific final status.

        Args:
            status: The final status to filter by (success, failed, partial, manual_review)

        Returns:
            List of chapter numbers with matching status
        """
        with self._lock:
            return [
                chapter
                for chapter, history in self.histories.items()
                if history.final_status == status
            ]

    def get_failed_chapters(self) -> list[int]:
        """Get list of chapters that failed repair.

        Returns:
            List of chapter numbers that failed
        """
        return self.get_chapters_by_status("failed")

    def get_successful_chapters(self) -> list[int]:
        """Get list of successfully repaired chapters.

        Returns:
            List of chapter numbers that were successfully repaired
        """
        return self.get_chapters_by_status("success")

    def get_manual_review_chapters(self) -> list[int]:
        """Get list of chapters requiring manual review.

        Returns:
            List of chapter numbers that need manual review
        """
        return self.get_chapters_by_status("manual_review")

    def export_summary(self, path: str) -> None:
        """Export a human-readable summary to a text file.

        Args:
            path: Path to export summary to
        """
        stats = self.get_statistics()
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "=" * 60,
            "REPAIR HISTORY SUMMARY",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            "",
            "OVERVIEW",
            "-" * 60,
            f"Total Chapters: {stats['total_chapters']}",
            f"Total Attempts: {stats['total_attempts']}",
            f"Average Iterations: {stats['average_iterations']:.2f}",
            "",
            "RESULTS",
            "-" * 60,
            f"Successful: {stats['successful_repairs']} ({stats['success_rate']:.1%})",
            f"Partial: {stats['partial_repairs']}",
            f"Failed: {stats['failed_repairs']}",
            f"Manual Review: {stats['manual_reviews']}",
            "",
            "ISSUES",
            "-" * 60,
            f"Total Found: {stats['total_issues_found']}",
            f"Total Fixed: {stats['total_issues_fixed']}",
            f"Total Remaining: {stats['total_issues_remaining']}",
            f"Fix Rate: {stats['fix_rate']:.1%}",
            "",
            "VALIDATOR USAGE",
            "-" * 60,
        ]

        for validator, count in sorted(
            stats["validator_usage"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {validator}: {count}")

        if stats["most_common_issues"]:
            lines.append("")
            lines.append("MOST COMMON ISSUES")
            lines.append("-" * 60)
            for issue_type, count in stats["most_common_issues"].items():
                lines.append(f"  {issue_type}: {count}")

        lines.append("")
        lines.append("=" * 60)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Exported summary to {path}")

    # Private methods

    def _auto_save(self) -> None:
        """Auto-save with backup rotation."""
        if os.path.exists(self.save_path):
            self._rotate_backups()
        self.save_to_file()

    def _rotate_backups(self) -> None:
        """Rotate backup files, keeping only backup_count most recent."""
        if self.backup_count <= 0:
            return

        save_path_obj = Path(self.save_path)
        base_path = save_path_obj.parent / save_path_obj.stem
        extension = save_path_obj.suffix

        # Remove oldest backup if at limit
        oldest_backup = Path(f"{base_path}.bak_{self.backup_count}{extension}")
        if oldest_backup.exists():
            oldest_backup.unlink()

        # Shift existing backups
        for i in range(self.backup_count - 1, 0, -1):
            old_backup = Path(f"{base_path}.bak_{i}{extension}")
            new_backup = Path(f"{base_path}.bak_{i + 1}{extension}")
            if old_backup.exists():
                shutil.move(str(old_backup), str(new_backup))

        # Create new backup
        first_backup = Path(f"{base_path}.bak_1{extension}")
        if save_path_obj.exists():
            shutil.copy2(str(save_path_obj), str(first_backup))

    def _create_backup(self, path: str) -> None:
        """Create a one-time backup before loading new data."""
        if not os.path.exists(path):
            return

        backup_path = f"{path}.pre_load_backup"
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{path}.pre_load_backup.{counter}"
            counter += 1

        shutil.copy2(path, backup_path)
        logger.info(f"Created backup at {backup_path}")

    def _dict_to_history(self, data: dict[str, Any]) -> RepairHistory:
        """Convert dictionary to RepairHistory object."""
        attempts = [
            RepairAttempt(
                attempt_number=a.get("attempt_number", 0),
                timestamp=a.get("timestamp", ""),
                issues_before=a.get("issues_before", []),
                issues_after=a.get("issues_after"),
                strategy_used=a.get("strategy_used", ""),
                llm_prompt=a.get("llm_prompt", ""),
                success=a.get("success", False),
                metadata=a.get("metadata", {}),
            )
            for a in data.get("attempts", [])
        ]

        return RepairHistory(
            chapter_number=data.get("chapter_number", 0),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            attempts=attempts,
            final_status=data.get("final_status", "in_progress"),
            validators_used=data.get("validators_used", []),
            total_issues_found=data.get("total_issues_found", 0),
            issues_fixed=data.get("issues_fixed", 0),
            issues_remaining=data.get("issues_remaining", 0),
            escalation_reason=data.get("escalation_reason", ""),
        )

    def _empty_statistics(self) -> dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_chapters": 0,
            "total_attempts": 0,
            "successful_repairs": 0,
            "failed_repairs": 0,
            "partial_repairs": 0,
            "manual_reviews": 0,
            "success_rate": 0.0,
            "average_iterations": 0.0,
            "total_issues_found": 0,
            "total_issues_fixed": 0,
            "total_issues_remaining": 0,
            "fix_rate": 0.0,
            "validator_usage": {},
            "most_common_issues": {},
        }
