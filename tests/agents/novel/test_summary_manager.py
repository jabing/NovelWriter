"""Tests for summary management system."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.llm.base import LLMResponse
from src.novel_agent.novel.continuity import CharacterState, PlotThread
from src.novel_agent.novel.summary_manager import SummaryManager


class TestSummaryManager:
    """Test SummaryManager class."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM instance."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        """Create a SummaryManager instance."""
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    def test_initialization(self, summary_manager: SummaryManager, temp_storage: Path) -> None:
        """Test summary manager initialization."""
        assert summary_manager.hierarchical_state is not None
        assert summary_manager.chapter_summarizer is not None
        assert summary_manager.arc_summarizer is not None

    def test_get_total_chapters_initial(self, summary_manager: SummaryManager) -> None:
        """Test initial total chapters is 0."""
        assert summary_manager.get_total_chapters() == 0

    def test_get_current_arc_initial(self, summary_manager: SummaryManager) -> None:
        """Test initial current arc is 1."""
        assert summary_manager.get_current_arc() == 1


class TestChapterProcessing:
    """Test chapter processing functionality."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "测试摘要", "key_events": ["事件1"], "sentiment": "neutral"}',
            tokens_used=100,
            model="test",
        )
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    @pytest.mark.asyncio
    async def test_process_chapter(self, summary_manager: SummaryManager) -> None:
        """Test processing a chapter."""
        summary = await summary_manager.process_chapter(
            chapter_number=1,
            title="第一章",
            content="这是第一章的内容。",
        )

        assert summary.chapter_number == 1
        assert summary.title == "第一章"
        assert summary.summary == "测试摘要"

    @pytest.mark.asyncio
    async def test_process_chapter_updates_total(self, summary_manager: SummaryManager) -> None:
        """Test that processing updates total chapters."""
        await summary_manager.process_chapter(
            chapter_number=1,
            title="Test",
            content="Content",
        )

        assert summary_manager.get_total_chapters() == 1

    @pytest.mark.asyncio
    async def test_process_chapter_saves_summary(self, summary_manager: SummaryManager) -> None:
        """Test that processing saves chapter summary."""
        await summary_manager.process_chapter(
            chapter_number=1,
            title="Test",
            content="Content",
        )

        # Should be able to retrieve the summary
        loaded = summary_manager.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.title == "Test"

    @pytest.mark.asyncio
    async def test_process_multiple_chapters(self, summary_manager: SummaryManager) -> None:
        """Test processing multiple chapters."""
        for i in range(1, 4):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content {i}",
            )

        assert summary_manager.get_total_chapters() == 3
        assert summary_manager.get_chapter_summary(1) is not None
        assert summary_manager.get_chapter_summary(2) is not None
        assert summary_manager.get_chapter_summary(3) is not None


class TestArcSummarization:
    """Test arc summarization functionality."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()

        # Default response for chapter summaries
        chapter_response = LLMResponse(
            content='{"summary": "章节摘要", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )

        # Response for arc summaries
        arc_response = LLMResponse(
            content='{"title": "第一卷", "summary": "弧线摘要", "major_events": [], "character_arcs": {}, "world_changes": [], "plot_threads_status": {}, "themes": []}',
            tokens_used=100,
            model="test",
        )

        # Return arc response for longer content (arc summarization)
        def side_effect(system_prompt, user_prompt, **kwargs):
            if "章节摘要" in user_prompt or len(user_prompt) < 500:
                return chapter_response
            return arc_response

        llm.generate_with_system.side_effect = side_effect
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    @pytest.mark.asyncio
    async def test_arc_summarization_triggered(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that arc summarization is triggered at chapter 10."""
        # Process 10 chapters
        for i in range(1, 11):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}" * 10,
            )

        # Arc summary should exist
        arc_summary = summary_manager.get_arc_summary(1)
        assert arc_summary is not None
        assert arc_summary.arc_number == 1
        assert arc_summary.start_chapter == 1
        assert arc_summary.end_chapter == 10

    @pytest.mark.asyncio
    async def test_no_arc_summarization_before_boundary(
        self, summary_manager: SummaryManager
    ) -> None:
        """Test that arc summarization is not triggered before chapter 10."""
        # Process 9 chapters
        for i in range(1, 10):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content {i}",
            )

        # Arc summary should not exist
        arc_summary = summary_manager.get_arc_summary(1)
        assert arc_summary is None

    @pytest.mark.asyncio
    async def test_second_arc_summarization(self, summary_manager: SummaryManager) -> None:
        """Test second arc summarization at chapter 20."""
        # Process 20 chapters
        for i in range(1, 21):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content {i}" * 10,
            )

        # Both arc summaries should exist
        arc1 = summary_manager.get_arc_summary(1)
        arc2 = summary_manager.get_arc_summary(2)

        assert arc1 is not None
        assert arc2 is not None
        assert arc2.start_chapter == 11
        assert arc2.end_chapter == 20


class TestShouldSummarizeArc:
    """Test arc summarization trigger logic."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    def test_should_summarize_at_arc_boundary(self, summary_manager: SummaryManager) -> None:
        """Test summarization at arc boundaries."""
        assert summary_manager._should_summarize_arc(10) is True
        assert summary_manager._should_summarize_arc(20) is True
        assert summary_manager._should_summarize_arc(30) is True

    def test_should_not_summarize_before_boundary(self, summary_manager: SummaryManager) -> None:
        """Test no summarization before boundaries."""
        assert summary_manager._should_summarize_arc(1) is False
        assert summary_manager._should_summarize_arc(5) is False
        assert summary_manager._should_summarize_arc(9) is False
        assert summary_manager._should_summarize_arc(11) is False


class TestContextGeneration:
    """Test context generation functionality."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "测试", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    def test_get_context_for_first_chapter(self, summary_manager: SummaryManager) -> None:
        """Test context generation for first chapter."""
        context = summary_manager.get_context_for_chapter(1)
        assert "全局状态" in context

    @pytest.mark.asyncio
    async def test_get_context_includes_previous_chapter(
        self, summary_manager: SummaryManager
    ) -> None:
        """Test that context includes previous chapter."""
        await summary_manager.process_chapter(1, "Ch1", "Content 1")

        context = summary_manager.get_context_for_chapter(2)
        assert "第1章" in context or "前一章" in context


class TestGlobalStateUpdates:
    """Test global state update functionality."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MagicMock) -> SummaryManager:
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    def test_update_global_characters_with_dict(self, summary_manager: SummaryManager) -> None:
        """Test updating global characters with dict data."""
        characters = {
            "Hero": {
                "name": "Hero",
                "status": "alive",
                "location": "Castle",
                "physical_form": "human",
            }
        }

        summary_manager.update_global_characters(characters)

        gs = summary_manager.hierarchical_state.global_state
        assert gs is not None
        assert "Hero" in gs.main_characters
        assert gs.main_characters["Hero"].status == "alive"

    def test_update_global_characters_with_state_objects(
        self, summary_manager: SummaryManager
    ) -> None:
        """Test updating global characters with CharacterState objects."""
        characters = {
            "Hero": CharacterState(
                name="Hero",
                status="alive",
                location="Forest",
                physical_form="human",
            )
        }

        summary_manager.update_global_characters(characters)

        gs = summary_manager.hierarchical_state.global_state
        assert gs is not None
        assert gs.main_characters["Hero"].location == "Forest"

    def test_update_global_plot_threads_with_dict(self, summary_manager: SummaryManager) -> None:
        """Test updating plot threads with dict data."""
        plot_threads = [
            {"name": "Main Quest", "status": "active"},
        ]

        summary_manager.update_global_plot_threads(plot_threads)

        gs = summary_manager.hierarchical_state.global_state
        assert gs is not None
        assert len(gs.main_plot_threads) == 1
        assert gs.main_plot_threads[0].name == "Main Quest"

    def test_update_global_plot_threads_with_objects(self, summary_manager: SummaryManager) -> None:
        """Test updating plot threads with PlotThread objects."""
        plot_threads = [
            PlotThread(name="Side Quest", status="pending"),
        ]

        summary_manager.update_global_plot_threads(plot_threads)

        gs = summary_manager.hierarchical_state.global_state
        assert gs is not None
        assert gs.main_plot_threads[0].name == "Side Quest"
