"""Language consistency checker for multi-language novel validation.

This module provides tools to detect and validate language consistency
across novel chapters, ensuring translations maintain consistent language use.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Language(Enum):
    """Language categories for chapter content.

    Categories are determined by CJK character ratio:
    - CHINESE: >70% CJK characters
    - ENGLISH: <30% CJK characters
    - MIXED: 30-70% CJK characters
    """

    CHINESE = "chinese"
    ENGLISH = "english"
    MIXED = "mixed"


@dataclass
class ChapterLanguageResult:
    """Result of language detection for a chapter.

    Attributes:
        chapter_id: Identifier of the chapter
        detected_language: Detected language category
        cjk_ratio: Ratio of CJK characters to total content
        is_consistent: Whether this chapter's language matches the expected
    """

    chapter_id: str
    detected_language: Language
    cjk_ratio: float
    is_consistent: bool = True


@dataclass
class LanguageConsistencyResult:
    """Result of language consistency check across chapters.

    Attributes:
        is_valid: Whether all chapters have consistent language
        issues: List of issues found during consistency check
        suggestions: List of suggestions for improvement
        chapter_results: Per-chapter language detection results
    """

    is_valid: bool
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    chapter_results: dict[str, ChapterLanguageResult] = field(default_factory=dict)


class LanguageConsistencyChecker:
    """Checker for language consistency across novel chapters.

    Detects the primary language of chapter content and validates
    consistency across multiple chapters to prevent language switching.

    CJK character range: U+4E00-U+9FFF (Kangxi Radicals and CJK Unified Ideographs)
    """

    # CJK Unified Ideographs range (U+4E00 to U+9FFF)
    CJK_PATTERN: re.Pattern[str] = re.compile(r"[\u4e00-\u9fff]")

    def _detect_language(self, content: str) -> Language:
        """Detect the primary language of content.

        Args:
            content: The text content to analyze

        Returns:
            Language category based on CJK character ratio:
            - CHINESE: >70% CJK characters
            - ENGLISH: <30% CJK characters
            - MIXED: 30-70% CJK characters
        """
        if not content:
            return Language.ENGLISH

        cjk_count = len(self.CJK_PATTERN.findall(content))

        total_chars = len(re.sub(r"\s", "", content))

        if total_chars == 0:
            return Language.ENGLISH

        cjk_ratio = cjk_count / total_chars

        if cjk_ratio > 0.7:
            return Language.CHINESE
        elif cjk_ratio < 0.3:
            return Language.ENGLISH
        else:
            return Language.MIXED

    def detect_language(self, content: str) -> Language:
        """Public method to detect the primary language of content.

        Args:
            content: The text content to analyze

        Returns:
            Language category based on CJK character ratio.
        """
        return self._detect_language(content)

    def check_consistency(self, chapters: dict[str, str]) -> LanguageConsistencyResult:
        """Check language consistency across multiple chapters.

        The first chapter always passes (no previous chapter to compare).
        Subsequent chapters are compared against the first chapter's language.

        Args:
            chapters: Dict mapping chapter_id to chapter content

        Returns:
            LanguageConsistencyResult with validation results
        """
        if not chapters:
            return LanguageConsistencyResult(is_valid=True)

        chapter_results: dict[str, ChapterLanguageResult] = {}
        issues: list[str] = []
        suggestions: list[str] = []
        expected_language: Language = Language.ENGLISH
        first_chapter_id: str = "unknown"

        for chapter_id, content in chapters.items():
            detected_language = self._detect_language(content)
            cjk_ratio = self._calculate_cjk_ratio(content)

            # Determine consistency
            is_consistent = True
            if first_chapter_id == "unknown":
                # First chapter: set expected language, always pass
                first_chapter_id = chapter_id
                expected_language = detected_language
            elif expected_language != detected_language:
                # Subsequent chapter with different language
                is_consistent = False

                # Add issue and suggestion
                issue = (
                    f"章节 '{chapter_id}' 语言不一致: "
                    f"预期 {expected_language.value}, 实际 {detected_language.value}"
                )
                issues.append(issue)

                suggestion = (
                    f"建议章节 '{chapter_id}' 保持与 '{first_chapter_id}' "
                    f"相同的语言风格 ({expected_language.value})"
                )
                suggestions.append(suggestion)

            chapter_results[chapter_id] = ChapterLanguageResult(
                chapter_id=chapter_id,
                detected_language=detected_language,
                cjk_ratio=cjk_ratio,
                is_consistent=is_consistent,
            )

        is_valid = len(issues) == 0

        return LanguageConsistencyResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            chapter_results=chapter_results,
        )

    def _calculate_cjk_ratio(self, content: str) -> float:
        """Calculate the ratio of CJK characters in content.

        Args:
            content: The text content to analyze

        Returns:
            Ratio of CJK characters (0.0 to 1.0)
        """
        if not content:
            return 0.0

        cjk_count = len(self.CJK_PATTERN.findall(content))
        total_chars = len(re.sub(r"\s", "", content))

        if total_chars == 0:
            return 0.0

        return cjk_count / total_chars
