"""Outline management system for novel generation.

This module provides classes for managing detailed chapter outlines,
validating outline completeness, and retrieving chapter specifications.
"""

from dataclasses import dataclass, field


@dataclass
class ChapterSpec:
    """Specification for a single chapter.

    Attributes:
        number: Chapter number
        title: Chapter title
        summary: Brief summary of the chapter
        characters: List of character names appearing in this chapter
        location: Primary location of the chapter
        key_events: List of key events that occur in this chapter
        plot_threads_resolved: List of plot threads resolved in this chapter
        plot_threads_started: List of plot threads started in this chapter
        character_states: Dictionary mapping character names to their states in this chapter
    """

    number: int
    title: str
    summary: str
    characters: list[str] = field(default_factory=list)
    location: str = ""
    key_events: list[str] = field(default_factory=list)
    plot_threads_resolved: list[str] = field(default_factory=list)
    plot_threads_started: list[str] = field(default_factory=list)
    character_states: dict[str, str] = field(default_factory=dict)

    def has_character(self, name: str) -> bool:
        """Check if a character appears in this chapter."""
        return name in self.characters

    def has_plot_thread(self, thread_name: str) -> bool:
        """Check if a plot thread is affected in this chapter."""
        return thread_name in self.plot_threads_started or thread_name in self.plot_threads_resolved


@dataclass
class DetailedOutline:
    """Detailed outline for an entire novel.

    This class manages a complete chapter-by-chapter outline with
    validation and retrieval capabilities.

    Attributes:
        chapters: List of ChapterSpec objects representing each chapter
    """

    chapters: list[ChapterSpec] = field(default_factory=list)

    def get_chapter_spec(self, chapter_number: int) -> ChapterSpec | None:
        """Get the specification for a specific chapter.

        Args:
            chapter_number: The chapter number to retrieve

        Returns:
            ChapterSpec if found, None otherwise
        """
        for chapter in self.chapters:
            if chapter.number == chapter_number:
                return chapter
        return None

    def get_character_states_for_chapter(self, chapter_number: int) -> dict[str, str]:
        """Get character states for a specific chapter.

        Returns the character states explicitly defined for this chapter.

        Args:
            chapter_number: The chapter number

        Returns:
            Dictionary mapping character names to their states
        """
        chapter = self.get_chapter_spec(chapter_number)
        if chapter:
            return chapter.character_states
        return {}

    def validate(self) -> list[str]:
        """Validate the outline for completeness and consistency.

        Checks for:
        - Missing chapter numbers
        - Duplicate chapter numbers
        - Empty required fields
        - Proper chapter numbering sequence

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.chapters:
            errors.append("Outline has no chapters")
            return errors

        # Check for duplicate chapter numbers
        chapter_numbers = [chapter.number for chapter in self.chapters]
        duplicates = [num for num in set(chapter_numbers) if chapter_numbers.count(num) > 1]
        for duplicate in duplicates:
            errors.append(f"Duplicate chapter number: {duplicate}")

        # Check for missing chapters
        if chapter_numbers:
            expected_chapters = set(range(1, max(chapter_numbers) + 1))
            actual_chapters = set(chapter_numbers)
            missing = expected_chapters - actual_chapters
            for missing_chapter in sorted(missing):
                errors.append(f"Missing chapter: {missing_chapter}")

        # Check each chapter for completeness
        for chapter in self.chapters:
            # Check required fields are not empty
            if not chapter.title:
                errors.append(f"Chapter {chapter.number}: Title is empty")

            if not chapter.summary:
                errors.append(f"Chapter {chapter.number}: Summary is empty")

            if not chapter.location:
                errors.append(f"Chapter {chapter.number}: Location is empty")

            # Check chapter number is positive
            if chapter.number <= 0:
                errors.append(f"Chapter {chapter.number}: Chapter number must be positive")

        return errors

    def get_total_chapters(self) -> int:
        """Get the total number of chapters in the outline."""
        return len(self.chapters)

    def get_chapters_for_character(self, character_name: str) -> list[ChapterSpec]:
        """Get all chapters where a specific character appears.

        Args:
            character_name: Name of the character

        Returns:
            List of ChapterSpec objects where the character appears
        """
        return [chapter for chapter in self.chapters if chapter.has_character(character_name)]

    def get_chapters_with_plot_thread(self, thread_name: str) -> list[ChapterSpec]:
        """Get all chapters where a plot thread is started or resolved.

        Args:
            thread_name: Name of the plot thread

        Returns:
            List of ChapterSpec objects affecting the plot thread
        """
        return [chapter for chapter in self.chapters if chapter.has_plot_thread(thread_name)]

    def get_plot_threads(self) -> dict[str, dict[str, int]]:
        """Get all plot threads and their chapter ranges.

        Returns:
            Dictionary mapping plot thread names to dicts with
            'started_chapter' and 'resolved_chapter' (or None if not resolved)
        """
        threads = {}

        for chapter in self.chapters:
            # Track started threads
            for thread_name in chapter.plot_threads_started:
                if thread_name not in threads:
                    threads[thread_name] = {
                        "started_chapter": chapter.number,
                        "resolved_chapter": None,
                    }

            # Track resolved threads
            for thread_name in chapter.plot_threads_resolved:
                if thread_name in threads:
                    threads[thread_name]["resolved_chapter"] = chapter.number
                else:
                    # Thread was resolved without being started (data issue)
                    threads[thread_name] = {
                        "started_chapter": None,
                        "resolved_chapter": chapter.number,
                    }

        return threads
