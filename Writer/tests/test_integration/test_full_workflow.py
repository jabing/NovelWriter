# tests/test_integration/test_full_workflow.py
"""Integration tests for the complete novel writing workflow."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.character import CharacterAgent
from src.agents.comment_analyzer import CommentAnalyzerAgent
from src.agents.editor import EditorAgent
from src.agents.engagement import EngagementAgent
from src.agents.market_research import MarketResearchAgent
from src.agents.orchestrator import AgentOrchestrator, WorkflowStep
from src.agents.plot import PlotAgent
from src.agents.publisher import PublisherAgent
from src.agents.worldbuilding import WorldbuildingAgent
from src.agents.writers.writer_factory import get_writer
from src.memory import MemSearchAdapter


class TestFullWritingWorkflow:
    """Tests for the complete writing workflow."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM with reasonable responses."""
        mock = MagicMock()
        mock.generate_with_system = AsyncMock(
            return_value=MagicMock(content='{"result": "success", "content": "Generated content"}')
        )
        return mock

    @pytest.fixture
    def memory(self, tmp_path: Any) -> MemSearchAdapter:
        """Create file memory with temp directory."""
        return MemSearchAdapter(base_path=str(tmp_path / "memory"))

    @pytest.fixture
    def orchestrator(self, mock_llm: MagicMock, memory: MemSearchAdapter) -> AgentOrchestrator:
        """Create orchestrator with mock LLM."""
        orchestrator = AgentOrchestrator()
        orchestrator.memory = memory
        return orchestrator

    @pytest.mark.asyncio
    async def test_plot_to_character_workflow(
        self, orchestrator: AgentOrchestrator, mock_llm: MagicMock
    ) -> None:
        """Test workflow from plot generation to character creation."""
        # Register agents
        plot_agent = PlotAgent(name="Plot Agent", llm=mock_llm)
        character_agent = CharacterAgent(name="Character Agent", llm=mock_llm)

        orchestrator.register_agent(plot_agent)
        orchestrator.register_agent(character_agent)

        # Define workflow
        orchestrator.define_workflow("plot_to_character", [
            WorkflowStep(agent_name="Plot Agent", input_transform=lambda x: {
                "genre": x.get("genre", "fantasy"),
                "target_chapters": x.get("target_chapters", 10),
            }),
            WorkflowStep(agent_name="Character Agent", input_transform=lambda x: {
                "genre": x.get("genre", "fantasy"),
                "count": 3,
            }),
        ])

        # Run workflow
        result = await orchestrator.run_workflow(
            "plot_to_character",
            {"genre": "fantasy", "target_chapters": 10}
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_worldbuilding_integration(
        self, mock_llm: MagicMock, memory: MemSearchAdapter
    ) -> None:
        """Test worldbuilding agent integration."""
        world_agent = WorldbuildingAgent(
            name="World Agent",
            llm=mock_llm,
            memory=memory
        )

        result = await world_agent.execute({
            "genre": "scifi",
            "themes": ["exploration", "first contact"],
        })

        assert result.success is True

    @pytest.mark.asyncio
    async def test_writer_to_editor_workflow(
        self, mock_llm: MagicMock
    ) -> None:
        """Test workflow from writer to editor."""
        # Create writer
        writer = get_writer("fantasy", mock_llm)

        # Create editor
        editor = EditorAgent(name="Editor", llm=mock_llm)

        # Mock writer generating content
        mock_llm.generate_with_system.return_value = MagicMock(
            content="The dragon soared through the clouds..."
        )

        chapter_result = await writer.execute({
            "chapter_number": 1,
            "chapter_outline": "Hero meets dragon",
            "characters": [{"name": "Hero", "role": "protagonist"}],
            "world_context": {},
        })

        assert chapter_result.success is True

        # Edit the content
        edit_result = await editor.execute({
            "content": chapter_result.data.get("content", ""),
            "characters": [{"name": "Hero"}],
            "world_context": {},
        })

        assert edit_result.success is True

    @pytest.mark.asyncio
    async def test_editor_to_publisher_workflow(
        self, mock_llm: MagicMock
    ) -> None:
        """Test workflow from editor to publisher."""
        # Create editor
        editor = EditorAgent(name="Editor", llm=mock_llm)

        # Create publisher
        publisher = PublisherAgent(name="Publisher")
        publisher.register_platform("wattpad", api_key="test_key")

        # Edit content
        edit_result = await editor.execute({
            "content": "This is a test chapter with great content.",
            "characters": [],
            "world_context": {},
        })

        assert edit_result.success is True

        # Publish content
        publish_result = await publisher.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": edit_result.data.get("edited_content", "Test content"),
            "platforms": ["wattpad"],
        })

        assert publish_result.success is True


