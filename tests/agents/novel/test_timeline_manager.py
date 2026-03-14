"""Tests for TimelineManager class."""

import json
from datetime import datetime

import pytest

from src.novel_agent.novel.timeline_manager import (
    TemporalRelation,
    TimelineEvent,
    TimelineManager,
    TimeUnit,
    create_timeline_manager,
)


class TestTimelineManagerInit:
    """Test TimelineManager initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        tm = TimelineManager()

        assert tm.timeline_id == "default"
        assert tm.storage_path is None
        assert len(tm._events) == 0
        assert len(tm._relations) == 0

    def test_custom_timeline_id(self):
        """Test initialization with custom timeline ID."""
        tm = TimelineManager(timeline_id="test_timeline")

        assert tm.timeline_id == "test_timeline"

    def test_with_storage_path(self, tmp_path):
        """Test initialization with storage path."""
        storage_path = tmp_path / "test_timeline"
        tm = TimelineManager(timeline_id="test", storage_path=storage_path)

        assert tm.storage_path == storage_path

    def test_load_from_nonexistent_storage(self, tmp_path):
        """Test initialization with non-existent storage path."""
        storage_path = tmp_path / "nonexistent"
        tm = TimelineManager(storage_path=storage_path)

        # Should not raise error
        assert len(tm._events) == 0
        assert len(tm._relations) == 0


class TestTimelineEventClass:
    """Test TimelineEvent class."""

    def test_timeline_event_initialization(self):
        """Test TimelineEvent initialization."""
        event = TimelineEvent(
            event_id="event_001",
            timestamp="Day 5, Morning",
            description="Alice discovers the anomaly",
            event_type="discovery",
            metadata={"location": "SETI Institute", "weather": "clear"},
            start_order=5,
            end_order=6,
            time_unit=TimeUnit.DAY,
        )

        assert event.event_id == "event_001"
        assert event.timestamp == "Day 5, Morning"
        assert event.description == "Alice discovers the anomaly"
        assert event.event_type == "discovery"
        assert event.metadata == {"location": "SETI Institute", "weather": "clear"}
        assert event.start_order == 5
        assert event.end_order == 6
        assert event.time_unit == TimeUnit.DAY
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.updated_at, datetime)

    def test_timeline_event_defaults(self):
        """Test TimelineEvent with default values."""
        event = TimelineEvent(
            event_id="event_002",
            timestamp="Chapter 3",
            description="Battle begins",
        )

        assert event.event_type == "generic"
        assert event.metadata == {}
        assert event.start_order is None
        assert event.end_order is None
        assert event.time_unit == TimeUnit.SCENE

    def test_to_dict_and_from_dict(self):
        """Test TimelineEvent serialization round-trip."""
        original = TimelineEvent(
            event_id="event_003",
            timestamp="Year 3025",
            description="Colony established",
            event_type="colony",
            metadata={"population": 1000},
            start_order=100,
            end_order=101,
            time_unit=TimeUnit.YEAR,
        )

        # Convert to dict
        data = original.to_dict()

        # Check dict structure
        assert data["event_id"] == "event_003"
        assert data["timestamp"] == "Year 3025"
        assert data["description"] == "Colony established"
        assert data["event_type"] == "colony"
        assert data["metadata"] == {"population": 1000}
        assert data["start_order"] == 100
        assert data["end_order"] == 101
        assert data["time_unit"] == "year"
        assert "created_at" in data
        assert "updated_at" in data

        # Convert back from dict
        restored = TimelineEvent.from_dict(data)

        assert restored.event_id == original.event_id
        assert restored.timestamp == original.timestamp
        assert restored.description == original.description
        assert restored.event_type == original.event_type
        assert restored.metadata == original.metadata
        assert restored.start_order == original.start_order
        assert restored.end_order == original.end_order
        assert restored.time_unit == original.time_unit
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at


class TestTimelineManagerAddEvent:
    """Test event operations."""

    @pytest.fixture
    def tm(self):
        """Create a fresh timeline manager."""
        return TimelineManager()

    def test_add_event_basic(self, tm):
        """Test adding a basic event."""
        event = tm.add_event(
            event_id="event_001",
            timestamp="Day 1, Morning",
            description="Alice arrives at the institute",
            event_type="arrival",
            metadata={"location": "SETI Institute"},
            start_order=1,
            end_order=2,
            time_unit=TimeUnit.DAY,
        )

        assert isinstance(event, TimelineEvent)
        assert event.event_id == "event_001"
        assert event.timestamp == "Day 1, Morning"
        assert event.description == "Alice arrives at the institute"
        assert event.event_type == "arrival"
        assert event.metadata == {"location": "SETI Institute"}
        assert event.start_order == 1
        assert event.end_order == 2
        assert event.time_unit == TimeUnit.DAY

        # Verify stored
        assert "event_001" in tm._events
        assert tm.get_event("event_001") == event

    def test_add_event_defaults(self, tm):
        """Test adding an event with default values."""
        event = tm.add_event(
            event_id="event_002",
            timestamp="Chapter 2",
            description="Mysterious signal detected",
        )

        assert event.event_type == "generic"
        assert event.metadata == {}
        assert event.start_order is None
        assert event.end_order is None
        assert event.time_unit == TimeUnit.SCENE

    def test_add_event_duplicate_id(self, tm):
        """Test adding event with duplicate ID raises error."""
        tm.add_event(
            event_id="test",
            timestamp="Day 1",
            description="First event",
        )

        with pytest.raises(ValueError, match="already exists"):
            tm.add_event(
                event_id="test",
                timestamp="Day 2",
                description="Second event",
            )

    def test_add_event_auto_save_with_storage(self, tmp_path):
        """Test that adding event triggers auto-save when storage configured."""
        storage_path = tmp_path / "test_timeline"
        tm = TimelineManager(storage_path=storage_path)

        tm.add_event(
            event_id="event_001",
            timestamp="Day 1",
            description="Test event",
        )

        # Verify file created
        events_file = storage_path / "events.json"
        assert events_file.exists()

        # Load and verify content
        with open(events_file, encoding="utf-8") as f:
            events_data = json.load(f)

        assert len(events_data) == 1
        assert events_data[0]["event_id"] == "event_001"
        assert events_data[0]["description"] == "Test event"


class TestTimelineManagerUpdateEvent:
    """Test event updates."""

    @pytest.fixture
    def tm_with_event(self):
        """Create a timeline manager with an event."""
        tm = TimelineManager()
        event = tm.add_event(
            event_id="event_001",
            timestamp="Day 1, Morning",
            description="Alice arrives",
            event_type="arrival",
            metadata={"location": "SETI"},
            start_order=1,
            end_order=2,
            time_unit=TimeUnit.DAY,
        )
        return tm, event

    def test_update_event_properties(self, tm_with_event):
        """Test updating event properties."""
        tm, original_event = tm_with_event

        updated = tm.update_event(
            event_id="event_001",
            timestamp="Day 1, Afternoon",
            description="Alice settles in",
            event_type="settlement",
            metadata={"status": "settled"},
            merge_metadata=True,
            start_order=2,
            end_order=3,
            time_unit=TimeUnit.DAY,
        )

        assert updated is not None
        assert updated.timestamp == "Day 1, Afternoon"
        assert updated.description == "Alice settles in"
        assert updated.event_type == "settlement"
        # Metadata merged
        assert updated.metadata == {"location": "SETI", "status": "settled"}
        assert updated.start_order == 2
        assert updated.end_order == 3
        assert updated.updated_at >= original_event.updated_at

    def test_update_event_replace_metadata(self, tm_with_event):
        """Test replacing metadata instead of merging."""
        tm, _ = tm_with_event

        updated = tm.update_event(
            event_id="event_001",
            metadata={"new": "data"},
            merge_metadata=False,
        )

        assert updated.metadata == {"new": "data"}

    def test_update_event_partial(self, tm_with_event):
        """Test updating only some fields."""
        tm, original_event = tm_with_event

        updated = tm.update_event(
            event_id="event_001",
            description="Updated description",
        )

        assert updated.timestamp == original_event.timestamp  # unchanged
        assert updated.description == "Updated description"  # updated
        assert updated.event_type == original_event.event_type  # unchanged
        assert updated.updated_at >= original_event.updated_at

    def test_update_nonexistent_event(self, tm_with_event):
        """Test updating non-existent event returns None."""
        tm, _ = tm_with_event

        updated = tm.update_event(
            event_id="nonexistent",
            description="Test",
        )

        assert updated is None

    def test_update_event_auto_save(self, tmp_path):
        """Test that updating event triggers auto-save."""
        storage_path = tmp_path / "test_timeline"
        tm = TimelineManager(storage_path=storage_path)

        tm.add_event(
            event_id="event_001",
            timestamp="Day 1",
            description="Original",
        )

        # Clear file to track new save
        events_file = storage_path / "events.json"
        original_mtime = events_file.stat().st_mtime

        # Update event
        tm.update_event("event_001", description="Updated")

        # Verify file updated
        assert events_file.stat().st_mtime > original_mtime


class TestTimelineManagerDeleteEvent:
    """Test event deletion."""

    @pytest.fixture
    def tm_with_events_and_relations(self):
        """Create a timeline manager with events and relations."""
        tm = TimelineManager()
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Event 1")
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Event 2")
        tm.add_event(event_id="event_003", timestamp="Day 3", description="Event 3")

        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_002",
            source_id="event_001",
            target_id="event_003",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_003",
            source_id="event_002",
            target_id="event_003",
            relation_type=TemporalRelation.BEFORE,
        )

        return tm

    def test_delete_event_without_cascade(self, tm_with_events_and_relations):
        """Test deleting event without cascading."""
        tm = tm_with_events_and_relations

        result = tm.delete_event("event_001", cascade=False)

        assert result is True
        assert "event_001" not in tm._events
        # Relations should remain (orphaned)
        assert "rel_001" in tm._relations
        assert "rel_002" in tm._relations

    def test_delete_event_with_cascade(self, tm_with_events_and_relations):
        """Test deleting event with cascading relation deletion."""
        tm = tm_with_events_and_relations

        result = tm.delete_event("event_001", cascade=True)

        assert result is True
        assert "event_001" not in tm._events
        # Relations connected to event_001 should be deleted
        assert "rel_001" not in tm._relations
        assert "rel_002" not in tm._relations
        # Other relations remain
        assert "rel_003" in tm._relations
        assert "event_002" in tm._events
        assert "event_003" in tm._events

    def test_delete_nonexistent_event(self, tm_with_events_and_relations):
        """Test deleting non-existent event returns False."""
        tm = tm_with_events_and_relations

        result = tm.delete_event("nonexistent")

        assert result is False


class TestTimelineManagerAddRelation:
    """Test temporal relation operations."""

    @pytest.fixture
    def tm_with_events(self):
        """Create a timeline manager with events."""
        tm = TimelineManager()
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Event 1")
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Event 2")
        tm.add_event(event_id="event_003", timestamp="Day 3", description="Event 3")
        return tm

    def test_add_relation_basic(self, tm_with_events):
        """Test adding a basic temporal relation."""
        tm = tm_with_events

        relation = tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        assert relation == ("event_001", "event_002", TemporalRelation.BEFORE)
        assert "rel_001" in tm._relations
        assert tm._relations["rel_001"] == relation

    def test_add_relation_duplicate_id(self, tm_with_events):
        """Test adding relation with duplicate ID raises error."""
        tm = tm_with_events
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        with pytest.raises(ValueError, match="already exists"):
            tm.add_relation(
                relation_id="rel_001",
                source_id="event_002",
                target_id="event_003",
                relation_type=TemporalRelation.AFTER,
            )

    def test_add_relation_nonexistent_source(self, tm_with_events):
        """Test adding relation with non-existent source event raises error."""
        tm = tm_with_events

        with pytest.raises(ValueError, match="Source event 'nonexistent' not found"):
            tm.add_relation(
                relation_id="rel_001",
                source_id="nonexistent",
                target_id="event_001",
                relation_type=TemporalRelation.BEFORE,
            )

    def test_add_relation_nonexistent_target(self, tm_with_events):
        """Test adding relation with non-existent target event raises error."""
        tm = tm_with_events

        with pytest.raises(ValueError, match="Target event 'nonexistent' not found"):
            tm.add_relation(
                relation_id="rel_001",
                source_id="event_001",
                target_id="nonexistent",
                relation_type=TemporalRelation.BEFORE,
            )

    def test_delete_relation(self, tm_with_events):
        """Test deleting a relation."""
        tm = tm_with_events
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        result = tm.delete_relation("rel_001")

        assert result is True
        assert "rel_001" not in tm._relations

    def test_delete_nonexistent_relation(self, tm_with_events):
        """Test deleting non-existent relation returns False."""
        tm = tm_with_events

        result = tm.delete_relation("nonexistent")

        assert result is False


class TestTimelineManagerQueryEvents:
    """Test event query operations."""

    @pytest.fixture
    def tm_with_various_events(self):
        """Create a timeline manager with various events."""
        tm = TimelineManager()
        tm.add_event(
            event_id="event_001",
            timestamp="Day 1, Morning",
            description="Arrival",
            event_type="arrival",
            time_unit=TimeUnit.DAY,
        )
        tm.add_event(
            event_id="event_002",
            timestamp="Day 1, Afternoon",
            description="Meeting",
            event_type="meeting",
            time_unit=TimeUnit.DAY,
        )
        tm.add_event(
            event_id="event_003",
            timestamp="Week 2",
            description="Travel",
            event_type="travel",
            time_unit=TimeUnit.WEEK,
        )
        tm.add_event(
            event_id="event_004",
            timestamp="Year 3025",
            description="Colony established",
            event_type="colony",
            time_unit=TimeUnit.YEAR,
        )
        return tm

    def test_find_events_by_type(self, tm_with_various_events):
        """Test finding events by event type."""
        tm = tm_with_various_events

        arrival_events = tm.find_events_by_type("arrival")
        assert len(arrival_events) == 1
        assert arrival_events[0].event_id == "event_001"

        meeting_events = tm.find_events_by_type("meeting")
        assert len(meeting_events) == 1
        assert meeting_events[0].event_id == "event_002"

        nonexistent_events = tm.find_events_by_type("nonexistent")
        assert len(nonexistent_events) == 0

    def test_find_events_by_timestamp(self, tm_with_various_events):
        """Test finding events by timestamp."""
        tm = tm_with_various_events

        day1_morning_events = tm.find_events_by_timestamp("Day 1, Morning")
        assert len(day1_morning_events) == 1
        assert day1_morning_events[0].event_id == "event_001"

        week2_events = tm.find_events_by_timestamp("Week 2")
        assert len(week2_events) == 1
        assert week2_events[0].event_id == "event_003"

    def test_find_events_by_time_unit(self, tm_with_various_events):
        """Test finding events by time unit."""
        tm = tm_with_various_events

        day_events = tm.find_events_by_time_unit(TimeUnit.DAY)
        assert len(day_events) == 2
        assert {e.event_id for e in day_events} == {"event_001", "event_002"}

        week_events = tm.find_events_by_time_unit(TimeUnit.WEEK)
        assert len(week_events) == 1
        assert week_events[0].event_id == "event_003"

        year_events = tm.find_events_by_time_unit(TimeUnit.YEAR)
        assert len(year_events) == 1
        assert year_events[0].event_id == "event_004"

    def test_get_relations(self, tm_with_various_events):
        """Test getting relations."""
        tm = tm_with_various_events
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_002",
            source_id="event_002",
            target_id="event_003",
            relation_type=TemporalRelation.BEFORE,
        )

        all_relations = tm.get_relations()
        assert len(all_relations) == 2
        assert ("event_001", "event_002", TemporalRelation.BEFORE) in all_relations
        assert ("event_002", "event_003", TemporalRelation.BEFORE) in all_relations

        event_002_relations = tm.get_relations(event_id="event_002")
        assert len(event_002_relations) == 2  # Both relations involve event_002

        event_004_relations = tm.get_relations(event_id="event_004")
        assert len(event_004_relations) == 0

    def test_get_events_in_order(self):
        """Test getting events in chronological order."""
        tm = TimelineManager()
        tm.add_event(event_id="event_003", timestamp="Day 3", description="Event 3", start_order=3)
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Event 1", start_order=1)
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Event 2", start_order=2)
        tm.add_event(event_id="event_no_order", timestamp="Unknown", description="No order")

        ascending_events = tm.get_events_in_order(ascending=True)
        assert [e.event_id for e in ascending_events] == ["event_001", "event_002", "event_003", "event_no_order"]

        descending_events = tm.get_events_in_order(ascending=False)
        assert [e.event_id for e in descending_events] == ["event_003", "event_002", "event_001", "event_no_order"]


class TestTimelineManagerValidation:
    """Test timeline validation."""

    def test_validate_temporal_consistency_empty(self):
        """Test validation on empty timeline."""
        tm = TimelineManager()

        issues = tm.validate_temporal_consistency()

        assert len(issues) == 0

    def test_validate_temporal_consistency_cycles(self):
        """Test detection of cycles in temporal relations."""
        tm = TimelineManager()
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Event 1")
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Event 2")
        tm.add_event(event_id="event_003", timestamp="Day 3", description="Event 3")

        # Create cycle: event_001 -> event_002 -> event_003 -> event_001
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_002",
            source_id="event_002",
            target_id="event_003",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_003",
            source_id="event_003",
            target_id="event_001",
            relation_type=TemporalRelation.BEFORE,
        )

        issues = tm.validate_temporal_consistency()

        assert len(issues) >= 1
        assert any("Cycle detected" in issue for issue in issues)

    def test_validate_temporal_consistency_conflicting_relations(self):
        """Test detection of conflicting relations."""
        tm = TimelineManager()
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Event 1")
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Event 2")

        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )
        tm.add_relation(
            relation_id="rel_002",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.AFTER,  # Conflict!
        )

        issues = tm.validate_temporal_consistency()

        assert len(issues) >= 1
        assert any("Conflicting relations" in issue for issue in issues)

    def test_validate_temporal_consistency_invalid_order(self):
        """Test detection of invalid start/end order."""
        tm = TimelineManager()
        tm.add_event(
            event_id="event_001",
            timestamp="Day 1",
            description="Event 1",
            start_order=10,
            end_order=5,  # end < start!
        )

        issues = tm.validate_temporal_consistency()

        assert len(issues) >= 1
        assert any("end_order" in issue for issue in issues) and any("start_order" in issue for issue in issues)


class TestTimelineManagerStorage:
    """Test timeline storage and persistence."""

    def test_save_and_load(self, tmp_path):
        """Test saving timeline to storage and loading it back."""
        storage_path = tmp_path / "test_timeline"

        # Create and populate timeline
        tm1 = TimelineManager(timeline_id="test", storage_path=storage_path)
        tm1.add_event(
            event_id="event_001",
            timestamp="Day 1, Morning",
            description="Arrival",
            event_type="arrival",
            metadata={"location": "SETI"},
        )
        tm1.add_event(event_id="event_002", timestamp="Day 2", description="Meeting")
        tm1.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        # Load new instance from same path
        tm2 = TimelineManager(timeline_id="test", storage_path=storage_path)

        # Verify data loaded
        assert len(tm2._events) == 2
        assert "event_001" in tm2._events
        assert "event_002" in tm2._events
        assert len(tm2._relations) == 1
        assert "rel_001" in tm2._relations

        # Verify event properties
        event_001 = tm2.get_event("event_001")
        assert event_001.timestamp == "Day 1, Morning"
        assert event_001.event_type == "arrival"
        assert event_001.metadata == {"location": "SETI"}

        # Verify relation
        assert tm2._relations["rel_001"] == ("event_001", "event_002", TemporalRelation.BEFORE)

    def test_auto_save_on_mutations(self, tmp_path):
        """Test that mutations trigger auto-save when storage configured."""
        storage_path = tmp_path / "test_timeline"
        tm = TimelineManager(storage_path=storage_path)

        # Add event - should trigger save
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Test")

        # Verify files created
        events_file = storage_path / "events.json"
        relations_file = storage_path / "relations.json"

        assert events_file.exists()
        assert relations_file.exists()  # Even empty relations file should exist

        # Verify event saved
        with open(events_file, encoding="utf-8") as f:
            events_data = json.load(f)
        assert len(events_data) == 1
        assert events_data[0]["event_id"] == "event_001"

    def test_load_corrupted_files(self, tmp_path):
        """Test handling of corrupted storage files."""
        storage_path = tmp_path / "test_timeline"
        storage_path.mkdir(parents=True)

        # Write invalid JSON
        events_file = storage_path / "events.json"
        with open(events_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        # Should not crash, should have empty timeline
        tm = TimelineManager(storage_path=storage_path)

        assert len(tm._events) == 0


class TestTimelineManagerStats:
    """Test timeline statistics and export."""

    def test_stats_empty(self):
        """Test statistics on empty timeline."""
        tm = TimelineManager()

        stats = tm.stats()

        assert stats["total_events"] == 0
        assert stats["total_relations"] == 0
        assert stats["event_types"] == {}
        assert stats["time_units"] == {}

    def test_stats_with_data(self):
        """Test statistics with populated timeline."""
        tm = TimelineManager()
        tm.add_event(
            event_id="event_001",
            timestamp="Day 1",
            description="Arrival",
            event_type="arrival",
            time_unit=TimeUnit.DAY,
        )
        tm.add_event(
            event_id="event_002",
            timestamp="Day 2",
            description="Meeting",
            event_type="meeting",
            time_unit=TimeUnit.DAY,
        )
        tm.add_event(
            event_id="event_003",
            timestamp="Week 2",
            description="Travel",
            event_type="travel",
            time_unit=TimeUnit.WEEK,
        )
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        stats = tm.stats()

        assert stats["total_events"] == 3
        assert stats["total_relations"] == 1
        assert stats["event_types"] == {"arrival": 1, "meeting": 1, "travel": 1}
        assert stats["time_units"] == {"day": 2, "week": 1}

    def test_export_to_dict(self):
        """Test exporting timeline to dictionary."""
        tm = TimelineManager(timeline_id="test_timeline")
        tm.add_event(
            event_id="event_001",
            timestamp="Day 1",
            description="Arrival",
            event_type="arrival",
        )
        tm.add_event(
            event_id="event_002",
            timestamp="Day 2",
            description="Second event",
            event_type="generic",
        )
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        export = tm.export_to_dict()

        assert export["timeline_id"] == "test_timeline"
        assert len(export["events"]) == 2
        assert len(export["relations"]) == 1
        assert "statistics" in export
        assert export["statistics"]["total_events"] == 2
        assert export["statistics"]["total_relations"] == 1

    def test_clear(self):
        """Test clearing all timeline data."""
        tm = TimelineManager()
        tm.add_event(event_id="event_001", timestamp="Day 1", description="Test")
        tm.add_event(event_id="event_002", timestamp="Day 2", description="Second event")
        tm.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        tm.clear()

        assert len(tm._events) == 0
        assert len(tm._relations) == 0
        assert len(tm._event_type_index) == 0
        assert len(tm._timestamp_index) == 0


class TestCreateTimelineManager:
    """Test factory function."""

    def test_create_timeline_manager_default(self):
        """Test creating timeline manager with default parameters."""
        tm = create_timeline_manager()

        assert tm.timeline_id == "default"
        assert tm.storage_path is not None
        assert str(tm.storage_path).replace('\\', '/').endswith('data/timelines/default')

    def test_create_timeline_manager_custom_id(self):
        """Test creating timeline manager with custom ID."""
        tm = create_timeline_manager(timeline_id="custom_timeline")

        assert tm.timeline_id == "custom_timeline"
        assert tm.storage_path is not None
        assert str(tm.storage_path).replace('\\', '/').endswith('data/timelines/custom_timeline')

    def test_create_timeline_manager_custom_storage_path(self, tmp_path):
        """Test creating timeline manager with custom storage path."""
        custom_path = tmp_path / "custom"
        tm = create_timeline_manager(timeline_id="test", storage_path=custom_path)

        assert tm.storage_path == custom_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
