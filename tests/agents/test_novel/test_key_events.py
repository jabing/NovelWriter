"""Tests for key events pruning in continuity management."""

import pytest

from src.novel_agent.novel.continuity import (
    MAX_KEY_EVENTS,
    CharacterState,
    PlotThread,
    StoryState,
    is_critical_event,
)


class TestIsCriticalEvent:
    """Tests for is_critical_event function."""

    def test_character_death(self) -> None:
        """Test detecting character death as critical."""
        assert is_critical_event("Alice died in battle") is True
        assert is_critical_event("Bob was killed by the dragon") is True
        assert is_critical_event("Charlie sacrificed himself") is True

    def test_revelation(self) -> None:
        """Test detecting revelation as critical."""
        assert is_critical_event("Alice discovered the truth") is True
        assert is_critical_event("Bob revealed his secret") is True

    def test_relationship_change(self) -> None:
        """Test detecting relationship changes as critical."""
        assert is_critical_event("Alice and Bob married") is True
        assert is_critical_event("Charlie betrayed the group") is True

    def test_status_change(self) -> None:
        """Test detecting status changes as critical."""
        assert is_critical_event("Alice was crowned Queen") is True
        assert is_critical_event("Bob was imprisoned") is True

    def test_item_acquisition(self) -> None:
        """Test detecting item acquisition as critical."""
        assert is_critical_event("Alice obtained the Sword of Light") is True
        assert is_critical_event("Bob found the Crystal Key") is True

    def test_non_critical_event(self) -> None:
        """Test non-critical events."""
        assert is_critical_event("Alice walked to the market") is False
        assert is_critical_event("Bob ate dinner") is False
        assert is_critical_event("They traveled to the next town") is False


class TestStoryStatePruning:
    """Tests for StoryState.prune_key_events method."""

    @pytest.fixture
    def story_state(self) -> StoryState:
        """Create a basic story state."""
        return StoryState(
            chapter=10,
            location="Crystal Palace",
            active_characters=["Alice", "Bob"],
            character_states={
                "Alice": CharacterState(
                    name="Alice", status="alive", location="Crystal Palace", physical_form="human"
                ),
                "Bob": CharacterState(
                    name="Bob", status="alive", location="Crystal Palace", physical_form="human"
                ),
            },
            plot_threads=[
                PlotThread(name="Main Quest", status="active"),
            ],
            key_events=[],
        )

    def test_no_pruning_needed(self, story_state: StoryState) -> None:
        """Test when pruning is not needed."""
        story_state.key_events = ["Event 1", "Event 2", "Event 3"]
        removed, climax = story_state.prune_key_events(max_events=10)
        assert removed == 0
        assert len(story_state.key_events) == 3

    def test_pruning_with_no_critical(self, story_state: StoryState) -> None:
        """Test pruning when no events are critical."""
        # Add 75 non-critical events
        story_state.key_events = [f"Minor event {i}" for i in range(75)]
        removed, climax = story_state.prune_key_events(max_events=50)
        assert removed == 25
        assert len(story_state.key_events) == 50

    def test_pruning_preserves_critical(self, story_state: StoryState) -> None:
        """Test that critical events are preserved."""
        # Mix of critical and non-critical
        story_state.key_events = [
            "Minor event 1",
            "Alice died in battle",  # Critical
            "Minor event 2",
            "Bob was crowned King",  # Critical
        ] + [f"Minor event {i}" for i in range(3, 100)]

        removed, climax = story_state.prune_key_events(max_events=50)

        # Critical events should be preserved
        assert "Alice died in battle" in story_state.key_events
        assert "Bob was crowned King" in story_state.key_events

    def test_pruning_keeps_recent(self, story_state: StoryState) -> None:
        """Test that recent events are prioritized."""
        story_state.key_events = [f"Event {i}" for i in range(100)]
        removed, _ = story_state.prune_key_events(max_events=50)

        # Most recent events should be kept
        assert "Event 99" in story_state.key_events
        assert "Event 98" in story_state.key_events

    def test_climax_detection(self, story_state: StoryState) -> None:
        """Test climax detection when many recent events are critical."""
        # Create events with high critical density at end
        story_state.key_events = [f"Minor event {i}" for i in range(30)] + [
            "Alice died",
            "Bob was killed",
            "Castle fell",
            "War ended",
            "Truth revealed",
        ] * 10
        removed, climax = story_state.prune_key_events(max_events=50)
        assert climax is True

    def test_climax_increases_limit(self, story_state: StoryState) -> None:
        """Test that climax increases effective limit."""
        # Create climax scenario
        story_state.key_events = [
            "Alice died",
            "Bob was crowned",
            "Truth revealed",
        ] * 20  # 60 critical events

        removed, climax = story_state.prune_key_events(max_events=50)

        # During climax, limit is 50 * 1.5 = 75
        # Since all 60 are critical, all should be kept
        assert len(story_state.key_events) == 60

    def test_ensure_character_continuity(self, story_state: StoryState) -> None:
        """Test character continuity preservation."""
        all_events = [
            "Alice started her journey",  # Alice's only event
        ] + [f"Bob event {i}" for i in range(60)]

        story_state.key_events = all_events[:50]  # Pruned without Alice
        story_state.ensure_character_continuity(all_events)

        # Alice should now be in key_events
        assert any("Alice" in e for e in story_state.key_events)

    def test_character_not_lost_after_pruning(self, story_state: StoryState) -> None:
        """Test that characters mentioned early aren't lost."""
        # Alice mentioned once in event 1
        story_state.key_events = [
            "Alice found the sword",  # Critical, will be kept
        ] + [f"Minor event {i}" for i in range(1, 100)]

        removed, _ = story_state.prune_key_events(max_events=50)

        # Alice should still be present
        assert any("Alice" in e for e in story_state.key_events)


class TestMAXKeyEvents:
    """Tests for MAX_KEY_EVENTS constant."""

    def test_max_key_events_value(self) -> None:
        """Test that MAX_KEY_EVENTS is set correctly."""
        assert MAX_KEY_EVENTS == 50

    def test_max_key_events_is_reasonable(self) -> None:
        """Test that MAX_KEY_EVENTS is within reasonable bounds."""
        # Should be enough to cover ~25 chapters of plot
        assert 30 <= MAX_KEY_EVENTS <= 100
