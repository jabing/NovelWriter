# tests/test_utils/test_cache.py
"""Tests for caching utilities."""

import asyncio
import time

import pytest

from src.novel_agent.utils.cache import (
    CacheEntry,
    LLMResponseCache,
    LRUCache,
    async_cached,
    cached,
    get_general_cache,
    get_response_cache,
)


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_cache_entry_creation(self) -> None:
        """Test creating a cache entry."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            ttl=60,
        )

        assert entry.value == "test"
        assert entry.hits == 0
        assert entry.is_expired() is False

    def test_cache_entry_expiration(self) -> None:
        """Test cache entry expiration."""
        # Already expired
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 100,
            ttl=50,
        )

        assert entry.is_expired() is True

    def test_cache_entry_no_expiration(self) -> None:
        """Test cache entry with no expiration."""
        entry = CacheEntry(
            value="test",
            created_at=0,
            ttl=0,  # Never expires
        )

        assert entry.is_expired() is False


class TestLRUCache:
    """Tests for LRUCache."""

    def test_cache_initialization(self) -> None:
        """Test cache initializes correctly."""
        cache = LRUCache(max_size=100, default_ttl=60)

        assert cache.max_size == 100
        assert cache.default_ttl == 60

    def test_cache_set_and_get(self) -> None:
        """Test setting and getting values."""
        cache = LRUCache()

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_cache_get_nonexistent(self) -> None:
        """Test getting nonexistent key."""
        cache = LRUCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_cache_delete(self) -> None:
        """Test deleting cache entry."""
        cache = LRUCache()

        cache.set("key1", "value1")
        result = cache.delete("key1")

        assert result is True
        assert cache.get("key1") is None

    def test_cache_delete_nonexistent(self) -> None:
        """Test deleting nonexistent key."""
        cache = LRUCache()

        result = cache.delete("nonexistent")

        assert result is False

    def test_cache_clear(self) -> None:
        """Test clearing cache."""
        cache = LRUCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_max_size_eviction(self) -> None:
        """Test LRU eviction when max size reached."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_cache_lru_order(self) -> None:
        """Test LRU ordering."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new item, should evict key2 (oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = LRUCache()

        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_cache_cleanup_expired(self) -> None:
        """Test cleanup of expired entries."""
        cache = LRUCache(default_ttl=0.1)  # 100ms TTL

        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=0)  # Never expires

        time.sleep(0.15)  # Wait for expiration

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestLLMResponseCache:
    """Tests for LLMResponseCache."""

    def test_llm_cache_initialization(self) -> None:
        """Test LLM cache initializes."""
        cache = LLMResponseCache()
        assert cache is not None

    def test_llm_cache_set_and_get(self) -> None:
        """Test setting and getting LLM responses."""
        cache = LLMResponseCache()

        cache.set_response(
            prompt="Test prompt",
            response="Test response",
            temperature=0.1,
        )

        result = cache.get_response(
            prompt="Test prompt",
            temperature=0.1,
        )

        assert result == "Test response"

    def test_llm_cache_skips_high_temperature(self) -> None:
        """Test that high temperature requests are not cached."""
        cache = LLMResponseCache()

        cache.set_response(
            prompt="Test prompt",
            response="Test response",
            temperature=0.8,  # High temperature
        )

        result = cache.get_response(
            prompt="Test prompt",
            temperature=0.8,
        )

        assert result is None

    def test_llm_cache_different_prompts(self) -> None:
        """Test that different prompts have different cache entries."""
        cache = LLMResponseCache()

        cache.set_response(prompt="Prompt 1", response="Response 1", temperature=0.1)
        cache.set_response(prompt="Prompt 2", response="Response 2", temperature=0.1)

        assert cache.get_response(prompt="Prompt 1", temperature=0.1) == "Response 1"
        assert cache.get_response(prompt="Prompt 2", temperature=0.1) == "Response 2"

    def test_llm_cache_stats(self) -> None:
        """Test LLM cache statistics."""
        cache = LLMResponseCache()

        cache.set_response(prompt="Test", response="Response", temperature=0.1)
        cache.get_response(prompt="Test", temperature=0.1)

        stats = cache.get_stats()

        assert stats["hits"] == 1


class TestCachedDecorator:
    """Tests for cached decorator."""

    def test_cached_decorator(self) -> None:
        """Test cached decorator."""
        cache = LRUCache()
        call_count = [0]

        @cached(cache)
        def expensive_func(x: int) -> int:
            call_count[0] += 1
            return x * 2

        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call (cached)
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not incremented

        # Different argument
        result3 = expensive_func(10)
        assert result3 == 20
        assert call_count[0] == 2


class TestAsyncCachedDecorator:
    """Tests for async_cached decorator."""

    @pytest.mark.asyncio
    async def test_async_cached_decorator(self) -> None:
        """Test async cached decorator."""
        cache = LRUCache()
        call_count = [0]

        @async_cached(cache)
        async def async_expensive_func(x: int) -> int:
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return x * 2

        # First call
        result1 = await async_expensive_func(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call (cached)
        result2 = await async_expensive_func(5)
        assert result2 == 10
        assert call_count[0] == 1


class TestGlobalCaches:
    """Tests for global cache instances."""

    def test_get_response_cache(self) -> None:
        """Test getting global response cache."""
        cache = get_response_cache()
        assert isinstance(cache, LLMResponseCache)

    def test_get_general_cache(self) -> None:
        """Test getting global general cache."""
        cache = get_general_cache()
        assert isinstance(cache, LRUCache)
