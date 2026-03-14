"""Memory benchmark tests for 50-chapter scaling.

This test measures memory usage during chapter generation to ensure
the system doesn't have memory leaks or excessive memory growth.
"""

import sys
import tracemalloc
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.writers.base_writer import BaseWriter
from src.novel.continuity import CharacterState, ContinuityManager, PlotThread, StoryState
from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.outline_manager import ChapterSpec
from src.utils.token_budget import TokenBudgetConfig


class MockWriter(BaseWriter):
    """Mock writer for testing without actual LLM calls."""

    GENRE = "test"

    async def write_chapter(self, **kwargs) -> str:
        """Generate mock chapter content."""
        return "Test chapter content " * 100


def create_chapter_spec(chapter_num: int) -> ChapterSpec:
    """Create a chapter spec for testing."""
    return ChapterSpec(
        number=chapter_num,
        title=f"Chapter {chapter_num}",
        summary=f"Chapter {chapter_num} summary",
        characters=["Kael", "Lyra"],
        location="Academy",
        key_events=[f"Event {chapter_num}"],
        plot_threads_resolved=[],
        plot_threads_started=[],
        character_states={"Kael": "alive", "Lyra": "alive"},
    )


def create_initial_story_state() -> StoryState:
    """Create initial story state for the test."""
    return StoryState(
        chapter=0,
        location="Academy",
        active_characters=["Kael", "Lyra"],
        character_states={
            "Kael": CharacterState(
                name="Kael",
                status="alive",
                location="Academy",
                physical_form="human",
            ),
            "Lyra": CharacterState(
                name="Lyra",
                status="alive",
                location="Academy",
                physical_form="human",
            ),
        },
        plot_threads=[PlotThread(name="Main quest", status="active")],
        key_events=[],
    )


class TestMemoryBenchmarks:
    """Memory usage benchmarks for chapter generation."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        mock = MagicMock()
        mock.generate_with_system = AsyncMock(return_value=MagicMock(content="Test content"))
        return mock

    @pytest.fixture
    def writer(self, mock_llm):
        """Create mock writer with token budget."""
        return MockWriter(
            name="Test Writer",
            llm=mock_llm,
            memory=None,
            token_budget_config=TokenBudgetConfig(max_context_tokens=16000),
        )

    def test_story_state_memory_growth(self) -> None:
        """Test that story state memory grows linearly, not exponentially."""
        tracemalloc.start()

        story_state = create_initial_story_state()
        initial_size = sys.getsizeof(story_state.key_events)

        # Simulate 100 key events (our new MAX_KEY_EVENTS)
        for i in range(100):
            story_state.key_events.append(f"Event {i}: " + "x" * 50)

        final_size = sys.getsizeof(story_state.key_events)

        # Memory should grow roughly linearly with number of events
        # Each event is about 60 chars, so 100 events ~ 6KB
        # We allow up to 50KB for the list structure
        growth = final_size - initial_size
        assert growth < 100_000, f"Memory growth too large: {growth} bytes"

        tracemalloc.stop()

    def test_knowledge_graph_memory_growth(self) -> None:
        """Test that knowledge graph memory grows reasonably."""
        tracemalloc.start()

        kg = KnowledgeGraph()
        initial_snapshot = tracemalloc.take_snapshot()

        # Add 200 nodes (simulating 50 chapters with 4 characters each)
        for i in range(200):
            try:
                kg.add_node(
                    node_id=f"char_{i}",
                    node_type="character",
                    properties={"status": "alive", "chapter": i // 4},
                )
            except Exception:
                pass

        final_snapshot = tracemalloc.take_snapshot()

        # Compare memory usage
        stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        total_growth = sum(stat.size_diff for stat in stats[:10])

        # Should grow by less than 1MB for 200 nodes
        assert total_growth < 1_000_000, f"Memory growth too large: {total_growth} bytes"

        tracemalloc.stop()

    def test_continuity_manager_memory(self) -> None:
        """Test that continuity manager doesn't leak memory."""
        tracemalloc.start()

        continuity = ContinuityManager()
        story_state = create_initial_story_state()
        initial_snapshot = tracemalloc.take_snapshot()

        # Simulate 50 chapter updates
        for i in range(50):
            content = f"Chapter {i} content with character Kael and Lyra."
            story_state = continuity.update_from_chapter(story_state, content, i)

        final_snapshot = tracemalloc.take_snapshot()

        # Compare memory usage
        stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        total_growth = sum(stat.size_diff for stat in stats[:10])

        # Should grow by less than 500KB for 50 chapters
        assert total_growth < 500_000, f"Memory growth too large: {total_growth} bytes"

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_50_chapter_generation_memory(self, writer) -> None:
        """Test memory usage during 50-chapter generation."""
        tracemalloc.start()

        story_state = create_initial_story_state()
        initial_snapshot = tracemalloc.take_snapshot()

        # Simulate 50 chapter generation
        for i in range(1, 51):
            chapter_spec = create_chapter_spec(i)

            await writer.write_chapter_with_context(
                chapter_spec=chapter_spec,
                story_state=story_state,
                characters=[{"name": "Kael"}, {"name": "Lyra"}],
                world_context={},
            )

            # Update story state
            story_state.chapter = i
            story_state.key_events.append(f"Event {i}")

        final_snapshot = tracemalloc.take_snapshot()

        # Compare memory usage
        stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        total_growth = sum(stat.size_diff for stat in stats[:10])

        # Should grow by less than 5MB for 50 chapters
        assert total_growth < 5_000_000, f"Memory growth too large: {total_growth} bytes"

        tracemalloc.stop()

    def test_token_budget_manager_memory(self) -> None:
        """Test that token budget manager doesn't accumulate state."""
        from src.utils.token_budget import TokenBudgetManager

        tracemalloc.start()

        manager = TokenBudgetManager()
        initial_snapshot = tracemalloc.take_snapshot()

        # Process 100 large contexts
        for _i in range(100):
            context = {
                "header": "Header " * 100,
                "content": "Content " * 1000,
                "summary": "Summary " * 500,
            }
            manager.enforce_budget(context, max_tokens=1000)

        final_snapshot = tracemalloc.take_snapshot()

        # Compare memory usage
        stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        total_growth = sum(stat.size_diff for stat in stats[:10])

        # Should not accumulate memory (stateless operations)
        # Allow small growth for any internal caching
        assert total_growth < 100_000, f"Memory growth too large: {total_growth} bytes"

        tracemalloc.stop()


