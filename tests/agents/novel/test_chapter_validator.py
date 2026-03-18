"""Tests for ChapterValidator class."""

import pytest

from src.novel_agent.novel.chapter_validator import (
    ChapterValidationResult,
    ChapterValidator,
)


class TestChapterValidationResult:
    """Test ChapterValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a ChapterValidationResult."""
        result = ChapterValidationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            word_count=500,
            has_title=True,
            has_ending=True,
        )

        assert result.is_valid is True
        assert result.issues == []
        assert result.suggestions == []
        assert result.word_count == 500
        assert result.has_title is True
        assert result.has_ending is True

    def test_result_defaults(self):
        """Test ChapterValidationResult with defaults."""
        result = ChapterValidationResult(is_valid=False)

        assert result.issues == []
        assert result.suggestions == []
        assert result.word_count == 0
        assert result.has_title is False
        assert result.has_ending is False

    def test_result_with_issues(self):
        """Test result with issues."""
        result = ChapterValidationResult(
            is_valid=False,
            issues=["Missing title", "Too short"],
            suggestions=["Add a title", "Write more content"],
        )

        assert result.is_valid is False
        assert len(result.issues) == 2
        assert len(result.suggestions) == 2


class TestChapterValidatorInit:
    """Test ChapterValidator initialization."""

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = ChapterValidator()

        assert isinstance(validator.ENDING_MARKERS, list)
        assert "完" in validator.ENDING_MARKERS
        assert "待续" in validator.ENDING_MARKERS
        assert "TBC" in validator.ENDING_MARKERS

        assert isinstance(validator.TITLE_PATTERNS, list)
        assert len(validator._compiled_title_patterns) == len(validator.TITLE_PATTERNS)


class TestCheckWordCount:
    """Test check_word_count method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ChapterValidator()

    def test_chinese_content_meets_minimum(self, validator):
        """Test Chinese content meets minimum word count."""
        content = "内容" * 600  # 600 Chinese characters
        assert validator.check_word_count(content, min_words=500) is True

    def test_chinese_content_below_minimum(self, validator):
        """Test Chinese content below minimum word count."""
        content = "内容" * 100  # 100 Chinese characters
        assert validator.check_word_count(content, min_words=500) is False

    def test_english_content_meets_minimum(self, validator):
        """Test English content meets minimum word count."""
        content = "word " * 600  # 600 English words
        assert validator.check_word_count(content, min_words=500) is True

    def test_english_content_below_minimum(self, validator):
        """Test English content below minimum word count."""
        content = "word " * 100  # 100 English words
        assert validator.check_word_count(content, min_words=500) is False

    def test_mixed_content_count(self, validator):
        """Test mixed Chinese and English content count."""
        # 300 Chinese chars + 300 English words = 600 total
        content = "内容" * 300 + " " + "word " * 300
        assert validator.check_word_count(content, min_words=500) is True

    def test_empty_content(self, validator):
        """Test empty content."""
        assert validator.check_word_count("", min_words=500) is False

    def test_custom_minimum(self, validator):
        """Test custom minimum word count."""
        content = "内容" * 150  # 300 Chinese characters
        assert validator.check_word_count(content, min_words=200) is True
        assert validator.check_word_count(content, min_words=500) is False


class TestCheckEnding:
    """Test check_ending method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ChapterValidator()

    def test_chinese_ending_marker_wan(self, validator):
        """Test Chinese ending marker '完'."""
        content = "这是一段内容。\n\n完"
        assert validator.check_ending(content) is True

    def test_chinese_ending_marker_daixu(self, validator):
        """Test Chinese ending marker '待续'."""
        content = "故事还在继续...\n待续"
        assert validator.check_ending(content) is True

    def test_chinese_ending_marker_weiwan_daixu(self, validator):
        """Test Chinese ending marker '未完待续'."""
        content = "未完待续"
        assert validator.check_ending(content) is True

    def test_separator_ending(self, validator):
        """Test separator ending '---'."""
        content = "内容结束\n---"
        assert validator.check_ending(content) is True

    def test_english_ending_tbc(self, validator):
        """Test English ending marker 'TBC'."""
        content = "The story continues...\n\nTBC"
        assert validator.check_ending(content) is True

    def test_english_ending_to_be_continued(self, validator):
        """Test English ending marker 'To be continued'."""
        content = "The hero walked away.\n\nTo be continued"
        assert validator.check_ending(content) is True

    def test_english_ending_the_end(self, validator):
        """Test English ending marker 'THE END'."""
        content = "They lived happily ever after.\n\nTHE END"
        assert validator.check_ending(content) is True

    def test_no_ending_marker(self, validator):
        """Test content without ending marker."""
        content = "这是一段没有结束标记的内容。"
        assert validator.check_ending(content) is False

    def test_ending_with_trailing_whitespace(self, validator):
        """Test ending marker with trailing whitespace."""
        content = "内容\n\n完   \n\n  "
        assert validator.check_ending(content) is True

    def test_empty_content(self, validator):
        """Test empty content."""
        assert validator.check_ending("") is False


