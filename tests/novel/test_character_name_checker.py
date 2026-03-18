import pytest
import sys
from pathlib import Path

# 在导入前添加 src 到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.novel_agent.novel.character_name_checker import CharacterNameChecker, CharacterNameResult


# 测试用例：包含主角"艾拉拉/Elara"的中文内容
CHINESE_CONTENT_WITH_ELARA = """
第一章 开端

艾拉拉走进房间，看着窗外的风景。艾拉拉想起了过去的事情。
"你好，"艾拉拉对陌生人说。
"""

# 测试用例：包含主角"Elara"的英文内容
ENGLISH_CONTENT_WITH_ELARA = """
Chapter 1: The Beginning

Elara walked into the room, looking at the scenery outside. Elara remembered the past.
"Hello," Elara said to the stranger.
"""

# 测试用例：主角名不一致的内容
CHINESE_CONTENT_INCONSISTENT = """
第一章 开端

艾拉拉走进房间，看着窗外的风景。

第二章 继续

主角走进房间，看着窗外的风景。
"""

# 测试用例：主角消失的内容
CHINESE_CONTENT_PROTAGONIST_DISAPPEARS = """
第一章 开端

艾拉拉走进房间，看着窗外的风景。艾拉拉想起了过去的事情。

第二章 继续

另一个角色走进房间，看着窗外的风景。
"""


class TestExtractProtagonistName:
    """测试主角名称提取功能"""

    def test_extract_protagonist_name(self) -> None:
        """提取最频繁的主角名称"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四", "王五"]

        result = checker.extract_protagonist_name(CHINESE_CONTENT_WITH_ELARA, character_names)

        assert result.is_valid is True
        assert result.protagonist_name == "艾拉拉"


class TestCharacterNameConsistencyPass:
    """测试主角名称一致性检查 - 通过场景"""

    def test_character_name_consistency_pass(self) -> None:
        """章节间主角名称一致 - 应该通过"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": CHINESE_CONTENT_WITH_ELARA,
        }

        result = checker.check_consistency(chapters, character_names)

        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.protagonist_name == "艾拉拉"


class TestCharacterNameConsistencyFail:
    """测试主角名称一致性检查 - 失败场景"""

    def test_character_name_consistency_fail(self) -> None:
        """第一章有名字"艾拉拉"，第二章未命名 - 应该失败"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": """第二章 继续\n\n主角走进房间，看着窗外的风景。""",
        }

        result = checker.check_consistency(chapters, character_names)

        assert result.is_valid is False
        assert len(result.issues) > 0
        assert result.protagonist_name == "艾拉拉"


class TestCharacterNameDisappears:
    """测试主角消失场景 - 警告而非失败"""

    def test_character_name_disappears(self) -> None:
        """主角名在第一章出现，第二章未出现 - 应该警告"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": """第二章 继续\n\n李四走进房间，看着窗外的风景。""",
        }

        result = checker.check_consistency(chapters, character_names)

        # 应该是警告而非失败
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert result.protagonist_name == "艾拉拉"


class TestSimilarNamesAllowed:
    """测试相似名称允许 - Levenshtein距离 < 2"""

    def test_similar_names_allowed(self) -> None:
        """测试"艾拉拉"与"艾琳娜"相似 - 应该允许"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "艾琳娜", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": """
第二章 继续

艾琳娜走进房间，看着窗外的风景。艾琳娜想起了过去的事情。
""",
        }

        result = checker.check_consistency(chapters, character_names)

        # 相似名称应该被允许
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.protagonist_name in ["艾拉拉", "艾琳娜"]


class TestCharacterProfileValidation:
    """测试角色档案验证"""

    def test_character_profile_validation(self) -> None:
        """验证主角名称在character_names列表中的有效性"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四", "王五"]

        # 验证在列表中的名字
        result1 = checker.validate_character_profile("艾拉拉", character_names)
        assert result1.is_valid is True
        assert result1.protagonist_name == "艾拉拉"
        assert len(result1.issues) == 0

        # 验证不在列表中的名字
        result2 = checker.validate_character_profile("赵六", character_names)
        assert result2.is_valid is False
        assert result2.protagonist_name == "赵六"
        assert len(result2.issues) > 0

        # 空列表处理
        result3 = checker.validate_character_profile("艾拉拉", [])
        assert len(result3.warnings) > 0 or len(result3.issues) > 0


class TestCharacterNameStrictMode:
    """测试角色名严格模式 - 可选阻塞"""

    def test_strict_mode_blocks_on_mismatch(self) -> None:
        """严格模式下主角名不一致应该导致失败"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": """
第二章 继续

李四走进房间，看着窗外的风景。李四想起了过去的事情。
""",
        }

        result = checker.check_consistency(chapters, character_names, strict_mode=True)

        assert result.is_valid is False
        assert len(result.issues) > 0
        assert "主角名称不一致" in result.issues[0]

    def test_non_strict_mode_warns_on_mismatch(self) -> None:
        """非严格模式下主角名不一致只是警告"""
        checker = CharacterNameChecker()
        character_names = ["艾拉拉", "李四"]

        chapters = {
            "chapter_1": CHINESE_CONTENT_WITH_ELARA,
            "chapter_2": """
第二章 继续

李四走进房间，看着窗外的风景。李四想起了过去的事情。
""",
        }

        result = checker.check_consistency(chapters, character_names, strict_mode=False)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "主角名称不一致" in result.warnings[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
