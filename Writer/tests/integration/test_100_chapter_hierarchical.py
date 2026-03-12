"""Integration test for 100-chapter hierarchical memory system.

This test validates Phase 2 of the 100-chapter scaling plan:
1. HierarchicalStoryState with LRU caching
2. SummaryManager for rolling updates
3. RelevantFactInjector for context injection
4. ConsistencyVerifier for validation
5. Mock LLM for fast testing (no API costs)

The test simulates 100 chapters of generation to verify:
- Memory usage stays bounded (< 500MB)
- Context generation is fast (< 100ms)
- All systems integrate properly
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.novel.consistency_verifier import ConsistencyVerifier
from src.novel.continuity import CharacterState, StoryState
from src.novel.fact_database import FactType
from src.novel.fact_injector import RelevantFactInjector
from src.novel.hierarchical_state import HierarchicalStoryState
from src.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel.summary_manager import SummaryManager


class MockLLM:
    """Mock LLM for testing without API calls.

    Simulates LLM responses for:
    - Chapter summarization
    - Arc summarization
    """

    def __init__(self, delay: float = 0.01) -> None:
        """Initialize mock LLM.

        Args:
            delay: Artificial delay to simulate LLM latency
        """
        self.delay = delay
        self.call_count = 0

    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Any:
        """Mock LLM call with system and user prompts."""
        self.call_count += 1
        await asyncio.sleep(self.delay)

        # Check if this is chapter or arc summarization
        if "弧线" in system_prompt or "弧线" in user_prompt:
            # Arc summarization
            return MagicMock(
                content=json.dumps(
                    {
                        "title": f"第{((self.call_count // 10) + 1)}卷",
                        "summary": f"这是第{self.call_count}次调用的弧线摘要。故事继续发展。",
                        "major_events": ["事件A", "事件B", "事件C"],
                        "character_arcs": {"主角": "成长中"},
                        "world_changes": ["变化1"],
                        "plot_threads_status": {"主线": "active"},
                        "themes": ["成长", "冒险"],
                    }
                ),
                tokens_used=200,
                model="mock",
            )
        else:
            # Chapter summarization
            return MagicMock(
                content=json.dumps(
                    {
                        "summary": f"这是第{self.call_count}章的摘要。主角继续冒险旅程。",
                        "key_events": [f"事件{self.call_count}A", f"事件{self.call_count}B"],
                        "character_changes": {"主角": "变得更强大"},
                        "location": "测试地点",
                        "plot_threads_advanced": ["主线剧情"],
                        "plot_threads_resolved": [],
                        "sentiment": "hopeful",
                    }
                ),
                tokens_used=100,
                model="mock",
            )


def create_100_chapter_outline() -> DetailedOutline:
    """Create a 100-chapter outline with escalating complexity.

    Structure:
    - Arc 1 (1-10): Introduction
    - Arc 2 (11-20): Rising Action
    - Arc 3 (21-30): Challenges
    - Arc 4 (31-40): Dark Night
    - Arc 5 (41-50): Preparation
    - Arc 6 (51-60): Battle Phase 1
    - Arc 7 (61-70): Battle Phase 2
    - Arc 8 (71-80): Aftermath
    - Arc 9 (81-90): New Threats
    - Arc 10 (91-100): Final Resolution
    """
    chapters = []

    arc_themes = [
        (1, 10, "Introduction", "Academy"),
        (11, 20, "Rising Action", "Enchanted Forest"),
        (21, 30, "Challenges", "Kingdom of Eldoria"),
        (31, 40, "Dark Night", "Shadow Realm"),
        (41, 50, "Preparation", "Alliance Headquarters"),
        (51, 60, "Battle Phase 1", "Northern Front"),
        (61, 70, "Battle Phase 2", "Eastern Front"),
        (71, 80, "Aftermath", "Rebuilding"),
        (81, 90, "New Threats", "Uncharted Lands"),
        (91, 100, "Final Resolution", "Final Battlefield"),
    ]

    for start, end, arc_name, location in arc_themes:
        for i in range(start, end + 1):
            is_arc_start = i == start
            is_arc_end = i == end

            chapters.append(
                ChapterSpec(
                    number=i,
                    title=f"Chapter {i}: {arc_name} {'Begins' if is_arc_start else 'Ends' if is_arc_end else 'Continues'}",
                    summary=f"""
                    Chapter {i} events:
                    - Story continues in {location}
                    - Character development
                    - Plot advancement
                    {"- Major arc event" if is_arc_start or is_arc_end else ""}
                    """,
                    characters=["Hero", "Mentor", "Ally"],
                    location=location,
                    key_events=[
                        f"Event {i}A",
                        f"Event {i}B",
                    ],
                    plot_threads_resolved=[] if not is_arc_end else ["Minor thread"],
                    plot_threads_started=[] if not is_arc_start else ["New thread"],
                    character_states={
                        "Hero": "alive",
                        "Mentor": "alive",
                        "Ally": "alive",
                    },
                )
            )

    return DetailedOutline(title="100 Chapter Test Novel", chapters=chapters)


class TestHierarchicalStateIntegration:
    """Test hierarchical state system integration."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "hierarchical_test"

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        """Create mock LLM instance."""
        return MockLLM(delay=0.005)

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MockLLM) -> SummaryManager:
        """Create SummaryManager with mock LLM."""
        return SummaryManager(temp_storage, "test_novel", mock_llm)

    @pytest.fixture
    def fact_injector(self, temp_storage: Path) -> RelevantFactInjector:
        """Create FactInjector."""
        return RelevantFactInjector(temp_storage, "test_novel")

    @pytest.fixture
    def verifier(self) -> ConsistencyVerifier:
        """Create ConsistencyVerifier."""
        return ConsistencyVerifier()

    @pytest.fixture
    def hierarchical_state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create HierarchicalStoryState."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_initialization(
        self,
        summary_manager: SummaryManager,
        hierarchical_state: HierarchicalStoryState,
    ) -> None:
        """Test that all systems initialize properly."""
        # Verify hierarchical state
        assert hierarchical_state.global_state is not None
        assert hierarchical_state.global_state.novel_id == "test_novel"

        # Verify summary manager
        assert summary_manager.hierarchical_state is not None
        assert summary_manager.chapter_summarizer is not None
        assert summary_manager.arc_summarizer is not None

        # Verify initial state
        assert summary_manager.get_total_chapters() == 0
        assert summary_manager.get_current_arc() == 1

    @pytest.mark.asyncio
    async def test_single_chapter_processing(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test processing a single chapter."""
        content = "This is test chapter content for chapter 1."
        summary = await summary_manager.process_chapter(
            chapter_number=1,
            title="Test Chapter 1",
            content=content,
        )

        assert summary is not None
        assert summary.chapter_number == 1
        assert summary.title == "Test Chapter 1"
        assert len(summary.summary) > 0

        # Verify it's stored
        retrieved = summary_manager.get_chapter_summary(1)
        assert retrieved is not None
        assert retrieved.chapter_number == 1

    @pytest.mark.asyncio
    async def test_arc_boundary_detection(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test that arc summarization triggers at boundaries."""
        # Process chapters 1-10
        for i in range(1, 11):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}",
            )

        # Arc summary should be created
        arc_summary = summary_manager.get_arc_summary(1)
        assert arc_summary is not None
        assert arc_summary.arc_number == 1
        assert arc_summary.start_chapter == 1
        assert arc_summary.end_chapter == 10

    @pytest.mark.asyncio
    async def test_context_generation(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test context generation for chapter writing."""
        # Process a few chapters
        for i in range(1, 6):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content {i}",
            )

        # Get context for chapter 6
        context = summary_manager.get_context_for_chapter(6)

        # Should include global state
        assert "全局状态" in context

        # Should include previous chapters
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_fact_injection_integration(
        self,
        summary_manager: SummaryManager,
        fact_injector: RelevantFactInjector,
    ) -> None:
        """Test that facts can be added and retrieved."""
        # Add facts
        fact_injector.add_fact(
            fact_type=FactType.CHARACTER,
            content="Hero is brave and skilled",
            chapter_origin=1,
            importance=0.9,
            entities=["Hero"],
        )
        fact_injector.add_fact(
            fact_type=FactType.LOCATION,
            content="Academy is the starting location",
            chapter_origin=1,
            importance=0.7,
            entities=["Academy"],
        )

        # Get context for chapter 2
        context = fact_injector.get_context_string(
            current_chapter=2,
            active_entities=["Hero"],
        )

        assert len(context) > 0
        assert "相关事实" in context

    @pytest.mark.asyncio
    async def test_consistency_check_integration(
        self,
        summary_manager: SummaryManager,
        verifier: ConsistencyVerifier,
    ) -> None:
        """Test consistency verification with story state."""
        # Create story state with dead character
        story_state = StoryState(
            chapter=5,
            location="Forest",
            active_characters=["Hero"],
            character_states={
                "Hero": CharacterState(
                    name="Hero",
                    status="alive",
                    location="Forest",
                    physical_form="human",
                ),
                "Villain": CharacterState(
                    name="Villain",
                    status="dead",
                    location="Grave",
                    physical_form="none",
                ),
            },
        )

        # Test with bad content (dead character active)
        # Must use Chinese text that matches ACTION_PATTERNS in ConsistencyVerifier
        bad_content = "Villain 说：我回来了！他挥动手臂。"
        result = verifier.verify(
            chapter_content=bad_content,
            chapter_number=5,
            story_state=story_state,
        )

        assert result.is_consistent is False
        assert len(result.inconsistencies) > 0


class TestMockLLM10Chapters:
    """Fast test with 10 chapters for quick validation."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "10_chapter_test"

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        return MockLLM(delay=0.01)

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MockLLM) -> SummaryManager:
        return SummaryManager(temp_storage, "test_10", mock_llm)

    @pytest.mark.asyncio
    async def test_10_chapter_flow(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test 10 chapter generation flow."""
        for i in range(1, 11):
            summary = await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}",
            )
            assert summary is not None

        # Verify arc summary created
        arc = summary_manager.get_arc_summary(1)
        assert arc is not None

        # Verify all chapters stored
        assert summary_manager.get_total_chapters() == 10


class TestMockLLM50Chapters:
    """Medium-scale test with 50 chapters."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "50_chapter_test"

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        return MockLLM(delay=0.02)

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MockLLM) -> SummaryManager:
        return SummaryManager(temp_storage, "test_50", mock_llm)

    @pytest.mark.asyncio
    async def test_50_chapter_flow(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test 50 chapter generation with memory bounds."""
        import tracemalloc

        tracemalloc.start()

        for i in range(1, 51):
            summary = await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i} " * 10,
            )
            assert summary is not None

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should stay bounded
        assert peak < 500 * 1024 * 1024  # 500MB

        # Verify arc summaries
        for arc_num in range(1, 6):
            arc = summary_manager.get_arc_summary(arc_num)
            assert arc is not None


class TestMockLLM100Chapters:
    """Full-scale test with 100 chapters."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "100_chapter_test"

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        return MockLLM(delay=0.02)

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, mock_llm: MockLLM) -> SummaryManager:
        return SummaryManager(temp_storage, "test_100", mock_llm)

    @pytest.mark.asyncio
    async def test_100_chapter_complete_flow(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test complete 100 chapter generation."""
        import time
        import tracemalloc

        tracemalloc.start()
        start_time = time.time()

        # Process 100 chapters
        for i in range(1, 101):
            summary = await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i} " * 10,
            )
            assert summary is not None

            # Log progress every 10 chapters
            if i % 10 == 0:
                elapsed = time.time() - start_time
                current, peak = tracemalloc.get_traced_memory()
                print(f"\n=== Progress: {i}/100 chapters ===")
                print(f"Time: {elapsed:.1f}s")
                print(f"Memory: {peak / 1024 / 1024:.1f}MB")

        elapsed = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print("\n=== Final Results ===")
        print(f"Total Time: {elapsed:.1f}s")
        print(f"Peak Memory: {peak / 1024 / 1024:.1f}MB")
        print(f"Total Chapters: {summary_manager.get_total_chapters()}")
        print(f"Current Arc: {summary_manager.get_current_arc()}")

        # Verify memory bounds
        assert peak < 500 * 1024 * 1024  # 500MB

        # Verify all arc summaries
        for arc_num in range(1, 11):
            arc = summary_manager.get_arc_summary(arc_num)
            assert arc is not None

        # Verify total chapters
        assert summary_manager.get_total_chapters() == 100
        assert summary_manager.get_current_arc() == 10

        # Verify context generation is fast
        context_start = time.time()
        context = summary_manager.get_context_for_chapter(101)
        context_time = time.time() - context_start
        assert context_time < 0.1  # 100ms
        assert len(context) > 0


class TestPersistenceAcrossSessions:
    """Test that state persists across sessions."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        return tmp_path / "persistence_test"

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        return MockLLM(delay=0.01)

    @pytest.mark.asyncio
    async def test_state_persistence(
        self,
        temp_storage: Path,
        mock_llm: MockLLM,
    ) -> None:
        """Test that hierarchical state persists."""
        # Session 1
        manager1 = SummaryManager(temp_storage, "persist_test", mock_llm)
        for i in range(1, 11):
            await manager1.process_chapter(
                chapter_number=i,
                title=f"Ch{i}",
                content=f"Content {i}",
            )

        # Session 2 (new instance, same storage)
        manager2 = SummaryManager(temp_storage, "persist_test", mock_llm)

        # Should have same state
        assert manager2.get_total_chapters() == 10
        assert manager2.get_current_arc() == 1

        # Should be able to load summaries
        for i in range(1, 11):
            summary = manager2.get_chapter_summary(i)
            assert summary is not None

        # Arc summary should exist
        arc = manager2.get_arc_summary(1)
        assert arc is not None
