import pytest
import sys
from pathlib import Path

# 在导入前添加 src 到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.novel_agent.novel.perspective_checker import NarrativePerspectiveChecker, Perspective


class TestPerspectiveEnum:
    """测试 Perspective 枚举"""

    def test_perspective_enum_values(self):
        """测试 Perspective 枚举值"""
        assert Perspective.FIRST_PERSON.value == "first_person"
        assert Perspective.THIRD_PERSON.value == "third_person"


class TestDetectFirstPersonChinese:
    """检测中文第一人称代词"""

    def test_detect_first_person_chinese(self):
        """检测 '我', '我的', '我看见' → FIRST_PERSON"""
        checker = NarrativePerspectiveChecker()
        content = "我看见了那只猫。这是我的书。"
        result = checker.detect_perspective(content)
        assert result == Perspective.FIRST_PERSON


class TestDetectThirdPersonChinese:
    """检测中文第三人称代词"""

    def test_detect_third_person_chinese(self):
        """检测 '他', '她', '他们' → THIRD_PERSON"""
        checker = NarrativePerspectiveChecker()
        content = "他走向了街道。她跟在他后面。他们一起去了公园。"
        result = checker.detect_perspective(content)
        assert result == Perspective.THIRD_PERSON


class TestDetectFirstPersonEnglish:
    """检测英文第一人称代词"""

    def test_detect_first_person_english(self):
        """检测 'I', 'my', 'me' as subjects → FIRST_PERSON"""
        checker = NarrativePerspectiveChecker()
        content = "I saw the cat. This is my book. He saw me at the store."
        result = checker.detect_perspective(content)
        assert result == Perspective.FIRST_PERSON


class TestDetectThirdPersonEnglish:
    """检测英文第三人称代词"""

    def test_detect_third_person_english(self):
        """检测 'he', 'she', 'they' as subjects → THIRD_PERSON"""
        checker = NarrativePerspectiveChecker()
        content = "He walked down the street. She likes reading. They are in the meeting."
        result = checker.detect_perspective(content)
        assert result == Perspective.THIRD_PERSON


class TestPerspectiveConsistencyPass:
    """透视一致性检查通过场景"""

    def test_perspective_consistency_pass(self):
        """检测相同视角 across chapters → PASS"""
        checker = NarrativePerspectiveChecker()

        chapter_1 = "他走向了街道。她跟在他后面。"
        chapter_2 = "他们一起去了公园。"
        chapter_3 = "他们在那里玩了很久。"

        chapters = {"chapter_1": chapter_1, "chapter_2": chapter_2, "chapter_3": chapter_3}

        result = checker.check_consistency(chapters)
        assert result.is_valid is True
        assert len(result.issues) == 0


class TestPerspectiveConsistencyFail:
    """透视一致性检查失败场景"""

    def test_perspective_consistency_fail(self):
        """检测章节 1 为第三人称、章节 2 为第一人称 → FAIL"""
        checker = NarrativePerspectiveChecker()

        chapter_1 = "他走向了街道。"
        chapter_2 = "我看见了他。"

        chapters = {"chapter_1": chapter_1, "chapter_2": chapter_2}

        result = checker.check_consistency(chapters)
        assert result.is_valid is False
        assert len(result.issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
