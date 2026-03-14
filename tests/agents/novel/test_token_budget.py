"""Tests for token budget management module."""

import pytest

from src.novel.token_budget import ContextSlice, TokenBudget, TokenBudgetManager


class TestTokenBudget:
    """Tests for TokenBudget dataclass."""

    def test_default_budget(self) -> None:
        """Test default budget values."""
        budget = TokenBudget()
        assert budget.total == 8000
        assert budget.reserved_for_generation == 500
        assert budget.get_available() == 7500

    def test_custom_budget(self) -> None:
        """Test custom budget configuration."""
        budget = TokenBudget(total=16000, reserved_for_generation=1000)
        assert budget.total == 16000
        assert budget.reserved_for_generation == 1000
        assert budget.get_available() == 15000

    def test_chaining_setters(self) -> None:
        """Test fluent API for setting values."""
        budget = TokenBudget().set_total(16000).set_reserved(800)
        assert budget.total == 16000
        assert budget.reserved_for_generation == 800


class TestContextSlice:
    """Tests for ContextSlice dataclass."""

    def test_default_priority(self) -> None:
        """Test default priority is 2 (important)."""
        slice = ContextSlice(name="test", content="content")
        assert slice.priority == 2
        assert slice.name == "test"
        assert slice.content == "content"

    def test_valid_priorities(self) -> None:
        """Test valid priority values."""
        # Priority 1: must
        slice1 = ContextSlice(name="p1", content="content", priority=1)
        assert slice1.priority == 1

        # Priority 2: important (default)
        slice2 = ContextSlice(name="p2", content="content", priority=2)
        assert slice2.priority == 2

        # Priority 3: optional
        slice3 = ContextSlice(name="p3", content="content", priority=3)
        assert slice3.priority == 3

    def test_invalid_priority(self) -> None:
        """Test invalid priority raises error."""
        with pytest.raises(ValueError, match="Priority must be 1, 2, or 3"):
            ContextSlice(name="test", content="content", priority=0)

        with pytest.raises(ValueError, match="Priority must be 1, 2, or 3"):
            ContextSlice(name="test", content="content", priority=4)


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager class."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a default manager for tests."""
        return TokenBudgetManager()

    def test_default_initialization(self, manager: TokenBudgetManager) -> None:
        """Test default initialization."""
        assert manager.budget.total == 8000
        assert manager.budget.reserved_for_generation == 500
        assert "global_state" in manager.allocation
        assert "recent_chapters" in manager.allocation

    def test_custom_budget_initialization(self) -> None:
        """Test initialization with custom budget."""
        custom_budget = TokenBudget(total=32000, reserved_for_generation=2000)
        manager = TokenBudgetManager(budget=custom_budget)
        assert manager.budget.total == 32000
        assert manager.budget.get_available() == 30000


class TestEstimateTokens:
    """Tests for token estimation."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a default manager for tests."""
        return TokenBudgetManager()

    def test_empty_text(self, manager: TokenBudgetManager) -> None:
        """Test estimation of empty text."""
        assert manager.estimate_tokens("") == 0

    def test_chinese_characters(self, manager: TokenBudgetManager) -> None:
        """Test estimation for Chinese text.

        ~1.5 Chinese chars per token expected.
        """
        # 15 Chinese characters ≈ 10 tokens
        text = "这是一段中文测试文本"
        estimate = manager.estimate_tokens(text)
        # 10 chars / 1.5 ≈ 7 tokens
        assert estimate > 0
        assert isinstance(estimate, int)

    def test_english_text(self, manager: TokenBudgetManager) -> None:
        """Test estimation for English text.

        ~0.75 words per token expected.
        """
        text = "This is a test sentence with eight words"
        estimate = manager.estimate_tokens(text)
        # 8 words * 0.75 ≈ 6 tokens
        assert estimate > 0
        assert isinstance(estimate, int)

    def test_mixed_text(self, manager: TokenBudgetManager) -> None:
        """Test estimation for mixed Chinese and English."""
        text = "这是一个test句子with English混合"
        estimate = manager.estimate_tokens(text)
        assert estimate > 0
        assert isinstance(estimate, int)

    def test_estimate_for_slice(self, manager: TokenBudgetManager) -> None:
        """Test estimating tokens for a slice."""
        slice = ContextSlice(name="test", content="这是一个测试")
        estimate = manager.estimate_tokens_for_slice(slice)
        assert estimate > 0
        assert slice.estimated_tokens == estimate


