"""Continuity validator that orchestrates all three checkers.

This module provides the main ContinuityValidator class that coordinates
LanguageConsistencyChecker, NarrativePerspectiveChecker, and CharacterNameChecker
to validate continuity across novel chapters.
"""

from dataclasses import dataclass, field
from src.novel_agent.novel.language_checker import LanguageConsistencyChecker, Language
from src.novel_agent.novel.perspective_checker import NarrativePerspectiveChecker, Perspective
from src.novel_agent.novel.character_name_checker import CharacterNameChecker, CharacterNameResult


@dataclass
class ContinuityContext:
    """Context for continuity validation.

    Attributes:
        chapter_number: The current chapter number being validated
        character_names: List of valid character names for this novel
        expected_language: Expected language ("chinese" or "english"), optional
        expected_perspective: Expected perspective ("first_person" or "third_person"), optional
        block_on_character_mismatch: If True, protagonist name mismatch causes failure
    """

    chapter_number: int
    character_names: list[str]
    expected_language: str | None = None  # "chinese" or "english"
    expected_perspective: str | None = None  # "first_person" or "third_person"
    block_on_character_mismatch: bool = False


@dataclass
class ContinuityValidationResult:
    """Aggregated result from all continuity checks.

    Attributes:
        is_valid: Overall validity - FAIL if ANY checker fails
        language_valid: Whether language consistency check passed
        perspective_valid: Whether perspective consistency check passed
        character_valid: Whether character name consistency check passed
        issues: All issues from all checkers
        warnings: All warnings from all checkers
    """

    is_valid: bool
    language_valid: bool = True
    perspective_valid: bool = True
    character_valid: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ContinuityValidator:
    """Orchestrates all three continuity checkers.

    Runs language, perspective, and character name checks on chapter content.
    Returns FAIL (is_valid=False) if ANY single checker reports a failure.

    First chapter (no previous) passes language and perspective checks
    since there's nothing to compare against.
    """

    def __init__(self):
        """Initialize all three checkers."""
        self.language_checker = LanguageConsistencyChecker()
        self.perspective_checker = NarrativePerspectiveChecker()
        self.character_checker = CharacterNameChecker()

    def validate_chapter(
        self, current: str, previous: str | None, context: ContinuityContext
    ) -> ContinuityValidationResult:
        """Run all checks and return aggregated result.

        Args:
            current: Current chapter content
            previous: Previous chapter content, or None for first chapter
            context: Validation context with chapter number and character names

        Returns:
            ContinuityValidationResult with aggregated results from all checkers
        """
        issues: list[str] = []
        warnings: list[str] = []
        language_valid = True
        perspective_valid = True
        character_valid = True

        # Language check - only if we have previous chapter to compare
        if previous is not None:
            lang_result = self.language_checker.check_consistency(
                {
                    "previous": previous,
                    "current": current,
                }
            )
            if not lang_result.is_valid:
                language_valid = False
                issues.extend(lang_result.issues)
        # First chapter passes language check (no comparison possible)

        # Perspective check - only if we have previous chapter to compare
        if previous is not None:
            persp_result = self.perspective_checker.check_consistency(
                {
                    "previous": previous,
                    "current": current,
                }
            )
            if not persp_result.is_valid:
                perspective_valid = False
                issues.extend(persp_result.issues)
        # First chapter passes perspective check (no comparison possible)

        # Character name check - always validate against character_names
        char_result = self.character_checker.check_consistency(
            {"current": current},
            context.character_names,
            strict_mode=context.block_on_character_mismatch,
        )
        if not char_result.is_valid:
            character_valid = False
            issues.extend(char_result.issues)
        warnings.extend(char_result.warnings)

        # Overall validity - FAIL if ANY checker fails
        is_valid = language_valid and perspective_valid and character_valid

        return ContinuityValidationResult(
            is_valid=is_valid,
            language_valid=language_valid,
            perspective_valid=perspective_valid,
            character_valid=character_valid,
            issues=issues,
            warnings=warnings,
        )
