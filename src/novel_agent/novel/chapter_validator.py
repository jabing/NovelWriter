"""Chapter content validator for multi-dimensional validation."""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChapterValidationResult:
    """Result of chapter content validation.

    Attributes:
        is_valid: Whether the chapter passed all validation checks
        issues: List of issues found during validation
        suggestions: List of suggestions for improvement
        word_count: Total word/character count of the content
        has_title: Whether a valid chapter title was found
        has_ending: Whether a valid ending marker was found
    """

    is_valid: bool
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    word_count: int = 0
    has_title: bool = False
    has_ending: bool = False


class ChapterValidator:
    """Validator for checking chapter content completeness.

    This class performs rule-based validation checks on chapter content:
    - Word/character count validation
    - Chapter title presence validation
    - Chapter ending marker validation
    - Combined completeness validation

    Example:
        >>> validator = ChapterValidator()
        >>> result = validator.check_completeness("第一章 开端\\n\\n内容..." * 500 + "\\n\\n完")
        >>> print(result.is_valid)
        True
    """

    # Ending markers (Chinese and English)
    ENDING_MARKERS: list[str] = [
        "完",
        "待续",
        "未完待续",
        "---",
        "TBC",
        "To be continued",
        "THE END",
    ]

    # Chinese numerals (零一二三四五六七八九十百千万亿)
    CHINESE_NUMERALS: str = r"[零一二三四五六七八九十百千万亿\d]+"

    # Title patterns (regex patterns for chapter titles)
    TITLE_PATTERNS: list[str] = [
        rf"第\s*{CHINESE_NUMERALS}\s*章",  # Chinese: 第一章, 第1章, 第 1 章, etc.
        r"Chapter\s*\d+",  # English: Chapter 1, Chapter 2, etc.
    ]

    def __init__(self) -> None:
        """Initialize the chapter validator."""
        # Pre-compile title patterns for efficiency
        self._compiled_title_patterns: list[re.Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in self.TITLE_PATTERNS
        ]

    def check_word_count(self, content: str, min_words: int = 500) -> bool:
        """Check if content has enough words/characters.

        For Chinese content, counts individual characters.
        For English content, counts whitespace-separated words.

        Args:
            content: The chapter content to check
            min_words: Minimum required word/character count

        Returns:
            True if content meets minimum word count, False otherwise
        """
        word_count = self._count_words(content)
        return word_count >= min_words

    def check_ending(self, content: str) -> bool:
        """Check if content has a proper ending marker.

        Looks for ending markers at the end of the content, allowing for
        trailing whitespace and newlines.

        Args:
            content: The chapter content to check

        Returns:
            True if a valid ending marker is found, False otherwise
        """
        # Strip trailing whitespace for checking
        content_stripped = content.rstrip()

        if not content_stripped:
            return False

        # Check for ending markers at the end of content
        for marker in self.ENDING_MARKERS:
            # Check if content ends with the marker (case-insensitive for English)
            if content_stripped.lower().endswith(marker.lower()):
                return True
            # Also check if marker is on its own line near the end
            lines = content_stripped.split("\n")
            for line in reversed(lines[-3:]):  # Check last 3 lines
                if line.strip().lower() == marker.lower():
                    return True

        return False

    def check_title(self, content: str) -> bool:
        """Check if content starts with a valid chapter title.

        Looks for chapter title patterns at the beginning of the content.

        Args:
            content: The chapter content to check

        Returns:
            True if a valid chapter title is found, False otherwise
        """
        if not content:
            return False

        lines = content.split("\n")
        checked_count = 0

        for line in lines[:5]:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            for pattern in self._compiled_title_patterns:
                if pattern.search(line_stripped):
                    return True
            checked_count += 1
            if checked_count >= 3:
                break

        return False

    def check_completeness(self, content: str, min_words: int = 500) -> ChapterValidationResult:
        """Run all validation checks and return combined result.

        Performs word count, title, and ending validation checks, then
        combines results into a single ChapterValidationResult.

        Args:
            content: The chapter content to validate
            min_words: Minimum required word/character count

        Returns:
            ChapterValidationResult with all validation information
        """
        issues: list[str] = []
        suggestions: list[str] = []

        # Count words/characters
        word_count = self._count_words(content)
        has_title = self.check_title(content)
        has_ending = self.check_ending(content)

        # Check word count
        if word_count < min_words:
            issues.append(f"章节数量不足: 当前{word_count}字/词，要求至少{min_words}字/词")
            suggestions.append(f"建议扩展章节内容，增加至少{min_words - word_count}字/词")

        # Check title
        if not has_title:
            issues.append("缺少章节标题")
            suggestions.append("建议添加章节标题，如'第N章 标题'或'Chapter N: Title'")

        # Check ending
        if not has_ending:
            issues.append("缺少章节结束标记")
            suggestions.append("建议添加章节结束标记，如'完'、'待续'或'---'")

        # Determine overall validity
        is_valid = word_count >= min_words and has_title and has_ending

        return ChapterValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            word_count=word_count,
            has_title=has_title,
            has_ending=has_ending,
        )

    def _count_words(self, content: str) -> int:
        """Count words/characters in content.

        For mixed Chinese/English content:
        - Chinese characters are counted individually
        - English words are counted by whitespace separation

        Args:
            content: The content to count

        Returns:
            Total word/character count
        """
        if not content:
            return 0

        # Count Chinese characters (CJK Unified Ideographs range)
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", content))

        # Count English words (sequences of Latin letters)
        english_words = len(re.findall(r"[a-zA-Z]+", content))

        # Total is sum of Chinese characters and English words
        return chinese_chars + english_words
