# src/utils/cache.py
"""Caching utilities for performance optimization."""

import hashlib
import json
import time
from collections import OrderedDict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cache entry with expiration."""

    value: Any
    created_at: float
    ttl: float  # Time to live in seconds
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl <= 0:
            return False  # Never expires
        return time.time() - self.created_at > self.ttl


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600) -> None:
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds (0 = never expire)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _hash_key(self, key: str) -> str:
        """Create hash of key for storage."""
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        hashed_key = self._hash_key(key)

        if hashed_key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[hashed_key]

        # Check expiration
        if entry.is_expired():
            del self._cache[hashed_key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(hashed_key)
        entry.hits += 1
        self._hits += 1

        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (uses default if None)
        """
        hashed_key = self._hash_key(key)

        # Remove oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        # Remove existing entry if present
        if hashed_key in self._cache:
            del self._cache[hashed_key]

        # Add new entry
        self._cache[hashed_key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl=ttl if ttl is not None else self.default_ttl,
        )

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted
        """
        hashed_key = self._hash_key(key)
        if hashed_key in self._cache:
            del self._cache[hashed_key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total_requests,
        }


class LLMResponseCache:
    """Specialized cache for LLM responses."""

    def __init__(self, max_size: int = 500, default_ttl: float = 7200) -> None:
        """Initialize LLM response cache.

        Args:
            max_size: Maximum cached responses
            default_ttl: Default TTL (2 hours)
        """
        self._cache = LRUCache(max_size=max_size, default_ttl=default_ttl)

    def _create_key(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Create cache key from request parameters."""
        key_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            **kwargs,
        }
        return json.dumps(key_data, sort_keys=True)

    def get_response(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str | None:
        """Get cached LLM response.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Temperature setting
            **kwargs: Additional parameters

        Returns:
            Cached response or None
        """
        # Only cache low-temperature responses (more deterministic)
        if temperature > 0.3:
            return None

        key = self._create_key(prompt, system_prompt, temperature, **kwargs)
        return self._cache.get(key)

    def set_response(
        self,
        prompt: str,
        response: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> None:
        """Cache LLM response.

        Args:
            prompt: User prompt
            response: LLM response to cache
            system_prompt: System prompt
            temperature: Temperature setting
            **kwargs: Additional parameters
        """
        # Only cache low-temperature responses
        if temperature > 0.3:
            return

        key = self._create_key(prompt, system_prompt, temperature, **kwargs)
        self._cache.set(key, response)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


def cached(
    cache: LRUCache,
    key_prefix: str = "",
    ttl: float | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for caching function results.

    Args:
        cache: LRUCache instance
        key_prefix: Prefix for cache keys
        ttl: Time-to-live for cached values

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key
            key_parts = [key_prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = ":".join(key_parts)

            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value  # type: ignore[no-any-return]

            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def async_cached(
    cache: LRUCache,
    key_prefix: str = "",
    ttl: float | None = None,
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator for caching async function results.

    Args:
        cache: LRUCache instance
        key_prefix: Prefix for cache keys
        ttl: Time-to-live for cached values

    Returns:
        Decorated async function
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key
            key_parts = [key_prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = ":".join(key_parts)

            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value  # type: ignore[no-any-return]

            # Compute and cache
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


# Global cache instances
_response_cache = LLMResponseCache()
_general_cache = LRUCache(max_size=2000, default_ttl=1800)


def get_response_cache() -> LLMResponseCache:
    """Get global LLM response cache."""
    return _response_cache


def get_general_cache() -> LRUCache:
    """Get global general-purpose cache."""
    return _general_cache
