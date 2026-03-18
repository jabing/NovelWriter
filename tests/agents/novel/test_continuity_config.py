# tests/agents/novel/test_continuity_config.py
"""Tests for continuity configuration system."""

import logging

import pytest

from src.novel_agent.novel.continuity_config import (
    ContinuityConfig,
    ContinuityStrictness,
)


class TestContinuityStrictness:
    """Test ContinuityStrictness enum."""

    def test_off_mode(self) -> None:
        """Test OFF mode value."""
        assert ContinuityStrictness.OFF == "off"
        assert ContinuityStrictness.OFF.value == "off"

    def test_warning_mode(self) -> None:
        """Test WARNING mode value."""
        assert ContinuityStrictness.WARNING == "warning"
        assert ContinuityStrictness.WARNING.value == "warning"

    def test_strict_mode(self) -> None:
        """Test STRICT mode value."""
        assert ContinuityStrictness.STRICT == "strict"
        assert ContinuityStrictness.STRICT.value == "strict"


class TestContinuityConfig:
    """Test ContinuityConfig class."""

    def test_default_is_strict(self) -> None:
        """Test that default strictness is STRICT."""
        config = ContinuityConfig()
        assert config.strictness == ContinuityStrictness.STRICT

    def test_explicit_strict_mode(self) -> None:
        """Test explicit STRICT mode."""
        config = ContinuityConfig(strictness=ContinuityStrictness.STRICT)
        assert config.strictness == ContinuityStrictness.STRICT

    def test_warning_mode(self) -> None:
        """Test WARNING mode."""
        config = ContinuityConfig(strictness=ContinuityStrictness.WARNING)
        assert config.strictness == ContinuityStrictness.WARNING

    def test_off_mode(self) -> None:
        """Test OFF mode."""
        config = ContinuityConfig(strictness=ContinuityStrictness.OFF)
        assert config.strictness == ContinuityStrictness.OFF

    def test_default_max_retries(self) -> None:
        """Test default max_retries is 3."""
        config = ContinuityConfig()
        assert config.max_retries == 3

    def test_custom_max_retries(self) -> None:
        """Test custom max_retries."""
        config = ContinuityConfig(max_retries=5)
        assert config.max_retries == 5

    def test_default_min_chapter_words(self) -> None:
        """Test default min_chapter_words is 500."""
        config = ContinuityConfig()
        assert config.min_chapter_words == 500

    def test_custom_min_chapter_words(self) -> None:
        """Test custom min_chapter_words."""
        config = ContinuityConfig(min_chapter_words=1000)
        assert config.min_chapter_words == 1000

    def test_default_enable_character_id(self) -> None:
        """Test default enable_character_id is False."""
        config = ContinuityConfig()
        assert config.enable_character_id is False

    def test_custom_enable_character_id(self) -> None:
        """Test custom enable_character_id."""
        config = ContinuityConfig(enable_character_id=True)
        assert config.enable_character_id is True

    def test_off_mode_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that OFF mode logs a warning."""
        with caplog.at_level(logging.WARNING):
            config = ContinuityConfig(strictness=ContinuityStrictness.OFF)

        # Check that warning was logged
        assert any("WARNING" in record.levelname for record in caplog.records)
        assert any("DISABLED" in record.message.upper() for record in caplog.records)

    def test_strict_mode_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that STRICT mode does not log a warning."""
        with caplog.at_level(logging.WARNING):
            config = ContinuityConfig(strictness=ContinuityStrictness.STRICT)

        # No warning should be logged for STRICT mode
        assert not any("DISABLED" in record.message.upper() for record in caplog.records)

    def test_with_minimal_parameters(self) -> None:
        """Test config with only strictness specified."""
        config = ContinuityConfig(strictness=ContinuityStrictness.WARNING)

        assert config.strictness == ContinuityStrictness.WARNING
        assert config.max_retries == 3  # default
        assert config.min_chapter_words == 500  # default
        assert config.enable_character_id is False  # default
