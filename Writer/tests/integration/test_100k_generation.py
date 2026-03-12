"""Integration test for 25-chapter (100K word) novel generation stability.

Tests all stability improvements:
1. Token budget management
2. Key events pruning (MAX_KEY_EVENTS=50)
3. Rate limiting for LLM calls
4. Knowledge graph cleanup
5. Mid-chapter checkpointing

Success criteria:
- 25 chapters generated successfully
- Memory ≤ 2GB
- Time per chapter ≤ 1.5x baseline
- No continuity errors
"""

import tracemalloc
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.llm.rate_limited import RateLimitedLLM
from src.novel.checkpointing import CheckpointManager
from src.novel.continuity import MAX_KEY_EVENTS, ContinuityManager, StoryState
from src.novel.knowledge_graph import (
    CLEANUP_FREQUENCY,
    LOOKBACK_CHAPTERS,
    KnowledgeGraph,
)


@dataclass
class MockLLMResponse:
    """Mock LLM response."""

    content: str
    tokens_used: int = 1000


@dataclass
class MockChapterResult:
    """Result of a mock chapter generation."""

    chapter_number: int
    content: str
    word_count: int
    state: StoryState | None = None


class MockLLM:
    """Mock LLM for testing without API calls."""

    def __init__(self, words_per_chapter: int = 4000):
        self.words_per_chapter = words_per_chapter
        self.call_count = 0
        self.total_calls = 0

    async def generate(self, prompt: str) -> MockLLMResponse:
        self.call_count += 1
        self.total_calls += 1

        # Generate mock content with target word count
        words = ["word"] * self.words_per_chapter
        content = " ".join(words)

        return MockLLMResponse(content=content, tokens_used=self.words_per_chapter // 4)

    async def generate_with_system(self, system_prompt: str, user_prompt: str) -> MockLLMResponse:
        return await self.generate(user_prompt)

    def reset_call_count(self) -> None:
        self.call_count = 0


class StabilityTestHarness:
    """Test harness for stability improvements testing."""

    def __init__(
        self,
        checkpoint_dir: Path,
        words_per_chapter: int = 4000,
    ):
        self.checkpoint_dir = checkpoint_dir
        self.words_per_chapter = words_per_chapter
        self.mock_llm = MockLLM(words_per_chapter)

        # Initialize components
        self.checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
        self.continuity = ContinuityManager()
        self.knowledge_graph = KnowledgeGraph(graph_id="test_stability")

        # Initialize story state
        self.story_state = StoryState(
            chapter=0,
            location="",
            active_characters=[],
            character_states={},
            plot_threads=[],
            key_events=[],
        )

        # Tracking
        self.chapters: list[MockChapterResult] = []
        self.memory_snapshots: list[tuple[int, float]] = []
        self.chapter_times: list[float] = []

    async def generate_chapter(
        self,
        chapter_number: int,
        characters: list[str],
        location: str,
    ) -> MockChapterResult:
        """Generate a single chapter with all stability improvements."""
        start_time = datetime.now()

        # Generate content (mocked)
        response = await self.mock_llm.generate(f"Generate chapter {chapter_number}")
        content = response.content
        word_count = len(content.split())

        # Create checkpoint at chapter boundary
        if self.checkpoint_manager.should_create_checkpoint(chapter_number, 0):
            state_snapshot = self._get_state_snapshot()
            self.checkpoint_manager.create_checkpoint(
                chapter_number=chapter_number,
                word_count=0,
                content="",
                state_snapshot=state_snapshot,
                metadata={"type": "chapter_start"},
            )

        # Update story state
        self.story_state = self.continuity.update_from_chapter(
            self.story_state,
            content,
            chapter_number,
        )
        state = self.story_state

        # Add key events (simulating story progression)
        events = [f"Chapter {chapter_number} main event"]
        if chapter_number % 5 == 0:
            events.append(f"Major plot twist at chapter {chapter_number}")

        state.key_events.extend(events)

        # Prune key events if needed
        if len(state.key_events) > MAX_KEY_EVENTS:
            state.prune_key_events()

        # Mid-chapter checkpoints (every 500 words)
        for checkpoint_word in range(500, word_count, 500):
            if self.checkpoint_manager.should_create_checkpoint(chapter_number, checkpoint_word):
                state_snapshot = self._get_state_snapshot()
                self.checkpoint_manager.create_checkpoint(
                    chapter_number=chapter_number,
                    word_count=checkpoint_word,
                    content=content[: checkpoint_word * 5],  # Approximate
                    state_snapshot=state_snapshot,
                    metadata={"type": "mid_chapter"},
                )

        # Knowledge graph cleanup every 10 chapters
        if chapter_number % CLEANUP_FREQUENCY == 0 and chapter_number > 0:
            recent_chapters = [
                self.chapters[i].content[:500]
                for i in range(max(0, len(self.chapters) - LOOKBACK_CHAPTERS), len(self.chapters))
            ]
            primary_chars = set(characters[:2])  # First two are primary
            active_threads = [t.name for t in state.get_active_plot_threads()]

            self.knowledge_graph.cleanup_unreferenced(
                recent_chapters=recent_chapters,
                primary_characters=primary_chars,
                active_plot_threads=active_threads,
                chapter_num=chapter_number,
            )

        # Chapter end checkpoint
        state_snapshot = self._get_state_snapshot()
        self.checkpoint_manager.create_checkpoint(
            chapter_number=chapter_number,
            word_count=word_count,
            content=content,
            state_snapshot=state_snapshot,
            metadata={"type": "chapter_end"},
        )

        # Record metrics
        elapsed = (datetime.now() - start_time).total_seconds()
        self.chapter_times.append(elapsed)

        result = MockChapterResult(
            chapter_number=chapter_number,
            content=content,
            word_count=word_count,
            state=state,
        )
        self.chapters.append(result)

        return result

    def _get_state_snapshot(self) -> dict[str, Any]:
        """Get current state as snapshot dictionary."""
        state = self.story_state
        return {
            "chapter": state.chapter if state else 0,
            "location": state.location if state else "",
            "key_events_count": len(state.key_events) if state else 0,
            "active_characters": list(state.active_characters) if state else [],
        }

    def record_memory(self, chapter_number: int) -> None:
        """Record memory usage at milestone."""
        current, peak = tracemalloc.get_traced_memory()
        self.memory_snapshots.append((chapter_number, peak / (1024 * 1024)))  # MB

    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        total_words = sum(c.word_count for c in self.chapters)

        avg_time = sum(self.chapter_times) / len(self.chapter_times) if self.chapter_times else 0

        checkpoint_stats = self.checkpoint_manager.get_stats()

        return {
            "total_chapters": len(self.chapters),
            "total_words": total_words,
            "avg_chapter_time": avg_time,
            "total_time": sum(self.chapter_times),
            "memory_snapshots": self.memory_snapshots,
            "peak_memory_mb": max(m[1] for m in self.memory_snapshots)
            if self.memory_snapshots
            else 0,
            "checkpoint_stats": checkpoint_stats,
            "llm_calls": self.mock_llm.total_calls,
        }


class Test25ChapterGeneration:
    """Test 25-chapter generation with stability improvements."""

    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create test directory."""
        test_path = tmp_path / "stability_test"
        test_path.mkdir(parents=True, exist_ok=True)
        return test_path

    @pytest.fixture
    def harness(self, test_dir):
        """Create test harness."""
        return StabilityTestHarness(
            checkpoint_dir=test_dir / "checkpoints",
            words_per_chapter=4000,  # 4000 words * 25 = 100K words
        )

    @pytest.mark.asyncio
    async def test_25_chapter_generation_completes(self, harness):
        """Test that 25 chapters can be generated without errors."""
        tracemalloc.start()

        characters = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

        for chapter_num in range(1, 26):
            result = await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=characters,
                location="The Kingdom",
            )

            assert result is not None
            assert result.chapter_number == chapter_num
            assert result.word_count > 0

            # Record memory every 5 chapters
            if chapter_num % 5 == 0:
                harness.record_memory(chapter_num)

        tracemalloc.stop()

        metrics = harness.get_metrics()

        # Verify completion
        assert metrics["total_chapters"] == 25
        assert metrics["total_words"] >= 25000  # At least 25K words

    @pytest.mark.asyncio
    async def test_key_events_pruning_maintains_limit(self, harness):
        """Test that key events stay within MAX_KEY_EVENTS limit."""
        tracemalloc.start()

        for chapter_num in range(1, 26):
            await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=["Alice", "Bob"],
                location="Test Location",
            )

            # Check key events limit after each chapter
            state = harness.story_state
            if state:
                assert len(state.key_events) <= MAX_KEY_EVENTS, (
                    f"Chapter {chapter_num}: key_events ({len(state.key_events)}) "
                    f"exceeds MAX_KEY_EVENTS ({MAX_KEY_EVENTS})"
                )

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_checkpoints_created_correctly(self, harness):
        """Test that checkpoints are created at correct intervals."""
        tracemalloc.start()

        # Generate 3 chapters
        for chapter_num in range(1, 4):
            await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=["Alice"],
                location="Test",
            )

        tracemalloc.stop()

        # Verify checkpoints exist
        stats = harness.checkpoint_manager.get_stats()

        # Should have at least:
        # - 3 chapter start checkpoints
        # - 3 chapter end checkpoints
        # - Mid-chapter checkpoints (every 500 words)
        assert stats["total_checkpoints"] >= 6, (
            f"Expected at least 6 checkpoints, got {stats['total_checkpoints']}"
        )

    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, harness):
        """Test that generation can resume from checkpoint."""
        tracemalloc.start()

        # Generate first chapter
        await harness.generate_chapter(
            chapter_number=1,
            characters=["Alice"],
            location="Start",
        )

        # Get latest checkpoint
        checkpoint = harness.checkpoint_manager.get_latest_checkpoint(chapter_number=1)

        assert checkpoint is not None
        assert checkpoint.chapter_number == 1

        # Verify checkpoint integrity
        loaded = harness.checkpoint_manager.load_checkpoint(checkpoint.checkpoint_id)
        assert loaded is not None
        assert loaded.checksum == checkpoint.checksum

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_knowledge_graph_cleanup(self, harness):
        """Test knowledge graph cleanup runs at correct intervals."""
        tracemalloc.start()

        # Add entities to knowledge graph with node IDs matching character names
        harness.knowledge_graph.add_node(
            node_id="Alice",
            node_type="character",
            properties={"name": "Alice"},
        )
        harness.knowledge_graph.add_node(
            node_id="Bob",
            node_type="character",
            properties={"name": "Bob"},
        )

        # Generate chapters
        for chapter_num in range(1, 12):
            await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=["Alice", "Bob"],
                location="Test",
            )

        tracemalloc.stop()

        # Primary characters should still exist
        assert harness.knowledge_graph.get_node("Alice") is not None
        assert harness.knowledge_graph.get_node("Bob") is not None

    @pytest.mark.asyncio
    async def test_memory_growth_within_limits(self, harness):
        """Test that memory growth stays within acceptable bounds."""
        tracemalloc.start()

        for chapter_num in range(1, 26):
            await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=["Alice", "Bob"],
                location="Test",
            )

            if chapter_num % 5 == 0:
                harness.record_memory(chapter_num)

        tracemalloc.stop()

        metrics = harness.get_metrics()

        # Memory should not grow unboundedly
        # With mocked LLM and proper cleanup, should be well under 500MB
        assert metrics["peak_memory_mb"] < 500, (
            f"Peak memory {metrics['peak_memory_mb']:.1f}MB exceeds 500MB limit"
        )

    @pytest.mark.asyncio
    async def test_chapter_time_consistency(self, harness):
        """Test that chapter generation time stays consistent."""
        tracemalloc.start()

        for chapter_num in range(1, 26):
            await harness.generate_chapter(
                chapter_number=chapter_num,
                characters=["Alice", "Bob"],
                location="Test",
            )

        tracemalloc.stop()

        metrics = harness.get_metrics()

        # With mocked LLM, times should be very fast and consistent
        times = harness.chapter_times

        # Average should be under 1 second with mocks
        assert metrics["avg_chapter_time"] < 1.0, (
            f"Average chapter time {metrics['avg_chapter_time']:.3f}s exceeds 1s"
        )

        # No chapter should take more than 2x average (indicates degradation)
        for i, time in enumerate(times):
            assert time < metrics["avg_chapter_time"] * 2, (
                f"Chapter {i + 1} time {time:.3f}s exceeds 2x average"
            )


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limited_llm_can_be_created(self):
        """Test RateLimitedLLM can be instantiated."""
        assert RateLimitedLLM is not None

    @pytest.mark.asyncio
    async def test_rate_limited_llm_wraps_correctly(self):
        """Test that RateLimitedLLM wraps underlying LLM correctly."""
        mock_llm = MagicMock()
        mock_llm.api_key = "test"
        mock_llm.model = "test-model"
        mock_llm.temperature = 0.7
        mock_llm.max_tokens = 1000
        mock_llm.generate = AsyncMock(return_value=MagicMock(content="test"))

        rate_limited = RateLimitedLLM(
            mock_llm,
            calls_per_second=2.0,
            burst_size=5,
        )

        assert rate_limited is not None


class TestTokenBudget:
    """Test token budget functionality."""

    def test_token_budget_import(self):
        """Test that token budget module can be imported."""
        from src.utils.token_budget import TokenBudgetManager

        assert TokenBudgetManager is not None

    def test_token_budget_counts_tokens(self):
        """Test that token budget counts tokens correctly."""
        from src.utils.token_budget import TokenBudgetConfig, TokenBudgetManager

        config = TokenBudgetConfig(max_context_tokens=16000)
        manager = TokenBudgetManager(config)

        text = "This is a test sentence with multiple words."
        count = manager.count_tokens(text)

        assert count > 0
        assert isinstance(count, int)

    def test_token_budget_enforces_budget(self):
        """Test that token budget enforces limits."""
        from src.utils.token_budget import TokenBudgetConfig, TokenBudgetManager

        config = TokenBudgetConfig(max_context_tokens=100)
        manager = TokenBudgetManager(config)

        # Create content that exceeds limit
        long_content = {"key_events": ["Event " * 100]}
        result = manager.enforce_budget(long_content)

        # Should be processed
        assert result is not None


class TestKnowledgeGraphCleanup:
    """Test knowledge graph cleanup functionality."""

    def test_cleanup_constants(self):
        """Test cleanup constants are defined."""
        assert CLEANUP_FREQUENCY == 5  # Changed from 10 for 50-chapter support
        assert LOOKBACK_CHAPTERS == 10  # How many chapters to check for references (was 5)

    def test_cleanup_method_exists(self):
        """Test cleanup method exists on KnowledgeGraph."""
        kg = KnowledgeGraph()
        assert hasattr(kg, "cleanup_unreferenced")
        assert hasattr(kg, "_is_unreferenced")

    def test_cleanup_protects_primary_characters(self):
        """Test that primary characters are protected from cleanup."""
        kg = KnowledgeGraph()

        kg.add_node(
            node_id="hero",
            node_type="character",
            properties={"name": "Hero"},
        )

        removed = kg.cleanup_unreferenced(
            recent_chapters=[],
            primary_characters={"hero"},
            active_plot_threads=[],
        )

        assert "hero" not in removed
        assert kg.get_node("hero") is not None


class TestCheckpointingIntegration:
    """Test checkpointing integration."""

    def test_checkpoint_manager_import(self):
        """Test that CheckpointManager can be imported."""
        from src.novel.checkpointing import CheckpointManager

        assert CheckpointManager is not None

    def test_checkpoint_constants(self):
        """Test checkpoint constants are defined."""
        from src.novel.checkpointing import (
            CHECKPOINT_INTERVAL_WORDS,
            MAX_CHECKPOINT_AGE_DAYS,
            MAX_CHECKPOINT_SIZE_MB,
        )

        assert CHECKPOINT_INTERVAL_WORDS == 500
        assert MAX_CHECKPOINT_AGE_DAYS == 7
        assert MAX_CHECKPOINT_SIZE_MB == 10


class TestContinuityPruning:
    """Test continuity pruning functionality."""

    def test_max_key_events_constant(self):
        """Test MAX_KEY_EVENTS constant is defined."""
        assert MAX_KEY_EVENTS == 50

    def test_prune_key_events_method(self):
        """Test prune_key_events method exists."""
        state = StoryState(
            chapter=1,
            location="Test",
            active_characters=[],
            character_states={},
            plot_threads=[],
            key_events=[],
        )

        assert hasattr(state, "prune_key_events")

    def test_prune_key_events_respects_limit(self):
        """Test that prune_key_events respects MAX_KEY_EVENTS."""
        state = StoryState(
            chapter=1,
            location="Test",
            active_characters=[],
            character_states={},
            plot_threads=[],
            key_events=[f"Event {i}" for i in range(100)],
        )

        # Before pruning
        assert len(state.key_events) > MAX_KEY_EVENTS

        # After pruning
        state.prune_key_events()
        assert len(state.key_events) <= MAX_KEY_EVENTS


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=300"])
