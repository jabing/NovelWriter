# src/memory/compression.py
"""Memory compression utilities for optimizing memory storage.

Provides functionality to:
- Compress similar memory entries by merging duplicates
- Clean up expired/old memory entries
- Run comprehensive compression operations

Usage:
    from src.novel_agent.memory.compression import MemoryCompressor
    from src.novel_agent.memory.base import BaseMemory

    memory = FileMemory()
    compressor = MemoryCompressor()

    # Compress similar entries
    merged_count = await compressor.compress_similar_entries(memory)

    # Clean up old entries
    deleted_count = await compressor.cleanup_expired_entries(memory, max_age_days=30)

    # Run all compression
    stats = await compressor.compress_all(memory)
"""

import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

from src.novel_agent.memory.base import BaseMemory, MemoryEntry

logger = logging.getLogger(__name__)


class MemoryCompressor:
    """Compresses and optimizes memory storage.

    Methods:
        compress_similar_entries: Merge similar memory entries
        cleanup_expired_entries: Remove old memory entries
        compress_all: Run all compression operations
    """

    def __init__(self, similarity_threshold: float = 0.8) -> None:
        """Initialize the memory compressor.

        Args:
            similarity_threshold: Threshold for considering entries similar (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold

    def _calculate_key_similarity(self, key1: str, key2: str) -> float:
        """Calculate similarity between two keys.

        Uses both prefix matching and sequence matching for robust comparison.

        Args:
            key1: First key
            key2: Second key

        Returns:
            Similarity score (0.0-1.0)
        """
        # Normalize keys
        k1 = key1.lower().strip("/")
        k2 = key2.lower().strip("/")

        # Exact match
        if k1 == k2:
            return 1.0

        # Check prefix match (same directory path)
        parts1 = k1.split("/")
        parts2 = k2.split("/")

        # Count matching path components
        common_prefix = 0
        for p1, p2 in zip(parts1[:-1], parts2[:-1], strict=False):  # Exclude filename
            if p1 == p2:
                common_prefix += 1
            else:
                break

        # If they share directory structure, boost similarity
        prefix_boost = common_prefix / max(len(parts1), len(parts2), 1)

        # Use sequence matcher for the full key
        seq_similarity = SequenceMatcher(None, k1, k2).ratio()

        # Weight: 40% prefix match, 60% sequence match
        return 0.4 * prefix_boost + 0.6 * seq_similarity

    def _calculate_value_similarity(self, value1: Any, value2: Any) -> float:
        """Calculate similarity between two values.

        Args:
            value1: First value
            value2: Second value

        Returns:
            Similarity score (0.0-1.0)
        """
        # Convert to strings for comparison
        str1 = str(value1) if value1 is not None else ""
        str2 = str(value2) if value2 is not None else ""

        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0

        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _entries_are_similar(
        self,
        entry1: MemoryEntry,
        entry2: MemoryEntry,
        threshold: float,
    ) -> bool:
        """Check if two entries are similar enough to merge.

        Args:
            entry1: First entry
            entry2: Second entry
            threshold: Similarity threshold

        Returns:
            True if entries are similar
        """
        # Must have same type in metadata
        type1 = entry1.metadata.get("type", "")
        type2 = entry2.metadata.get("type", "")

        if type1 and type2 and type1 != type2:
            return False

        # Calculate combined similarity
        key_sim = self._calculate_key_similarity(entry1.key, entry2.key)
        value_sim = self._calculate_value_similarity(entry1.value, entry2.value)

        # Weight: 30% key similarity, 70% value similarity
        combined = 0.3 * key_sim + 0.7 * value_sim

        return combined >= threshold

    def _merge_entries(self, entry1: MemoryEntry, entry2: MemoryEntry) -> MemoryEntry:
        """Merge two similar entries into one.

        Keeps the entry with more recent data, preserving important metadata.

        Args:
            entry1: First entry
            entry2: Second entry

        Returns:
            Merged entry
        """
        # Determine which is newer based on metadata
        time1 = entry1.metadata.get("created_at") or entry1.metadata.get("updated_at")
        time2 = entry2.metadata.get("created_at") or entry2.metadata.get("updated_at")

        if time1 and time2:
            try:
                dt1 = datetime.fromisoformat(str(time1))
                dt2 = datetime.fromisoformat(str(time2))
                newer, older = (entry1, entry2) if dt1 >= dt2 else (entry2, entry1)
            except (ValueError, TypeError):
                newer, older = entry1, entry2
        else:
            newer, older = entry1, entry2

        # Merge metadata
        merged_metadata = {**older.metadata, **newer.metadata}
        merged_metadata["merged_from"] = older.key
        merged_metadata["merged_at"] = datetime.now().isoformat()

        # Use newer's value, but keep older value in metadata if different
        merged_value = newer.value
        if newer.value != older.value:
            merged_metadata["previous_value"] = str(older.value)[:500]  # Truncate

        return MemoryEntry(
            key=newer.key,
            value=merged_value,
            metadata=merged_metadata,
        )

    def _get_entry_age_days(self, entry: MemoryEntry) -> int:
        """Get the age of an entry in days.

        Args:
            entry: Memory entry

        Returns:
            Age in days (0 if no timestamp found)
        """
        timestamp = entry.metadata.get("created_at") or entry.metadata.get("updated_at")

        if not timestamp:
            return 0

        try:
            created = datetime.fromisoformat(str(timestamp))
            age = datetime.now() - created
            return age.days
        except (ValueError, TypeError):
            return 0

    async def compress_similar_entries(
        self,
        memory: BaseMemory,
        similarity_threshold: float | None = None,
        dry_run: bool = False,
    ) -> int:
        """Compress memory by merging similar entries.

        Identifies entries with similar keys and values, then merges them
        to reduce redundancy.

        Args:
            memory: BaseMemory instance to compress
            similarity_threshold: Override default threshold (0.0-1.0)
            dry_run: If True, only report what would be merged

        Returns:
            Number of entries merged
        """
        threshold = similarity_threshold or self.similarity_threshold
        merged_count = 0

        # Get all keys
        all_keys = await memory.list_keys()

        if not all_keys:
            logger.info("No entries to compress")
            return 0

        logger.info(f"Analyzing {len(all_keys)} entries for similarity (threshold={threshold})")

        # Load all entries
        entries: dict[str, MemoryEntry] = {}
        for key in all_keys:
            entry = await memory.retrieve(key)
            if entry:
                entries[key] = entry

        # Find similar pairs
        processed: set[str] = set()
        merge_operations: list[tuple[MemoryEntry, MemoryEntry]] = []

        keys_list = list(entries.keys())
        for i, key1 in enumerate(keys_list):
            if key1 in processed:
                continue

            entry1 = entries[key1]

            for key2 in keys_list[i + 1 :]:
                if key2 in processed:
                    continue

                entry2 = entries[key2]

                if self._entries_are_similar(entry1, entry2, threshold):
                    merge_operations.append((entry1, entry2))
                    processed.add(key1)
                    processed.add(key2)
                    break

        # Perform merges
        for entry1, entry2 in merge_operations:
            merged = self._merge_entries(entry1, entry2)
            older_key = entry2.key if merged.key == entry1.key else entry1.key

            if dry_run:
                logger.info(f"[DRY RUN] Would merge: {older_key} -> {merged.key}")
            else:
                # Store merged entry
                await memory.store(merged.key, merged.value, merged.metadata)
                # Delete older entry
                await memory.delete(older_key)
                logger.info(f"Merged: {older_key} -> {merged.key}")

            merged_count += 1

        logger.info(f"Compressed {merged_count} similar entry pairs")
        return merged_count

    async def cleanup_expired_entries(
        self,
        memory: BaseMemory,
        max_age_days: int = 30,
        dry_run: bool = False,
        entry_types: list[str] | None = None,
    ) -> int:
        """Remove expired/old entries from memory.

        Args:
            memory: BaseMemory instance to clean
            max_age_days: Maximum age in days before expiry
            dry_run: If True, only report what would be deleted
            entry_types: Only clean specific entry types (e.g., ["character", "plot"])

        Returns:
            Number of entries deleted
        """
        deleted_count = 0
        datetime.now() - timedelta(days=max_age_days)

        # Get all keys
        all_keys = await memory.list_keys()

        if not all_keys:
            logger.info("No entries to clean up")
            return 0

        logger.info(f"Checking {len(all_keys)} entries for expiry (max_age={max_age_days} days)")

        for key in all_keys:
            entry = await memory.retrieve(key)
            if not entry:
                continue

            # Check entry type filter
            if entry_types:
                entry_type = entry.metadata.get("type", "")
                if entry_type not in entry_types:
                    continue

            # Check age
            age_days = self._get_entry_age_days(entry)

            if age_days > max_age_days:
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete: {key} (age: {age_days} days)")
                else:
                    await memory.delete(key)
                    logger.info(f"Deleted expired entry: {key} (age: {age_days} days)")

                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} expired entries")
        return deleted_count

    async def compress_all(
        self,
        memory: BaseMemory,
        max_age_days: int = 30,
        similarity_threshold: float = 0.8,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """Run all compression operations.

        Args:
            memory: BaseMemory instance to compress
            max_age_days: Maximum age for expired entries
            similarity_threshold: Threshold for merging similar entries
            dry_run: If True, only report what would be done

        Returns:
            Dictionary with compression statistics
        """
        logger.info("Starting full memory compression...")

        # Get initial stats
        initial_keys = await memory.list_keys()
        initial_count = len(initial_keys)

        stats = {
            "initial_entries": initial_count,
            "merged_entries": 0,
            "deleted_entries": 0,
            "final_entries": 0,
            "space_saved": 0,
        }

        # Step 1: Compress similar entries
        stats["merged_entries"] = await self.compress_similar_entries(
            memory, similarity_threshold, dry_run
        )

        # Step 2: Clean up expired entries
        stats["deleted_entries"] = await self.cleanup_expired_entries(
            memory, max_age_days, dry_run
        )

        # Get final stats
        if not dry_run:
            final_keys = await memory.list_keys()
            stats["final_entries"] = len(final_keys)
            stats["space_saved"] = initial_count - stats["final_entries"]
        else:
            stats["final_entries"] = initial_count - stats["merged_entries"] - stats["deleted_entries"]
            stats["space_saved"] = stats["merged_entries"] + stats["deleted_entries"]

        logger.info(
            f"Compression complete: {stats['space_saved']} entries saved "
            f"({stats['merged_entries']} merged, {stats['deleted_entries']} deleted)"
        )

        return stats

    async def get_compression_preview(
        self,
        memory: BaseMemory,
    ) -> dict[str, Any]:
        """Get a preview of potential compression savings.

        Args:
            memory: BaseMemory instance to analyze

        Returns:
            Dictionary with analysis results
        """
        keys = await memory.list_keys()

        # Group by type
        by_type: dict[str, int] = {}
        old_entries = 0
        potential_merges = 0

        entries: list[MemoryEntry] = []
        for key in keys:
            entry = await memory.retrieve(key)
            if entry:
                entries.append(entry)
                entry_type = entry.metadata.get("type", "unknown")
                by_type[entry_type] = by_type.get(entry_type, 0) + 1

                # Check age
                age = self._get_entry_age_days(entry)
                if age > 30:
                    old_entries += 1

        # Check for potential merges
        for i, e1 in enumerate(entries):
            for e2 in entries[i + 1 :]:
                if self._entries_are_similar(e1, e2, self.similarity_threshold):
                    potential_merges += 1
                    break

        return {
            "total_entries": len(keys),
            "by_type": by_type,
            "old_entries_30d": old_entries,
            "potential_merges": potential_merges,
            "estimated_savings": potential_merges + old_entries,
        }
