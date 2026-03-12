"""Checkpointing system for mid-chapter progress preservation.

Provides checkpoint functionality to preserve generation progress during
chapter writing, enabling recovery from failures and resumption of work.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Configuration constants
CHECKPOINT_INTERVAL_WORDS = 500  # Create checkpoint every N words
MAX_CHECKPOINT_AGE_DAYS = 7  # Cleanup checkpoints older than N days
MAX_CHECKPOINT_SIZE_MB = 10  # Maximum size per checkpoint in MB
MAX_CHECKPOINTS_PER_CHAPTER = 20  # Limit checkpoints to prevent disk bloat


@dataclass
class Checkpoint:
    """A checkpoint representing generation progress."""

    checkpoint_id: str
    chapter_number: int
    word_count: int
    content: str
    state_snapshot: dict[str, Any]
    created_at: datetime
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize checkpoint to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "chapter_number": self.chapter_number,
            "word_count": self.word_count,
            "content": self.content,
            "state_snapshot": self.state_snapshot,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Deserialize checkpoint from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            chapter_number=data["chapter_number"],
            word_count=data["word_count"],
            content=data["content"],
            state_snapshot=data["state_snapshot"],
            created_at=datetime.fromisoformat(data["created_at"]),
            checksum=data["checksum"],
            metadata=data.get("metadata", {}),
        )


class CheckpointManager:
    """Manages checkpoints for chapter generation.

    Creates checkpoints at:
    - Chapter boundaries (start and end of each chapter)
    - Mid-chapter intervals (every 500 words by default)

    Features:
    - Integrity verification via checksums
    - Automatic cleanup of old checkpoints
    - Size limits to prevent disk bloat
    """

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        interval_words: int = CHECKPOINT_INTERVAL_WORDS,
        max_age_days: int = MAX_CHECKPOINT_AGE_DAYS,
        max_checkpoints_per_chapter: int = MAX_CHECKPOINTS_PER_CHAPTER,
    ) -> None:
        """Initialize the checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints (default: data/checkpoints)
            interval_words: Word interval for mid-chapter checkpoints
            max_age_days: Maximum age in days before cleanup
            max_checkpoints_per_chapter: Maximum checkpoints to keep per chapter
        """
        self.checkpoint_dir = checkpoint_dir or Path("data/checkpoints")
        self.interval_words = interval_words
        self.max_age_days = max_age_days
        self.max_checkpoints_per_chapter = max_checkpoints_per_chapter

        # Ensure directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Track checkpoints for current chapter
        self._current_chapter: int | None = None
        self._last_checkpoint_words: int = 0
        self._chapter_checkpoints: list[str] = []

        logger.info(
            f"CheckpointManager initialized: dir={self.checkpoint_dir}, "
            f"interval={self.interval_words} words"
        )

    def _generate_checksum(self, content: str, state_snapshot: dict[str, Any]) -> str:
        """Generate checksum for content and state.

        Args:
            content: Chapter content
            state_snapshot: Story state snapshot

        Returns:
            SHA256 checksum string
        """
        data = content + json.dumps(state_snapshot, sort_keys=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get the file path for a checkpoint.

        Args:
            checkpoint_id: Unique checkpoint identifier

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"{checkpoint_id}.json"

    def _validate_checkpoint_size(self, checkpoint: Checkpoint) -> bool:
        """Validate checkpoint size is within limits.

        Args:
            checkpoint: Checkpoint to validate

        Returns:
            True if size is acceptable
        """
        # Estimate size in bytes (JSON representation)
        json_str = json.dumps(checkpoint.to_dict())
        size_mb = len(json_str.encode("utf-8")) / (1024 * 1024)

        if size_mb > MAX_CHECKPOINT_SIZE_MB:
            logger.warning(
                f"Checkpoint {checkpoint.checkpoint_id} exceeds size limit: "
                f"{size_mb:.2f}MB > {MAX_CHECKPOINT_SIZE_MB}MB"
            )
            return False
        return True

    def create_checkpoint(
        self,
        chapter_number: int,
        word_count: int,
        content: str,
        state_snapshot: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint | None:
        """Create a new checkpoint.

        Args:
            chapter_number: Current chapter number
            word_count: Current word count in chapter
            content: Current chapter content
            state_snapshot: Current story state
            metadata: Optional additional metadata

        Returns:
            Created checkpoint or None if creation failed
        """
        # Reset tracking if chapter changed
        if self._current_chapter != chapter_number:
            self._current_chapter = chapter_number
            self._last_checkpoint_words = 0
            self._chapter_checkpoints = []

        # Generate checkpoint ID
        timestamp = datetime.now()
        checkpoint_id = (
            f"chapter{chapter_number}_words{word_count}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        )

        # Calculate checksum
        checksum = self._generate_checksum(content, state_snapshot)

        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            chapter_number=chapter_number,
            word_count=word_count,
            content=content,
            state_snapshot=state_snapshot,
            created_at=timestamp,
            checksum=checksum,
            metadata=metadata or {},
        )

        # Validate size
        if not self._validate_checkpoint_size(checkpoint):
            return None

        # Save checkpoint
        try:
            checkpoint_path = self._get_checkpoint_path(checkpoint_id)
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)

            self._last_checkpoint_words = word_count
            self._chapter_checkpoints.append(checkpoint_id)

            logger.info(
                f"Created checkpoint: {checkpoint_id} "
                f"(chapter={chapter_number}, words={word_count})"
            )

            # Enforce max checkpoints per chapter
            self._enforce_checkpoint_limit(chapter_number)

            return checkpoint

        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint_id}: {e}")
            return None

    def should_create_checkpoint(self, chapter_number: int, word_count: int) -> bool:
        """Determine if a checkpoint should be created.

        Creates checkpoints:
        - At chapter start (word_count == 0)
        - At every interval_words thereafter

        Args:
            chapter_number: Current chapter number
            word_count: Current word count

        Returns:
            True if checkpoint should be created
        """
        # Reset tracking if chapter changed
        if self._current_chapter != chapter_number:
            return True  # Always checkpoint at chapter start

        # Check if we've reached the interval threshold
        words_since_last = word_count - self._last_checkpoint_words
        return words_since_last >= self.interval_words

    def _enforce_checkpoint_limit(self, chapter_number: int) -> None:
        """Enforce maximum checkpoints per chapter.

        Removes oldest checkpoints if limit exceeded.

        Args:
            chapter_number: Chapter to enforce limit for
        """
        chapter_checkpoints = list(self.checkpoint_dir.glob(f"chapter{chapter_number}_*.json"))

        if len(chapter_checkpoints) > self.max_checkpoints_per_chapter:
            # Sort by modification time, oldest first
            chapter_checkpoints.sort(key=lambda p: p.stat().st_mtime)

            # Remove oldest
            to_remove = chapter_checkpoints[
                : len(chapter_checkpoints) - self.max_checkpoints_per_chapter
            ]
            for path in to_remove:
                try:
                    path.unlink()
                    logger.debug(f"Removed old checkpoint: {path.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove checkpoint {path}: {e}")

    def load_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Loaded checkpoint or None if not found/invalid
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)

            checkpoint = Checkpoint.from_dict(data)

            # Verify checksum
            expected_checksum = self._generate_checksum(
                checkpoint.content, checkpoint.state_snapshot
            )
            if checkpoint.checksum != expected_checksum:
                logger.error(
                    f"Checkpoint {checkpoint_id} checksum mismatch: "
                    f"expected {expected_checksum}, got {checkpoint.checksum}"
                )
                return None

            logger.info(f"Loaded checkpoint: {checkpoint_id}")
            return checkpoint

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    def get_latest_checkpoint(self, chapter_number: int | None = None) -> Checkpoint | None:
        """Get the most recent checkpoint.

        Args:
            chapter_number: Optional chapter to get latest for

        Returns:
            Latest checkpoint or None if none exist
        """
        if chapter_number is not None:
            pattern = f"chapter{chapter_number}_*.json"
        else:
            pattern = "chapter*_*.json"

        checkpoints = list(self.checkpoint_dir.glob(pattern))

        if not checkpoints:
            return None

        # Sort by modification time, newest first
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Load and return the newest valid checkpoint
        for path in checkpoints:
            checkpoint_id = path.stem
            checkpoint = self.load_checkpoint(checkpoint_id)
            if checkpoint is not None:
                return checkpoint

        return None

    def list_checkpoints(self, chapter_number: int | None = None) -> list[dict[str, Any]]:
        """List all checkpoints with metadata.

        Args:
            chapter_number: Optional chapter to filter by

        Returns:
            List of checkpoint metadata dictionaries
        """
        if chapter_number is not None:
            pattern = f"chapter{chapter_number}_*.json"
        else:
            pattern = "chapter*_*.json"

        checkpoints = []
        for path in self.checkpoint_dir.glob(pattern):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                checkpoints.append(
                    {
                        "checkpoint_id": data["checkpoint_id"],
                        "chapter_number": data["chapter_number"],
                        "word_count": data["word_count"],
                        "created_at": data["created_at"],
                        "size_bytes": path.stat().st_size,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read checkpoint {path}: {e}")

        # Sort by creation time, newest first
        checkpoints.sort(key=lambda c: c["created_at"], reverse=True)
        return checkpoints

    def cleanup_old_checkpoints(self) -> int:
        """Remove checkpoints older than max_age_days.

        Returns:
            Number of checkpoints removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        removed_count = 0

        for path in self.checkpoint_dir.glob("chapter*_*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                created_at = datetime.fromisoformat(data["created_at"])

                if created_at < cutoff_date:
                    path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old checkpoint: {path.name}")

            except Exception as e:
                logger.warning(f"Failed to process checkpoint {path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old checkpoints")

        return removed_count

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint.

        Args:
            checkpoint_id: Checkpoint to delete

        Returns:
            True if deletion successful
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)

        if not checkpoint_path.exists():
            return False

        try:
            checkpoint_path.unlink()
            logger.info(f"Deleted checkpoint: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get checkpoint statistics.

        Returns:
            Dictionary with checkpoint statistics
        """
        checkpoints = self.list_checkpoints()

        total_size = sum(c["size_bytes"] for c in checkpoints)
        chapters = {c["chapter_number"] for c in checkpoints}

        return {
            "total_checkpoints": len(checkpoints),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "chapters_with_checkpoints": len(chapters),
            "oldest_checkpoint": checkpoints[-1]["created_at"] if checkpoints else None,
            "newest_checkpoint": checkpoints[0]["created_at"] if checkpoints else None,
        }


def create_checkpoint_manager(
    checkpoint_dir: Path | None = None,
) -> CheckpointManager:
    """Factory function to create a CheckpointManager.

    Args:
        checkpoint_dir: Optional custom checkpoint directory

    Returns:
        Configured CheckpointManager instance
    """
    if checkpoint_dir is None:
        # Default to data/checkpoints in project root
        project_root = Path(__file__).parent.parent.parent
        checkpoint_dir = project_root / "data" / "checkpoints"

    return CheckpointManager(checkpoint_dir=checkpoint_dir)


__all__ = [
    "CheckpointManager",
    "Checkpoint",
    "create_checkpoint_manager",
    "CHECKPOINT_INTERVAL_WORDS",
    "MAX_CHECKPOINT_AGE_DAYS",
    "MAX_CHECKPOINT_SIZE_MB",
    "MAX_CHECKPOINTS_PER_CHAPTER",
]
