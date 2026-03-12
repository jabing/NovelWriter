"""Unit tests for hierarchical story state management.

This module tests the HierarchicalStoryState class and related data structures
used for 100+ chapter novel generation.
"""

from pathlib import Path

import pytest

from src.novel.continuity import CharacterState, PlotThread
from src.novel.hierarchical_state import (
    CHAPTERS_PER_ARC,
    MAX_CACHED_ARCS,
    MAX_CACHED_CHAPTERS,
    GlobalStoryState,
    HierarchicalStoryState,
)
from src.novel.summaries import ArcSummary, ChapterSummary


class TestGlobalStoryState:
    """Test GlobalStoryState dataclass."""

    def test_create_global_state(self) -> None:
        """Test creating a global story state."""
        state = GlobalStoryState(
            novel_id="test_novel",
            genre="fantasy",
        )
        assert state.novel_id == "test_novel"
        assert state.genre == "fantasy"
        assert state.current_arc == 1
        assert state.total_chapters == 0

    def test_global_state_with_characters(self) -> None:
        """Test global state with character data."""
        characters = {
            "Hero": CharacterState(
                name="Hero",
                status="alive",
                location="Castle",
                physical_form="human",
            )
        }
        state = GlobalStoryState(
            novel_id="test",
            genre="fantasy",
            main_characters=characters,
        )
        assert "Hero" in state.main_characters
        assert state.main_characters["Hero"].status == "alive"

    def test_global_state_with_plot_threads(self) -> None:
        """Test global state with plot threads."""
        threads = [
            PlotThread(name="Main Quest", status="active"),
            PlotThread(name="Romance", status="pending"),
        ]
        state = GlobalStoryState(
            novel_id="test",
            genre="fantasy",
            main_plot_threads=threads,
        )
        assert len(state.main_plot_threads) == 2
        assert state.main_plot_threads[0].name == "Main Quest"


class TestHierarchicalStoryStateInit:
    """Test HierarchicalStoryState initialization."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_initialization(self, state: HierarchicalStoryState) -> None:
        """Test state initialization."""
        assert state.global_state is not None
        assert state.global_state.novel_id == "test_novel"
        assert state.global_state.genre == "fantasy"

    def test_directories_created(self, state: HierarchicalStoryState) -> None:
        """Test that storage directories are created."""
        assert state.storage_path.exists()
        assert (state.storage_path / "arcs").exists()
        assert (state.storage_path / "chapters").exists()

    def test_empty_caches_on_init(self, state: HierarchicalStoryState) -> None:
        """Test that caches are empty on initialization."""
        assert len(state._arc_cache) == 0
        assert len(state._chapter_cache) == 0


class TestArcNumberCalculation:
    """Test arc number calculation logic."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_first_arc(self, state: HierarchicalStoryState) -> None:
        """Test arc calculation for first arc."""
        assert state.get_arc_number(1) == 1
        assert state.get_arc_number(5) == 1
        assert state.get_arc_number(10) == 1

    def test_second_arc(self, state: HierarchicalStoryState) -> None:
        """Test arc calculation for second arc."""
        assert state.get_arc_number(11) == 2
        assert state.get_arc_number(15) == 2
        assert state.get_arc_number(20) == 2

    def test_later_arcs(self, state: HierarchicalStoryState) -> None:
        """Test arc calculation for later arcs."""
        assert state.get_arc_number(21) == 3
        assert state.get_arc_number(50) == 5
        assert state.get_arc_number(100) == 10

    def test_chapters_per_arc_constant(self) -> None:
        """Verify CHAPTERS_PER_ARC constant."""
        assert CHAPTERS_PER_ARC == 10


