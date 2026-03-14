"""Token budget management for context window optimization.

Provides TokenBudget dataclass, ContextSlice for prioritized context,
and TokenBudgetManager for smart context allocation.
"""

import re
from dataclasses import dataclass


@dataclass
class TokenBudget:
    """Token budget configuration.

    Attributes:
        total: Total token budget (default 8000 for DeepSeek 8K)
        reserved_for_generation: Tokens reserved for LLM output (default 500)
    """

    total: int = 8000
    reserved_for_generation: int = 500

    def get_available(self) -> int:
        """Calculate available tokens for context."""
        return self.total - self.reserved_for_generation

    def set_total(self, total: int) -> "TokenBudget":
        """Set total budget and return self for chaining."""
        self.total = total
        return self

    def set_reserved(self, reserved: int) -> "TokenBudget":
        """Set reserved tokens and return self for chaining."""
        self.reserved_for_generation = reserved
        return self


@dataclass
class ContextSlice:
    """A slice of context with priority and token estimate.

    Attributes:
        name: Identifier for this context slice
        content: The actual content text
        priority: 1=必须, 2=重要, 3=可选
        estimated_tokens: Estimated token count for this slice
    """

    name: str
    content: str
    priority: int = 2  # Default to important
    estimated_tokens: int = 0

    def __post_init__(self):
        """Validate priority value."""
        if self.priority not in (1, 2, 3):
            raise ValueError(f"Priority must be 1, 2, or 3, got {self.priority}")


class TokenBudgetManager:
    """Manages token budget allocation for context building.

    Provides token estimation and smart context allocation based on priorities.
    """

    # Default allocation strategy
    DEFAULT_ALLOCATION = {
        "global_state": 500,  # L0: 全局状态
        "current_arc": 400,  # L1: 当前卷
        "recent_chapters": 2000,  # L2: 最近章节 (自适应)
        "previous_chapter": 200,  # 前一章详细
        "buffer": 3400,  # 预留空间
    }

    def __init__(self, budget: TokenBudget | None = None):
        """Initialize with optional custom budget.

        Args:
            budget: TokenBudget instance, or None for default 8K budget
        """
        self.budget = budget or TokenBudget()
        self.allocation = self.DEFAULT_ALLOCATION.copy()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses simple heuristic:
        - Chinese characters: 1 token ≈ 1.5 chars
        - English words: 1 token ≈ 4 chars ≈ 0.75 words

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Count Chinese characters (CJK Unified Ideographs and extensions)
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))

        # Count English words (sequences of letters)
        english_words = len(re.findall(r"[a-zA-Z]+", text))

        # Count remaining characters (punctuation, numbers, etc.)
        remaining_chars = (
            len(text) - chinese_chars - sum(len(word) for word in re.findall(r"[a-zA-Z]+", text))
        )

        # Calculate tokens
        chinese_tokens = chinese_chars / 1.5
        english_tokens = english_words * 0.75
        remaining_tokens = remaining_chars / 4  # Assume mixed/symbols

        return int(chinese_tokens + english_tokens + remaining_tokens)

    def estimate_tokens_for_slice(self, slice: ContextSlice) -> int:
        """Estimate and update token count for a slice.

        Args:
            slice: ContextSlice to estimate

        Returns:
            Estimated token count
        """
        slice.estimated_tokens = self.estimate_tokens(slice.content)
        return slice.estimated_tokens

    def allocate_context(
        self, slices: list[ContextSlice], strict_priority: bool = True
    ) -> list[ContextSlice]:
        """Allocate context slices within budget.

        Selects slices to include based on priority and budget.
        Priority 1 (必须) slices are always included.
        Priority 2 (重要) and 3 (可选) are included if space allows.

        Args:
            slices: List of context slices to consider
            strict_priority: If True, never skip priority 1 even if over budget

        Returns:
            List of selected slices that fit in budget
        """
        available = self.budget.get_available()

        # Update estimates for all slices
        for slice in slices:
            if slice.estimated_tokens == 0:
                self.estimate_tokens_for_slice(slice)

        # Sort by priority (lower number = higher priority)
        sorted_slices = sorted(slices, key=lambda s: s.priority)

        selected: list[ContextSlice] = []
        total_tokens = 0

        for slice in sorted_slices:
            new_total = total_tokens + slice.estimated_tokens

            if slice.priority == 1:
                # Priority 1: must include (unless strict_priority=False and over budget)
                if strict_priority or new_total <= available:
                    selected.append(slice)
                    total_tokens = new_total
            elif new_total <= available:
                # Priority 2 & 3: include only if within budget
                selected.append(slice)
                total_tokens = new_total

        return selected

    def build_context(
        self, slices: list[ContextSlice], separator: str = "\n\n", strict_priority: bool = True
    ) -> str:
        """Build final context string from allocated slices.

        Args:
            slices: List of context slices
            separator: String to join slices with
            strict_priority: Whether to strictly enforce priority 1 inclusion

        Returns:
            Concatenated context string
        """
        selected = self.allocate_context(slices, strict_priority)

        # Sort selected by priority for consistent ordering
        selected = sorted(selected, key=lambda s: s.priority)

        return separator.join(slice.content for slice in selected)

    def get_budget_summary(self, slices: list[ContextSlice]) -> dict:
        """Get summary of budget usage.

        Args:
            slices: All available context slices

        Returns:
            Dictionary with budget statistics
        """
        available = self.budget.get_available()
        total = self.budget.total
        reserved = self.budget.reserved_for_generation

        # Calculate totals by priority
        total_by_priority = {1: 0, 2: 0, 3: 0}
        for slice in slices:
            if slice.estimated_tokens == 0:
                self.estimate_tokens_for_slice(slice)
            total_by_priority[slice.priority] += slice.estimated_tokens

        total_all = sum(total_by_priority.values())

        return {
            "total_budget": total,
            "reserved": reserved,
            "available": available,
            "total_required": total_all,
            "over_budget": total_all > available,
            "deficit": max(0, total_all - available),
            "by_priority": {
                "must": total_by_priority[1],
                "important": total_by_priority[2],
                "optional": total_by_priority[3],
            },
        }

    def set_allocation(self, allocation: dict[str, int]) -> None:
        """Set custom allocation strategy.

        Args:
            allocation: Dictionary mapping context names to token limits
        """
        self.allocation = allocation.copy()

    def get_allocation(self) -> dict[str, int]:
        """Get current allocation strategy."""
        return self.allocation.copy()

    def create_slice(self, name: str, content: str, priority: int = 2) -> ContextSlice:
        """Factory method to create a ContextSlice with auto-estimated tokens.

        Args:
            name: Slice identifier
            content: Content text
            priority: 1=必须, 2=重要, 3=可选

        Returns:
            New ContextSlice with estimated tokens
        """
        slice = ContextSlice(name=name, content=content, priority=priority)
        self.estimate_tokens_for_slice(slice)
        return slice
