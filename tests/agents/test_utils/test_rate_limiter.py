#!/usr/bin/env python3
"""Tests for API rate limiter."""

import asyncio
import time
import pytest

from src.utils.rate_limiter import (
    APILimiter,
    RateLimitResult,
    get_api_limiter,
    rate_limit,
)


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self) -> None:
        """Test allowed result."""
        result = RateLimitResult(
            allowed=True,
            remaining=59,
            reset_time=time.time() + 60,
        )
        assert result.allowed is True
        assert result.remaining == 59
        assert result.retry_after is None

    def test_denied_result(self) -> None:
        """Test denied result."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_time=time.time() + 60,
            retry_after=30.5,
        )
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30.5


class TestAPILimiter:
    """Tests for APILimiter."""

    @pytest.fixture
    def limiter(self) -> APILimiter:
        """Create a rate limiter with default settings."""
        # Use fresh instance for each test to avoid state pollution
        return APILimiter(requests_per_minute=60, requests_per_hour=1000)

    @pytest.fixture
    def strict_limiter(self) -> APILimiter:
        """Create a rate limiter with strict settings for testing."""
        return APILimiter(requests_per_minute=5, requests_per_hour=10)

    @pytest.fixture
    def fresh_limiter(self) -> APILimiter:
        """Create a fresh rate limiter for tests that need clean state."""
        return APILimiter(requests_per_minute=60, requests_per_hour=1000)

    def test_init_default(self) -> None:
        """Test default initialization."""
        limiter = APILimiter()
        assert limiter.requests_per_minute == 60
        assert limiter.requests_per_hour == 0  # No hour limit by default

    def test_init_custom(self) -> None:
        """Test custom initialization."""
        limiter = APILimiter(requests_per_minute=30, requests_per_hour=500)
        assert limiter.requests_per_minute == 30
        assert limiter.requests_per_hour == 500

    def test_is_allowed_under_limit(self, fresh_limiter: APILimiter) -> None:
        """Test requests under limit are allowed."""
        client_id = "test_client_1"
        result = fresh_limiter.is_allowed(client_id)

        assert result.allowed is True
        assert result.remaining >= 0  # Should have remaining quota
        assert result.retry_after is None

    def test_is_allowed_exceeds_minute_limit(self, strict_limiter: APILimiter) -> None:
        """Test requests exceeding minute limit are denied."""
        client_id = "test_client_2"

        # Make 5 requests (reach limit)
        for i in range(5):
            result = strict_limiter.is_allowed(client_id)
            assert result.allowed is True

        # 6th request should be denied
        result = strict_limiter.is_allowed(client_id)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
        assert 0 < result.retry_after <= 60

    def test_is_allowed_exceeds_hour_limit(self, strict_limiter: APILimiter) -> None:
        """Test requests exceeding hour limit are denied."""
        client_id = "test_client_3"

        # Make 10 requests (reach hour limit)
        for i in range(10):
            result = strict_limiter.is_allowed(client_id)
            # First 5 should be allowed (minute limit), then denied
            # But we're testing hour limit, so use different client per minute

        # Create new client to test hour limit specifically
        hour_limiter = APILimiter(requests_per_minute=100, requests_per_hour=3)
        client_id = "test_client_hour"

        for i in range(3):
            result = hour_limiter.is_allowed(client_id)
            assert result.allowed is True

        # 4th request should be denied due to hour limit
        result = hour_limiter.is_allowed(client_id)
        assert result.allowed is False
        assert result.retry_after is not None
        assert 0 < result.retry_after <= 3600

    def test_is_allowed_multiple_clients(self, fresh_limiter: APILimiter) -> None:
        """Test multiple clients are tracked separately."""
        client1 = "client_1"
        client2 = "client_2"

        # Make requests for client1
        result1 = fresh_limiter.is_allowed(client1)
        assert result1.allowed is True
        remaining1 = result1.remaining

        # Make requests for client2
        result2 = fresh_limiter.is_allowed(client2)
        assert result2.allowed is True
        assert result2.remaining == remaining1  # Same quota for both clients

    def test_get_client_stats(self, limiter: APILimiter) -> None:
        """Test getting client statistics."""
        client_id = "stats_client"

        # Make some requests
        limiter.is_allowed(client_id)
        limiter.is_allowed(client_id)
        limiter.is_allowed(client_id)

        stats = limiter.get_client_stats(client_id)

        assert stats["client_id"] == client_id
        assert stats["requests_last_minute"] == 3
        assert stats["requests_last_hour"] == 3
        assert stats["minute_limit"] == 60
        assert stats["hour_limit"] == 1000
        assert stats["minute_remaining"] == 57
        assert stats["hour_remaining"] == 997

    def test_get_client_stats_unknown_client(self, limiter: APILimiter) -> None:
        """Test stats for unknown client."""
        stats = limiter.get_client_stats("unknown_client")

        assert stats["requests_last_minute"] == 0
        assert stats["requests_last_hour"] == 0
        assert stats["minute_remaining"] == 60
        assert stats["hour_remaining"] == 1000

    def test_reset_client(self, limiter: APILimiter) -> None:
        """Test resetting a specific client."""
        client_id = "reset_client"

        # Make some requests
        limiter.is_allowed(client_id)
        limiter.is_allowed(client_id)

        # Reset
        limiter.reset_client(client_id)

        # Should be back to full quota
        stats = limiter.get_client_stats(client_id)
        assert stats["requests_last_minute"] == 0
        assert stats["requests_last_hour"] == 0

    def test_reset_all(self, limiter: APILimiter) -> None:
        """Test resetting all clients."""
        # Make requests for multiple clients
        limiter.is_allowed("client_a")
        limiter.is_allowed("client_b")
        limiter.is_allowed("client_c")

        # Reset all
        limiter.reset_all()

        # All should be reset
        assert limiter.get_client_stats("client_a")["requests_last_minute"] == 0
        assert limiter.get_client_stats("client_b")["requests_last_minute"] == 0
        assert limiter.get_client_stats("client_c")["requests_last_minute"] == 0

    def test_thread_safety(self, limiter: APILimiter) -> None:
        """Test thread safety with concurrent requests."""
        client_id = "concurrent_client"
        results: list[RateLimitResult] = []

        def make_request() -> None:
            result = limiter.is_allowed(client_id)
            results.append(result)

        # Create multiple threads
        import threading

        threads = [threading.Thread(target=make_request) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have 10 results, all allowed (under limit of 60)
        assert len(results) == 10
        assert all(r.allowed for r in results)


class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    def test_rate_limit_decorator_allows_under_limit(self) -> None:
        """Test decorator allows requests under limit."""
        limiter = APILimiter(requests_per_minute=5)

        @limiter.rate_limit(requests_per_minute=5)
        async def test_endpoint(client_id: str = "test") -> str:
            return "success"

        # Should work under limit
        import asyncio

        async def run_test() -> str:
            return await test_endpoint(client_id="decorator_test_1")

        result = asyncio.run(run_test())
        assert result == "success"

    def test_rate_limit_decorator_denies_over_limit(self) -> None:
        """Test decorator denies requests over limit."""
        limiter = APILimiter(requests_per_minute=2)
        call_count = [0]  # Use list to allow modification in nested function

        @limiter.rate_limit(requests_per_minute=2)
        async def test_endpoint(client_id: str = "test") -> str:
            call_count[0] += 1
            return "success"

        import asyncio
        from fastapi import HTTPException

        async def run_test() -> tuple[int, bool]:
            success_count = 0
            denied = False

            # Make 3 requests
            for i in range(3):
                try:
                    await test_endpoint(client_id="decorator_test_2")
                    success_count += 1
                except HTTPException as e:
                    if i == 2:  # Third should fail
                        denied = True
                        assert e.status_code == 429

            return (success_count, denied)

        success_count, denied = asyncio.run(run_test())
        assert success_count == 2  # First two succeed
        assert denied is True  # Third denied


class TestGetAPILimiter:
    """Tests for get_api_limiter singleton."""

    def test_get_api_limiter_singleton(self) -> None:
        """Test that get_api_limiter returns same instance."""
        limiter1 = get_api_limiter(requests_per_minute=60, requests_per_hour=1000)
        limiter2 = get_api_limiter(requests_per_minute=60, requests_per_hour=1000)

        # Should be same instance
        assert limiter1 is limiter2

    def test_get_api_limiter_different_params_ignored(self) -> None:
        """Test that subsequent calls ignore different params."""
        limiter1 = get_api_limiter(requests_per_minute=60, requests_per_hour=1000)
        # Second call with different params should still return same instance
        limiter2 = get_api_limiter(requests_per_minute=30, requests_per_hour=500)

        assert limiter1 is limiter2
        assert limiter1.requests_per_minute == 60  # Original params preserved


class TestRateLimitFunction:
    """Tests for rate_limit convenience function."""

    def test_rate_limit_function(self) -> None:
        """Test rate_limit function creates decorator."""
        decorator = rate_limit(requests_per_minute=10, requests_per_hour=100)

        assert callable(decorator)

        @decorator
        async def test_endpoint(client_id: str = "test") -> str:
            return "success"

        import asyncio

        async def run_test() -> str:
            return await test_endpoint(client_id="func_test")

        result = asyncio.run(run_test())
        assert result == "success"


class TestSlidingWindow:
    """Tests for sliding window behavior."""

    def test_old_requests_expire(self) -> None:
        """Test that old requests are cleaned up."""
        limiter = APILimiter(requests_per_minute=5)
        client_id = "expire_test"

        # Make requests
        for _ in range(3):
            limiter.is_allowed(client_id)

        # Manually age the requests by modifying internal state (2 minutes ago)
        old_time = time.time() - 120
        limiter.requests_per_minute_data[client_id] = [old_time]

        # New request should be allowed (old ones expired - older than 1 minute)
        result = limiter.is_allowed(client_id)
        assert result.allowed is True
        # After cleanup, old requests should be removed, leaving most of quota
        assert result.remaining >= 3  # Should have most of quota back

    def test_hourly_limit_independent(self) -> None:
        """Test hourly limit is independent of minute limit."""
        limiter = APILimiter(requests_per_minute=100, requests_per_hour=3)
        client_id = "hourly_test"

        # Make 3 requests (hit hourly limit)
        for _ in range(3):
            result = limiter.is_allowed(client_id)
            assert result.allowed is True

        # 4th request should be denied due to hourly limit
        result = limiter.is_allowed(client_id)
        assert result.allowed is False

        # Stats should show hourly limit hit
        stats = limiter.get_client_stats(client_id)
        assert stats["requests_last_hour"] == 3
        assert stats["hour_remaining"] == 0
