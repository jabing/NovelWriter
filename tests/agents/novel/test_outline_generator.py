"""Tests for outline generator module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.novel.outline_generator import DetailedChapterSpec, OutlineGenerator, PlotEvent


@pytest.mark.asyncio
class TestOutlineGenerator:
    """Test cases for OutlineGenerator class."""

    async def test_outline_generator_initialization(self):
        """Test that OutlineGenerator can be initialized."""
        mock_llm = MagicMock(spec=BaseLLM)
        generator = OutlineGenerator(mock_llm)
        assert generator is not None
        assert generator.llm == mock_llm

    async def test_generate_outline_with_llm_success(self):
        """Test successful outline generation with LLM."""
        mock_llm = MagicMock(spec=BaseLLM)
        mock_response = MagicMock(
            content="""
        {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1: Discovery",
                    "summary": "The hero finds a mysterious egg.",
                    "plot_events": [
                        {
                            "description": "Hero finds glowing egg",
                            "characters_involved": ["Kael"],
                            "location": "Vault",
                            "time_of_day": "Midnight"
                        }
                    ],
                    "state_changes": {"Egg": "Found"},
                    "characters": ["Kael"],
                    "location": "Vault",
                    "key_events": ["Discovery"],
                    "plot_threads_started": ["Dragon mystery"],
                    "plot_threads_resolved": []
                }
            ]
        }
        """
        )
        mock_llm.generate = AsyncMock(return_value=mock_response)

        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("Story about a dragon egg", num_chapters=1)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].number == 1
        assert result[0].title == "Chapter 1: Discovery"
        assert len(result[0].plot_events) == 1
        assert result[0].plot_events[0].description == "Hero finds glowing egg"

    async def test_generate_outline_with_llm_json_in_markdown(self):
        """Test JSON parsing from markdown code blocks."""
        mock_llm = MagicMock(spec=BaseLLM)
        mock_response = MagicMock(
            content="""
```json
{
    "chapters": [
        {
            "number": 1,
            "title": "Chapter 1"
        }
    ]
}
```
        """
        )
        mock_llm.generate = AsyncMock(return_value=mock_response)

        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("Story", num_chapters=1)

        assert len(result) == 1
        assert result[0].number == 1

    async def test_generate_outline_empty_story(self):
        """Test outline generation with empty story."""
        mock_llm = MagicMock(spec=BaseLLM)
        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("", num_chapters=3)

        assert result == []

    async def test_generate_outline_invalid_chapter_count(self):
        """Test outline generation with invalid chapter count."""
        mock_llm = MagicMock(spec=BaseLLM)
        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("Story", num_chapters=0)

        assert result == []

    async def test_generate_outline_llm_failure_fallback(self):
        """Test that fallback to simple outline is used when LLM fails."""
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM error"))

        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("Story", num_chapters=2)

        # Should return simple outline
        assert isinstance(result, list)
        assert len(result) == 2
        assert "Act I" in result[0].title
        assert len(result[0].plot_events) == 1

    async def test_generate_outline_llm_invalid_json_fallback(self):
        """Test fallback when LLM returns invalid JSON."""
        mock_llm = MagicMock(spec=BaseLLM)
        mock_response = MagicMock(content="This is not valid JSON")

        mock_llm.generate = AsyncMock(return_value=mock_response)

        generator = OutlineGenerator(mock_llm)
        result = await generator.generate_outline("Story", num_chapters=2)

        # Should fall back to simple outline
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].title.startswith("Chapter 1:")

    def test_parse_outline_response_valid_json(self):
        """Test parsing valid JSON response."""
        generator = OutlineGenerator.__new__(OutlineGenerator)

        json_content = """
        {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1"
                }
            ]
        }
        """
        result = generator._parse_outline_response(json_content)

        assert len(result) == 1
        assert result[0].number == 1
        assert result[0].title == "Chapter 1"

    def test_parse_outline_response_empty(self):
        """Test parsing empty response."""
        generator = OutlineGenerator.__new__(OutlineGenerator)
        result = generator._parse_outline_response("")

        assert result == []

    def test_parse_outline_response_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        generator = OutlineGenerator.__new__(OutlineGenerator)
        result = generator._parse_outline_response("invalid")

        assert result == []

    def test_extract_json_from_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        generator = OutlineGenerator.__new__(OutlineGenerator)
        content = '```json\n{"key": "value"}\n```'

        result = generator._extract_json_from_markdown(content)

        assert result == '{"key": "value"}'

    def test_extract_json_from_markdown_no_code_block(self):
        """Test that content without code block is returned as-is."""
        generator = OutlineGenerator.__new__(OutlineGenerator)
        content = '{"key": "value"}'

        result = generator._extract_json_from_markdown(content)

        assert result == content

    def test_create_simple_outline(self):
        """Test simple outline creation."""
        generator = OutlineGenerator.__new__(OutlineGenerator)
        result = generator._create_simple_outline("Test story", num_chapters=5)

        assert len(result) == 5
        assert result[0].number == 1
        assert result[1].number == 2
        assert result[2].number == 3
        assert "Act I" in result[0].title
        assert "Act II" in result[2].title

    def test_plot_event_dataclass(self):
        """Test PlotEvent dataclass structure."""
        event = PlotEvent(
            description="Hero finds egg", characters_involved=["Kael"], location="Vault"
        )

        assert event.description == "Hero finds egg"
        assert event.characters_involved == ["Kael"]
        assert event.location == "Vault"
        assert event.time_of_day == ""

    def test_detailed_chapter_spec_dataclass(self):
        """Test DetailedChapterSpec dataclass structure."""
        chapter = DetailedChapterSpec(
            number=1,
            title="Chapter 1",
            summary="Hero finds egg",
            characters=["Kael"],
            location="Vault",
        )

        assert chapter.number == 1
        assert chapter.title == "Chapter 1"
        assert chapter.summary == "Hero finds egg"
        assert isinstance(chapter.plot_events, list)
        assert isinstance(chapter.state_changes, dict)
        assert isinstance(chapter.characters, list)
