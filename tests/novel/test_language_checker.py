"""Tests for language consistency checker in novel writing."""

import pytest
import sys
from pathlib import Path
from enum import Enum

# 在导入前添加 src 到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
src_path = PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.novel_agent.novel.language_checker import LanguageConsistencyChecker, Language


class TestDetectChineseContent:
    """测试中文内容检测 - CJK比例 > 70% = CHINESE"""

    def test_chinese_majority_content(self):
        """测试中文内容占比检测（中文 > 70%）"""
        content = "这是一段中文内容，占比很高。只有少数英文单词here。"
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.CHINESE

    def test_all_chinese_content(self):
        """测试纯中文内容"""
        content = "小说情节跌宕起伏，主角历经磨难，最终获得成功。"
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.CHINESE


class TestDetectEnglishContent:
    """测试英文内容检测 - CJK比例 < 30% = ENGLISH"""

    def test_english_majority_content(self):
        """测试英文内容占比检测（中文 < 30%）"""
        content = "This is a long English content with some 中文 characters here and there."
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.ENGLISH

    def test_all_english_content(self):
        """测试纯英文内容"""
        content = "The novel follows a protagonist who discovers magical abilities."
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.ENGLISH

    def test_english_with_few_chinese_chars(self):
        """测试少量中文字符的英文内容"""
        content = "The book features a character named 李雷 and his adventures."
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.ENGLISH


class TestDetectMixedContent:
    """测试混合内容检测 - CJK比例 30-70% = MIXED"""

    def test_mixed_language_content(self):
        """测试混合语言内容 - CJK ~43%"""
        content = "这是一段中英文混合内容测试。Some English text."
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.MIXED

    def test_alternating_language_content(self):
        """测试交替语言内容 - CJK ~33%"""
        content = "Some text here. 第二段中文内容。"
        checker = LanguageConsistencyChecker()
        assert checker._detect_language(content) == Language.MIXED


class TestLanguageConsistencyPass:
    """测试语言一致性通过场景 - 相同语言章节"""

    def test_same_chinese_chapters_pass(self):
        """测试相同中文章节一致性检查通过"""
        chapters = {
            "chapter_1": "这是第一章内容，中文撰写。",
            "chapter_2": "这是第二章内容，同样使用中文。",
            "chapter_3": "这是第三章内容，保持中文不变。",
        }
        checker = LanguageConsistencyChecker()
        result = checker.check_consistency(chapters)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_same_english_chapters_pass(self):
        """测试相同英文章节一致性检查通过"""
        chapters = {
            "chapter_1": "This is the first chapter in English.",
            "chapter_2": "This is the second chapter, also in English.",
            "chapter_3": "This is the third chapter, English throughout.",
        }
        checker = LanguageConsistencyChecker()
        result = checker.check_consistency(chapters)
        assert result.is_valid is True
        assert len(result.issues) == 0


class TestLanguageConsistencyFail:
    """测试语言一致性失败场景 - 章节语言不一致"""

    def test_mixed_chinese_english_failure(self):
        """测试中英文混合章节一致性检查失败"""
        chapters = {
            "chapter_1": "Chapter one starts in English language.",
            "chapter_2": "第二章内容使用中文撰写。",
        }
        checker = LanguageConsistencyChecker()
        result = checker.check_consistency(chapters)
        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("不一致" in issue or "different" in issue.lower() for issue in result.issues)


class TestFirstChapterNoPrevious:
    """测试首章无比较对象场景"""

    def test_single_chinese_chapter_pass(self):
        """测试单章（章节1）中文内容通过检查"""
        chapters = {"chapter_1": "第一章内容，纯中文写作。"}
        checker = LanguageConsistencyChecker()
        result = checker.check_consistency(chapters)
        assert result.is_valid is True

    def test_single_english_chapter_pass(self):
        """测试单章（章节1）英文内容通过检查"""
        chapters = {"chapter_1": "Chapter one in English language."}
        checker = LanguageConsistencyChecker()
        result = checker.check_consistency(chapters)
        assert result.is_valid is True
