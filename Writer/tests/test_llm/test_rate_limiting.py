"""Tests for rate-limited LLM wrapper."""

import pytest

from src.llm.base import BaseLLM, LLMResponse
from src.llm.rate_limited import RateLimitedLLM, create_rate_limited_llm


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.call_count = 0
        self._should_fail = False
        self._fail_count = 0

    def set_fail_mode(self, should_fail: bool, fail_count: int = 1) -> None:
        """Set the mock to fail."""
        self._should_fail = should_fail
        self._fail_count = fail_count

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: any,
    ) -> LLMResponse:
        self.call_count += 1

        if self._should_fail and self._fail_count > 0:
            self._fail_count -= 1
            raise Exception("429 Too Many Requests")

        self._total_tokens_used += 100
        return LLMResponse(
            content=f"Response to: {prompt}",
            tokens_used=100,
            model=self.model,
        )

    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: any,
    ) -> LLMResponse:
        self.call_count += 1

        if self._should_fail and self._fail_count > 0:
            self._fail_count -= 1
            raise Exception("429 Too Many Requests")

        self._total_tokens_used += 150
        return LLMResponse(
            content=f"System: {system_prompt}, User: {user_prompt}",
            tokens_used=150,
            model=self.model,
        )


class TestRateLimitedLLM:
    """Tests for RateLimitedLLM class."""

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        """Create a mock LLM."""
        return MockLLM(api_key="test", model="test-model")

    @pytest.fixture
    def rate_limited_llm(self, mock_llm: MockLLM) -> RateLimitedLLM:
        """Create a rate-limited LLM."""
        return RateLimitedLLM(
            base_llm=mock_llm,
            calls_per_second=10.0,  # High rate for faster tests
            burst_size=5,
        )

    @pytest.mark.asyncio
    async def test_generate_passes_through(
        self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM
    ) -> None:
        """Test that generate passes through to base LLM."""
        response = await rate_limited_llm.generate("Hello")
        assert "Hello" in response.content
        assert mock_llm.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_with_system_passes_through(
        self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM
    ) -> None:
        """Test that generate_with_system passes through to base LLM."""
        response = await rate_limited_llm.generate_with_system("You are helpful", "Hi")
        assert "You are helpful" in response.content
        assert "Hi" in response.content
        assert mock_llm.call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limiting_delays_calls(self, mock_llm: MockLLM) -> None:
        """Test that rate limiting delays rapid calls."""
        # Use very low rate for testing
        rate_limited = RateLimitedLLM(
            base_llm=mock_llm,
            calls_per_second=2.0,
            burst_size=1,  # Only 1 burst
        )

        import time

        start = time.time()

        # Make 3 calls - should take at least 1 second due to rate limiting
        await rate_limited.generate("Call 1")
        await rate_limited.generate("Call 2")
        await rate_limited.generate("Call 3")

        elapsed = time.time() - start
        # With burst_size=1 and 3 calls at 2/sec, should take ~1 second
        assert elapsed >= 0.8  # Allow some margin

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit_error(
        self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM
    ) -> None:
        """Test that rate limit errors are retried."""
        # Set mock to fail once, then succeed
        mock_llm.set_fail_mode(True, fail_count=1)

        response = await rate_limited_llm.generate("Hello")

        # Should have retried and succeeded
        assert response is not None
        assert mock_llm.call_count == 2  # 1 fail + 1 success

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(
        self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM
    ) -> None:
        """Test that exception is raised after max retries."""
        # Set mock to always fail with rate limit error
        mock_llm.set_fail_mode(True, fail_count=10)  # More than max retries

        with pytest.raises(Exception) as exc_info:
            await rate_limited_llm.generate("Hello")

        assert "429" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_rate_limit_error_not_retried(
        self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM
    ) -> None:
        """Test that non-rate-limit errors are not retried."""

        # Mock to raise non-rate-limit error
        async def failing_generate(*args: any, **kwargs: any) -> LLMResponse:
            mock_llm.call_count += 1
            raise ValueError("Some other error")

        mock_llm.generate = failing_generate

        with pytest.raises(ValueError) as exc_info:
            await rate_limited_llm.generate("Hello")

        assert "Some other error" in str(exc_info.value)
        assert mock_llm.call_count == 1  # Only called once

    def test_stats_tracking(self, rate_limited_llm: RateLimitedLLM, mock_llm: MockLLM) -> None:
        """Test that statistics are tracked."""
        stats = rate_limited_llm.stats

        assert "total_calls" in stats
        assert "rate_limited_count" in stats
        assert "total_wait_time" in stats
        assert stats["base_llm_model"] == "test-model"

    def test_reset_stats(self, rate_limited_llm: RateLimitedLLM) -> None:
        """Test that statistics can be reset."""
        rate_limited_llm._total_calls = 10
        rate_limited_llm._rate_limited_count = 5
        rate_limited_llm._total_wait_time = 2.5

        rate_limited_llm.reset_stats()

        stats = rate_limited_llm.stats
        assert stats["total_calls"] == 0
        assert stats["rate_limited_count"] == 0
        assert stats["total_wait_time"] == 0.0


class TestRateLimitedLLMDetection:
    """Tests for rate limit error detection."""

    @pytest.fixture
    def rate_limited_llm(self) -> RateLimitedLLM:
        """Create a rate-limited LLM."""
        mock = MockLLM(api_key="test", model="test")
        return RateLimitedLLM(base_llm=mock)

    def test_detects_429_error(self, rate_limited_llm: RateLimitedLLM) -> None:
        """Test detection of 429 status code."""
        error = Exception("Error: 429 Too Many Requests")
        assert rate_limited_llm._is_rate_limit_error(error) is True

    def test_detects_rate_limit_string(self, rate_limited_llm: RateLimitedLLM) -> None:
        """Test detection of 'rate limit' string."""
        error = Exception("Rate limit exceeded")
        assert rate_limited_llm._is_rate_limit_error(error) is True

    def test_detects_throttling(self, rate_limited_llm: RateLimitedLLM) -> None:
        """Test detection of throttling."""
        error = Exception("Request was throttled")
        assert rate_limited_llm._is_rate_limit_error(error) is True

    def test_non_rate_limit_error(self, rate_limited_llm: RateLimitedLLM) -> None:
        """Test that other errors are not detected as rate limit."""
        error = ValueError("Invalid input")
        assert rate_limited_llm._is_rate_limit_error(error) is False


class TestCreateRateLimitedLLM:
    """Tests for factory function."""

    def test_factory_creates_wrapper(self) -> None:
        """Test that factory creates a RateLimitedLLM."""
        mock = MockLLM(api_key="test", model="test")
        wrapped = create_rate_limited_llm(mock, calls_per_second=5.0)

        assert isinstance(wrapped, RateLimitedLLM)
        assert wrapped._base_llm is mock

    def test_factory_uses_default_settings(self) -> None:
        """Test that factory uses default settings."""
        mock = MockLLM(api_key="test", model="test")
        wrapped = create_rate_limited_llm(mock)

        assert wrapped._rate_limiter.calls_per_second == 2.0
        assert wrapped._rate_limiter.burst_size == 5
