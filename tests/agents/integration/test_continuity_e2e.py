"""E2E test for continuity validation across chapters.

This test validates the full continuity checking pipeline:
1. Language consistency (Chinese vs English)
2. Narrative perspective (first-person vs third-person)
3. Character name consistency

All tests use mock data - no real LLM API calls.
"""

import pytest

from src.novel_agent.novel.continuity_validator import (
    ContinuityContext,
    ContinuityValidationResult,
    ContinuityValidator,
)
from src.novel_agent.novel.character_name_checker import CharacterNameChecker


# Sample test content - Chinese third person with protagonist "艾拉拉"
CHINESE_THIRD_PERSON_CH1 = """
第一章 开端

艾拉拉走进房间，看着窗外的风景。她想起了过去的事情。

"你好，"艾拉拉对陌生人说。

天空中的云彩慢慢飘过，阳光洒在她的脸上。艾拉拉深吸一口气，
感受着清新的空气。她知道，今天将会是特别的一天。

陌生人点了点头，然后离开了。艾拉拉站在窗前，思考着未来。

她转身走出了房间。
"""

CHINESE_THIRD_PERSON_CH2 = """
第二章 相遇

艾拉拉走在街道上，看着周围的人群。她看到了一个熟悉的身影。

"是你吗？"艾拉拉问道。

那个人转过身来，露出了微笑。艾拉拉感到很惊讶，她没有想到
会在这里遇到老朋友。

他们一起走进了咖啡馆，开始聊起了往事。艾拉拉听着对方的讲述，
心中涌起一股暖流。

她意识到，命运有时候真的很奇妙。
"""

CHINESE_THIRD_PERSON_CH3 = """
第三章 抉择

艾拉拉站在十字路口，思考着该往哪个方向走。她的心中充满了困惑。

左侧是熟悉的道路，右侧则是未知的冒险。艾拉拉知道，无论选择哪条路，
都将改变她的人生。

"我应该怎么做？"她自言自语道。

就在这时，一阵风吹过，带来了远方的气息。艾拉拉闭上眼睛，
感受着风的指引。

当她再次睁开眼睛时，她已经做出了决定。
"""

CHINESE_THIRD_PERSON_CH4 = """
第四章 旅程

艾拉拉背起行囊，开始了她的旅程。她知道前方的道路不会平坦，
但她已经准备好了。

路上，她遇到了许多有趣的人。有一位老者告诉她关于远方的传说，
有一个小女孩送给她一朵小花。

艾拉拉把这些都记在了心里。她知道，这些都是珍贵的回忆。

夜幕降临，艾拉拉找了一处安静的地方休息。她看着满天的星星，
期待着明天的到来。
"""

CHINESE_THIRD_PERSON_CH5 = """
第五章 到达

经过几天的旅行，艾拉拉终于到达了目的地。眼前的景象让她惊叹不已。

高耸的山峰，清澈的溪流，还有那片美丽的花海。艾拉拉感到
所有的辛苦都是值得的。

她走进花海中，感受着花朵的芬芳。蝴蝶在她身边飞舞，
鸟儿在枝头歌唱。

艾拉拉微笑着，她知道这就是她一直在寻找的地方。
"""

# English content - for language mismatch test
ENGLISH_THIRD_PERSON = """
Chapter 1: The Beginning

Elara walked into the room, looking at the scenery outside. She remembered the past.

"Hello," Elara said to the stranger.

The clouds drifted slowly across the sky, and sunlight fell on her face.
Elara took a deep breath, feeling the fresh air. She knew today would be special.

The stranger nodded and then left. Elara stood by the window, thinking about the future.

She turned and walked out of the room.
"""

# Chinese first-person content - for perspective mismatch test
CHINESE_FIRST_PERSON = """
第一章 故事开始

我走进房间，看着窗外的风景。我回想起过去发生的事情。

"你好，"我对陌生人说。

天空中的云彩慢慢飘过，阳光洒在我的脸上。我深吸一口气，
感受着清新的空气。我知道，今天将会是特别的一天。

陌生人点了点头，然后离开了。我站在窗前，思考着未来。

我转身走出了房间。
"""