class TestChapterSummaryManagement:
    """Test chapter summary save/load operations."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_save_chapter_summary(self, state: HierarchicalStoryState, temp_storage: Path) -> None:
        """Test saving a chapter summary."""
        summary = ChapterSummary(
            chapter_number=1,
            title="The Beginning",
            summary="The hero begins their journey.",
            key_events=["Hero leaves home"],
        )
        state.save_chapter_summary(summary)

        # Check file was created
        expected_path = temp_storage / "test_novel" / "chapters" / "chapter_0001.json"
        assert expected_path.exists()

    def test_load_chapter_summary(self, state: HierarchicalStoryState) -> None:
        """Test loading a chapter summary."""
        # First save
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary="Test content",
            key_events=["Event A", "Event B"],
        )
        state.save_chapter_summary(summary)

        # Then load
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.chapter_number == 1
        assert loaded.title == "Test Chapter"
        assert loaded.key_events == ["Event A", "Event B"]

    def test_load_nonexistent_chapter(self, state: HierarchicalStoryState) -> None:
        """Test loading a chapter that doesn't exist."""
        loaded = state.get_chapter_summary(999)
        assert loaded is None

    def test_chapter_caching(self, state: HierarchicalStoryState) -> None:
        """Test that chapter summaries are cached properly."""
        summary = ChapterSummary(
            chapter_number=1,
            title="Cached Chapter",
            summary="This should be cached",
        )
        state.save_chapter_summary(summary)

        # First load - should be cached
        loaded1 = state.get_chapter_summary(1)
        assert loaded1 is not None

        # Second load - should come from cache
        loaded2 = state.get_chapter_summary(1)
        assert loaded2 is not None
        assert loaded1 is loaded2  # Same object reference

    def test_lru_eviction(self, state: HierarchicalStoryState) -> None:
        """Test LRU cache eviction when exceeding max size."""
        # Save more than MAX_CACHED_CHAPTERS
        for i in range(1, MAX_CACHED_CHAPTERS + 5):
            summary = ChapterSummary(
                chapter_number=i,
                title=f"Chapter {i}",
                summary=f"Summary {i}",
            )
            state.save_chapter_summary(summary)

        # Cache should not exceed max
        assert len(state._chapter_cache) <= MAX_CACHED_CHAPTERS

    def test_cache_move_to_end(self, state: HierarchicalStoryState) -> None:
        """Test that accessing an item moves it to end of LRU."""
        # Save several chapters
        for i in range(1, 5):
            summary = ChapterSummary(
                chapter_number=i,
                title=f"Chapter {i}",
                summary=f"Summary {i}",
            )
            state.save_chapter_summary(summary)

        # Access chapter 1 (should move to end)
        state.get_chapter_summary(1)

        # Chapter 1 should be the most recently accessed
        # (last item in OrderedDict)
        last_key = list(state._chapter_cache.keys())[-1]
        assert last_key == 1


class TestArcSummaryManagement:
    """Test arc summary save/load operations."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_save_arc_summary(self, state: HierarchicalStoryState, temp_storage: Path) -> None:
        """Test saving an arc summary."""
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="The Beginning Arc",
            summary="The story begins with the hero's journey.",
        )
        state.save_arc_summary(summary)

        # Check file was created
        expected_path = temp_storage / "test_novel" / "arcs" / "arc_001.json"
        assert expected_path.exists()

    def test_load_arc_summary(self, state: HierarchicalStoryState) -> None:
        """Test loading an arc summary."""
        # First save
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary="Arc summary content",
            major_events=["Event 1", "Event 2"],
        )
        state.save_arc_summary(summary)

        # Then load
        loaded = state.get_arc_summary(1)
        assert loaded is not None
        assert loaded.arc_number == 1
        assert loaded.title == "Test Arc"
        assert loaded.major_events == ["Event 1", "Event 2"]

    def test_load_nonexistent_arc(self, state: HierarchicalStoryState) -> None:
        """Test loading an arc that doesn't exist."""
        loaded = state.get_arc_summary(999)
        assert loaded is None

    def test_arc_caching(self, state: HierarchicalStoryState) -> None:
        """Test that arc summaries are cached properly."""
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Cached Arc",
            summary="This should be cached",
        )
        state.save_arc_summary(summary)

        # First load - should be cached
        loaded1 = state.get_arc_summary(1)
        assert loaded1 is not None

        # Second load - should come from cache
        loaded2 = state.get_arc_summary(1)
        assert loaded2 is not None
        assert loaded1 is loaded2  # Same object reference

    def test_arc_lru_eviction(self, state: HierarchicalStoryState) -> None:
        """Test LRU cache eviction for arcs."""
        # Save more than MAX_CACHED_ARCS
        for i in range(1, MAX_CACHED_ARCS + 5):
            summary = ArcSummary(
                arc_number=i,
                start_chapter=(i - 1) * 10 + 1,
                end_chapter=i * 10,
                title=f"Arc {i}",
                summary=f"Arc summary {i}",
            )
            state.save_arc_summary(summary)

        # Cache should not exceed max
        assert len(state._arc_cache) <= MAX_CACHED_ARCS