class TestCheckTitle:
    """Test check_title method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ChapterValidator()

    def test_chinese_title_with_number(self, validator):
        """Test Chinese title with number '第一章'."""
        content = "第一章 开端\n\n正文内容..."
        assert validator.check_title(content) is True

    def test_chinese_title_with_spaces(self, validator):
        """Test Chinese title with spaces '第 1 章'."""
        content = "第 1 章  测试标题\n\n内容"
        assert validator.check_title(content) is True

    def test_chinese_title_larger_number(self, validator):
        """Test Chinese title with larger number '第100章'."""
        content = "第100章 大结局\n\n最后的决战..."
        assert validator.check_title(content) is True

    def test_english_title(self, validator):
        """Test English title 'Chapter 1'."""
        content = "Chapter 1: The Beginning\n\nThe story starts..."
        assert validator.check_title(content) is True

    def test_english_title_lowercase(self, validator):
        """Test English title in lowercase."""
        content = "chapter 1\n\nContent..."
        assert validator.check_title(content) is True

    def test_english_title_with_number(self, validator):
        """Test English title with number."""
        content = "Chapter 42: The Answer\n\nContent..."
        assert validator.check_title(content) is True

    def test_no_title(self, validator):
        """Test content without title."""
        content = "这是没有标题的一章，直接开始内容。"
        assert validator.check_title(content) is False

    def test_title_after_blank_lines(self, validator):
        """Test title after blank lines."""
        content = "\n\n第一章 测试\n\n内容"
        assert validator.check_title(content) is True

    def test_empty_content(self, validator):
        """Test empty content."""
        assert validator.check_title("") is False


class TestCheckCompleteness:
    """Test check_completeness method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ChapterValidator()

    def test_valid_chapter_passes(self, validator):
        """Test a valid chapter passes all checks."""
        # "内容" is 2 chars, so "内容" * 300 = 600 chars
        content = "第一章 开端\n\n" + "内容" * 300 + "\n\n完"
        result = validator.check_completeness(content)

        assert result.is_valid is True
        # Title (5 chars) + content (600 chars) + ending (1 char) = 606 chars
        assert result.word_count >= 500
        assert result.has_title is True
        assert result.has_ending is True
        assert len(result.issues) == 0

    def test_short_chapter_fails(self, validator):
        """Test short chapter fails validation."""
        content = "第一章\n\n" + "内容" * 100
        result = validator.check_completeness(content, min_words=500)

        assert result.is_valid is False
        # Title (3 chars) + content (200 chars) = 203, but still under 500
        assert result.word_count < 500
        assert "字数" in str(result.issues) or "字/词" in str(result.issues)

    def test_missing_title_fails(self, validator):
        """Test missing title fails validation."""
        content = "内容" * 600 + "\n\n完"
        result = validator.check_completeness(content)

        assert result.is_valid is False
        assert result.has_title is False
        assert "标题" in str(result.issues)

    def test_missing_ending_fails(self, validator):
        """Test missing ending fails validation."""
        content = "第一章 开端\n\n" + "内容" * 600
        result = validator.check_completeness(content)

        assert result.is_valid is False
        assert result.has_ending is False
        assert "结束标记" in str(result.issues)

    def test_multiple_issues(self, validator):
        """Test chapter with multiple issues."""
        content = "内容" * 100  # No title, no ending, too short
        result = validator.check_completeness(content, min_words=500)

        assert result.is_valid is False
        assert len(result.issues) == 3
        assert len(result.suggestions) == 3

    def test_english_valid_chapter(self, validator):
        """Test valid English chapter."""
        content = "Chapter 1: The Beginning\n\n" + "word " * 600 + "\n\nTHE END"
        result = validator.check_completeness(content)

        assert result.is_valid is True
        # 600 words + "Chapter" + "THE" + "END" + "The" + "Beginning" = 605
        assert result.word_count >= 600
        assert result.has_title is True
        assert result.has_ending is True

    def test_custom_min_words(self, validator):
        """Test custom minimum word count."""
        content = "第一章 测试\n\n" + "内容" * 150 + "\n\n完"  # 300 + 5 chars
        result = validator.check_completeness(content, min_words=200)

        assert result.is_valid is True

        result2 = validator.check_completeness(content, min_words=500)
        assert result2.is_valid is False

    def test_suggestions_provided(self, validator):
        """Test that suggestions are provided for issues."""
        content = "内容" * 100
        result = validator.check_completeness(content)

        assert len(result.suggestions) > 0
        assert any("建议" in s for s in result.suggestions)


class TestCountWords:
    """Test _count_words helper method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ChapterValidator()

    def test_chinese_only(self, validator):
        """Test counting Chinese characters only."""
        content = "这是一段中文内容"
        assert validator._count_words(content) == 8

    def test_english_only(self, validator):
        """Test counting English words only."""
        content = "This is English content"
        assert validator._count_words(content) == 4

    def test_mixed_content(self, validator):
        """Test counting mixed Chinese and English."""
        content = "这是Chinese mixed内容"
        # 4 Chinese chars + 2 English words = 6
        assert validator._count_words(content) == 6

    def test_empty_string(self, validator):
        """Test empty string returns zero."""
        assert validator._count_words("") == 0

    def test_whitespace_only(self, validator):
        """Test whitespace only returns zero."""
        assert validator._count_words("   \n\t  ") == 0

    def test_numbers_not_counted_separately(self, validator):
        """Test that standalone numbers are not counted as words."""
        content = "123 456 789"
        # No Chinese chars or English letters
        assert validator._count_words(content) == 0

    def test_punctuation_not_counted(self, validator):
        """Test that punctuation is not counted."""
        content = "内容，。！？"
        assert validator._count_words(content) == 2  # Only Chinese characters
