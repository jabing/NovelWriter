"""Token budget management for LLM context window control.

This module provides utilities for counting tokens and enforcing token budgets
before LLM API calls to prevent context window overflow.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Try to import tiktoken, fall back to approximation if not available
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
    # DeepSeek uses cl100k_base encoding (same as GPT-4)
    _encoding = tiktoken.get_encoding("cl100k_base")
except ImportError:
    TIKTOKEN_AVAILABLE = False
    _encoding = None
    logger.warning("tiktoken not available, using character-based approximation")


@dataclass
class TokenBudgetConfig:
    """Configuration for token budget management."""

    max_context_tokens: int = 16000  # Maximum tokens for context
    system_prompt_reserve: int = 500  # Tokens reserved for system prompt
    response_reserve: int = 4096  # Tokens reserved for response
    safety_margin: int = 100  # Extra safety margin

    @property
    def available_context_tokens(self) -> int:
        """Calculate available tokens for context."""
        return (
            self.max_context_tokens
            - self.system_prompt_reserve
            - self.response_reserve
            - self.safety_margin
        )


@dataclass
class TokenCount:
    """Result of token counting."""

    total: int
    by_section: dict[str, int] = field(default_factory=dict)
    truncated: bool = False
    truncated_sections: list[str] = field(default_factory=list)


class TokenBudgetManager:
    """Manages token budgets for LLM context windows.

    This class provides methods for:
    - Counting tokens in text using tiktoken (or approximation)
    - Enforcing token budgets by truncating content
    - Ensuring truncation happens at sentence boundaries
    - Priority-based truncation to preserve important content

    Example:
        >>> manager = TokenBudgetManager()
        >>> count = manager.count_tokens("Hello, world!")
        >>> print(count.total)
        4

        >>> truncated = manager.enforce_budget(
        ...     {"key_events": events_list},
        ...     max_tokens=1000
        ... )
    """

    # Pattern for sentence boundaries
    SENTENCE_END_PATTERN = re.compile(r"[.!?。！？]\s*")

    # Context priority levels (higher number = higher priority, less likely to truncate)
    CONTEXT_PRIORITY = {
        "header": 10,  # 核心规则、标题
        "chapter_outline": 9,  # 当前章节大纲
        "continuity": 8,  # 连续性上下文
        "character_info": 7,  # 角色信息
        "relationships": 6,  # 角色关系
        "world_settings": 5,  # 世界设定
        "full_outline": 4,  # 完整大纲
        "learning_hints": 3,  # 学习提示
        "style_guide": 2,  # 风格指南
        "market_keywords": 1,  # 市场关键词
    }

    def __init__(self, config: TokenBudgetConfig | None = None) -> None:
        """Initialize the token budget manager.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or TokenBudgetConfig()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses tiktoken if available, otherwise uses character-based approximation
        (4 characters per token on average).

        Args:
            text: Text to count tokens for.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0

        if TIKTOKEN_AVAILABLE and _encoding is not None:
            return len(_encoding.encode(text))
        else:
            # Approximation: 4 characters per token
            return len(text) // 4

    def count_tokens_in_dict(self, data: dict[str, Any]) -> TokenCount:
        """Count tokens in a dictionary structure.

        Args:
            data: Dictionary to count tokens for.

        Returns:
            TokenCount with total and per-section breakdown.
        """
        by_section: dict[str, int] = {}
        total = 0

        for key, value in data.items():
            if isinstance(value, str):
                tokens = self.count_tokens(value)
            elif isinstance(value, list):
                # Join list items for counting
                text = " ".join(str(item) for item in value)
                tokens = self.count_tokens(text)
            elif isinstance(value, dict):
                # Recursively count nested dict
                nested = self.count_tokens_in_dict(value)
                tokens = nested.total
            else:
                tokens = self.count_tokens(str(value))

            by_section[key] = tokens
            total += tokens

        return TokenCount(total=total, by_section=by_section)

    def find_sentence_boundary(self, text: str, max_position: int) -> int:
        """Find the nearest sentence boundary before max_position.

        Args:
            text: Text to search.
            max_position: Maximum character position.

        Returns:
            Position of sentence boundary, or max_position if none found.
        """
        if max_position >= len(text):
            return len(text)

        # Search for sentence end before max_position
        search_text = text[:max_position]
        matches = list(self.SENTENCE_END_PATTERN.finditer(search_text))

        if matches:
            # Return position after last sentence end
            last_match = matches[-1]
            return last_match.end()

        # No sentence boundary found, look for any space
        last_space = search_text.rfind(" ")
        if last_space > 0:
            return last_space

        # No good boundary, return max_position
        return max_position

    def truncate_to_budget(
        self, text: str, max_tokens: int, preserve_end: bool = False
    ) -> tuple[str, bool]:
        """Truncate text to fit within token budget.

        Args:
            text: Text to truncate.
            max_tokens: Maximum tokens allowed.
            preserve_end: If True, preserve end of text (for summaries).

        Returns:
            Tuple of (truncated text, was_truncated).
        """
        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text, False

        # Approximate character limit (4 chars per token)
        target_chars = max_tokens * 4

        if preserve_end:
            # Keep end of text
            len(text) - target_chars
            boundary = self.find_sentence_boundary(text, len(text) - target_chars)
            truncated = "..." + text[boundary:].lstrip()
        else:
            # Keep start of text
            boundary = self.find_sentence_boundary(text, target_chars)
            truncated = text[:boundary].rstrip() + "..."

        return truncated, True

    def truncate_list_to_budget(
        self, items: list[str], max_tokens: int, preserve_recent: bool = True
    ) -> tuple[list[str], bool]:
        """Truncate a list of strings to fit within token budget.

        Args:
            items: List of strings to truncate.
            max_tokens: Maximum tokens allowed.
            preserve_recent: If True, keep most recent items.

        Returns:
            Tuple of (truncated list, was_truncated).
        """
        if not items:
            return items, False

        # Count tokens for all items
        item_tokens = [(item, self.count_tokens(item)) for item in items]
        total_tokens = sum(t for _, t in item_tokens)

        if total_tokens <= max_tokens:
            return items, False

        # Need to truncate
        result = []
        remaining_budget = max_tokens

        # Process items based on preserve_recent setting
        if preserve_recent:
            # Start from most recent
            for item, tokens in reversed(item_tokens):
                if tokens <= remaining_budget:
                    result.insert(0, item)  # Maintain order
                    remaining_budget -= tokens
                else:
                    break
        else:
            # Start from oldest
            for item, tokens in item_tokens:
                if tokens <= remaining_budget:
                    result.append(item)
                    remaining_budget -= tokens
                else:
                    break

        return result, True

    def enforce_budget(
        self,
        context: dict[str, Any],
        max_tokens: int | None = None,
        truncation_priority: list[str] | None = None,
    ) -> tuple[dict[str, Any], TokenCount]:
        """Enforce token budget on context dictionary.

        Args:
            context: Context dictionary to enforce budget on.
            max_tokens: Maximum tokens. Uses config if not provided.
            truncation_priority: Order of sections to truncate (first truncated).

        Returns:
            Tuple of (potentially modified context, token count result).
        """
        max_tokens = max_tokens or self.config.available_context_tokens
        truncation_priority = truncation_priority or ["key_events", "plot_threads", "world_state"]

        result = dict(context)
        token_count = self.count_tokens_in_dict(result)

        if token_count.total <= max_tokens:
            return result, token_count

        # Need to truncate - process by priority
        for section in truncation_priority:
            if token_count.total <= max_tokens:
                break

            if section not in result:
                continue

            value = result[section]

            if isinstance(value, list):
                # Truncate list
                truncated_list, was_truncated = self.truncate_list_to_budget(
                    value,
                    max_tokens // 3,  # Give each section at most 1/3 of budget
                )
                if was_truncated:
                    result[section] = truncated_list
                    token_count.truncated = True
                    token_count.truncated_sections.append(section)

            elif isinstance(value, str):
                # Truncate string
                truncated_str, was_truncated = self.truncate_to_budget(value, max_tokens // 3)
                if was_truncated:
                    result[section] = truncated_str
                    token_count.truncated = True
                    token_count.truncated_sections.append(section)

        # Track truncated sections before recounting
        truncated_sections = token_count.truncated_sections.copy()

        # Recount after truncation
        token_count = self.count_tokens_in_dict(result)
        token_count.truncated = len(truncated_sections) > 0
        token_count.truncated_sections = truncated_sections

        return result, token_count

    def enforce_budget_with_priority(
        self,
        context: dict[str, Any],
        max_tokens: int | None = None,
        priority_map: dict[str, int] | None = None,
    ) -> tuple[dict[str, Any], TokenCount]:
        """Enforce token budget with priority-based truncation.

        Args:
            context: Context dictionary to enforce budget on.
            max_tokens: Maximum tokens. Uses config if not provided.
            priority_map: Optional custom priority map. Uses default if not provided.

        Returns:
            Tuple of (potentially modified context, token count result).
        """
        max_tokens = max_tokens or self.config.available_context_tokens
        priority_map = priority_map or self.CONTEXT_PRIORITY

        result = dict(context)
        token_count = self.count_tokens_in_dict(result)

        if token_count.total <= max_tokens:
            return result, token_count

        # Sort sections by priority (ascending - lowest priority first)
        sections = sorted(
            result.keys(),
            key=lambda k: priority_map.get(k, 0),
        )

        # Truncate from lowest priority until within budget
        truncated_sections = []
        for section in sections:
            if token_count.total <= max_tokens:
                break

            # Never truncate high-priority sections (priority >= 8)
            if priority_map.get(section, 0) >= 8:
                continue

            value = result[section]
            if isinstance(value, list):
                truncated_list, was_truncated = self.truncate_list_to_budget(
                    value,
                    max_tokens // 4,  # Give each section at most 1/4 of budget
                )
                if was_truncated:
                    result[section] = truncated_list
                    token_count.truncated = True
                    truncated_sections.append(section)
            elif isinstance(value, str) and len(value) > 100:
                truncated_str, was_truncated = self.truncate_to_budget(value, max_tokens // 4)
                if was_truncated:
                    result[section] = truncated_str
                    token_count.truncated = True
                    truncated_sections.append(section)

        # Recount after truncation
        final_count = self.count_tokens_in_dict(result)
        final_count.truncated = len(truncated_sections) > 0
        final_count.truncated_sections = truncated_sections

        return result, final_count


# Global instance for convenience
_default_manager: TokenBudgetManager | None = None


def get_token_budget_manager() -> TokenBudgetManager:
    """Get the global TokenBudgetManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = TokenBudgetManager()
    return _default_manager


def count_tokens(text: str) -> int:
    """Convenience function to count tokens using global manager."""
    return get_token_budget_manager().count_tokens(text)