# Chapter without protagonist "艾拉拉" - for character mismatch warning
CHINESE_THIRD_PERSON_NO_PROTAGONIST = """
第二章 新的开始

城市里的人们匆匆忙忙地走过。街道两旁的商店闪烁着霓虹灯。

一个年轻人站在路口，看着来来往往的人群。他不知道自己该去哪里。

"生活真是复杂，"他自言自语道。

风吹过，带来了远处花朵的香气。年轻人深吸一口气，
决定继续向前走。

天空中，一只鸟儿飞过，留下一道优美的弧线。
"""


class TestContinuityE2E:
    """End-to-end tests for continuity validation."""

    @pytest.fixture
    def validator(self) -> ContinuityValidator:
        """Create a ContinuityValidator instance."""
        return ContinuityValidator()

    @pytest.fixture
    def character_names(self) -> list[str]:
        """List of valid character names."""
        return ["艾拉拉", "陌生人", "老者", "小女孩", "年轻人"]

    def test_e2e_consistent_chapters_pass(
        self,
        validator: ContinuityValidator,
        character_names: list[str],
    ) -> None:
        """Test that 5 consistent chapters pass validation.

        All chapters are:
        - Chinese language (high CJK ratio)
        - Third person perspective
        - Feature protagonist "艾拉拉"
        """
        chapters = [
            CHINESE_THIRD_PERSON_CH1,
            CHINESE_THIRD_PERSON_CH2,
            CHINESE_THIRD_PERSON_CH3,
            CHINESE_THIRD_PERSON_CH4,
            CHINESE_THIRD_PERSON_CH5,
        ]

        previous: str | None = None
        results: list[ContinuityValidationResult] = []

        for i, chapter in enumerate(chapters, start=1):
            context = ContinuityContext(
                chapter_number=i,
                character_names=character_names,
                expected_language="chinese",
                expected_perspective="third_person",
            )

            result = validator.validate_chapter(
                current=chapter,
                previous=previous,
                context=context,
            )

            results.append(result)
            previous = chapter

        # All chapters should pass validation
        for i, result in enumerate(results, start=1):
            assert result.is_valid, f"Chapter {i} failed: {result.issues}"
            assert result.language_valid, f"Chapter {i} language check failed"
            assert result.perspective_valid, f"Chapter {i} perspective check failed"
            # Character check should also pass (protagonist present)
            assert result.character_valid, f"Chapter {i} character check failed: {result.issues}"

    def test_e2e_language_mismatch_blocks(
        self,
        validator: ContinuityValidator,
        character_names: list[str],
    ) -> None:
        """Test that language mismatch between chapters blocks validation.

        Chapter 1: Chinese (high CJK ratio)
        Chapter 2: English (low CJK ratio)
        Expected: Validation fails with language issue
        """
        # Chapter 1 - Chinese
        context1 = ContinuityContext(
            chapter_number=1,
            character_names=character_names,
            expected_language="chinese",
        )
        result1 = validator.validate_chapter(
            current=CHINESE_THIRD_PERSON_CH1,
            previous=None,
            context=context1,
        )
        # First chapter always passes (no comparison)
        assert result1.is_valid
        assert result1.language_valid

        # Chapter 2 - English (language mismatch!)
        context2 = ContinuityContext(
            chapter_number=2,
            character_names=character_names,
            expected_language="chinese",
        )
        result2 = validator.validate_chapter(
            current=ENGLISH_THIRD_PERSON,
            previous=CHINESE_THIRD_PERSON_CH1,
            context=context2,
        )

        # Should fail due to language mismatch
        assert not result2.is_valid, "Expected validation to fail due to language mismatch"
        assert not result2.language_valid, "Expected language check to fail"
        # Verify language issue is in the issues list
        assert len(result2.issues) > 0, "Expected language issue in issues list"
        assert any("语言" in issue or "language" in issue.lower() for issue in result2.issues)

    def test_e2e_perspective_mismatch_blocks(
        self,
        validator: ContinuityValidator,
        character_names: list[str],
    ) -> None:
        """Test that perspective mismatch between chapters blocks validation.

        Chapter 1: Third person (她/艾拉拉)
        Chapter 2: First person (我/我的)
        Expected: Validation fails with perspective issue
        """
        # Chapter 1 - Third person
        context1 = ContinuityContext(
            chapter_number=1,
            character_names=character_names,
            expected_perspective="third_person",
        )
        result1 = validator.validate_chapter(
            current=CHINESE_THIRD_PERSON_CH1,
            previous=None,
            context=context1,
        )
        # First chapter always passes
        assert result1.is_valid
        assert result1.perspective_valid

        # Chapter 2 - First person (perspective mismatch!)
        context2 = ContinuityContext(
            chapter_number=2,
            character_names=character_names,
            expected_perspective="third_person",
        )
        result2 = validator.validate_chapter(
            current=CHINESE_FIRST_PERSON,
            previous=CHINESE_THIRD_PERSON_CH1,
            context=context2,
        )

        # Should fail due to perspective mismatch
        assert not result2.is_valid, "Expected validation to fail due to perspective mismatch"
        assert not result2.perspective_valid, "Expected perspective check to fail"
        # Verify perspective issue is in the issues list
        assert len(result2.issues) > 0, "Expected perspective issue in issues list"
        assert any("视角" in issue or "perspective" in issue.lower() for issue in result2.issues)

    def test_e2e_character_mismatch_warns(
        self,
        validator: ContinuityValidator,
        character_names: list[str],
    ) -> None:
        """Test that character name validation works correctly.

        Note: ContinuityValidator.validate_chapter only passes the current chapter
        to CharacterNameChecker (not previous chapters), so it validates that
        character names exist in the content, not cross-chapter consistency.

        This test verifies:
        1. Chapter with known character names passes validation
        2. Chapter with only one character also passes (any valid character is ok)
        """
        # Chapter 1 - Has protagonist "艾拉拉"
        context1 = ContinuityContext(
            chapter_number=1,
            character_names=character_names,
        )
        result1 = validator.validate_chapter(
            current=CHINESE_THIRD_PERSON_CH1,
            previous=None,
            context=context1,
        )
        assert result1.is_valid
        assert result1.character_valid

        # Chapter 2 - Has different character "年轻人" (still valid - it's in character_names)
        context2 = ContinuityContext(
            chapter_number=2,
            character_names=character_names,
        )
        result2 = validator.validate_chapter(
            current=CHINESE_THIRD_PERSON_NO_PROTAGONIST,
            previous=CHINESE_THIRD_PERSON_CH1,
            context=context2,
        )

        # Both chapters should pass - CharacterNameChecker validates per-chapter
        # that character names exist, not cross-chapter consistency
        assert result2.is_valid, "Expected validation to pass (valid character names present)"
        assert result2.character_valid, "Expected character check to pass"

    def test_e2e_character_name_checker_cross_chapter_warning(
        self,
        character_names: list[str],
    ) -> None:
        """Test CharacterNameChecker's cross-chapter consistency warning.

        This test directly uses CharacterNameChecker to demonstrate that:
        1. When protagonist disappears completely (no names) -> ISSUE (fail)
        2. When different protagonist appears -> WARNING (pass)

        Note: ContinuityValidator passes only current chapter to CharacterNameChecker.
        To get cross-chapter consistency checks, CharacterNameChecker must be used
        directly with multiple chapters.
        """
        checker = CharacterNameChecker()

        # Scenario 1: Protagonist disappears (no character names at all)
        # This should generate an ISSUE, not a warning
        chapters_with_disappearance = {
            "chapter_1": CHINESE_THIRD_PERSON_CH1,  # Has "艾拉拉"
            "chapter_2": "这是一段没有任何角色名称的内容。天空很蓝，云很白。",  # No names
        }

        result_disappear = checker.check_consistency(
            chapters=chapters_with_disappearance,
            character_names=character_names,
        )

        # Missing protagonist is an ISSUE (fail)
        assert not result_disappear.is_valid, "Expected failure when protagonist disappears"
        assert len(result_disappear.issues) > 0, "Expected issue for missing protagonist"
        assert any("艾拉拉" in issue and "未出现" in issue for issue in result_disappear.issues)

        # Scenario 2: Different protagonist appears (protagonist changes)
        # This should generate a WARNING, not an issue
        chapters_with_different = {
            "chapter_1": CHINESE_THIRD_PERSON_CH1,  # Has "艾拉拉"
            "chapter_2": CHINESE_THIRD_PERSON_NO_PROTAGONIST,  # Has "年轻人" instead
        }

        result_different = checker.check_consistency(
            chapters=chapters_with_different,
            character_names=character_names,
        )

        # Different protagonist is a WARNING (pass)
        assert result_different.is_valid, (
            "Expected pass when different protagonist appears (warning only)"
        )
        assert len(result_different.warnings) > 0, "Expected warning for different protagonist"
        assert any("艾拉拉" in warning for warning in result_different.warnings), (
            "Expected warning to mention original protagonist"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
