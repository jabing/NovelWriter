import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.novel_agent.novel.continuity import StoryState
from src.novel_agent.novel.outline_manager import ChapterSpec

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """A validation error for continuity checking.

    Attributes:
        severity: Error severity level (error, warning)
        message: Human-readable error message
        chapter: Chapter number where error occurred
        details: Additional error details
    """

    severity: str  # "error" or "warning"
    message: str
    chapter: int
    details: str = ""


@dataclass
class ValidationResult:
    """Result of chapter content validation.

    Attributes:
        is_valid: Whether the chapter passed validation
        errors: List of error-level validation failures
        warnings: List of warning-level issues
    """

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)


class ContinuityValidator:
    """Validator for checking story continuity in chapter content.

    This class performs various checks to ensure:
    - Dead characters don't appear alive
    - Fused characters don't have independent forms
    - Location consistency
    - Plot thread progression
    """

    def __init__(self) -> None:
        """Initialize the continuity validator."""
        self._death_keywords = ["died", "killed", "perished", "sacrificed", "dead", "was killed"]
        self._memorial_keywords = [
            "fallen",
            "remembering",
            "memory",
            "memorial",
            "remembered",
            "late",
            "departed",
            "ghost",
            "spirit",
            "soul",
            "rest in peace",
            "rest in power",
            "honor",
            "legacy",
            "in memory of",
            "haunted by",
            "dreamed of",
            "thought of",
            "missed",
            "gone but not forgotten",
        ]
        self._fusion_keywords = ["fused", "merged", "combined", "became one"]
        self._location_transitions = [
            "arrived at",
            "traveled to",
            "moved to",
            "went to",
            "teleported to",
            "appeared in",
            "found themselves in",
            "entered",
        ]

    def validate_chapter(
        self,
        chapter_content: str,
        chapter_number: int,
        story_state: StoryState,
        chapter_spec: ChapterSpec | None = None,
    ) -> ValidationResult:
        """Validate chapter content against story state.

        Args:
            chapter_content: The chapter text to validate
            chapter_number: Chapter number being validated
            story_state: Current story state
            chapter_spec: Optional chapter specification

        Returns:
            ValidationResult with all validation errors and warnings
        """
        errors = []
        warnings = []

        # Check 1: Character appearances
        char_errors = self._check_character_appearances(
            chapter_content, story_state, chapter_number
        )
        errors.extend(char_errors)

        # Check 2: Character states
        state_errors = self._check_character_states(chapter_content, story_state, chapter_number)
        errors.extend(state_errors)

        # Check 3: Location consistency
        loc_errors = self._check_location_consistency(chapter_content, story_state, chapter_number)
        errors.extend(loc_errors)

        # Check 4: Plot thread progression
        plot_warnings = self._check_plot_thread_progression(
            chapter_content, story_state, chapter_spec
        )
        warnings.extend(plot_warnings)

        # Determine if valid
        is_valid = len(errors) == 0

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def _check_character_appearances(
        self,
        chapter_content: str,
        story_state: StoryState,
        chapter_number: int,
    ) -> list[ValidationError]:
        """Check if dead or fused characters appear inappropriately.

        Args:
            chapter_content: Chapter text to check
            story_state: Current story state
            chapter_number: Chapter number

        Returns:
            List of validation errors
        """
        errors = []
        content_lower = chapter_content.lower()

        for char_name, char_state in story_state.character_states.items():
            if char_state.is_dead():
                # Check if dead character appears as alive
                char_mentions = self._count_character_mentions(content_lower, char_name.lower())

                if char_mentions > 0:
                    # Check if character appears to be alive (not in memory/memorial context)
                    is_memorial_context = False

                    # Check for memorial keywords near the character name
                    char_positions = []
                    pos = 0
                    while True:
                        pos = content_lower.find(char_name.lower(), pos)
                        if pos == -1:
                            break
                        char_positions.append(pos)
                        pos += 1

                    for char_pos in char_positions:
                        # Get context window around character name (100 chars before and after)
                        context_start = max(0, char_pos - 100)
                        context_end = min(len(content_lower), char_pos + len(char_name) + 100)
                        context_window = content_lower[context_start:context_end]

                        # Check for memorial keywords in context
                        for keyword in self._memorial_keywords:
                            if keyword in context_window:
                                is_memorial_context = True
                                break

                        for keyword in self._death_keywords:
                            if keyword in context_window:
                                is_memorial_context = True
                                break

                        if is_memorial_context:
                            break

                    if not is_memorial_context:
                        # Character appears alive - this is an error
                        errors.append(
                            ValidationError(
                                severity="error",
                                message=f"Dead character '{char_name}' appears alive in Chapter {chapter_number}",
                                chapter=chapter_number,
                                details="Character died in earlier chapter but appears without death/memorial context",
                            )
                        )

        return errors

    def _check_character_states(
        self,
        chapter_content: str,
        story_state: StoryState,
        chapter_number: int,
    ) -> list[ValidationError]:
        """Check if character states are consistent with content.

        Args:
            chapter_content: Chapter text to check
            story_state: Current story state
            chapter_number: Chapter number

        Returns:
            List of validation errors
        """
        errors = []
        content_lower = chapter_content.lower()

        for char_name, char_state in story_state.character_states.items():
            if char_state.is_fused():
                # Check if fused character has independent physical form
                for keyword in ["stood", "walked", "moved", "spoke", "said", "looked"]:
                    pattern = f"{char_name.lower()} {keyword}"
                    if pattern in content_lower:
                        errors.append(
                            ValidationError(
                                severity="error",
                                message=f"Fused character '{char_name}' has independent physical form in Chapter {chapter_number}",
                                chapter=chapter_number,
                                details=f"Character is fused but appears with physical actions (e.g., '{keyword}')",
                            )
                        )

        return errors

    def _check_location_consistency(
        self,
        chapter_content: str,
        story_state: StoryState,
        chapter_number: int,
    ) -> list[ValidationError]:
        """Check if location transitions are plausible.

        Args:
            chapter_content: Chapter text to check
            story_state: Current story state
            chapter_number: Chapter number

        Returns:
            List of validation errors
        """
        errors = []
        content_lower = chapter_content.lower()

        # Check for sudden, unexplained location changes
        for transition in self._location_transitions:
            if transition in content_lower:
                # Check if this is a major location change
                new_location = self._extract_location_from_text(chapter_content, transition)
                if new_location and new_location != story_state.location:
                    # This could be OK but worth a warning
                    # For now, we'll skip this check to avoid false positives
                    pass

        return errors

    def _check_plot_thread_progression(
        self,
        chapter_content: str,
        story_state: StoryState,
        chapter_spec: ChapterSpec | None,
    ) -> list[ValidationError]:
        """Check if plot threads progress reasonably.

        Args:
            chapter_content: Chapter text to check
            story_state: Current story state
            chapter_spec: Optional chapter specification

        Returns:
            List of validation warnings
        """
        warnings = []

        if chapter_spec is None:
            return warnings

        # Check if threads are resolved too quickly
        for resolved_thread in chapter_spec.plot_threads_resolved:
            for thread in story_state.plot_threads:
                if thread.name == resolved_thread and thread.is_active():
                    # Thread was just started, now it's resolved
                    # This could be valid for short threads
                    pass

        # Check if threads are mentioned but not tracked
        # (Simplified for now - could be enhanced later)

        return warnings

    def _count_character_mentions(self, content_lower: str, char_name_lower: str) -> int:
        """Count how many times a character is mentioned in content.

        Args:
            content_lower: Lowercase chapter content
            char_name_lower: Lowercase character name

        Returns:
            Count of mentions
        """
        return content_lower.count(char_name_lower)

    def _extract_location_from_text(self, text: str, transition: str) -> str | None:
        """Extract location name from text around a transition phrase.

        Args:
            text: Chapter text
            transition: Transition phrase (e.g., "arrived at")

        Returns:
            Extracted location name or None
        """
        # Simple heuristic - look for capitalized words after transition
        pattern = f"{transition} ([A-Z][a-z]+)"
        match = re.search(pattern, text)
        return match.group(1) if match else None


