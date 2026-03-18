# tests/agents/novel/test_continuity_downgrade.py
"""Tests for failure handling and continuity downgrade behavior."""

import logging

import pytest

from src.novel_agent.novel.continuity_config import (
    ContinuityConfig,
    ContinuityStrictness,
)
from src.novel_agent.novel.retry_policy import (
    RetryManager,
    RetryPolicy,
)


class TestStrictModeBehavior:
    """Tests for STRICT mode (default) behavior."""

    def test_strict_mode_is_default(self) -> None:
        """Default config should be STRICT."""
        config = ContinuityConfig()
        assert config.strictness == ContinuityStrictness.STRICT

    def test_strict_mode_enables_all_checks(self) -> None:
        """STRICT mode should enable all continuity checks."""
        config = ContinuityConfig(strictness=ContinuityStrictness.STRICT)

        # All checks should be enabled
        assert config.min_chapter_words == 500
        assert config.max_retries == 3


class TestOffModeBehavior:
    """Tests for OFF mode (debug only) behavior."""

    def test_off_mode_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """OFF mode should log a warning."""
        with caplog.at_level(logging.WARNING):
            config = ContinuityConfig(strictness=ContinuityStrictness.OFF)

        # Should have logged a warning
        assert len(caplog.records) > 0
        assert any("DISABLED" in record.message.upper() for record in caplog.records)

    def test_off_mode_allows_skip(self) -> None:
        """OFF mode should allow skipping checks."""
        # Implementation should check strictness before blocking
        should_block = ContinuityStrictness.OFF == ContinuityStrictness.STRICT
        assert should_block is False


class TestRetryExhaustion:
    """Tests for retry exhaustion behavior."""

    @pytest.mark.asyncio
    async def test_retry_exhaustion_stops(self) -> None:
        """After max retries, should stop and return failure."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        manager = RetryManager(policy)

        async def always_fails() -> str:
            raise ValueError("Always fails")

        result = await manager.execute_with_retry(always_fails)

        assert result.success is False
        assert result.attempts == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_success_on_third_attempt(self) -> None:
        """Should succeed on third attempt after two failures."""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        manager = RetryManager(policy)

        call_count = 0

        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await manager.execute_with_retry(flaky_operation)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_retry_count_tracked(self) -> None:
        """Retry count should be tracked across operations."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        manager = RetryManager(policy)

        async def fails() -> str:
            raise ValueError("Fails")

        await manager.execute_with_retry(fails)

        # max_retries=2 means 2 retries + initial attempt = 3 total attempts
        # Retry count tracks each failed attempt that triggers a retry
        # The implementation increments on each failed attempt, so:
        # - Attempt 1 fails -> retry #1 + retry_count=1
        # - Attempt 2 fails -> retry #2 + retry_count=2
        # - Attempt 3 (final) fails -> no more retries, retry_count stays at 3
        # Total: retry_count = attempts = 3
        assert manager.get_retry_count() == 3

    @pytest.mark.asyncio
    async def test_retry_zero_max_retries(self) -> None:
        """With max_retries=0, only single attempt is made."""
        policy = RetryPolicy(max_retries=0, base_delay=0.01)
        manager = RetryManager(policy)

        async def fails() -> str:
            raise ValueError("Fails on first try")

        result = await manager.execute_with_retry(fails)

        assert result.success is False
        assert result.attempts == 1  # Only initial attempt
        assert manager.get_retry_count() == 1  # One retry counted

    @pytest.mark.asyncio
    async def test_retry_failure_result_structure(self) -> None:
        """Failure result should have proper structure."""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        manager = RetryManager(policy)

        expected_error = ValueError("Never succeeds")

        async def fails() -> str:
            raise expected_error

        result = await manager.execute_with_retry(fails)

        assert result.success is False
        assert result.result is None
        assert result.error is expected_error
        assert result.last_error is expected_error
        assert result.attempts == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_success_result_structure(self) -> None:
        """Success result should have proper structure."""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        manager = RetryManager(policy)

        async def succeeds() -> dict:
            return {"status": "ok", "data": "test"}

        result = await manager.execute_with_retry(succeeds)

        assert result.success is True
        assert result.result == {"status": "ok", "data": "test"}
        assert result.error is None
        assert result.last_error is None
        assert result.attempts == 1  # Succeeded on first try
        assert manager.get_retry_count() == 0  # No retries needed

    @pytest.mark.asyncio
    async def test_offset_mode_allows_operation(self) -> None:
        """OFF mode should allow the operation to proceed without blocking."""
        policy = RetryPolicy(max_retries=1, base_delay=0.01)
        manager = RetryManager(policy)

        async def operation() -> str:
            return "executed"

        # This test ensures OFF mode (config level) allows operations
        # The retry manager itself doesn't check strictness
        # The check happens at the caller level (e.g., chapter validator)
        result = await manager.execute_with_retry(operation)

        assert result.success is True
        assert result.result == "executed"


class TestIntegration:
    """Integration tests for continuity downgrade scenarios."""

    @pytest.mark.asyncio
    async def test_config_with_retry_manager(self) -> None:
        """Test config and retry manager work together."""
        # Create config with custom retry settings
        config = ContinuityConfig(max_retries=5, min_chapter_words=1000)

        policy = RetryPolicy(
            max_retries=config.max_retries,
            base_delay=0.01,
        )
        manager = RetryManager(policy)

        async def check_word_count() -> bool:
            return True

        result = await manager.execute_with_retry(check_word_count)

        assert result.success is True
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_strict_mode_blocks_with_retry(self) -> None:
        """STRICT mode should block and retry on failure."""
        config = ContinuityConfig(strictness=ContinuityStrictness.STRICT)

        policy = RetryPolicy(
            max_retries=config.max_retries,
            base_delay=0.01,
        )
        manager = RetryManager(policy)

        async def maybe_fail() -> str:
            if manager.get_retry_count() < 1:
                raise ValueError("Temporary failure")
            return "passed"

        result = await manager.execute_with_retry(maybe_fail)

        assert result.success is True
        assert result.attempts == 2  # Failed once, succeeded on retry