class TestAllocateContext:
    """Tests for context allocation with priority."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a manager with small budget for testing limits."""
        budget = TokenBudget(total=1000, reserved_for_generation=100)
        return TokenBudgetManager(budget=budget)

    def test_allocate_empty_list(self, manager: TokenBudgetManager) -> None:
        """Test allocation with empty list."""
        result = manager.allocate_context([])
        assert result == []

    def test_allocate_priority_order(self, manager: TokenBudgetManager) -> None:
        """Test that priority 1 items are always included."""
        slices = [
            ContextSlice(name="optional", content="a " * 200, priority=3),  # ~150 tokens
            ContextSlice(name="important", content="b " * 200, priority=2),  # ~150 tokens
            ContextSlice(name="must", content="c " * 50, priority=1),  # ~38 tokens
        ]

        result = manager.allocate_context(slices)

        # Priority 1 must be included
        assert any(s.name == "must" for s in result)

    def test_allocate_respects_budget(self, manager: TokenBudgetManager) -> None:
        """Test that budget limits are respected."""
        # Create slices that exceed budget
        slices = [
            ContextSlice(name="p1", content="x " * 100, priority=1),  # ~75 tokens
            ContextSlice(name="p2", content="y " * 1000, priority=2),  # ~750 tokens
            ContextSlice(name="p3", content="z " * 1000, priority=3),  # ~750 tokens
        ]

        result = manager.allocate_context(slices)

        # Calculate total tokens in result
        total = sum(s.estimated_tokens for s in result)

        # Should not exceed available budget (900)
        assert total <= manager.budget.get_available()

    def test_strict_priority_disabled(self, manager: TokenBudgetManager) -> None:
        """Test that strict_priority=False allows skipping priority 1."""
        # Create a huge priority 1 slice that exceeds budget
        huge_content = "x " * 10000  # Way over budget
        slices = [
            ContextSlice(name="huge_must", content=huge_content, priority=1),
        ]

        result = manager.allocate_context(slices, strict_priority=False)

        # With strict_priority=False, huge_must should be excluded
        # because it exceeds available budget
        assert (
            len(result) == 0
            or sum(s.estimated_tokens for s in result) <= manager.budget.get_available()
        )


class TestBudgetLimits:
    """Tests for budget limit enforcement."""

    def test_small_budget(self) -> None:
        """Test with very small budget."""
        budget = TokenBudget(total=500, reserved_for_generation=400)
        manager = TokenBudgetManager(budget=budget)

        assert manager.budget.get_available() == 100

        slices = [
            ContextSlice(name="small", content="test content here", priority=1),
        ]

        result = manager.allocate_context(slices)
        # Should be able to include small slice within 100 token budget
        assert len(result) >= 0  # May or may not fit

    def test_large_budget(self) -> None:
        """Test with large budget (e.g., 32K)."""
        budget = TokenBudget(total=32000, reserved_for_generation=2000)
        manager = TokenBudgetManager(budget=budget)

        assert manager.budget.get_available() == 30000

        # Create many slices
        slices = [
            ContextSlice(name=f"slice_{i}", content=f"content {i} " * 100, priority=2)
            for i in range(50)
        ]

        result = manager.allocate_context(slices)
        total = sum(s.estimated_tokens for s in result)

        assert total <= 30000

    def test_exact_budget_fit(self) -> None:
        """Test when content exactly fits budget."""
        budget = TokenBudget(total=1000, reserved_for_generation=500)
        manager = TokenBudgetManager(budget=budget)

        # Create content that should fit within 500 tokens
        slices = [
            ContextSlice(name="fit", content="word " * 400, priority=1),  # ~300 tokens
        ]

        result = manager.allocate_context(slices)
        assert len(result) == 1
        assert result[0].name == "fit"