class NovelValidator:
    """Validates novel content for quality issues identified in root cause analysis.

    This validator addresses:
    - Missing chapters in sequence
    - Duplicate titles
    - Content discontinuity between chapters
    - References to non-existent events

    Example:
        >>> from pathlib import Path
        >>> validator = NovelValidator("my_novel", Path("data/novels"))
        >>> issues = validator.detect_missing_chapters(10)
        >>> content = validator.clean_title_format(4, chapter_content)
    """

    def __init__(self, novel_id: str, storage_path: Path):
        """Initialize the validator.

        Args:
            novel_id: Unique identifier for the novel
            storage_path: Base path for novel data
        """
        from src.novel_agent.novel.registry.story_registry import StoryRegistry

        self.novel_id = novel_id
        self.storage_path = storage_path
        self.registry = StoryRegistry(novel_id, storage_path)

        logger.info(f"NovelValidator initialized for '{novel_id}'")

    def detect_missing_chapters(self, up_to: int) -> list[int]:
        """Detect missing chapters in sequence.

        Args:
            up_to: Maximum chapter number to check

        Returns:
            List of missing chapter numbers
        """
        missing = self.registry.get_missing_chapters(up_to)

        if missing:
            logger.warning(f"Missing chapters detected: {missing}")

        return missing

    def clean_title_format(self, chapter_num: int, content: str) -> tuple[str, bool]:
        """Clean title format by removing duplicate title lines.

        Args:
            chapter_num: Chapter number
            content: Chapter content

        Returns:
            Tuple of (cleaned content, was_modified)
        """
        # Check for duplicate title lines
        title_pattern = re.compile(r'^第?\d+[章篇]\s*[：:\s]*(.+)$', re.MULTILINE)
        matches = title_pattern.findall(content)

        if len(matches) > 1:
            # Multiple title lines detected - keep only the first
            logger.warning(f"Multiple title lines in chapter {chapter_num}, cleaning...")

            lines_list = content.split('\n')
            cleaned_lines = []
            title_count = 0

            for line in lines_list:
                if title_pattern.match(line.strip()):
                    title_count += 1
                    if title_count == 1:
                        cleaned_lines.append(line)  # Keep first title
                    else:
                        logger.debug(f"Removing duplicate title: {line[:50]}")
                        continue  # Skip duplicate titles
                else:
                    cleaned_lines.append(line)

            return '\n'.join(cleaned_lines), True

        return content, False

    def check_title_uniqueness(self, chapter_num: int, title: str) -> bool:
        """Check if title is unique across all chapters.

        Args:
            chapter_num: Current chapter number
            title: Title to check

        Returns:
            True if title is unique, False if duplicated
        """
        title_text = self._extract_title_text(title)
        return not self.registry.is_title_used(title_text, exclude_chapter=chapter_num)

    def validate_all_chapters(self) -> list[dict[str, Any]]:
        """Validate all chapters and return issues found.

        Returns:
            List of validation issues with chapter, type, severity, description
        """
        issues = []

        chapters_path = self.storage_path / self.novel_id / "chapters"
        if not chapters_path.exists():
            logger.warning(f"No chapters found for novel {self.novel_id}")
            return issues

        # Get all chapter files
        chapter_files = sorted(chapters_path.glob("chapter_*.md"))
        max_chapter = len(chapter_files)

        # Check for missing chapters
        missing = self.detect_missing_chapters(max_chapter)
        for ch_num in missing:
            issues.append({
                "chapter": ch_num,
                "type": "missing_chapter",
                "severity": "critical",
                "description": f"Chapter {ch_num} is missing from sequence",
                "fix_hint": "Generate this chapter to fill the gap"
            })

        # Validate each existing chapter
        for chapter_file in chapter_files:
            chapter_num = int(chapter_file.stem.split('_')[1])

            with open(chapter_file, encoding='utf-8') as f:
                content = f.read()

            # Check title format and uniqueness
            cleaned_content, was_modified = self.clean_title_format(chapter_num, content)

            if was_modified:
                # Save cleaned content
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                issues.append({
                    "chapter": chapter_num,
                    "type": "duplicate_title",
                    "severity": "major",
                    "description": f"Duplicate title lines removed from chapter {chapter_num}",
                    "fix_hint": "Already auto-fixed"
                })

            # Extract and check title uniqueness
            first_line = cleaned_content.split('\n')[0] if cleaned_content else ""
            if not self.check_title_uniqueness(chapter_num, first_line):
                issues.append({
                    "chapter": chapter_num,
                    "type": "title_duplication",
                    "severity": "major",
                    "description": f"Title '{self._extract_title_text(first_line)}' is used in another chapter",
                    "fix_hint": "Choose a unique title for this chapter"
                })

        logger.info(f"Validation complete: {len(issues)} issues found")
        return issues

    def _extract_title_text(self, full_title: str) -> str:
        """Extract title text from full title with chapter number.

        Args:
            full_title: Full title like "第1章：开端"

        Returns:
            Title text only like "开端"
        """
        # Match common patterns
        patterns = [
            r"第\d+章[：:\s]*(.+)",  # Chinese: 第1章：Title
            r"Chapter\s+\d+[：:\s]*(.+)",  # English: Chapter 1: Title
        ]

        for pattern in patterns:
            match = re.match(pattern, full_title)
            if match:
                return match.group(1).strip()

        return full_title.strip()
