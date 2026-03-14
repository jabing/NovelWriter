"""Tests for token budget management."""

import pytest

from src.utils.token_budget import (
    TokenBudgetConfig,
    TokenBudgetManager,
    TokenCount,
    count_tokens,
    get_token_budget_manager,
)


class TestTokenBudgetConfig:
    """Tests for TokenBudgetConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TokenBudgetConfig()
        assert config.max_context_tokens == 16000
        assert config.system_prompt_reserve == 500
        assert config.response_reserve == 4096
        assert config.safety_margin == 100

    def test_available_context_tokens(self) -> None:
        """Test available context tokens calculation."""
        config = TokenBudgetConfig()
        # 16000 - 500 - 4096 - 100 = 11304
        assert config.available_context_tokens == 11304

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = TokenBudgetConfig(
            max_context_tokens=8000,
            system_prompt_reserve=200,
            response_reserve=2000,
            safety_margin=50,
        )
        assert config.available_context_tokens == 5750


class TestTokenCount:
    """Tests for TokenCount dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        count = TokenCount(total=100)
        assert count.total == 100
        assert count.by_section == {}
        assert count.truncated is False
        assert count.truncated_sections == []

    def test_with_sections(self) -> None:
        """Test with section breakdown."""
        count = TokenCount(total=100, by_section={"key_events": 50, "characters": 30, "world": 20})
        assert count.total == 100
        assert count.by_section["key_events"] == 50


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a manager instance."""
        return TokenBudgetManager()

    def test_count_tokens_empty_string(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in empty string."""
        assert manager.count_tokens("") == 0

    def test_count_tokens_simple_text(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in simple text."""
        # "Hello, world!" should be ~4 tokens
        count = manager.count_tokens("Hello, world!")
        assert 2 <= count <= 6  # Allow some variance for different tokenizers

    def test_count_tokens_longer_text(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in longer text."""
        text = "The quick brown fox jumps over the lazy dog. " * 10
        count = manager.count_tokens(text)
        # Should be proportional to length
        assert count > 50

    def test_count_tokens_in_dict_strings(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in dictionary with strings."""
        data = {"key_events": ["Event 1", "Event 2", "Event 3"], "location": "Crystal Palace"}
        result = manager.count_tokens_in_dict(data)
        assert result.total > 0
        assert "key_events" in result.by_section
        assert "location" in result.by_section

    def test_find_sentence_boundary_period(self, manager: TokenBudgetManager) -> None:
        """Test finding sentence boundary at period."""
        text = "First sentence. Second sentence. Third sentence."
        # Find boundary before "Third"
        boundary = manager.find_sentence_boundary(text, 30)
        # Should find the period after "Second sentence"
        assert boundary > 15
        assert boundary < 40

    def test_find_sentence_boundary_no_match(self, manager: TokenBudgetManager) -> None:
        """Test finding boundary when no sentence end exists."""
        text = "no punctuation here just words"
        boundary = manager.find_sentence_boundary(text, 15)
        # Should fall back to space or original position
        assert boundary >= 0

    def test_truncate_to_budget_no_truncation_needed(self, manager: TokenBudgetManager) -> None:
        """Test truncation when text fits budget."""
        text = "Short text"
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=100)
        assert result == text
        assert was_truncated is False

    def test_truncate_to_budget_with_truncation(self, manager: TokenBudgetManager) -> None:
        """Test truncation when text exceeds budget."""
        text = "This is a long sentence. This is another. And a third one."
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=5)
        assert was_truncated is True
        assert "..." in result
        assert len(result) < len(text)

    def test_truncate_to_budget_preserve_end(self, manager: TokenBudgetManager) -> None:
        """Test truncation preserving end of text."""
        text = "Start of text. Middle part. End of text that matters."
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=5, preserve_end=True)
        assert was_truncated is True
        assert "..." in result
        # Should contain end of text
        assert "matters" in result

    def test_truncate_list_to_budget_no_truncation(self, manager: TokenBudgetManager) -> None:
        """Test list truncation when items fit."""
        items = ["Item 1", "Item 2", "Item 3"]
        result, was_truncated = manager.truncate_list_to_budget(items, max_tokens=100)
        assert result == items
        assert was_truncated is False

    def test_truncate_list_to_budget_with_truncation(self, manager: TokenBudgetManager) -> None:
        """Test list truncation when items exceed budget."""
        items = [f"Event number {i} with a longer description" for i in range(20)]
        result, was_truncated = manager.truncate_list_to_budget(items, max_tokens=20)
        assert was_truncated is True
        assert len(result) < len(items)

    def test_truncate_list_preserve_recent(self, manager: TokenBudgetManager) -> None:
        """Test list truncation preserves recent items."""
        items = ["Old event 1", "Old event 2", "Recent event 3", "Recent event 4"]
        result, _ = manager.truncate_list_to_budget(items, max_tokens=10, preserve_recent=True)
        # Should keep recent items
        assert "Recent event 4" in result

    def test_enforce_budget_no_truncation_needed(self, manager: TokenBudgetManager) -> None:
        """Test budget enforcement when context fits."""
        context = {"key_events": ["Event 1"], "location": "Palace"}
        result, count = manager.enforce_budget(context, max_tokens=1000)
        assert result == context
        assert count.truncated is False

    def test_enforce_budget_with_truncation(self, manager: TokenBudgetManager) -> None:
        """Test budget enforcement with truncation."""
        context = {
            "key_events": [f"Event number {i} with more details" for i in range(50)],
            "location": "The Grand Crystal Palace of the Ancient Kingdom",
            "world_state": "A" * 2000,  # ~500 tokens
        }
        result, count = manager.enforce_budget(context, max_tokens=10)  # Very small budget
        assert count.truncated is True
        assert len(count.truncated_sections) > 0
        # Result should be smaller than original
        assert len(result.get("key_events", [])) < 50
        """Test budget enforcement with truncation."""
        context = {
            "key_events": [f"Event {i}" for i in range(100)],
            "location": "Palace",
            "world_state": "A" * 1000,
        }
        result, count = manager.enforce_budget(context, max_tokens=50)
        assert count.truncated is True
        assert len(count.truncated_sections) > 0

    def test_enforce_budget_respects_priority(self, manager: TokenBudgetManager) -> None:
        """Test budget enforcement respects truncation priority."""
        context = {
            "key_events": [f"Event {i}" for i in range(50)],
            "important": "This should not be truncated",
        }
        result, count = manager.enforce_budget(
            context,
            max_tokens=20,
            truncation_priority=["key_events"],  # Only truncate key_events
        )
        # important section should remain
        assert "important" in result


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_token_budget_manager_returns_singleton(self) -> None:
        """Test that get_token_budget_manager returns same instance."""
        manager1 = get_token_budget_manager()
        manager2 = get_token_budget_manager()
        assert manager1 is manager2

    def test_count_tokens_global(self) -> None:
        """Test global count_tokens function."""
        count = count_tokens("Hello, world!")
        assert count > 0