class TestContextGeneration:
    """Test context generation for chapter writing."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState with sample data."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_context_includes_global_state(self, state: HierarchicalStoryState) -> None:
        """Test that context includes global state."""
        context = state.get_context_for_chapter(1)
        assert "全局状态" in context
        assert "test_novel" in context or "总章数" in context

    def test_context_includes_previous_chapter(self, state: HierarchicalStoryState) -> None:
        """Test that context includes previous chapter details."""
        # Add a previous chapter
        prev_summary = ChapterSummary(
            chapter_number=1,
            title="Previous Chapter",
            summary="What happened before.",
            key_events=["Previous event"],
        )
        state.save_chapter_summary(prev_summary)

        context = state.get_context_for_chapter(2)
        assert "第1章" in context or "前一章" in context

    def test_context_includes_recent_chapters(self, state: HierarchicalStoryState) -> None:
        """Test that context includes last 5 chapter summaries."""
        # Add multiple chapters
        for i in range(1, 10):
            summary = ChapterSummary(
                chapter_number=i,
                title=f"Chapter {i}",
                summary=f"Summary for chapter {i}",
            )
            state.save_chapter_summary(summary)

        context = state.get_context_for_chapter(10)
        # Should include chapters 5-9 (last 5 before chapter 10)
        assert "第5章" in context or "第9章" in context

    def test_context_includes_arc_summary(self, state: HierarchicalStoryState) -> None:
        """Test that context includes current arc summary."""
        arc_summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="First Arc",
            summary="The beginning of the story.",
        )
        state.save_arc_summary(arc_summary)

        context = state.get_context_for_chapter(5)
        assert "第1卷" in context or "First Arc" in context

    def test_empty_context_for_first_chapter(self, state: HierarchicalStoryState) -> None:
        """Test context generation for first chapter with no history."""
        context = state.get_context_for_chapter(1)
        # Should only have global state
        assert "全局状态" in context
        assert len(context) > 0


class TestStateUpdate:
    """Test state update after chapter generation."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_update_after_chapter(self, state: HierarchicalStoryState) -> None:
        """Test updating state after chapter generation."""
        summary = ChapterSummary(
            chapter_number=5,
            title="Chapter 5",
            summary="The hero advances.",
        )
        state.update_after_chapter(5, summary)

        assert state.current_chapter == 5
        assert state.global_state is not None
        assert state.global_state.total_chapters == 5

    def test_update_saves_chapter_summary(self, state: HierarchicalStoryState) -> None:
        """Test that update saves the chapter summary."""
        summary = ChapterSummary(
            chapter_number=1,
            title="Test",
            summary="Test summary",
        )
        state.update_after_chapter(1, summary)

        # Should be able to load it back
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.title == "Test"

    def test_update_updates_arc_number(self, state: HierarchicalStoryState) -> None:
        """Test that update updates current arc number."""
        summary = ChapterSummary(
            chapter_number=15,
            title="Chapter 15",
            summary="Second arc chapter.",
        )
        state.update_after_chapter(15, summary)

        assert state.global_state is not None
        assert state.global_state.current_arc == 2

    def test_update_saves_global_state(
        self, state: HierarchicalStoryState, temp_storage: Path
    ) -> None:
        """Test that update persists global state to disk."""
        summary = ChapterSummary(
            chapter_number=10,
            title="Chapter 10",
            summary="Tenth chapter.",
        )
        state.update_after_chapter(10, summary)

        # Check that global state file was updated
        global_path = temp_storage / "test_novel" / "global_state.json"
        assert global_path.exists()

        # Create new instance to verify persistence
        new_state = HierarchicalStoryState(temp_storage, "test_novel")
        assert new_state.global_state is not None
        assert new_state.global_state.total_chapters == 10


