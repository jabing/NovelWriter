"""Perspective checker for narrative point of view validation.

This module provides tools to detect and validate narrative perspective
(first-person vs third-person) across novel chapters.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Perspective(str, Enum):
    """Narrative perspective categories.

    Categories:
        FIRST_PERSON: First-person narration ("I", "we", "我", "我们", etc.)
        THIRD_PERSON: Third-person narration ("he", "she", "they", "他", "她", etc.)
    """

    FIRST_PERSON = "first_person"
    THIRD_PERSON = "third_person"


@dataclass
class ValidationResult:
    """Result of perspective consistency check across chapters.

    Attributes:
        is_valid: Whether all chapters have consistent perspective
        issues: List of issues found during consistency check
    """

    is_valid: bool
    issues: list[str] = field(default_factory=list)


class NarrativePerspectiveChecker:
    """Checker for narrative perspective consistency across novel chapters.

    Detects the primary narrative perspective of chapter content (first-person
    or third-person) by counting pronoun usage and validates consistency
    across multiple chapters.

    Supports both Chinese and English perspective markers:
    - Chinese: 我/我们/我的 vs 他/她/它/他们/她们/它们
    - English: I/me/my vs he/she/it/they/them/their
    """

    # Chinese first-person pronouns
    CHINESE_FIRST_PERSON: list[str] = [
        "我",
        "我们",
        "我的",
        "我的",
        " myself",
        "我们自己",
        " ourselves",
        "我本人",
        "本人",
    ]

    # Chinese third-person pronouns
    CHINESE_THIRD_PERSON: list[str] = [
        "他",
        "她",
        "它",
        "他们",
        "她们",
        "它们",
        "他的",
        "她的",
        "它的",
        "他们的",
        "她们的",
        "它们的",
        "他本人",
        "她本人",
        "它本人",
    ]

    # English first-person pronouns (case-insensitive matching)
    ENGLISH_FIRST_PERSON: list[str] = [
        "i",
        "me",
        "my",
        "mine",
        "myself",
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
    ]

    # English third-person pronouns (case-insensitive matching)
    ENGLISH_THIRD_PERSON: list[str] = [
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "theirs",
    ]

    def detect_perspective(self, content: str) -> Perspective:
        """Detect the primary narrative perspective of content.

        Counts pronoun occurrences and determines perspective based on
        which type (first-person or third-person) appears more frequently.

        Args:
            content: The text content to analyze

        Returns:
            Perspective category:
            - FIRST_PERSON if first-person pronouns dominate
            - THIRD_PERSON if third-person pronouns dominate
        """
        if not content:
            return Perspective.THIRD_PERSON

        # Count first-person and third-person pronouns
        first_person_count = self._count_first_person(content)
        third_person_count = self._count_third_person(content)

        # Determine perspective based on which is higher
        # When counts are equal, prefer FIRST_PERSON
        if first_person_count > third_person_count:
            return Perspective.FIRST_PERSON
        elif third_person_count > first_person_count:
            return Perspective.THIRD_PERSON
        else:
            # Tie-breaker: prefer FIRST_PERSON when counts are equal
            return Perspective.FIRST_PERSON

    def check_consistency(self, chapters: dict[str, str]) -> ValidationResult:
        """Check perspective consistency across multiple chapters.

        All chapters must have the same perspective as the first chapter
        to be considered consistent.

        Args:
            chapters: Dict mapping chapter_id to chapter content

        Returns:
            ValidationResult with validation status and issues list
        """
        if not chapters:
            return ValidationResult(is_valid=True)

        chapter_perspectives: dict[str, Perspective] = {}
        issues: list[str] = []
        first_chapter_id: str = ""
        expected_perspective: Perspective | None = None

        for chapter_id, content in chapters.items():
            perspective = self.detect_perspective(content)
            chapter_perspectives[chapter_id] = perspective

            if first_chapter_id == "":
                # First chapter: set expected perspective
                first_chapter_id = chapter_id
                expected_perspective = perspective
            elif expected_perspective is not None and expected_perspective != perspective:
                # Subsequent chapter with different perspective
                issue = (
                    f"章节 '{chapter_id}' 视角不一致: "
                    f"预期 {expected_perspective.value}, 实际 {perspective.value}"
                )
                issues.append(issue)

        is_valid = len(issues) == 0

        return ValidationResult(is_valid=is_valid, issues=issues)

    def _count_first_person(self, content: str) -> int:
        """Count first-person pronouns in content.

        Args:
            content: The text content to analyze

        Returns:
            Total count of first-person pronouns
        """
        count = 0

        # Count Chinese first-person pronouns
        for pronoun in self.CHINESE_FIRST_PERSON:
            count += content.count(pronoun)

        # Count English first-person pronouns (case-insensitive)
        content_lower = content.lower()
        for pronoun in self.ENGLISH_FIRST_PERSON:
            # Use word boundary matching for English
            pattern = r"\b" + re.escape(pronoun) + r"\b"
            count += len(re.findall(pattern, content_lower))

        return count

    def _count_third_person(self, content: str) -> int:
        """Count third-person pronouns in content.

        Args:
            content: The text content to analyze

        Returns:
            Total count of third-person pronouns
        """
        count = 0

        # Count Chinese third-person pronouns
        for pronoun in self.CHINESE_THIRD_PERSON:
            count += content.count(pronoun)

        # Count English third-person pronouns (case-insensitive)
        content_lower = content.lower()
        for pronoun in self.ENGLISH_THIRD_PERSON:
            # Use word boundary matching for English
            pattern = r"\b" + re.escape(pronoun) + r"\b"
            count += len(re.findall(pattern, content_lower))

        return count
