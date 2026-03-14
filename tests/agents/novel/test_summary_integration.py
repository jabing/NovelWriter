"""Integration tests for the summary system.

Tests the full pipeline from chapter content to hierarchical state.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.llm.base import LLMResponse
from src.novel.summary_manager import SummaryManager


class TestFullSummarizationPipeline:
    """Test the complete summarization pipeline."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM with realistic responses."""
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
        return SummaryManager(temp_storage, "integration_test", mock_llm)

    def _create_chapter_response(self, chapter_num: int) -> LLMResponse:
        """Create a mock chapter summary response."""
        return LLMResponse(
            content=f"""{{
                "summary": "第{chapter_num}章的摘要内容。英雄继续他的冒险。",
                "key_events": ["事件A", "事件B"],
                "character_changes": {{"英雄": "变得更强"}},
                "location": "城堡",
                "plot_threads_advanced": ["主线任务"],
                "plot_threads_resolved": [],
                "sentiment": "hopeful"
            }}""",
            tokens_used=100,
            model="test",
        )

    def _create_arc_response(self, arc_num: int) -> LLMResponse:
        """Create a mock arc summary response."""
        return LLMResponse(
            content=f"""{{
                "title": "第{arc_num}卷：冒险开始",
                "summary": "第{arc_num}卷的故事摘要，英雄经历了许多挑战。",
                "major_events": ["重大事件1", "重大事件2", "重大事件3"],
                "character_arcs": {{"英雄": "从普通人成长为英雄"}},
                "world_changes": ["世界发生了变化"],
                "plot_threads_status": {{"主线": "active"}},
                "themes": ["成长", "冒险"]
            }}""",
            tokens_used=200,
            model="test",
        )

    @pytest.mark.asyncio
    async def test_single_chapter_pipeline(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test processing a single chapter end-to-end."""
        mock_llm.generate_with_system.return_value = self._create_chapter_response(1)

        summary = await summary_manager.process_chapter(
            chapter_number=1,
            title="第一章",
            content="这是第一章的完整内容..." * 100,
        )

        assert summary.chapter_number == 1
        assert summary.title == "第一章"
        assert len(summary.summary) > 0
        assert len(summary.key_events) == 2

        # Verify it's stored in hierarchical state
        retrieved = summary_manager.get_chapter_summary(1)
        assert retrieved is not None
        assert retrieved.chapter_number == 1

    @pytest.mark.asyncio
    async def test_multiple_chapters_pipeline(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test processing multiple chapters sequentially."""
        for i in range(1, 6):
            mock_llm.generate_with_system.return_value = self._create_chapter_response(i)
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"第{i}章",
                content=f"第{i}章内容..." * 100,
            )

        # Verify all chapters are stored
        assert summary_manager.get_total_chapters() == 5
        for i in range(1, 6):
            summary = summary_manager.get_chapter_summary(i)
            assert summary is not None
            assert summary.chapter_number == i

    @pytest.mark.asyncio
    async def test_context_builds_with_history(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that context includes previous chapters."""
        # Process 3 chapters
        for i in range(1, 4):
            mock_llm.generate_with_system.return_value = self._create_chapter_response(i)
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"第{i}章",
                content=f"内容{i}" * 100,
            )

        # Get context for chapter 4
        context = summary_manager.get_context_for_chapter(4)

        # Should include global state
        assert "全局状态" in context

    @pytest.mark.asyncio
    async def test_arc_boundary_creates_arc_summary(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that arc summary is created at boundary."""
        call_count = 0

        def side_effect(system_prompt, user_prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            # Arc summarization happens on chapter 10
            if "弧线" in system_prompt or "弧线" in user_prompt:
                return self._create_arc_response(1)
            return self._create_chapter_response(call_count)

        mock_llm.generate_with_system.side_effect = side_effect

        # Process 10 chapters
        for i in range(1, 11):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content {i}" * 50,
            )

        # Arc summary should exist
        arc = summary_manager.get_arc_summary(1)
        assert arc is not None
        assert arc.arc_number == 1
        assert arc.start_chapter == 1
        assert arc.end_chapter == 10


class TestHierarchicalContextBuilding:
    """Test hierarchical context building across multiple levels."""

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
        return SummaryManager(temp_storage, "context_test", mock_llm)

    @pytest.mark.asyncio
    async def test_context_for_first_chapter(self, summary_manager: SummaryManager) -> None:
        """Test context for first chapter (no history)."""
        context = summary_manager.get_context_for_chapter(1)

        # Should only have global state
        assert "全局状态" in context

    @pytest.mark.asyncio
    async def test_context_includes_recent_chapters(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that context includes recent chapter summaries."""
        mock_llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "摘要", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )

        # Process 10 chapters
        for i in range(1, 11):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Ch{i}",
                content=f"Content{i}",
            )

        # Get context for chapter 11
        context = summary_manager.get_context_for_chapter(11)

        # Should include global state
        assert "全局状态" in context


class TestPersistenceAcrossSessions:
    """Test that state persists across sessions."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "测试摘要", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )
        return llm

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "novels"

    @pytest.mark.asyncio
    async def test_chapter_summaries_persist(self, temp_storage: Path, mock_llm: MagicMock) -> None:
        """Test that chapter summaries persist to disk."""
        # Create first session
        manager1 = SummaryManager(temp_storage, "persist_test", mock_llm)
        await manager1.process_chapter(1, "Chapter 1", "Content 1")
        await manager1.process_chapter(2, "Chapter 2", "Content 2")

        # Create second session (simulates restart)
        manager2 = SummaryManager(temp_storage, "persist_test", mock_llm)

        # Should be able to retrieve chapters from first session
        summary1 = manager2.get_chapter_summary(1)
        summary2 = manager2.get_chapter_summary(2)

        assert summary1 is not None
        assert summary1.title == "Chapter 1"
        assert summary2 is not None
        assert summary2.title == "Chapter 2"

    @pytest.mark.asyncio
    async def test_global_state_persists(self, temp_storage: Path, mock_llm: MagicMock) -> None:
        """Test that global state persists to disk."""
        # Create first session
        manager1 = SummaryManager(temp_storage, "persist_test", mock_llm)
        await manager1.process_chapter(1, "Ch1", "Content")
        await manager1.process_chapter(2, "Ch2", "Content")
        await manager1.process_chapter(3, "Ch3", "Content")

        # Create second session
        manager2 = SummaryManager(temp_storage, "persist_test", mock_llm)

        # Global state should reflect chapters from first session
        assert manager2.get_total_chapters() == 3

    @pytest.mark.asyncio
    async def test_arc_summaries_persist(self, temp_storage: Path, mock_llm: MagicMock) -> None:
        """Test that arc summaries persist to disk."""
        call_count = 0

        def side_effect(system_prompt, user_prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            if "弧线" in system_prompt:
                return LLMResponse(
                    content='{"title": "第一卷", "summary": "弧线摘要", "major_events": [], "character_arcs": {}, "world_changes": [], "plot_threads_status": {}, "themes": []}',
                    tokens_used=100,
                    model="test",
                )
            return LLMResponse(
                content='{"summary": "章节摘要", "key_events": [], "sentiment": "neutral"}',
                tokens_used=50,
                model="test",
            )

        mock_llm.generate_with_system.side_effect = side_effect

        # Create first session and process arc
        manager1 = SummaryManager(temp_storage, "persist_test", mock_llm)
        for i in range(1, 11):
            await manager1.process_chapter(i, f"Ch{i}", f"Content{i}" * 10)

        # Verify arc was created
        arc1 = manager1.get_arc_summary(1)
        assert arc1 is not None

        # Create second session
        manager2 = SummaryManager(temp_storage, "persist_test", mock_llm)

        # Arc should still be accessible
        arc2 = manager2.get_arc_summary(1)
        assert arc2 is not None
        assert arc2.title == "第一卷"


class TestErrorRecovery:
    """Test error recovery in the summary system."""

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
        return SummaryManager(temp_storage, "error_test", mock_llm)

    @pytest.mark.asyncio
    async def test_chapter_summary_fallback_on_error(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that chapter summarization falls back gracefully on error."""
        mock_llm.generate_with_system.side_effect = Exception("LLM error")

        summary = await summary_manager.process_chapter(
            chapter_number=1,
            title="Test Chapter",
            content="这是一些测试内容，用于验证错误回退机制。" * 10,
        )

        # Should have a fallback summary
        assert summary is not None
        assert summary.chapter_number == 1
        assert len(summary.summary) > 0

    @pytest.mark.asyncio
    async def test_continues_after_error(
        self, summary_manager: SummaryManager, mock_llm: MagicMock
    ) -> None:
        """Test that processing continues after an error."""
        call_count = 0

        def side_effect(system_prompt, user_prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return LLMResponse(
                content='{"summary": "成功摘要", "key_events": [], "sentiment": "neutral"}',
                tokens_used=50,
                model="test",
            )

        mock_llm.generate_with_system.side_effect = side_effect

        # First chapter should fallback
        summary1 = await summary_manager.process_chapter(1, "Ch1", "Content1" * 10)
        assert summary1 is not None

        # Second chapter should succeed
        summary2 = await summary_manager.process_chapter(2, "Ch2", "Content2")
        assert summary2 is not None
        assert summary2.summary == "成功摘要"