class TestMarketResearchWorkflow:
    """Tests for market research integration."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_market_research_informs_writing(self, agent: MarketResearchAgent) -> None:
        """Test that market research can inform writing decisions."""
        # Get market research
        result = await agent.execute({
            "genre": "fantasy",
            "platform": "royalroad",
        })

        assert result.success is True
        assert "recommendations" in result.data

        # Verify recommendations exist
        recs = result.data["recommendations"]
        assert len(recs.get("genre_recommendations", [])) >= 0
        assert len(recs.get("content_strategy", [])) >= 0


class TestCommentAnalysisWorkflow:
    """Tests for comment analysis and engagement workflow."""

    @pytest.fixture
    def comment_analyzer(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    @pytest.fixture
    def engagement_agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    @pytest.mark.asyncio
    async def test_analyze_and_respond_workflow(
        self,
        comment_analyzer: CommentAnalyzerAgent,
        engagement_agent: EngagementAgent,
    ) -> None:
        """Test workflow from comment analysis to engagement."""
        comments = [
            {"id": "1", "text": "Love this story! Can't wait for more!"},
            {"id": "2", "text": "Great chapter!"},
            {"id": "3", "text": "The pacing seems a bit slow."},
        ]

        # Analyze comments
        analysis = await comment_analyzer.execute({"comments": comments})

        assert analysis.success is True
        assert "sentiment" in analysis.data

        # Generate replies
        engagement = await engagement_agent.execute({
            "comments": comments,
            "platform": "wattpad",
        })

        assert engagement.success is True
        assert engagement.data["replies_generated"] == 3

    @pytest.mark.asyncio
    async def test_negative_feedback_handling(
        self,
        comment_analyzer: CommentAnalyzerAgent,
        engagement_agent: EngagementAgent,
    ) -> None:
        """Test handling of negative feedback."""
        comments = [
            {"id": "1", "text": "This is terrible and boring."},
        ]

        # Analyze
        analysis = await comment_analyzer.execute({"comments": comments})

        # Should detect negative sentiment
        assert analysis.data["sentiment"]["negative"] >= 1

        # Should generate appropriate suggestions
        suggestions = analysis.data.get("suggestions", [])
        assert len(suggestions) > 0


class TestScheduledWorkflow:
    """Tests for scheduled workflow execution."""

    @pytest.mark.asyncio
    async def test_daily_chapter_workflow(self) -> None:
        """Test the daily chapter generation workflow."""
        from src.scheduler.tasks import (
            TaskScheduler,
            daily_chapter_generation_handler,
        )

        scheduler = TaskScheduler(name="TestScheduler")

        executed = []

        async def tracked_handler(novel_id: str) -> dict:
            result = await daily_chapter_generation_handler(novel_id)
            executed.append(result)
            return result

        scheduler.register_task(
            "daily_chapter",
            "Daily Chapter",
            tracked_handler,
            60,
            args=("test_novel",),
        )

        # Run the task immediately
        await scheduler.run_task_now("daily_chapter")

        assert len(executed) == 1
        assert executed[0]["chapter_generated"] is True


class TestMemoryConsistency:
    """Tests for memory consistency across workflow."""

    @pytest.fixture
    def memory(self, tmp_path) -> MemSearchAdapter:
        """Create file memory."""
        return MemSearchAdapter(base_path=str(tmp_path / "memory"))

    @pytest.mark.asyncio
    async def test_character_memory_persistence(self, memory: MemSearchAdapter) -> None:
        """Test that character data persists in memory."""
        # Store character
        character_data = {
            "name": "Alice",
            "role": "protagonist",
            "traits": ["brave", "curious"],
        }

        await memory.store(
            "/memory/characters/main/alice",
            character_data,
            {"level": "L0"}
        )

        # Retrieve character
        stored = await memory.retrieve("/memory/characters/main/alice")

        assert stored is not None
        assert stored.value["name"] == "Alice"
        assert "brave" in stored.value["traits"]

    @pytest.mark.asyncio
    async def test_plot_memory_persistence(self, memory: MemSearchAdapter) -> None:
        """Test that plot data persists in memory."""
        plot_data = {
            "title": "The Adventure",
            "chapters": 50,
            "main_arc": "Hero saves the world",
        }

        await memory.store(
            "/memory/plot/main_arc",
            plot_data,
            {"level": "L0"}
        )

        stored = await memory.retrieve("/memory/plot/main_arc")

        assert stored is not None
        assert stored.value["title"] == "The Adventure"


class TestErrorRecovery:
    """Tests for error recovery in workflows."""

    @pytest.fixture
    def mock_llm_with_failure(self) -> MagicMock:
        """Create mock LLM that fails initially then succeeds."""
        mock = MagicMock()
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Temporary failure")
            return MagicMock(content='{"result": "success"}')

        mock.generate_with_system = side_effect
        return mock

    @pytest.mark.asyncio
    async def test_orchestrator_handles_agent_failure(
        self, mock_llm_with_failure: MagicMock
    ) -> None:
        """Test that orchestrator handles agent failures gracefully."""
        orchestrator = AgentOrchestrator()

        plot_agent = PlotAgent(name="Plot Agent", llm=mock_llm_with_failure)
        orchestrator.register_agent(plot_agent)

        # First call will fail
        result1 = await plot_agent.execute({"genre": "fantasy"})
        assert result1.success is False

        # Second call should succeed (mock recovers)
        result2 = await plot_agent.execute({"genre": "fantasy"})
        assert result2.success is True


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def full_setup(self, tmp_path) -> dict:
        """Create full setup with all agents."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content='{"title": "Test", "content": "Test content"}')
        )

        memory = MemSearchAdapter(base_path=str(tmp_path / "memory"))

        return {
            "llm": mock_llm,
            "memory": memory,
            "orchestrator": AgentOrchestrator(),
        }

    @pytest.mark.asyncio
    async def test_minimal_end_to_end(self, full_setup: dict) -> None:
        """Test minimal end-to-end workflow."""
        llm = full_setup["llm"]
        orchestrator = full_setup["orchestrator"]

        # Register all key agents
        plot_agent = PlotAgent(name="Plot Agent", llm=llm)
        orchestrator.register_agent(plot_agent)

        # Run a simple workflow
        orchestrator.define_workflow("minimal", [
            WorkflowStep(agent_name="Plot Agent", input_transform=lambda x: x),
        ])

        result = await orchestrator.run_workflow("minimal", {
            "genre": "fantasy",
            "target_chapters": 10,
        })

        assert result.success is True
