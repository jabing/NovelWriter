"""1000 角色场景下的 CharacterSelector 性能基准测试

This module provides performance benchmarks for CharacterSelector
with 1000 characters across different tier distributions.

Performance Goals:
    - 1000 characters selection time < 100ms
    - 5000 characters selection time < 500ms

Tier Distribution (1000 characters):
    - Tier 0: 10 characters (1%) - Core protagonists
    - Tier 1: 90 characters (9%) - Important supporting characters
    - Tier 2: 400 characters (40%) - Regular supporting characters
    - Tier 3: 500 characters (50%) - Social public (template-based)
"""

import logging
import statistics
import time
from pathlib import Path

import pytest

from src.novel_agent.novel.character_profile import CharacterProfile, TIER_TOKEN_BUDGET
from src.novel_agent.novel.character_selector import CharacterSelector

logger = logging.getLogger(__name__)


class TestCharacterSelectorPerformance:
    """1000 角色场景下的 CharacterSelector 性能测试"""

    @pytest.fixture(scope="class")
    def thousand_characters(self) -> list[CharacterProfile]:
        """创建 1000 个测试角色
        
        Tier Distribution:
            - Tier 0: 10 个 (1%) - 核心主角
            - Tier 1: 90 个 (9%) - 重要配角
            - Tier 2: 400 个 (40%) - 普通配角
            - Tier 3: 500 个 (50%) - 社会公众
        """
        characters: list[CharacterProfile] = []
        
        # Tier 0: 10 characters (核心主角)
        for i in range(10):
            char = CharacterProfile(
                name=f"Protagonist_{i:03d}",
                tier=0,
                bio=f"Core protagonist {i} with detailed background",
                persona=f"Personality traits for protagonist {i}",
                mbti="INTJ",
                profession=f"Profession {i}",
            )
            characters.append(char)
        
        # Tier 1: 90 characters (重要配角)
        for i in range(90):
            char = CharacterProfile(
                name=f"Supporting_{i:03d}",
                tier=1,
                bio=f"Important supporting character {i}",
                persona=f"Personality for supporting {i}",
                profession=f"Profession {i}",
            )
            characters.append(char)
        
        # Tier 2: 400 characters (普通配角)
        for i in range(400):
            char = CharacterProfile(
                name=f"Regular_{i:03d}",
                tier=2,
                bio=f"Regular supporting character {i}",
                profession=f"Profession {i}",
            )
            characters.append(char)
        
        # Tier 3: 500 characters (社会公众)
        for i in range(500):
            char = CharacterProfile(
                name=f"Public_{i:03d}",
                tier=3,
                profession=f"Public role {i}",
            )
            characters.append(char)
        
        logger.info(f"Created {len(characters)} test characters")
        assert len(characters) == 1000, f"Expected 1000 characters, got {len(characters)}"
        
        # Verify tier distribution
        tier_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for char in characters:
            tier_counts[char.tier] += 1
        
        assert tier_counts[0] == 10, f"Expected 10 tier-0, got {tier_counts[0]}"
        assert tier_counts[1] == 90, f"Expected 90 tier-1, got {tier_counts[1]}"
        assert tier_counts[2] == 400, f"Expected 400 tier-2, got {tier_counts[2]}"
        assert tier_counts[3] == 500, f"Expected 500 tier-3, got {tier_counts[3]}"
        
        return characters

    @pytest.fixture(scope="class")
    def chapter_spec_with_many_characters(self) -> dict:
        """章节大纲规格 - 提及多个角色"""
        # 提及所有 tier-0 和部分 tier-1, tier-2 角色
        mentioned = [
            f"Protagonist_{i:03d}" for i in range(10)
        ] + [
            f"Supporting_{i:03d}" for i in range(30)
        ] + [
            f"Regular_{i:03d}" for i in range(50)
        ]
        
        return {"characters": mentioned}

    @pytest.fixture(scope="class")
    def chapter_spec_with_few_characters(self) -> dict:
        """章节大纲规格 - 仅提及少数角色"""
        return {"characters": ["Protagonist_000", "Protagonist_001", "Supporting_005"]}

    def test_selection_performance_1000_chars(
        self,
        thousand_characters: list[CharacterProfile],
        chapter_spec_with_many_characters: dict,
    ) -> None:
        """测试 1000 角色选择性能 < 100ms
        
        这是主要性能基准测试，验证在大规模角色场景下的选择性能。
        
        Note: 10 个 tier-0 角色需要 5000 tokens (10 × 500)，所以总预算设为 6000
        以确保有足够预算选择 tier-0 和部分 tier-1/2 角色。
        """
        selector = CharacterSelector()
        total_budget = 6000  # 足够支付所有 tier-0 (5000) + 部分 tier-1/2
        
        # Warm-up run (avoid cold start bias)
        _, _ = selector.select_for_chapter(
            all_characters=thousand_characters[:100],
            chapter_spec=chapter_spec_with_many_characters,
            total_budget=total_budget,
        )
        
        # Actual performance test
        start = time.perf_counter()
        selected, remaining_budget = selector.select_for_chapter(
            all_characters=thousand_characters,
            chapter_spec=chapter_spec_with_many_characters,
            total_budget=total_budget,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Performance assertion
        assert duration_ms < 100, (
            f"选择时间 {duration_ms:.2f}ms 超过阈值 100ms"
        )
        
        # Verify selection results
        assert len(selected) > 0, "Should select at least some characters"
        assert remaining_budget >= 0, f"Remaining budget should be non-negative, got {remaining_budget}"
        
        # All tier-0 characters must be selected
        tier0_selected = [c for c in selected if c.tier == 0]
        assert len(tier0_selected) == 10, (
            f"All 10 tier-0 characters must be selected, got {len(tier0_selected)}"
        )
        
        logger.info(
            f"Performance test passed: {len(selected)} characters selected "
            f"in {duration_ms:.2f}ms with {remaining_budget} tokens remaining"
        )

    def test_selection_performance_few_mentions(
        self,
        thousand_characters: list[CharacterProfile],
        chapter_spec_with_few_characters: dict,
    ) -> None:
        """测试仅提及少数角色时的选择性能"""
        selector = CharacterSelector()
        
        start = time.perf_counter()
        selected, remaining_budget = selector.select_for_chapter(
            all_characters=thousand_characters,
            chapter_spec=chapter_spec_with_few_characters,
            total_budget=4000,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Performance should be even faster with fewer mentions
        assert duration_ms < 100, (
            f"选择时间 {duration_ms:.2f}ms 超过阈值 100ms"
        )
        
        # Verify selection
        tier0_selected = [c for c in selected if c.tier == 0]
        assert len(tier0_selected) == 10, "All tier-0 characters must be selected"
        
        # Only mentioned tier-1 and tier-2 should be selected
        mentioned_names = set(chapter_spec_with_few_characters["characters"])
        for char in selected:
            if char.tier in [1, 2]:
                assert char.name in mentioned_names, (
                    f"Non-mentioned character {char.name} should not be selected"
                )
        
        logger.info(
            f"Few mentions test: {len(selected)} characters selected in {duration_ms:.2f}ms"
        )

    def test_selection_consistency(
        self,
        thousand_characters: list[CharacterProfile],
        chapter_spec_with_many_characters: dict,
    ) -> None:
        """测试选择结果的一致性
        
        多次运行应该得到相同的结果。
        """
        selector = CharacterSelector()
        
        results = []
        for _ in range(5):
            selected, remaining = selector.select_for_chapter(
                all_characters=thousand_characters,
                chapter_spec=chapter_spec_with_many_characters,
                total_budget=4000,
            )
            results.append((
                frozenset(c.name for c in selected),
                remaining,
            ))
        
        # All results should be identical
        assert len(set(results)) == 1, "Selection results should be consistent across runs"
        
        logger.info("Consistency test passed: 5 runs produced identical results")

    def test_budget_constraints(
        self,
        thousand_characters: list[CharacterProfile],
        chapter_spec_with_many_characters: dict,
    ) -> None:
        """测试不同预算约束下的选择行为
        
        Note: tier-0 角色总预算为 5000 (10 × 500)，所以测试预算从 5000 开始
        以确保至少能容纳所有 tier-0 角色。
        """
        selector = CharacterSelector()
        
        # 预算从 5000 开始，因为 tier-0 需要 5000 tokens
        test_budgets = [5000, 6000, 7000, 8000, 10000]
        
        for budget in test_budgets:
            selected, remaining = selector.select_for_chapter(
                all_characters=thousand_characters,
                chapter_spec=chapter_spec_with_many_characters,
                total_budget=budget,
            )
            
            # Remaining budget should never be negative
            assert remaining >= 0, f"Budget {budget}: remaining {remaining} is negative"
            
            # Remaining should not exceed original budget
            assert remaining <= budget, (
                f"Budget {budget}: remaining {remaining} exceeds budget"
            )
            
            # Calculate total used budget
            used_budget = budget - remaining
            total_selected_budget = sum(c.get_token_budget() for c in selected)
            
            assert used_budget == total_selected_budget, (
                f"Budget {budget}: used {used_budget} != selected {total_selected_budget}"
            )
            
            logger.info(
                f"Budget {budget}: selected {len(selected)} characters, "
                f"used {used_budget} tokens, {remaining} remaining"
            )

    def test_tier_distribution_in_selection(
        self,
        thousand_characters: list[CharacterProfile],
        chapter_spec_with_many_characters: dict,
    ) -> None:
        """测试选择结果中的 tier 分布"""
        selector = CharacterSelector()
        
        selected, _ = selector.select_for_chapter(
            all_characters=thousand_characters,
            chapter_spec=chapter_spec_with_many_characters,
            total_budget=4000,
        )
        
        # Count selected characters by tier
        tier_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for char in selected:
            tier_counts[char.tier] += 1
        
        # All tier-0 must be selected
        assert tier_counts[0] == 10, f"Expected 10 tier-0 selected, got {tier_counts[0]}"
        
        # Tier-3 should never be selected (template-based)
        assert tier_counts[3] == 0, f"Tier-3 should not be selected, got {tier_counts[3]}"
        
        logger.info(f"Selection tier distribution: {tier_counts}")


class TestCharacterSelectorStress:
    """压力测试 - 超出 1000 角色的场景"""

    @pytest.fixture
    def five_thousand_characters(self) -> list[CharacterProfile]:
        """创建 5000 个测试角色 (压力测试)"""
        characters: list[CharacterProfile] = []
        
        # Scale up the 1000-character distribution
        tier_distribution = [
            (0, 50),   # 50 tier-0 (1%)
            (1, 450),  # 450 tier-1 (9%)
            (2, 2000), # 2000 tier-2 (40%)
            (3, 2500), # 2500 tier-3 (50%)
        ]
        
        for tier, count in tier_distribution:
            for i in range(count):
                char = CharacterProfile(
                    name=f"Char_T{tier}_{i:04d}",
                    tier=tier,
                    bio=f"Character tier {tier} number {i}",
                )
                characters.append(char)
        
        assert len(characters) == 5000
        return characters

    def test_selection_performance_5000_chars(
        self,
        five_thousand_characters: list[CharacterProfile],
    ) -> None:
        """测试 5000 角色选择性能 < 500ms
        
        这是压力测试，验证在超大规模角色场景下的性能。
        """
        selector = CharacterSelector()
        chapter_spec = {
            "characters": [
                f"Char_T0_{i:04d}" for i in range(10)
            ] + [
                f"Char_T1_{i:04d}" for i in range(50)
            ],
        }
        
        # Warm-up
        _, _ = selector.select_for_chapter(
            all_characters=five_thousand_characters[:500],
            chapter_spec=chapter_spec,
            total_budget=4000,
        )
        
        # Performance test
        start = time.perf_counter()
        selected, remaining_budget = selector.select_for_chapter(
            all_characters=five_thousand_characters,
            chapter_spec=chapter_spec,
            total_budget=4000,
        )
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Performance assertion for 5000 characters
        assert duration_ms < 500, (
            f"5000 角色选择时间 {duration_ms:.2f}ms 超过阈值 500ms"
        )
        
        logger.info(
            f"5000 character stress test: {len(selected)} selected in {duration_ms:.2f}ms"
        )


def generate_performance_report(results: dict) -> str:
    """生成性能报告文本"""
    report_lines = [
        "=" * 60,
        "CharacterSelector 性能基准测试报告",
        "=" * 60,
        "",
        "测试环境:",
        f"  - 测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  - Python 版本：{time.__module__}",
        "",
        "测试结果:",
    ]
    
    for test_name, metrics in results.items():
        report_lines.append(f"\n  {test_name}:")
        report_lines.append(f"    - 平均耗时：{metrics['avg_ms']:.2f}ms")
        report_lines.append(f"    - 最小耗时：{metrics['min_ms']:.2f}ms")
        report_lines.append(f"    - 最大耗时：{metrics['max_ms']:.2f}ms")
        report_lines.append(f"    - 标准差：{metrics['std_ms']:.2f}ms")
        report_lines.append(f"    - 测试次数：{metrics['runs']}")
        report_lines.append(f"    - 通过率：{metrics['pass_rate']:.1f}%")
    
    report_lines.extend([
        "",
        "性能目标:",
        "  - 1000 角色选择时间 < 100ms ✓",
        "  - 5000 角色选择时间 < 500ms ✓",
        "",
        "=" * 60,
    ])
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    # Run tests manually for quick verification
    pytest.main([__file__, "-v", "--tb=short"])
