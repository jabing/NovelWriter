# tests/agents/novel/test_retry_policy.py
"""Tests for RetryPolicy and RetryManager."""

import pytest
from unittest.mock import AsyncMock

from src.novel_agent.novel.retry_policy import RetryPolicy, RetryManager, RetryResult


class TestRetryPolicy:
    """Tests for RetryPolicy dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        policy = RetryPolicy()

        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.exponential_base == 2.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            exponential_base=3.0,
        )

        assert policy.max_retries == 5
        assert policy.base_delay == 2.0
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 3.0

    def test_calculate_delay_basic(self) -> None:
        """Test basic exponential backoff calculation."""
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0, exponential_base=2.0)

        # Formula: base_delay * (exponential_base ** attempt)
        assert policy.calculate_delay(0) == 1.0  # 1.0 * 2^0 = 1.0
        assert policy.calculate_delay(1) == 2.0  # 1.0 * 2^1 = 2.0
        assert policy.calculate_delay(2) == 4.0  # 1.0 * 2^2 = 4.0
        assert policy.calculate_delay(3) == 8.0  # 1.0 * 2^3 = 8.0

    def test_calculate_delay_capped_at_max(self) -> None:
        """Test that delay is capped at max_delay."""
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0, exponential_base=2.0)

        # At attempt 5: 1.0 * 2^5 = 32.0, but capped at 30.0
        assert policy.calculate_delay(5) == 30.0

        # At attempt 10: 1.0 * 2^10 = 1024.0, but capped at 30.0
        assert policy.calculate_delay(10) == 30.0

    def test_calculate_delay_different_base(self) -> None:
        """Test with different exponential base."""
        policy = RetryPolicy(base_delay=2.0, max_delay=100.0, exponential_base=3.0)

        # Formula: 2.0 * (3.0 ** attempt)
        assert policy.calculate_delay(0) == 2.0  # 2.0 * 3^0 = 2.0
        assert policy.calculate_delay(1) == 6.0  # 2.0 * 3^1 = 6.0
        assert policy.calculate_delay(2) == 18.0  # 2.0 * 3^2 = 18.0
        assert policy.calculate_delay(3) == 54.0  # 2.0 * 3^3 = 54.0

    def test_calculate_delay_zero_base_delay(self) -> None:
        """Test with zero base delay (immediate retries)."""
        policy = RetryPolicy(base_delay=0.0, max_delay=30.0, exponential_base=2.0)

        # All delays should be 0 when base_delay is 0
        assert policy.calculate_delay(0) == 0.0
        assert policy.calculate_delay(5) == 0.0
        assert policy.calculate_delay(10) == 0.0


class TestRetryResult:
    """Tests for RetryResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful retry result."""
        result = RetryResult(
            success=True,
            result="operation output",
            attempts=1,
        )

        assert result.success is True
        assert result.result == "operation output"
        assert result.error is None
        assert result.attempts == 1
        assert result.last_error is None

    def test_failure_result(self) -> None:
        """Test failed retry result."""
        error = ValueError("test error")
        result = RetryResult(
            success=False,
            error=error,
            attempts=3,
            last_error=error,
        )

        assert result.success is False
        assert result.result is None
        assert result.error is error
        assert result.attempts == 3
        assert result.last_error is error


class TestRetryManager:
    """Tests for RetryManager class."""

    def test_default_policy(self) -> None:
        """Test default policy initialization."""
        manager = RetryManager()

        assert manager.policy.max_retries == 3
        assert manager.get_retry_count() == 0

    def test_custom_policy(self) -> None:
        """Test custom policy initialization."""
        policy = RetryPolicy(max_retries=5, base_delay=0.5)
        manager = RetryManager(policy)

        assert manager.policy.max_retries == 5
        assert manager.policy.base_delay == 0.5

    @pytest.mark.asyncio
    async def test_retry_success_first_try(self) -> None:
        """Test successful operation on first attempt."""
        policy = RetryPolicy(max_retries=3)
        manager = RetryManager(policy)
        operation = AsyncMock(return_value="success")

        result = await manager.execute_with_retry(operation)

        assert result.success is True
        assert result.attempts == 1
        assert result.result == "success"
        assert result.error is None
        assert manager.get_retry_count() == 0

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self) -> None:
        """Test successful operation after some failures."""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)  # Fast for testing
        manager = RetryManager(policy)

        call_count = 0

        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await manager.execute_with_retry(flaky_operation)

        assert result.success is True
        assert result.attempts == 3
        assert result.result == "success"
        assert manager.get_retry_count() == 2  # Two retries needed

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """Test operation that exhausts all retries."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)  # Fast for testing
        manager = RetryManager(policy)

        async def always_fail() -> str:
            raise ValueError("Always fails")

        result = await manager.execute_with_retry(always_fail)

        assert result.success is False
        assert result.attempts == 3  # Initial + 2 retries = 3 attempts
        assert result.error is not None
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Always fails"
        assert manager.get_retry_count() == 3

    @pytest.mark.asyncio
    async def test_retry_with_args_and_kwargs(self) -> None:
        """Test operation with arguments."""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        manager = RetryManager(policy)

        async def operation_with_args(a: int, b: int, *, c: int) -> int:
            return a + b + c

        result = await manager.execute_with_retry(operation_with_args, 1, 2, c=3)

        assert result.success is True
        assert result.result == 6

    @pytest.mark.asyncio
    async def test_zero_retries(self) -> None:
        """Test with zero retries allowed (single attempt only)."""
        policy = RetryPolicy(max_retries=0, base_delay=0.01)
        manager = RetryManager(policy)

        call_count = 0

        async def failing_operation() -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Failed")

        result = await manager.execute_with_retry(failing_operation)

        assert result.success is False
        assert result.attempts == 1  # Only one attempt made
        assert manager.get_retry_count() == 1

    def test_reset_retry_count(self) -> None:
        """Test reset_retry_count functionality."""
        manager = RetryManager()
        manager._retry_count = 10

        assert manager.get_retry_count() == 10

        manager.reset_retry_count()

        assert manager.get_retry_count() == 0

    @pytest.mark.asyncio
    async def test_different_exception_types(self) -> None:
        """Test that different exception types are handled."""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        manager = RetryManager(policy)

        async def raise_type_error() -> str:
            raise TypeError("Wrong type")

        result = await manager.execute_with_retry(raise_type_error)

        assert result.success is False
        assert isinstance(result.error, TypeError)
        assert isinstance(result.last_error, TypeError)

    @pytest.mark.asyncio
    async def test_multiple_operations_retry_count(self) -> None:
        """Test that retry count accumulates across operations."""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        manager = RetryManager(policy)

        async def always_fail() -> str:
            raise ValueError("fail")

        # First operation - 2 attempts, 2 retries counted
        await manager.execute_with_retry(always_fail)
        assert manager.get_retry_count() == 2

        # Second operation - 2 more attempts, 2 more retries counted
        await manager.execute_with_retry(always_fail)
        assert manager.get_retry_count() == 4

        # Reset
        manager.reset_retry_count()
        assert manager.get_retry_count() == 0


