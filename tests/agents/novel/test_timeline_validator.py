"""Unit tests for TimelineValidator.

This module tests the TimelineValidator class for ensuring
- Event time ordering validation
- Time conflict detection (dead characters, missing characters)
- Interval validation
- Report generation
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.db.postgres_models import EventType, ImportanceLevel
from src.novel_agent.novel.timeline_validator import (
    Configuration,
    IntervalWarning,
    OrderViolation,
    Severity,
    TimeConflict,
    TimeConflictType,
    TimelineEventData,
    TimelineReport,
    TimelineValidator,
    create_timeline_validator,
)


class TestTimelineEventData:
    """Test TimelineEventData dataclass."""

    def test_creation(self) -> None:
        """Test creating TimelineEventData."""
        datetime.now()
        event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Alice appears in the story",
            importance=ImportanceLevel.HIGH.value,
        )

        assert event.event_id == "event_001"
        assert event.character_name == "Alice"
        assert event.chapter == 1

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Alice appears in the story",
            importance=ImportanceLevel.HIGH.value,
        )

        data = event.to_dict()

        assert data["event_id"] == "event_001"
        assert data["character_name"] == "Alice"
        assert data["chapter"] == 1

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        data = {
            "event_id": "event_001",
            "character_id": 1,
            "character_name": "Bob",
            "chapter": 2,
            "event_type": EventType.APPEARANCE.value,
            "description": "Bob appears",
            "importance": "medium",
        }

        event = TimelineEventData.from_dict(data)

        assert event.event_id == "event_001"
        assert event.character_name == "Bob"
        assert event.chapter == 2


class TestConfiguration:
    """Test Configuration dataclass."""

    def test_default(self) -> None:
        """Test default configuration."""
        config = Configuration()

        assert config.min_chapter_gap == 1
        assert config.max_chapter_gap == 50
        assert config.dead_character_action_threshold == 5

    def test_custom(self) -> None:
        """Test custom configuration."""
        config = Configuration(
            min_chapter_gap=2,
            max_chapter_gap=100,
            dead_character_action_threshold=10,
            missing_character_threshold=5,
            min_event_gap=1,
            max_event_gap=30,
        )

        assert config.min_chapter_gap == 2
        assert config.max_chapter_gap == 100
        assert config.max_event_gap == 30


class TestTimeConflict:
    """Test TimeConflict dataclass."""

    def test_creation(self) -> None:
        """Test creating TimeConflict."""
        conflict = TimeConflict(
            conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
            character_name="Alice",
            chapter=10,
            event_description="Alice speaks",
            reason="Character is dead",
            severity=Severity.ERROR,
        )

        assert conflict.conflict_type == TimeConflictType.DEAD_CHARACTER_ACTION.value
        assert conflict.character_name == "Alice"
        assert conflict.severity == Severity.ERROR

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        conflict = TimeConflict(
            conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
            character_name="Alice",
            chapter=10,
            event_description="Alice speaks",
            reason="Character is dead",
            severity=Severity.ERROR,
            evidence="Event type: appearance",
        )

        data = conflict.to_dict()

        assert data["conflict_type"] == TimeConflictType.DEAD_CHARACTER_ACTION.value
        assert data["severity"] == "error"


class TestOrderViolation:
    """Test OrderViolation dataclass."""

    def test_creation(self) -> None:
        """Test creating OrderViolation."""
        violation = OrderViolation(
            earlier_event="Alice died",
            later_event="Alice appears alive",
            earlier_chapter=5,
            later_chapter=10,
            reason="Resurrection without explanation",
            severity=Severity.ERROR,
        )

        assert violation.earlier_event == "Alice died"
        assert violation.later_chapter == 10
        assert violation.severity == Severity.ERROR

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        violation = OrderViolation(
            earlier_event="Alice died",
            later_event="Alice appears alive",
            earlier_chapter=5,
            later_chapter=10,
            reason="Resurrection without explanation",
            severity=Severity.ERROR,
        )

        data = violation.to_dict()

        assert data["earlier_chapter"] == 5
        assert data["later_chapter"] == 10
        assert data["severity"] == "error"


class TestIntervalWarning:
    """Test IntervalWarning dataclass."""

    def test_creation(self) -> None:
        """Test creating IntervalWarning."""
        warning = IntervalWarning(
            warning_type="too_short_interval",
            chapter_start=1,
            chapter_end=2,
            event_count=5,
            description="Events happen too quickly",
            severity=Severity.WARNING,
        )

        assert warning.warning_type == "too_short_interval"
        assert warning.chapter_start == 1
        assert warning.severity == Severity.WARNING

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        warning = IntervalWarning(
            warning_type="too_short_interval",
            chapter_start=1,
            chapter_end=2,
            event_count=5,
            description="Events happen too quickly",
            severity=Severity.WARNING,
            suggestion="Add more time passage",
        )

        data = warning.to_dict()

        assert data["warning_type"] == "too_short_interval"
        assert data["suggestion"] == "Add more time passage"


class TestTimelineReport:
    """Test TimelineReport dataclass."""

    def test_creation(self) -> None:
        """Test creating TimelineReport."""
        # Create with explicit lists
        conflict = TimeConflict(
            conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
            character_name="Alice",
            chapter=1,
            event_description="Test",
            reason="Test reason",
            severity=Severity.ERROR,
        )
        report = TimelineReport(
            novel_id="novel_001",
            total_events=10,
            conflicts=[conflict],
            order_violations=[],
            interval_warnings=[],
        )

        assert report.novel_id == "novel_001"
        assert report.total_events == 10
        assert report.total_conflicts == 1  # Computed property
        assert report.has_issues() is True

    def test_critical_count(self) -> None:
        """Test critical count calculation."""
        conflict1 = TimeConflict(
            conflict_type=TimeConflictType.BORN_AFTER_DEATH.value,
            character_name="A",
            chapter=1,
            event_description="",
            reason="",
            severity=Severity.CRITICAL,
        )

        conflict2 = TimeConflict(
            conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
            character_name="B",
            chapter=2,
            event_description="",
            reason="",
            severity=Severity.ERROR,
        )

        conflict3 = TimeConflict(
            conflict_type=TimeConflictType.MISSING_CHARACTER_ACTION.value,
            character_name="C",
            chapter=3,
            event_description="",
            reason="",
            severity=Severity.WARNING,
        )

        report = TimelineReport(
            novel_id="test",
            total_events=10,
            conflicts=[conflict1, conflict2, conflict3],
        )

        assert report.get_critical_count() == 1
        assert report.get_error_count() == 1  # Only conflict2 is ERROR
        assert report.has_issues() is True

    def test_no_issues(self) -> None:
        """Test report with no issues."""
        report = TimelineReport(
            novel_id="novel_001",
            total_events=10,
        )

        assert report.has_issues() is False
        assert report.total_conflicts == 0
        assert report.summary == ""

    def test_to_dict(self) -> None:
        """Test converting report to dictionary."""
        conflict = TimeConflict(
            conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
            character_name="Alice",
            chapter=10,
            event_description="Alice speaks",
            reason="Character is dead",
            severity=Severity.ERROR,
        )

        report = TimelineReport(
            novel_id="novel_001",
            total_events=10,
            conflicts=[conflict],
        )

        data = report.to_dict()

        assert data["novel_id"] == "novel_001"
        assert data["total_events"] == 10
        assert len(data["conflicts"]) == 1
        assert "validated_at" in data


class TestTimelineValidator:
    """Test TimelineValidator class."""

    @pytest.fixture
    def validator(self) -> TimelineValidator:
        """Create a TimelineValidator without database."""
        return TimelineValidator(postgres_client=None)

    @pytest.fixture
    def mock_postgres_client(self) -> MagicMock:
        """Create a mock PostgreSQL client."""
        client = MagicMock()
        client.list_characters = AsyncMock(return_value=[])
        client.session = MagicMock()
        return client

    @pytest.fixture
    def sample_events(self) -> list[TimelineEventData]:
        """Create sample events for testing."""
        return [
            TimelineEventData(
                event_id="event_001",
                character_id=1,
                character_name="Alice",
                chapter=1,
                event_type=EventType.APPEARANCE.value,
                description="Alice is introduced in the story",
                importance=ImportanceLevel.HIGH.value,
            ),
            TimelineEventData(
                event_id="event_002",
                character_id=1,
                character_name="Alice",
                chapter=5,
                event_type=EventType.MAJOR_EVENT.value,
                description="Alice fights the dragon",
                importance=ImportanceLevel.HIGH.value,
            ),
            TimelineEventData(
                event_id="event_003",
                character_id=1,
                character_name="Alice",
                chapter=10,
                event_type=EventType.DEATH.value,
                description="Alice died in battle",
                importance=ImportanceLevel.CRITICAL.value,
            ),
        ]

    @pytest.fixture
    def sample_character_states(self) -> dict[str, dict]:
        """Create sample character states for testing."""
        return {
            "Alice": {
                "birth_chapter": 1,
                "death_chapter": 10,
                "status": "deceased",
            },
            "Bob": {
                "birth_chapter": 3,
                "death_chapter": None,
                "status": "active",
            },
        }

    def test_init(self, validator: TimelineValidator) -> None:
        """Test validator initialization."""
        assert validator.postgres_client is None
        assert validator.config is not None
        assert isinstance(validator.config, Configuration)

    def test_init_with_postgres(self, mock_postgres_client: MagicMock) -> None:
        """Test validator initialization with PostgreSQL client."""
        validator = TimelineValidator(postgres_client=mock_postgres_client)

        assert validator.postgres_client is mock_postgres_client
        assert isinstance(validator.config, Configuration)

    @pytest.mark.asyncio
    async def test_load_events_without_postgres(self, validator: TimelineValidator) -> None:
        """Test _load_events returns empty list without PostgreSQL client."""
        events = await validator._load_events("novel_001")

        assert events == []

    def test_is_character_action(self, validator: TimelineValidator) -> None:
        """Test _is_character_action method."""
        # Action event
        action_event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Alice arrived",
            importance=ImportanceLevel.HIGH.value,
        )

        assert validator._is_character_action(action_event) is True

        # Death event is not an action
        death_event = TimelineEventData(
            event_id="event_002",
            character_id=1,
            character_name="Alice",
            chapter=10,
            event_type=EventType.DEATH.value,
            description="Alice died",
            importance=ImportanceLevel.CRITICAL.value,
        )

        assert validator._is_character_action(death_event) is False

    def test_is_memorial_reference(self, validator: TimelineValidator) -> None:
        """Test _is_memorial_reference method."""
        # Memorial reference
        memorial_event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=15,
            event_type=EventType.MAJOR_EVENT.value,
            description="Bob remembered Alice",
            importance=ImportanceLevel.HIGH.value,
        )

        assert validator._is_memorial_reference(memorial_event) is True

        # Action event (not memorial)
        action_event = TimelineEventData(
            event_id="event_002",
            character_id=1,
            character_name="Alice",
            chapter=15,
            event_type=EventType.MAJOR_EVENT.value,
            description="Alice fought the enemy",
            importance=ImportanceLevel.HIGH.value,
        )

        assert validator._is_memorial_reference(action_event) is False

    def test_check_dead_character_action(
        self, validator: TimelineValidator, sample_character_states: dict
    ) -> None:
        """Test _check_dead_character_action method."""
        validator._character_states = sample_character_states

        # Action after death
        action_event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=15,
            event_type=EventType.APPEARANCE.value,
            description="Alice appears",
            importance=ImportanceLevel.HIGH.value,
        )

        conflict = validator._check_dead_character_action(action_event)
        assert conflict is not None
        assert conflict.conflict_type == TimeConflictType.DEAD_CHARACTER_ACTION.value
        assert conflict.character_name == "Alice"
        assert conflict.severity == Severity.ERROR

        # Memorial reference (allowed)
        memorial_event = TimelineEventData(
            event_id="event_002",
            character_id=1,
            character_name="Alice",
            chapter=15,
            event_type=EventType.MAJOR_EVENT.value,
            description="Bob remembered Alice's sacrifice",
            importance=ImportanceLevel.HIGH.value,
        )

        conflict = validator._check_dead_character_action(memorial_event)
        assert conflict is None

        # Event before death
        before_death_event = TimelineEventData(
            event_id="event_003",
            character_id=1,
            character_name="Alice",
            chapter=5,
            event_type=EventType.APPEARANCE.value,
            description="Alice appears",
            importance=ImportanceLevel.HIGH.value,
        )

        conflict = validator._check_dead_character_action(before_death_event)
        assert conflict is None

    def test_check_missing_character_action(
        self, validator: TimelineValidator, sample_character_states: dict
    ) -> None:
        """Test _check_missing_character_action method."""
        validator._character_states = sample_character_states

        # Action before introduction
        action_event = TimelineEventData(
            event_id="event_001",
            character_id=2,
            character_name="Bob",
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Bob appears",
            importance=ImportanceLevel.HIGH.value,
        )

        conflict = validator._check_missing_character_action(action_event)
        assert conflict is not None
        assert conflict.conflict_type == TimeConflictType.MISSING_CHARACTER_ACTION.value
        assert conflict.character_name == "Bob"
        assert conflict.severity == Severity.WARNING

        # Event after introduction
        after_intro_event = TimelineEventData(
            event_id="event_002",
            character_id=2,
            character_name="Bob",
            chapter=5,
            event_type=EventType.APPEARANCE.value,
            description="Bob appears",
            importance=ImportanceLevel.HIGH.value,
        )

        conflict = validator._check_missing_character_action(after_intro_event)
        assert conflict is None

    def test_check_born_after_death(
        self, validator: TimelineValidator, sample_character_states: dict
    ) -> None:
        """Test _check_born_after_death method."""
        validator._character_states = sample_character_states

        # Birth event (not after death)
        birth_event = TimelineEventData(
            event_id="event_001",
            character_id=1,
            character_name="Alice",
            chapter=5,
            event_type=EventType.BIRTH.value,
            description="Alice was born",
            importance=ImportanceLevel.HIGH.value,
        )

        # Modify character state to have birth after death
        validator._character_states["Alice"]["birth_chapter"] = 5
        conflict = validator._check_born_after_death(birth_event)
        assert conflict is None  # Birth chapter equals event chapter, not after

        # Birth after death
        validator._character_states["Alice"]["birth_chapter"] = 15
        conflict = validator._check_born_after_death(birth_event)
        assert conflict is not None
        assert conflict.conflict_type == TimeConflictType.BORN_AFTER_DEATH.value
        assert conflict.severity == Severity.CRITICAL

    def test_detect_time_conflicts(
        self,
        validator: TimelineValidator,
        sample_events: list[TimelineEventData],
        sample_character_states: dict,
    ) -> None:
        """Test detect_time_conflicts method."""
        validator._character_states = sample_character_states

        # Add an action after death
        events = sample_events + [
            TimelineEventData(
                event_id="event_004",
                character_id=1,
                character_name="Alice",
                chapter=15,  # After death at chapter 10
                event_type=EventType.APPEARANCE.value,
                description="Alice speaks to the crowd",
                importance=ImportanceLevel.HIGH.value,
            ),
        ]

        conflicts = validator.detect_time_conflicts(events)

        assert len(conflicts) > 0
        # Find the dead character action conflict
        dead_conflict = next(
            (
                c
                for c in conflicts
                if c.conflict_type == TimeConflictType.DEAD_CHARACTER_ACTION.value
            ),
            None,
        )
        assert dead_conflict is not None
        assert dead_conflict.character_name == "Alice"

    def test_validate_event_order(
        self, validator: TimelineValidator, sample_events: list[TimelineEventData]
    ) -> None:
        """Test validate_event_order method."""
        # Events are already in order (chapters 1, 5, 10)
        violations = validator.validate_event_order(sample_events)

        # No violations expected for well-ordered events
        assert len(violations) == 0

        # Add resurrection without explanation
        events = sample_events + [
            TimelineEventData(
                event_id="event_004",
                character_id=1,
                character_name="Alice",
                chapter=12,  # After death at chapter 10
                event_type=EventType.APPEARANCE.value,
                description="Alice appears alive again",  # No resurrection explanation
                importance=ImportanceLevel.HIGH.value,
            ),
        ]

        violations = validator.validate_event_order(events)

        # Should detect resurrection without explanation
        assert len(violations) > 0
        res_violation = next(
            (v for v in violations if v.earlier_chapter == 10 and v.later_chapter == 12), None
        )
        assert res_violation is not None
        assert res_violation.severity == Severity.ERROR

    def test_validate_intervals(
        self, validator: TimelineValidator, sample_events: list[TimelineEventData]
    ) -> None:
        """Test validate_intervals method."""
        # Sample events have reasonable intervals
        warnings = validator.validate_intervals(sample_events)

        # No warnings expected for reasonable intervals
        assert len(warnings) == 0

        # Add events with too short interval (same chapter incompatible)
        events = [
            TimelineEventData(
                event_id="event_001",
                character_id=1,
                character_name="Alice",
                chapter=1,
                event_type=EventType.BIRTH.value,
                description="Alice was born",
                importance=ImportanceLevel.HIGH.value,
            ),
            TimelineEventData(
                event_id="event_002",
                character_id=1,
                character_name="Alice",
                chapter=1,  # Same chapter as birth
                event_type=EventType.DEATH.value,
                description="Alice died",
                importance=ImportanceLevel.CRITICAL.value,
            ),
        ]

        warnings = validator.validate_intervals(events)

        # Should detect impossibly fast events
        assert len(warnings) > 0
        too_short_warning = next(
            (w for w in warnings if w.warning_type == "too_short_interval"), None
        )
        assert too_short_warning is not None
        assert too_short_warning.severity == Severity.WARNING

    def test_validate_intervals_large_gap(self, validator: TimelineValidator) -> None:
        """Test validate_intervals with large gap warning."""
        # Create events with large gap
        events = [
            TimelineEventData(
                event_id="event_001",
                character_id=1,
                character_name="Alice",
                chapter=1,
                event_type=EventType.APPEARANCE.value,
                description="Alice appears",
                importance=ImportanceLevel.HIGH.value,
            ),
            TimelineEventData(
                event_id="event_002",
                character_id=1,
                character_name="Alice",
                chapter=25,  # Large gap of 24 chapters
                event_type=EventType.APPEARANCE.value,
                description="Alice appears again",
                importance=ImportanceLevel.HIGH.value,
            ),
        ]

        warnings = validator.validate_intervals(events)

        # Should detect large gap (exceeds default max_event_gap of 20)
        large_gap_warning = next((w for w in warnings if w.warning_type == "too_long_gap"), None)
        assert large_gap_warning is not None
        assert large_gap_warning.chapter_start == 1
        assert large_gap_warning.chapter_end == 25

    @pytest.mark.asyncio
    async def test_validate_timeline(
        self, validator: TimelineValidator, sample_events: list[TimelineEventData]
    ) -> None:
        """Test validate_timeline method."""
        # Mock _load_events to return sample events
        validator._load_events = AsyncMock(return_value=sample_events)
        validator._load_character_states = AsyncMock(return_value=None)

        report = await validator.validate_timeline("novel_001")

        assert report.novel_id == "novel_001"
        assert report.total_events == 3
        assert isinstance(report, TimelineReport)
        assert isinstance(report.validated_at, datetime)

    @pytest.mark.asyncio
    async def test_validate_timeline_with_conflicts(self, validator: TimelineValidator) -> None:
        """Test validate_timeline with conflicts."""
        # Create events with conflicts
        events = [
            TimelineEventData(
                event_id="event_001",
                character_id=1,
                character_name="Alice",
                chapter=1,
                event_type=EventType.APPEARANCE.value,
                description="Alice is introduced",
                importance=ImportanceLevel.HIGH.value,
            ),
            TimelineEventData(
                event_id="event_002",
                character_id=1,
                character_name="Alice",
                chapter=5,
                event_type=EventType.DEATH.value,
                description="Alice died",
                importance=ImportanceLevel.CRITICAL.value,
            ),
            TimelineEventData(
                event_id="event_003",
                character_id=1,
                character_name="Alice",
                chapter=10,  # Action after death
                event_type=EventType.APPEARANCE.value,
                description="Alice appears and speaks",
                importance=ImportanceLevel.HIGH.value,
            ),
        ]

        # Mock _load_events and _load_character_states
        validator._load_events = AsyncMock(return_value=events)
        validator._load_character_states = AsyncMock(return_value=None)

        report = await validator.validate_timeline("novel_001")

        assert report.total_events == 3
        # Without character states, dead character conflicts won't be detected
        assert isinstance(report, TimelineReport)

    def test_generate_summary(self, validator: TimelineValidator) -> None:
        """Test _generate_summary method."""
        # No issues
        summary = validator._generate_summary([], [], [])
        assert summary == "Timeline validation passed with no issues."

        # With critical issues
        conflicts = [
            TimeConflict(
                conflict_type=TimeConflictType.BORN_AFTER_DEATH.value,
                character_name="A",
                chapter=1,
                event_description="",
                reason="",
                severity=Severity.CRITICAL,
            )
        ]
        summary = validator._generate_summary(conflicts, [], [])
        assert "critical" in summary.lower()
        assert "1" in summary

        # With warnings
        warnings = [
            IntervalWarning(
                warning_type="test",
                chapter_start=1,
                chapter_end=2,
                event_count=1,
                description="test",
                severity=Severity.WARNING,
            )
        ]
        summary = validator._generate_summary([], [], warnings)
        assert "warning" in summary.lower()
        assert "1" in summary


class TestCreateTimelineValidator:
    """Test factory function."""

    def test_create_timeline_validator(self) -> None:
        """Test create_timeline_validator factory."""
        validator = create_timeline_validator()
        assert isinstance(validator, TimelineValidator)

        config = Configuration(min_chapter_gap=5)
        validator = create_timeline_validator(config=config)
        assert validator.config.min_chapter_gap == 5
