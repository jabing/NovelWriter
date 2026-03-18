"""Character name checker for novel validation.

This module provides tools to verify character name consistency across chapters,
ensuring protagonist names are used consistently and valid character profiles exist.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CharacterNameResult:
    """Result of character name validation.

    Attributes:
        is_valid: Whether the character name validation passed
        protagonist_name: The detected protagonist name (if any)
        issues: List of critical issues found
        warnings: List of non-critical warnings
    """

    is_valid: bool
    protagonist_name: str | None = None
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CharacterNameChecker:
    """Checker for character name consistency across novel chapters.

    Validates:
    - Protagonist name extraction from content
    - Name consistency across multiple chapters
    - Character profile validation against known names

    Uses Levenshtein distance < 2 for fuzzy name matching to allow
    similar names (typos, alternate spellings).
    """

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance between the two strings
        """
        if not s1:
            return len(s2)
        if not s2:
            return len(s1)

        # Create distance matrix
        rows = len(s1) + 1
        cols = len(s2) + 1
        dp = [[0] * cols for _ in range(rows)]

        # Initialize first row and column
        for i in range(rows):
            dp[i][0] = i
        for j in range(cols):
            dp[0][j] = j

        # Fill the matrix
        for i in range(1, rows):
            for j in range(1, cols):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,  # deletion
                        dp[i][j - 1] + 1,  # insertion
                        dp[i - 1][j - 1] + 1,  # substitution
                    )

        return dp[rows - 1][cols - 1]

    def _are_similar_names(self, name1: str, name2: str) -> bool:
        distance = self._levenshtein_distance(name1, name2)
        return distance < 2

    def _extract_names_from_content(self, content: str, character_names: list[str]) -> list[str]:
        """Extract all occurrences of character names from content.

        Args:
            content: Text content to search
            character_names: List of valid character names to look for

        Returns:
            List of names found (may contain duplicates)
        """
        found_names = []
        for name in character_names:
            if not name:
                continue
            # Count ALL occurrences, not just presence
            count = len(re.findall(re.escape(name), content))
            found_names.extend([name] * count)
        return found_names

    def _get_most_frequent_name(self, names: list[str]) -> str | None:
        """Get the most frequently occurring name from a list.

        Args:
            names: List of names (may contain duplicates)

        Returns:
            Most frequent name, or None if list is empty
        """
        if not names:
            return None

        name_counts: dict[str, int] = {}
        for name in names:
            name_counts[name] = name_counts.get(name, 0) + 1

        # Return name with highest count
        return max(name_counts.keys(), key=lambda x: name_counts[x])  # type: ignore[call-overload]

    def extract_protagonist_name(
        self, content: str, character_names: list[str]
    ) -> CharacterNameResult:
        """Extract the protagonist name from content.

        Finds the most frequently mentioned character name from the
        character_names list in the given content.

        Args:
            content: Text content to analyze
            character_names: List of valid character names

        Returns:
            CharacterNameResult with protagonist name if found
        """
        if not content or not character_names:
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=None,
                warnings=["No content or character names provided"],
            )

        found_names = self._extract_names_from_content(content, character_names)

        if not found_names:
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=None,
                warnings=["No character names found in content"],
            )

        protagonist_name = self._get_most_frequent_name(found_names)

        return CharacterNameResult(
            is_valid=True,
            protagonist_name=protagonist_name,
            issues=[],
            warnings=[],
        )

    def check_consistency(
        self, chapters: dict[str, str], character_names: list[str], strict_mode: bool = False
    ) -> CharacterNameResult:
        """Check character name consistency across chapters.

        Validates that the protagonist name remains consistent across
        all chapters. A warning is issued if the protagonist name
        disappears, but it's only a failure if a different character
        replaces the protagonist.

        Args:
            chapters: Dict mapping chapter_id to chapter content
            character_names: List of valid character names
            strict_mode: If True, protagonist name mismatch causes failure (blocking)

        Returns:
            CharacterNameResult with validation status
        """
        if not chapters or not character_names:
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=None,
                warnings=["No chapters or character names provided"],
            )

        issues: list[str] = []
        warnings: list[str] = []
        expected_protagonist: str | None = None

        chapter_names: dict[str, list[str]] = {}
        name_counts: dict[str, int] = {}

        # Extract names from each chapter
        for chapter_id, content in chapters.items():
            found = self._extract_names_from_content(content, character_names)
            chapter_names[chapter_id] = found

            for name in found:
                name_counts[name] = name_counts.get(name, 0) + 1

        # Determine expected protagonist from first chapter with names
        first_chapter_with_names: str | None = None
        for chapter_id, names in chapter_names.items():
            if names:
                first_chapter_with_names = chapter_id
                expected_protagonist = self._get_most_frequent_name(names)
                break

        # If no names found anywhere, return with warning
        if expected_protagonist is None:
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=None,
                warnings=["No character names found in any chapter"],
            )

        # Check each chapter for consistency
        for chapter_id, names in chapter_names.items():
            if not names:
                # No names in this chapter - FAIL if protagonist name was not found
                # because the protagonist is missing from the chapter
                if expected_protagonist:
                    issues.append(f"章节 '{chapter_id}' 中主角 '{expected_protagonist}' 未出现")
                continue

            latest_name = self._get_most_frequent_name(names)

            # Check if this is the expected protagonist or similar
            if latest_name is None:
                continue
            is_same = latest_name == expected_protagonist or self._are_similar_names(
                latest_name, expected_protagonist or ""
            )

            if not is_same:
                msg = (
                    f"章节 '{chapter_id}' 中主角名称不一致: "
                    f"预期 '{expected_protagonist}', 实际 '{latest_name}'"
                )
                if strict_mode:
                    issues.append(msg)
                else:
                    warnings.append(msg)

        # If we have issues, mark as invalid
        is_valid = len(issues) == 0

        return CharacterNameResult(
            is_valid=is_valid,
            protagonist_name=expected_protagonist,
            issues=issues,
            warnings=warnings,
        )

    def validate_character_profile(
        self, name: str, character_names: list[str]
    ) -> CharacterNameResult:
        """Validate that a character name exists in the character list.

        Args:
            name: Character name to validate
            character_names: List of valid character names

        Returns:
            CharacterNameResult with validation status
        """
        if not character_names:
            return CharacterNameResult(
                is_valid=False,
                protagonist_name=name,
                issues=["Character names list is empty"],
            )

        # Check for exact match
        if name in character_names:
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=name,
                issues=[],
            )

        # Check for similar names (Levenshtein < 2)
        similar_names = [cn for cn in character_names if self._are_similar_names(name, cn)]

        if similar_names:
            # Similar name found - allow it
            return CharacterNameResult(
                is_valid=True,
                protagonist_name=name,
                issues=[],
                warnings=[
                    f"Name '{name}' not found exactly, but similar name '{similar_names[0]}' exists"
                ],
            )

        # No match found
        return CharacterNameResult(
            is_valid=False,
            protagonist_name=name,
            issues=[f"Character '{name}' not found in character names list"],
        )