class TestIntegration:
    """Integration tests for retry policy scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_api_retry_scenario(self) -> None:
        """Test a realistic API call retry scenario."""
        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,  # Fast for testing
            max_delay=30.0,
            exponential_base=2.0,
        )
        manager = RetryManager(policy)

        call_count = 0

        async def mock_api_call() -> dict:
            nonlocal call_count
            call_count += 1

            # Simulate rate limiting on first two calls
            if call_count <= 2:
                raise ConnectionError("Rate limited")

            # Success on third call
            return {"status": "ok", "data": "response"}

        result = await manager.execute_with_retry(mock_api_call)

        assert result.success is True
        assert result.result == {"status": "ok", "data": "response"}
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_delay_progression(self) -> None:
        """Test that delays follow exponential backoff."""
        import time

        policy = RetryPolicy(
            max_retries=2,
            base_delay=0.1,  # Small but measurable
            max_delay=30.0,
            exponential_base=2.0,
        )
        manager = RetryManager(policy)

        delays = []

        async def track_delays() -> str:
            delays.append(time.time())
            if len(delays) < 3:
                raise ValueError("fail")
            return "success"

        start = time.time()
        result = await manager.execute_with_retry(track_delays)
        end = time.time()

        assert result.success is True
        # Total expected delay: 0.1 + 0.2 = 0.3 seconds
        # Allow some tolerance for async overhead
        assert end - start >= 0.25  # At least the expected delay