class TestCacheManagement:
    """Test cache management operations."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_clear_cache(self, state: HierarchicalStoryState) -> None:
        """Test clearing all caches."""
        # Add some items to cache
        for i in range(1, 4):
            summary = ChapterSummary(
                chapter_number=i,
                title=f"Chapter {i}",
                summary=f"Summary {i}",
            )
            state.save_chapter_summary(summary)

        arc = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Arc 1",
            summary="Arc summary",
        )
        state.save_arc_summary(arc)

        # Clear cache
        state.clear_cache()

        assert len(state._chapter_cache) == 0
        assert len(state._arc_cache) == 0

    def test_clear_cache_does_not_delete_files(self, state: HierarchicalStoryState) -> None:
        """Test that clearing cache doesn't delete saved files."""
        summary = ChapterSummary(
            chapter_number=1,
            title="Test",
            summary="Test summary",
        )
        state.save_chapter_summary(summary)

        state.clear_cache()

        # Should still be able to load from disk
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.title == "Test"


class TestGlobalStateSerialization:
    """Test global state serialization and deserialization."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def state(self, temp_storage: Path) -> HierarchicalStoryState:
        """Create a HierarchicalStoryState instance."""
        return HierarchicalStoryState(temp_storage, "test_novel")

    def test_serialize_with_characters(self, state: HierarchicalStoryState) -> None:
        """Test serialization with character data."""
        if state.global_state is None:
            return

        state.global_state.main_characters = {
            "Hero": CharacterState(
                name="Hero",
                status="alive",
                location="Castle",
                physical_form="human",
                relationships={"Mentor": "student"},
            )
        }
        state.save_global_state()

        # Reload and verify
        new_state = HierarchicalStoryState(state.storage_path.parent, "test_novel")
        assert "Hero" in new_state.global_state.main_characters
        hero = new_state.global_state.main_characters["Hero"]
        assert hero.status == "alive"
        assert hero.location == "Castle"

    def test_serialize_with_plot_threads(self, state: HierarchicalStoryState) -> None:
        """Test serialization with plot thread data."""
        if state.global_state is None:
            return

        state.global_state.main_plot_threads = [
            PlotThread(name="Main Quest", status="active"),
            PlotThread(name="Side Story", status="pending"),
        ]
        state.save_global_state()

        # Reload and verify
        new_state = HierarchicalStoryState(state.storage_path.parent, "test_novel")
        assert len(new_state.global_state.main_plot_threads) == 2
        assert new_state.global_state.main_plot_threads[0].name == "Main Quest"

    def test_serialize_with_world_rules(self, state: HierarchicalStoryState) -> None:
        """Test serialization with world rule data."""
        if state.global_state is None:
            return

        state.global_state.world_rules = {
            "magic_system": "elemental",
            "technology_level": "medieval",
        }
        state.save_global_state()

        # Reload and verify
        new_state = HierarchicalStoryState(state.storage_path.parent, "test_novel")
        assert new_state.global_state.world_rules["magic_system"] == "elemental"


class TestConstants:
    """Test module constants."""

    def test_chapters_per_arc(self) -> None:
        """Verify CHAPTERS_PER_ARC constant."""
        assert CHAPTERS_PER_ARC == 10

    def test_max_cached_chapters(self) -> None:
        """Verify MAX_CACHED_CHAPTERS constant."""
        assert MAX_CACHED_CHAPTERS == 10

    def test_max_cached_arcs(self) -> None:
        """Verify MAX_CACHED_ARCS constant."""
        assert MAX_CACHED_ARCS == 3
