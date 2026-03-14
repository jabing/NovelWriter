# src/crawlers/cache.py
"""Cache manager for crawler data with file persistence."""

import json
import logging
import time
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages persistent cache for crawler data.

    Features:
    - File-based persistence
    - TTL-based expiration
    - Automatic cleanup
    - Thread-safe operations
    """

    DEFAULT_CACHE_DIR = "data/cache/crawlers"
    DEFAULT_TTL = 3600  # 1 hour

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        default_ttl: int = DEFAULT_TTL,
    ) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir or self.DEFAULT_CACHE_DIR)
        self.default_ttl = default_ttl
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Sanitize key for filesystem
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    async def get(self, key: str) -> tuple[bool, Any]:
        """Get data from cache.

        Args:
            key: Cache key

        Returns:
            Tuple of (found, data)
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return False, None

        try:
            async with aiofiles.open(cache_path) as f:
                content = await f.read()
                cache_data = json.loads(content)

            # Check expiration
            if time.time() > cache_data.get("expires_at", 0):
                # Cache expired
                cache_path.unlink(missing_ok=True)
                return False, None

            return True, cache_data.get("data")

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to read cache {key}: {e}")
            return False, None

    async def set(
        self,
        key: str,
        data: Any,
        ttl: int | None = None,
    ) -> None:
        """Save data to cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_path = self._get_cache_path(key)
        ttl = ttl if ttl is not None else self.default_ttl

        cache_data = {
            "data": data,
            "cached_at": time.time(),
            "expires_at": time.time() + ttl,
            "key": key,
        }

        try:
            async with aiofiles.open(cache_path, "w") as f:
                await f.write(json.dumps(cache_data, indent=2, ensure_ascii=False))
            logger.debug(f"Cached data for key: {key}")
        except OSError as e:
            logger.warning(f"Failed to write cache {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a cache entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    async def clear_expired(self) -> int:
        """Clear all expired cache entries.

        Returns:
            Number of entries cleared
        """
        cleared = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                async with aiofiles.open(cache_file) as f:
                    content = await f.read()
                    cache_data = json.loads(content)

                if current_time > cache_data.get("expires_at", 0):
                    cache_file.unlink()
                    cleared += 1

            except (OSError, json.JSONDecodeError, KeyError):
                # Invalid cache file, remove it
                cache_file.unlink(missing_ok=True)
                cleared += 1

        if cleared > 0:
            logger.info(f"Cleared {cleared} expired cache entries")

        return cleared

    async def clear_all(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        cleared = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            cleared += 1

        logger.info(f"Cleared all {cleared} cache entries")
        return cleared

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics about the cache
        """
        total_size = 0
        entry_count = 0
        expired_count = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            entry_count += 1
            total_size += cache_file.stat().st_size

            try:
                async with aiofiles.open(cache_file) as f:
                    content = await f.read()
                    cache_data = json.loads(content)

                if current_time > cache_data.get("expires_at", 0):
                    expired_count += 1

            except (OSError, json.JSONDecodeError, KeyError):
                expired_count += 1

        return {
            "entry_count": entry_count,
            "expired_count": expired_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