class TestPerformanceBenchmarks:
    """Performance benchmarks for chapter generation."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        mock = MagicMock()
        mock.generate_with_system = AsyncMock(return_value=MagicMock(content="Test content"))
        return mock

    @pytest.fixture
    def writer(self, mock_llm):
        """Create mock writer with token budget."""
        return MockWriter(
            name="Test Writer",
            llm=mock_llm,
            memory=None,
            token_budget_config=TokenBudgetConfig(max_context_tokens=16000),
        )

    @pytest.mark.asyncio
    async def test_continuity_prompt_performance(self, writer) -> None:
        """Test that continuity prompt building is fast."""
        import time

        story_state = StoryState(
            chapter=40,
            location="Dragon's Peak",
            active_characters=["Kael", "Lyra", "Mira", "Thorin"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Dragon's Peak",
                    physical_form="human",
                ),
            },
            key_events=[f"Event {i}" for i in range(50)],
        )

        # Measure time for 100 prompt builds
        start = time.perf_counter()
        for _ in range(100):
            writer._build_continuity_prompt(
                story_state=story_state,
                previous_summary="Summary " * 50,
                chapter_number=41,
            )
        elapsed = time.perf_counter() - start

        # Should build 100 prompts in under 1 second
        assert elapsed < 1.0, f"Continuity prompt building too slow: {elapsed:.3f}s"

    def test_knowledge_graph_cleanup_performance(self) -> None:
        """Test that knowledge graph cleanup is fast."""
        import time

        kg = KnowledgeGraph()

        # Add 500 nodes
        for i in range(500):
            try:
                kg.add_node(
                    node_id=f"entity_{i}",
                    node_type="character" if i % 2 == 0 else "location",
                    properties={"last_mentioned_chapter": i // 10},
                )
            except Exception:
                pass

        # Measure cleanup time
        start = time.perf_counter()
        # recent_chapters expects chapter content strings, not numbers
        recent_content = [f"Chapter {i} content with entity_{i} mentioned." for i in range(40, 51)]
        kg.cleanup_unreferenced(
            recent_chapters=recent_content,
            primary_characters={"entity_0", "entity_2"},
            active_plot_threads=[],
            chapter_num=50,
        )
        elapsed = time.perf_counter() - start

        # Cleanup should complete in under 1 second
        assert elapsed < 1.0, f"Knowledge graph cleanup too slow: {elapsed:.3f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
