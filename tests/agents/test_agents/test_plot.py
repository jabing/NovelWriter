# tests/test_agents/test_plot.py
"""Tests for Plot Agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.plot import PlotAgent


class TestPlotAgent:
    """Tests for Plot Agent."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def agent(self, mock_llm: MagicMock) -> PlotAgent:
        """Create Plot Agent with mock LLM."""
        return PlotAgent(name="Test Plot Agent", llm=mock_llm)

    def test_initialization(self, agent: PlotAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "Test Plot Agent"
        assert "three_act" in agent.STORY_STRUCTURES
        assert "heros_journey" in agent.STORY_STRUCTURES

    @pytest.mark.asyncio
    async def test_execute_basic(self, agent: PlotAgent, mock_llm: MagicMock) -> None:
        """Test basic execution."""
        # Mock LLM responses
        mock_llm.generate_with_system.side_effect = [
            MagicMock(content='{"title": "Test Story", "logline": "A test", "theme": "test", "main_conflict": "test", "stakes": "test", "acts": [], "climax": "test", "resolution": "test"}'),
            MagicMock(content='[{"chapter": 1, "title": "Test Chapter", "summary": "test"}]'),
            MagicMock(content='[]'),
        ]

        result = await agent.execute({
            "genre": "fantasy",
            "target_chapters": 1,
            "premise": "A test story",
        })

        assert result.success is True
        assert "outline" in result.data
        assert result.data["outline"]["genre"] == "fantasy"

    @pytest.mark.asyncio
    async def test_generate_main_arc(self, agent: PlotAgent, mock_llm: MagicMock) -> None:
        """Test main arc generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='{"title": "Test Arc", "logline": "Test logline"}'
        )

        arc = await agent.generate_main_arc("fantasy", "A hero's journey")

        assert "title" in arc
        assert arc["title"] == "Test Arc"

    @pytest.mark.asyncio
    async def test_generate_main_arc_json_with_markdown(
        self, agent: PlotAgent, mock_llm: MagicMock
    ) -> None:
        """Test parsing JSON wrapped in markdown."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='```json\n{"title": "Test", "logline": "Test"}\n```'
        )

        arc = await agent.generate_main_arc("fantasy", "Test")

        assert arc["title"] == "Test"

    @pytest.mark.asyncio
    async def test_generate_chapter_outlines(
        self, agent: PlotAgent, mock_llm: MagicMock
    ) -> None:
        """Test chapter outline generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='[{"chapter": 1, "title": "Chapter 1"}, {"chapter": 2, "title": "Chapter 2"}]'
        )

        chapters = await agent.generate_chapter_outlines({}, 2)

        assert len(chapters) == 2
        assert chapters[0]["chapter"] == 1

    @pytest.mark.asyncio
    async def test_generate_chapter_outlines_pads(
        self, agent: PlotAgent, mock_llm: MagicMock
    ) -> None:
        """Test chapter padding when LLM returns fewer than requested."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='[{"chapter": 1, "title": "Chapter 1"}]'
        )

        chapters = await agent.generate_chapter_outlines({}, 5)

        assert len(chapters) == 5

    def test_story_structures(self, agent: PlotAgent) -> None:
        """Test story structure templates."""
        assert "act_1" in agent.STORY_STRUCTURES["three_act"]
        assert "departure" in agent.STORY_STRUCTURES["heros_journey"]
        assert "opening" in agent.STORY_STRUCTURES["save_the_cat"]


class TestPlotAgentErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def agent(self) -> PlotAgent:
        """Create agent with mock LLM that returns invalid JSON."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="invalid json"))
        return PlotAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_handles_invalid_json_in_arc(self, agent: PlotAgent) -> None:
        """Test that invalid JSON in arc generation is handled."""
        arc = await agent.generate_main_arc("fantasy", "Test")

        # Should return a fallback structure
        assert "title" in arc

    @pytest.mark.asyncio
    async def test_handles_invalid_json_in_chapters(self, agent: PlotAgent) -> None:
        """Test that invalid JSON in chapter generation is handled."""
        chapters = await agent.generate_chapter_outlines({}, 3)

        # Should return basic chapter structure
        assert isinstance(chapters, list)
        assert len(chapters) == 3
