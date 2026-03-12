"""Caching utilities for creative workflow.

This module provides caching mechanisms to avoid regenerating
content like outlines and characters.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cache entry with metadata."""

    key: str
    data: Any
    timestamp: float
    content_hash: str


class CreativeCache:
    """Cache for creative content generation.

    Caches generated outlines and characters to avoid
    regenerating them when the context hasn't changed.

    Usage:
        cache = CreativeCache(cache_dir=".cache/creative")

        # Try to get cached result
        result = cache.get("outline", context_hash)
        if result:
            return result

        # Generate and cache
        result = await generate_outline(context)
        cache.set("outline", context_hash, result)
    """

    def __init__(self, cache_dir: str = ".cache/creative"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, CacheEntry] = {}

    def _get_cache_path(self, content_type: str, key: str) -> Path:
        """Get the file path for a cache entry."""
        safe_key = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{content_type}_{safe_key}.json"

    def _compute_context_hash(self, context: str) -> str:
        """Compute a hash of the context for cache key."""
        return hashlib.sha256(context.encode()).hexdigest()[:32]

    def get(self, content_type: str, context: str) -> Any | None:
        """Get cached content if available.

        Args:
            content_type: Type of content (outline, characters, etc.)
            context: The context used to generate the content

        Returns:
            Cached data or None if not found
        """
        context_hash = self._compute_context_hash(context)
        cache_key = f"{content_type}:{context_hash}"

        # Check memory cache first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            logger.debug(f"Memory cache hit for {content_type}")
            return entry.data

        # Check file cache
        cache_path = self._get_cache_path(content_type, context_hash)
        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cached_data = json.load(f)

                # Store in memory cache for faster access
                import time

                self._memory_cache[cache_key] = CacheEntry(
                    key=cache_key,
                    data=cached_data,
                    timestamp=time.time(),
                    content_hash=context_hash,
                )

                logger.info(f"Cache hit for {content_type}")
                return cached_data

            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        return None

    def set(self, content_type: str, context: str, data: Any) -> None:
        """Cache generated content.

        Args:
            content_type: Type of content (outline, characters, etc.)
            context: The context used to generate the content
            data: The data to cache
        """
        context_hash = self._compute_context_hash(context)
        cache_key = f"{content_type}:{context_hash}"

        # Store in memory cache
        import time

        self._memory_cache[cache_key] = CacheEntry(
            key=cache_key, data=data, timestamp=time.time(), content_hash=context_hash
        )

        # Store in file cache
        cache_path = self._get_cache_path(content_type, context_hash)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cached {content_type} to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def invalidate(self, content_type: str | None = None) -> int:
        """Invalidate cached entries.

        Args:
            content_type: Type to invalidate, or None for all

        Returns:
            Number of entries invalidated
        """
        count = 0

        # Clear memory cache
        if content_type:
            keys_to_remove = [
                k for k in self._memory_cache.keys() if k.startswith(f"{content_type}:")
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
                count += 1
        else:
            count = len(self._memory_cache)
            self._memory_cache.clear()

        # Clear file cache
        if self.cache_dir.exists():
            pattern = f"{content_type}_*.json" if content_type else "*.json"
            for cache_file in self.cache_dir.glob(pattern):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache file: {e}")

        logger.info(f"Invalidated {count} cache entries")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        file_count = len(list(self.cache_dir.glob("*.json")))
        memory_count = len(self._memory_cache)

        # Calculate total size
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            "memory_entries": memory_count,
            "file_entries": file_count,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir),
        }

    def clear_old_entries(self, max_age_hours: int = 24) -> int:
        """Clear cache entries older than specified hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of entries cleared
        """
        import time

        count = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        # Check memory cache
        keys_to_remove = []
        for key, entry in self._memory_cache.items():
            if current_time - entry.timestamp > max_age_seconds:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._memory_cache[key]
            count += 1

        # Check file cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                if current_time - cache_file.stat().st_mtime > max_age_seconds:
                    cache_file.unlink()
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to delete old cache file: {e}")

        logger.info(f"Cleared {count} old cache entries")
        return count


class DiscussionCache(CreativeCache):
    """Specialized cache for discussion-based planning.

    Provides convenient methods for caching outlines and characters
    based on discussion context.
    """

    def get_outline(self, discussion_context: str) -> str | None:
        """Get cached outline for discussion context.

        Args:
            discussion_context: The full discussion context

        Returns:
            Cached outline or None
        """
        return self.get("outline", discussion_context)

    def set_outline(self, discussion_context: str, outline: str) -> None:
        """Cache outline for discussion context.

        Args:
            discussion_context: The full discussion context
            outline: The generated outline
        """
        self.set("outline", discussion_context, outline)

    def get_characters(self, discussion_context: str, outline: str) -> list[dict] | None:
        """Get cached characters for discussion context.

        Args:
            discussion_context: The full discussion context
            outline: The story outline

        Returns:
            Cached characters or None
        """
        # Include outline hash in context for character cache
        combined = f"{discussion_context}\n\n{outline}"
        return self.get("characters", combined)

    def set_characters(self, discussion_context: str, outline: str, characters: list[dict]) -> None:
        """Cache characters for discussion context.

        Args:
            discussion_context: The full discussion context
            outline: The story outline
            characters: The generated characters
        """
        combined = f"{discussion_context}\n\n{outline}"
        self.set("characters", combined, characters)

    def invalidate_outline(self) -> int:
        """Invalidate all cached outlines."""
        return self.invalidate("outline")

    def invalidate_characters(self) -> int:
        """Invalidate all cached characters."""
        return self.invalidate("characters")
