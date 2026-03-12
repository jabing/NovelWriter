"""Outline generator for creating detailed chapter outlines from story ideas.

This module provides the OutlineGenerator class which uses LLM to generate
structured chapter outlines with plot events and state changes.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.llm.base import BaseLLM

logger = logging.getLogger(__name__)


@dataclass
class PlotEvent:
    """A single plot event within a chapter.

    Attributes:
        description: Description of what happens in this event
        characters_involved: List of characters participating in this event
        location: Where this event takes place
        time_of_day: Time of day when this event occurs (optional)
    """

    description: str
    characters_involved: list[str] = field(default_factory=list)
    location: str = ""
    time_of_day: str = ""


@dataclass
class DetailedChapterSpec:
    """Detailed specification for a single chapter.

    This extends the basic ChapterSpec with plot events and state tracking.

    Attributes:
        number: Chapter number
        title: Chapter title
        summary: Brief summary of the chapter
        plot_events: List of plot events that occur in this chapter
        state_changes: Dictionary mapping character names to their state changes
        characters: List of character names appearing in this chapter
        location: Primary location of the chapter
        key_events: List of key events (legacy support)
        plot_threads_resolved: List of plot threads resolved in this chapter
        plot_threads_started: List of plot threads started in this chapter
    """

    number: int
    title: str
    summary: str
    plot_events: list[PlotEvent] = field(default_factory=list)
    state_changes: dict[str, str] = field(default_factory=dict)
    characters: list[str] = field(default_factory=list)
    location: str = ""
    key_events: list[str] = field(default_factory=list)
    plot_threads_resolved: list[str] = field(default_factory=list)
    plot_threads_started: list[str] = field(default_factory=list)


# Prompt template for outline generation
OUTLINE_GENERATION_PROMPT = """You are an expert story outline generator. Create a detailed chapter-by-chapter outline for the following story idea.

Story Idea:
{story_idea}

Requirements:
- Generate exactly {num_chapters} chapters
- Each chapter should have a clear title and summary
- Include 2-4 plot events per chapter with specific details
- Track character state changes (emotions, relationships, physical state)
- Identify which characters appear in each chapter
- Note primary locations
- Track plot threads that start or resolve

Respond with a JSON object in the following format:
{{
    "chapters": [
        {{
            "number": 1,
            "title": "Chapter Title",
            "summary": "Brief summary of the chapter",
            "plot_events": [
                {{
                    "description": "What happens in this event",
                    "characters_involved": ["Character Name"],
                    "location": "Where it happens",
                    "time_of_day": "Optional time description"
                }}
            ],
            "state_changes": {{
                "Character Name": "Description of how their state changes"
            }},
            "characters": ["List of all characters in this chapter"],
            "location": "Primary location",
            "plot_threads_started": ["Threads started"],
            "plot_threads_resolved": ["Threads resolved"]
        }}
    ]
}}

