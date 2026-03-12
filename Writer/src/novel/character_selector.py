"""Character selector for tier-based character selection with token budget.

This module provides a simplified character selection strategy that selects
characters based on their tier and token budget constraints.

Usage:
    from src.novel.character_selector import CharacterSelector
    from src.novel.character_profile import CharacterProfile

    selector = CharacterSelector()
    characters = [CharacterProfile(name="Alice", tier=0), ...]
    chapter_spec = {"characters": ["Alice", "Bob"]}
    selected, remaining = selector.select_for_chapter(characters, chapter_spec)
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.novel.character_profile import CharacterProfile

logger = logging.getLogger(__name__)


class CharacterSelector:
    """基于层级的角色选择器 (简化版)

    Selects characters for chapter generation based on tier and token budget:

    Selection Strategy:
        - tier=0: 全部激活 (必须) - All tier 0 characters must be included
        - tier=1: 章节大纲提及的角色激活 - Tier 1 characters mentioned in chapter spec
        - tier=2: 预算允许时激活 - Tier 2 characters if budget allows
        - tier=3: 模板处理，不计入预算 - Tier 3 characters use templates, not counted

    Example:
        >>> selector = CharacterSelector()
        >>> characters = [CharacterProfile(name="Alice", tier=0), ...]
        >>> chapter_spec = {"characters": ["Alice", "Bob"]}
        >>> selected, remaining = selector.select_for_chapter(characters, chapter_spec)
        >>> print(f"Selected {len(selected)} characters, {remaining} tokens remaining")
    """

    DEFAULT_TOTAL_BUDGET: int = 4000

    def __init__(self) -> None:
        """Initialize CharacterSelector."""
        # Import TIER_TOKEN_BUDGET here to avoid circular import
        from src.novel.character_profile import TIER_TOKEN_BUDGET

        self.tier_budget: dict[int, int] = TIER_TOKEN_BUDGET

    def select_for_chapter(
        self,
        all_characters: list["CharacterProfile"],
        chapter_spec: dict[str, Any],
        total_budget: int = DEFAULT_TOTAL_BUDGET,
    ) -> tuple[list["CharacterProfile"], int]:
        """为章节选择角色

        Args:
            all_characters: 所有可用的角色档案
            chapter_spec: 章节大纲规格 (包含'characters'字段)
            total_budget: 总Token预算 (默认4000)

        Returns:
            tuple: (选中角色列表, 剩余预算)

        激活策略 (简化版):
            - tier=0: 全部激活 (必须)
            - tier=1: 章节大纲提及的角色
            - tier=2: 预算允许时激活
            - tier=3: 模板处理，不计入预算

        Example:
            >>> selector = CharacterSelector()
            >>> characters = [CharacterProfile(name="Alice", tier=0), ...]
            >>> chapter_spec = {"characters": ["Alice", "Bob"]}
            >>> selected, remaining = selector.select_for_chapter(characters, chapter_spec)
        """
        selected = []
        remaining_budget = total_budget

        # 1. 必须包含所有 tier=0 角色
        for char in all_characters:
            if char.tier == 0:
                selected.append(char)
                remaining_budget -= char.get_token_budget()
                logger.debug(f"Selected tier=0 character: {char.name}")

        # 2. 检查章节大纲提及的 tier=1 角色
        mentioned_names = self._extract_mentioned_names(chapter_spec)
        for char in all_characters:
            if char.tier == 1 and char.name in mentioned_names:
                budget = char.get_token_budget()
                if remaining_budget >= budget:
                    selected.append(char)
                    remaining_budget -= budget
                    logger.debug(f"Selected tier=1 character: {char.name}")

        # 3. 检查章节大纲提及的 tier=2 角色 (预算允许)
        for char in all_characters:
            if char.tier == 2 and char.name in mentioned_names:
                budget = char.get_token_budget()
                if remaining_budget >= budget:
                    selected.append(char)
                    remaining_budget -= budget
                    logger.debug(f"Selected tier=2 character: {char.name}")

        # 4. tier=3 不处理，在生成时用模板

        logger.info(
            f"Selected {len(selected)} characters from {len(all_characters)} available, {remaining_budget} tokens remaining"
        )

        return selected, remaining_budget

    def _extract_mentioned_names(self, chapter_spec: dict[str, Any]) -> set[str]:
        """从章节大纲中提取提及的角色名

        简化实现: 直接从chapter_spec['characters']获取

        Args:
            chapter_spec: 章节大纲规格字典

        Returns:
            set: 提及的角色名集合

        Example:
            >>> spec = {"characters": ["Alice", "Bob"]}
            >>> names = selector._extract_mentioned_names(spec)
            >>> print(names)  # {"Alice", "Bob"}
        """
        return set(chapter_spec.get("characters", []))


__all__ = ["CharacterSelector"]
