"""Tests for token budget management accuracy."""

import pytest

from src.utils.token_budget import (
    TokenBudgetConfig,
    TokenBudgetManager,
    TokenCount,
    count_tokens,
    get_token_budget_manager,
)


class TestTokenCountingAccuracy:
    """Test that token counting is accurate."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a token budget manager for testing."""
        return TokenBudgetManager()

    def test_empty_string_has_zero_tokens(self, manager: TokenBudgetManager) -> None:
        """Empty strings should have zero tokens."""
        assert manager.count_tokens("") == 0

    def test_simple_text_counting(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in simple text."""
        # "Hello, world!" is typically 4 tokens in cl100k_base
        count = manager.count_tokens("Hello, world!")
        assert count >= 3  # At minimum
        assert count <= 6  # At maximum

    def test_chinese_text_counting(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in Chinese text."""
        # Chinese characters typically use more tokens per character
        text = "你好世界"  # "Hello world" in Chinese
        count = manager.count_tokens(text)
        assert count >= 2  # At minimum
        assert count <= 10  # At maximum

    def test_mixed_language_counting(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in mixed language text."""
        text = "Hello 你好 World 世界"
        count = manager.count_tokens(text)
        assert count >= 4  # At minimum

    def test_long_text_approximation(self, manager: TokenBudgetManager) -> None:
        """Test that long text counting is reasonable."""
        # Generate a long text
        text = "The quick brown fox jumps over the lazy dog. " * 100
        count = manager.count_tokens(text)
        # Should be roughly proportional to length
        # Approximation: 4 chars per token
        expected_approx = len(text) // 4
        # Allow 50% variance
        assert count >= expected_approx * 0.5
        assert count <= expected_approx * 2.0


class TestTokenBudgetConfig:
    """Test TokenBudgetConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TokenBudgetConfig()
        assert config.max_context_tokens == 16000
        assert config.system_prompt_reserve == 500
        assert config.response_reserve == 4096
        assert config.safety_margin == 100

    def test_available_context_tokens(self) -> None:
        """Test calculation of available context tokens."""
        config = TokenBudgetConfig()
        available = config.available_context_tokens
        # 16000 - 500 - 4096 - 100 = 11304
        assert available == 11304

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = TokenBudgetConfig(
            max_context_tokens=32000,
            system_prompt_reserve=1000,
            response_reserve=8192,
            safety_margin=200,
        )
        assert config.max_context_tokens == 32000
        assert config.available_context_tokens == 32000 - 1000 - 8192 - 200


class TestTokenCount:
    """Test TokenCount dataclass."""

    def test_default_values(self) -> None:
        """Test default values of TokenCount."""
        count = TokenCount(total=100)
        assert count.total == 100
        assert count.by_section == {}
        assert count.truncated is False
        assert count.truncated_sections == []

    def test_with_sections(self) -> None:
        """Test TokenCount with section breakdown."""
        count = TokenCount(
            total=100,
            by_section={"a": 30, "b": 70},
            truncated=True,
            truncated_sections=["b"],
        )
        assert count.total == 100
        assert count.by_section["a"] == 30
        assert count.truncated is True
        assert "b" in count.truncated_sections


class TestCountTokensInDict:
    """Test counting tokens in dictionary structures."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a token budget manager for testing."""
        return TokenBudgetManager()

    def test_simple_dict(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in a simple dict."""
        data = {
            "key1": "Hello world",
            "key2": "Test content",
        }
        result = manager.count_tokens_in_dict(data)
        assert result.total > 0
        assert "key1" in result.by_section
        assert "key2" in result.by_section

    def test_dict_with_list(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in a dict with list values."""
        data = {
            "items": ["item1", "item2", "item3"],
        }
        result = manager.count_tokens_in_dict(data)
        assert result.total > 0
        assert "items" in result.by_section

    def test_nested_dict(self, manager: TokenBudgetManager) -> None:
        """Test counting tokens in nested dicts."""
        data = {
            "outer": {
                "inner": "content",
            },
        }
        result = manager.count_tokens_in_dict(data)
        assert result.total > 0


class TestEnforceBudget:
    """Test budget enforcement."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a token budget manager with small budget for testing."""
        config = TokenBudgetConfig(max_context_tokens=500)
        return TokenBudgetManager(config)

    def test_within_budget(self, manager: TokenBudgetManager) -> None:
        """Test that content within budget is unchanged."""
        data = {"key": "Hello world"}
        result, count = manager.enforce_budget(data, max_tokens=100)
        assert result == data
        assert count.truncated is False

    def test_truncation_happens(self, manager: TokenBudgetManager) -> None:
        """Test that truncation happens when over budget."""
        # Create content that exceeds budget
        data = {
            "key1": "x" * 1000,
            "key2": "y" * 1000,
            "key3": "z" * 1000,
        }
        result, count = manager.enforce_budget(
            data,
            max_tokens=100,
            truncation_priority=["key1", "key2", "key3"],
        )
        # Check that truncation happened
        assert count.truncated is True
        assert len(count.truncated_sections) > 0

    def test_truncation_priority(self, manager: TokenBudgetManager) -> None:
        """Test that truncation follows priority order."""
        data = {
            "important": "Keep this content",
            "less_important": "x" * 1000,
        }
        result, count = manager.enforce_budget(
            data,
            max_tokens=100,
            truncation_priority=["less_important"],
        )
        # Important key should be preserved
        assert "important" in result


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_count_tokens_function(self) -> None:
        """Test global count_tokens function."""
        count = count_tokens("Hello world")
        assert count > 0

    def test_get_token_budget_manager_singleton(self) -> None:
        """Test that get_token_budget_manager returns singleton."""
        manager1 = get_token_budget_manager()
        manager2 = get_token_budget_manager()
        assert manager1 is manager2


class TestTruncateToBudget:
    """Test truncation to budget."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a token budget manager for testing."""
        return TokenBudgetManager()

    def test_short_text_not_truncated(self, manager: TokenBudgetManager) -> None:
        """Short text should not be truncated."""
        text = "Hello world"
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=100)
        assert result == text
        assert was_truncated is False

    def test_long_text_is_truncated(self, manager: TokenBudgetManager) -> None:
        """Long text should be truncated."""
        text = "x" * 1000
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=10)
        assert was_truncated is True
        assert len(result) < len(text)
        assert result.endswith("...")

    def test_preserve_end_mode(self, manager: TokenBudgetManager) -> None:
        """Test preserve_end mode keeps end of text."""
        text = "start" + "x" * 100 + "end"
        result, was_truncated = manager.truncate_to_budget(text, max_tokens=10, preserve_end=True)
        assert was_truncated is True
        assert result.startswith("...")
        assert "end" in result


class TestTruncateListToBudget:
    """Test list truncation to budget."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a token budget manager for testing."""
        return TokenBudgetManager()

    def test_short_list_not_truncated(self, manager: TokenBudgetManager) -> None:
        """Short list should not be truncated."""
        items = ["item1", "item2"]
        result, was_truncated = manager.truncate_list_to_budget(items, max_tokens=100)
        assert result == items
        assert was_truncated is False

    def test_long_list_is_truncated(self, manager: TokenBudgetManager) -> None:
        """Long list should be truncated."""
        items = ["x" * 100 for _ in range(10)]
        result, was_truncated = manager.truncate_list_to_budget(items, max_tokens=50)
        assert was_truncated is True
        assert len(result) < len(items)

    def test_preserve_recent_keeps_end(self, manager: TokenBudgetManager) -> None:
        """Test preserve_recent keeps most recent items."""
        items = ["old item text here", "middle item text here", "new item text here"]
        result, was_truncated = manager.truncate_list_to_budget(
            items, max_tokens=10, preserve_recent=True
        )
        # If truncated, should keep "new item text here" (most recent)
        if was_truncated:
            assert "new item text here" in result
        else:
            # If not truncated, all items fit
            assert len(result) == 3