Ensure the JSON is valid and properly formatted. The outline should create a coherent narrative arc across all chapters."""


class OutlineGenerator:
    """Generator for creating detailed chapter outlines from story ideas.

    This class uses an LLM to generate structured chapter outlines with
    detailed plot events, character state changes, and narrative progression.
    Includes fallback mechanism for when LLM generation fails.

    Attributes:
        llm: BaseLLM instance for generating outlines
    """

    def __init__(self, llm: BaseLLM) -> None:
        """Initialize the outline generator.

        Args:
            llm: BaseLLM instance for generating outlines
        """
        self.llm = llm

    async def generate_outline(
        self, story_idea: str, num_chapters: int
    ) -> list[DetailedChapterSpec]:
        """Generate a detailed chapter outline from a story idea.

        Uses the LLM to generate a structured outline with plot events,
        character states, and narrative progression. Falls back to a
        simple outline if LLM generation fails.

        Args:
            story_idea: The story idea or concept to base the outline on
            num_chapters: Number of chapters to generate

        Returns:
            List of DetailedChapterSpec objects representing the outline.
            Returns empty list if generation completely fails.
        """
        if not story_idea.strip():
            logger.warning("Empty story idea provided, returning empty outline")
            return []

        if num_chapters <= 0:
            logger.warning(f"Invalid chapter count: {num_chapters}, returning empty outline")
            return []

        try:
            # Format the prompt with story idea and chapter count
            prompt = OUTLINE_GENERATION_PROMPT.format(
                story_idea=story_idea, num_chapters=num_chapters
            )

            # Generate outline from LLM
            response = await self.llm.generate(prompt)

            # Parse the response
            chapters = self._parse_outline_response(response.content)

            if chapters:
                logger.info(f"Successfully generated outline with {len(chapters)} chapters")
                return chapters
            else:
                logger.warning("LLM returned empty outline, using fallback")
                return self._create_simple_outline(story_idea, num_chapters)

        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            return self._create_simple_outline(story_idea, num_chapters)

    def _parse_outline_response(self, content: str) -> list[DetailedChapterSpec]:
        """Parse the LLM response into a list of DetailedChapterSpec objects.

        Extracts JSON from markdown code blocks if present, then parses
        the chapter data into DetailedChapterSpec and PlotEvent objects.

        Args:
            content: The raw LLM response content

        Returns:
            List of DetailedChapterSpec objects. Returns empty list if parsing fails.
        """
        if not content.strip():
            return []

        try:
            # Extract JSON from markdown code blocks if present
            json_content = self._extract_json_from_markdown(content)

            # Parse the JSON
            data = json.loads(json_content)

            if "chapters" not in data or not isinstance(data["chapters"], list):
                logger.warning("Invalid outline structure: missing 'chapters' key")
                return []

            chapters = []
            for chapter_data in data["chapters"]:
                try:
                    chapter = self._parse_chapter_data(chapter_data)
                    chapters.append(chapter)
                except Exception as e:
                    logger.warning(f"Error parsing chapter data: {e}")
                    continue

            return chapters

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing outline response: {e}")
            return []

    def _extract_json_from_markdown(self, content: str) -> str:
        """Extract JSON content from markdown code blocks.

        If the content contains markdown code blocks (```json ... ```),
        extracts the JSON portion. Otherwise returns the content as-is.

        Args:
            content: Raw content that may contain markdown code blocks

        Returns:
            JSON string extracted from markdown or original content
        """
        # Match JSON code blocks: ```json ... ``` or just ``` ... ```
        patterns = [
            r"```json\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # No code block found, return content as-is
        return content.strip()

    def _parse_chapter_data(self, chapter_data: dict[str, Any]) -> DetailedChapterSpec:
        """Parse a single chapter's data into a DetailedChapterSpec.

        Args:
            chapter_data: Dictionary containing chapter data from JSON

        Returns:
            DetailedChapterSpec object
        """
        # Parse plot events
        plot_events = []
        for event_data in chapter_data.get("plot_events", []):
            event = PlotEvent(
                description=event_data.get("description", ""),
                characters_involved=event_data.get("characters_involved", []),
                location=event_data.get("location", ""),
                time_of_day=event_data.get("time_of_day", ""),
            )
            plot_events.append(event)

        # Build key_events list from plot event descriptions (for compatibility)
        key_events = chapter_data.get("key_events", [])
        if not key_events and plot_events:
            key_events = [e.description for e in plot_events]

        return DetailedChapterSpec(
            number=chapter_data.get("number", 0),
            title=chapter_data.get("title", "Untitled"),
            summary=chapter_data.get("summary", ""),
            plot_events=plot_events,
            state_changes=chapter_data.get("state_changes", {}),
            characters=chapter_data.get("characters", []),
            location=chapter_data.get("location", ""),
            key_events=key_events,
            plot_threads_resolved=chapter_data.get("plot_threads_resolved", []),
            plot_threads_started=chapter_data.get("plot_threads_started", []),
        )

    def _create_simple_outline(
        self, story_idea: str, num_chapters: int
    ) -> list[DetailedChapterSpec]:
        """Create a simple fallback outline when LLM generation fails.

        Generates basic chapter specifications with minimal structure
        to ensure continuity system has something to work with.

        Args:
            story_idea: The story idea or concept
            num_chapters: Number of chapters to generate

        Returns:
            List of basic DetailedChapterSpec objects
        """
        logger.info(f"Creating simple fallback outline with {num_chapters} chapters")

        chapters = []

        # Divide story into three acts roughly
        act_break_1 = max(1, num_chapters // 3)
        act_break_2 = max(act_break_1 + 1, 2 * num_chapters // 3)

        for i in range(1, num_chapters + 1):
            # Determine which act this chapter belongs to
            if i <= act_break_1:
                act = "Act I - Setup"
            elif i <= act_break_2:
                act = "Act II - Confrontation"
            else:
                act = "Act III - Resolution"

            chapter = DetailedChapterSpec(
                number=i,
                title=f"Chapter {i}: {act}",
                summary=f"Part {i} of the story based on: {story_idea[:100]}...",
                plot_events=[
                    PlotEvent(
                        description=f"Scene {i}: The story progresses",
                        characters_involved=["Protagonist"],
                        location="TBD",
                    )
                ],
                state_changes={},
                characters=["Protagonist"],
                location="TBD",
                key_events=[f"Chapter {i} events"],
                plot_threads_started=[],
                plot_threads_resolved=[],
            )
            chapters.append(chapter)

        return chapters


def create_simple_outline(story_idea: str, num_chapters: int) -> list[DetailedChapterSpec]:
    """Create a simple outline without using LLM.

    This is a standalone function that creates a basic outline structure
    when LLM is unavailable or fails. Useful for testing and fallback scenarios.

    Args:
        story_idea: The story idea or concept
        num_chapters: Number of chapters to generate

    Returns:
        List of basic DetailedChapterSpec objects
    """
    if not story_idea.strip() or num_chapters <= 0:
        return []

    generator = OutlineGenerator.__new__(OutlineGenerator)
    return generator._create_simple_outline(story_idea, num_chapters)