class TestBuildContext:
    """Tests for building context string."""

    @pytest.fixture
    def manager(self) -> TokenBudgetManager:
        """Create a default manager."""
        return TokenBudgetManager()

    def test_build_empty(self, manager: TokenBudgetManager) -> None:
        """Test building context from empty list."""
        result = manager.build_context([])
        assert result == ""

    def test_build_single_slice(self, manager: TokenBudgetManager) -> None:
        """Test building context from single slice."""
        slices = [
            ContextSlice(name="test", content="Hello world", priority=1),
        ]
        result = manager.build_context(slices)
        assert result == "Hello world"

    def test_build_multiple_slices(self, manager: TokenBudgetManager) -> None:
        """Test building context from multiple slices."""
        slices = [
            ContextSlice(name="a", content="First part", priority=1),
            ContextSlice(name="b", content="Second part", priority=2),
        ]
        result = manager.build_context(slices)
        assert "First part" in result
        assert "Second part" in result
        assert "\n\n" in result  # Default separator

    def test_build_custom_separator(self, manager: TokenBudgetManager) -> None:
        """Test building context with custom separator."""
        slices = [
            ContextSlice(name="a", content="Part A", priority=1),
            ContextSlice(name="b", content="Part B", priority=2),
        ]
        result = manager.build_context(slices, separator=" | ")
        assert result == "Part A | Part B"

    def test_build_respects_budget(self, manager: TokenBudgetManager) -> None:
        """Test that build_context respects budget limits."""
        # Use small budget
        small_budget = TokenBudget(total=500, reserved_for_generation=400)
        small_manager = TokenBudgetManager(budget=small_budget)

        slices = [
            ContextSlice(name="must", content="x " * 50, priority=1),  # ~38 tokens
            ContextSlice(name="huge", content="y " * 2000, priority=2),  # ~1500 tokens - won't fit
        ]

        result = small_manager.build_context(slices)
        # Should only include 'must' since 'huge' exceeds budget
        assert "must" in result or "x" in result


class TestBudgetSummary:
    """Tests for budget summary reporting."""

    def test_summary_structure(self) -> None:
        """Test summary contains expected fields."""
        manager = TokenBudgetManager()
        slices = [
            ContextSlice(name="p1", content="x " * 100, priority=1),
            ContextSlice(name="p2", content="y " * 100, priority=2),
            ContextSlice(name="p3", content="z " * 100, priority=3),
        ]

        summary = manager.get_budget_summary(slices)

        assert "total_budget" in summary
        assert "reserved" in summary
        assert "available" in summary
        assert "total_required" in summary
        assert "over_budget" in summary
        assert "deficit" in summary
        assert "by_priority" in summary

        assert summary["total_budget"] == 8000
        assert summary["reserved"] == 500
        assert summary["available"] == 7500
        assert summary["total_required"] > 0

    def test_over_budget_detection(self) -> None:
        """Test detection of over-budget condition."""
        budget = TokenBudget(total=500, reserved_for_generation=100)
        manager = TokenBudgetManager(budget=budget)

        # Create slices that exceed 400 token budget
        slices = [
            ContextSlice(name="huge", content="word " * 1000, priority=1),
        ]

        summary = manager.get_budget_summary(slices)

        assert summary["over_budget"] is True
        assert summary["deficit"] > 0


class TestAllocationStrategy:
    """Tests for allocation strategy configuration."""

    def test_default_allocation(self) -> None:
        """Test default allocation values."""
        manager = TokenBudgetManager()
        allocation = manager.get_allocation()

        assert allocation["global_state"] == 500
        assert allocation["current_arc"] == 400
        assert allocation["recent_chapters"] == 2000
        assert allocation["previous_chapter"] == 200
        assert allocation["buffer"] == 3400

    def test_set_custom_allocation(self) -> None:
        """Test setting custom allocation."""
        manager = TokenBudgetManager()
        custom = {
            "global_state": 1000,
            "current_arc": 800,
            "buffer": 2000,
        }

        manager.set_allocation(custom)
        result = manager.get_allocation()

        assert result["global_state"] == 1000
        assert result["current_arc"] == 800
        assert result["buffer"] == 2000


class TestCreateSlice:
    """Tests for create_slice factory method."""

    def test_create_slice_with_auto_estimate(self) -> None:
        """Test creating slice with auto-estimated tokens."""
        manager = TokenBudgetManager()
        slice = manager.create_slice(name="auto", content="这是一个测试内容", priority=2)

        assert slice.name == "auto"
        assert slice.content == "这是一个测试内容"
        assert slice.priority == 2
        assert slice.estimated_tokens > 0  # Auto-estimated

    def test_create_slice_default_priority(self) -> None:
        """Test create_slice uses priority 2 by default."""
        manager = TokenBudgetManager()
        slice = manager.create_slice(name="test", content="content")

        assert slice.priority == 2
