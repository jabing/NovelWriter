"""Unit tests for CharacterProfileManager.

Tests cover:
- CharacterProfile CRUD operations
- Timeline event extraction from chapter text
- Timeline conflict detection
- PostgreSQL integration
"""

import logging
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.novel.character_profile import (
    CharacterProfile,
    CharacterProfileManager,
    CharacterStatus,
    CharacterTimelineEvent,
    ConflictType,
    EventImportance,
    EventType,
)

logger = logging.getLogger(__name__)


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def temp_storage(tmp_path: Path) -> None:
    """Create a temporary storage path."""
    path = tmp_path / "character_profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def mock_postgres_client():
    """Create a mock PostgresClient for testing."""
    mock = AsyncMock()
    mock.create_character = AsyncMock()
    mock.get_character = AsyncMock()
    mock.get_character_by_name = AsyncMock()
    mock.list_characters = AsyncMock()
    mock.update_character = AsyncMock()
    mock.delete_character = AsyncMock()
    mock.create_timeline_event = AsyncMock()
    mock.get_character_timeline = AsyncMock()
    return mock


@pytest.fixture
def manager_without_db():
    """Create a manager without database for unit tests."""
    return CharacterProfileManager(storage_path=None)


@pytest.fixture
def manager_with_mock_db(mock_postgres_client):
    """Create a manager with mock database."""
    return CharacterProfileManager(postgres_client=mock_postgres_client)


# ========================================
# CharacterProfile Tests
# ========================================


class TestCharacterProfile:
    """Tests for CharacterProfile dataclass."""

    def test_creation(self) -> None:
        """Test creating a profile."""
        profile = CharacterProfile(
            name="Alice",
            aliases=["Ally", "Alyssa"],
            birth_chapter=1,
            death_chapter=100,
            current_status=CharacterStatus.ALIVE,
        )

        assert profile.name == "Alice"
        assert profile.aliases == ["Ally", "Alyssa"]
        assert profile.birth_chapter == 1
        assert profile.death_chapter == 100
        assert profile.is_alive is True
        assert not profile.is_deceased
        assert len(profile.timeline) == 0

    def test_post_init_status_normalization(self) -> None:
        """Test status normalization."""
        profile = CharacterProfile(
            name="Bob",
            current_status="alive",
        )
        assert profile.current_status == CharacterStatus.ALIVE
        assert profile.is_alive is True

        profile = CharacterProfile(name="Charlie", current_status="deceased")
        assert profile.current_status == CharacterStatus.DECEASED
        assert profile.is_deceased is True
        assert not profile.is_alive

    def test_from_dict(self) -> None:
        """Test serialization/deserialization."""
        data = {
            "name": "Diana",
            "aliases": ["Di", "DiDi"],
            "birth_chapter": 5,
            "death_chapter": 50,
            "current_status": "deceased",
            "timeline": [
                {
                    "chapter": 5,
                    "event_type": "birth",
                    "description": "Diana was born",
                    "importance": "critical",
                },
                {
                    "chapter": 50,
                    "event_type": "death",
                    "description": "Diana died in battle",
                    "importance": "critical",
                },
            ],
            "immutable_facts": {"hair_color": "blonde", "eye_color": "blue"},
            "relationships": {"Alice": "sister", "Bob": "friend"},
        }

        profile = CharacterProfile.from_dict(data)

        assert profile.name == "Diana"
        assert profile.aliases == ["Di", "DiDi"]
        assert profile.birth_chapter == 5
        assert profile.death_chapter == 50
        assert profile.is_deceased
        assert len(profile.timeline) == 2
        assert profile.timeline[0].event_type == EventType.BIRTH
        assert profile.timeline[1].event_type == EventType.DEATH
        assert profile.immutable_facts == {"hair_color": "blonde", "eye_color": "blue"}
        assert profile.relationships == {"Alice": "sister", "Bob": "friend"}

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        profile = CharacterProfile(
            name="Eve",
            birth_chapter=1,
            timeline=[
                CharacterTimelineEvent(
                    chapter=10,
                    event_type=EventType.INJURY,
                    description="Eve was injured",
                    importance=EventImportance.MAJOR,
                    evidence="Eve fell from the cliff",
                )
            ],
        )

        data = profile.to_dict()

        assert data["name"] == "Eve"
        assert data["birth_chapter"] == 1
        assert len(data["timeline"]) == 1
        assert data["timeline"][0]["event_type"] == "injury"
        assert data["timeline"][0]["importance"] == "major"
        assert data["timeline"][0]["evidence"] == "Eve fell from the cliff"
        assert data["current_status"] == "alive"

    def test_get_events_by_type(self) -> None:
        """Test getting events by type."""
        profile = CharacterProfile(
            name="Test",
            timeline=[
                CharacterTimelineEvent(chapter=1, event_type=EventType.BIRTH, description="Born"),
                CharacterTimelineEvent(
                    chapter=5, event_type=EventType.INJURY, description="Injured"
                ),
                CharacterTimelineEvent(
                    chapter=5, event_type=EventType.RECOVERY, description="Recovered"
                ),
            ],
        )

        birth_events = profile.get_events_by_type(EventType.BIRTH)
        assert len(birth_events) == 1
        assert birth_events[0].chapter == 1

        injury_events = profile.get_events_by_type(EventType.INJURY)
        assert len(injury_events) == 1
        assert injury_events[0].event_type == EventType.INJURY

    def test_get_death_events(self) -> None:
        """Test getting death events."""
        profile = CharacterProfile(
            name="Ghost",
            timeline=[
                CharacterTimelineEvent(
                    chapter=10, event_type=EventType.DEATH, description="First death"
                ),
                CharacterTimelineEvent(
                    chapter=20, event_type=EventType.DEATH, description="Second death"
                ),
            ],
        )

        deaths = profile.get_death_events()
        assert len(deaths) == 2
        assert all(d.event_type == EventType.DEATH for d in deaths)

    def test_get_appearance_chapters(self) -> None:
        """Test getting appearance chapters."""
        profile = CharacterProfile(
            name="Wanderer",
            timeline=[
                CharacterTimelineEvent(
                    chapter=1, event_type=EventType.APPEARANCE, description="Appeared"
                ),
                CharacterTimelineEvent(
                    chapter=5, event_type=EventType.MAJOR_EVENT, description="Major event"
                ),
                CharacterTimelineEvent(
                    chapter=10, event_type=EventType.RELATIONSHIP_CHANGE, description="Met someone"
                ),
            ],
        )

        chapters = profile.get_appearance_chapters()
        assert chapters == [1, 5, 10]


# ========================================
# CharacterTimelineEvent Tests
# ========================================


class TestCharacterTimelineEvent:
    """Tests for CharacterTimelineEvent dataclass."""

    def test_creation(self) -> None:
        """Test creating a timeline event."""
        event = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.DEATH,
            description="Character died",
            importance=EventImportance.CRITICAL,
            evidence="He drew his last breath",
        )

        assert event.chapter == 10
        assert event.event_type == EventType.DEATH
        assert event.importance == EventImportance.CRITICAL
        assert event.evidence == "He drew his last breath"
        assert isinstance(event.event_type, EventType)
        assert isinstance(event.importance, EventImportance)

    def test_string_event_type(self) -> None:
        """Test string event type conversion."""
        event = CharacterTimelineEvent(
            chapter=5,
            event_type="custom_event",
            description="Custom event",
        )

        assert event.event_type == "custom_event"
        assert not isinstance(event.event_type, EventType)

    def test_from_dict(self) -> None:
        """Test creating event from dict."""
        data = {
            "chapter": 15,
            "event_type": "recovery",
            "description": "Recovered from injury",
            "importance": "major",
            "evidence": "Healed quickly",
            "metadata": {"healer": "Dr. Smith"},
        }

        event = CharacterTimelineEvent.from_dict(data)

        assert event.chapter == 15
        assert event.event_type == EventType.RECOVERY
        assert event.description == "Recovered from injury"
        assert event.importance == EventImportance.MAJOR
        assert event.metadata == {"healer": "Dr. Smith"}

    def test_to_dict(self) -> None:
        """Test converting event to dict."""
        event = CharacterTimelineEvent(
            chapter=20,
            event_type=EventType.STATUS_CHANGE,
            description="Status changed",
            metadata={"reason": "Promotion"},
        )

        data = event.to_dict()

        assert data["chapter"] == 20
        assert data["event_type"] == "status_change"
        assert data["importance"] == "minor"
        assert data["metadata"] == {"reason": "Promotion"}


# ========================================
# CharacterProfileManager CRUD Tests
# ========================================


class TestCharacterProfileManagerCRUD:
    """Tests for CharacterProfileManager CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_profile(self, manager_without_db: CharacterProfileManager) -> None:
        """Test creating a new profile."""
        profile = await manager_without_db.create_profile(
            name="Alice",
            aliases=["Ally"],
            current_status=CharacterStatus.ALIVE,
        )

        assert profile.name == "Alice"
        assert profile.aliases == ["Ally"]
        assert profile.current_status == CharacterStatus.ALIVE
        assert "Alice" in manager_without_db._profiles

    @pytest.mark.asyncio
    async def test_create_profile_with_chapters(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test creating profile with birth/death chapters."""
        profile = await manager_without_db.create_profile(
            name="Bob",
            birth_chapter=1,
            death_chapter=100,
        )

        assert profile.birth_chapter == 1
        assert profile.death_chapter == 100
        assert profile.id is None  # No DB ID without storage

    @pytest.mark.asyncio
    async def test_get_profile(self, manager_without_db: CharacterProfileManager) -> None:
        """Test getting profile."""
        await manager_without_db.create_profile(name="Charlie")

        profile = manager_without_db.get_profile("Charlie")
        assert profile is not None
        assert profile.name == "Charlie"

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test getting nonexistent profile."""
        profile = manager_without_db.get_profile("Nonexistent")
        assert profile is None

    @pytest.mark.asyncio
    async def test_update_profile(self, manager_without_db: CharacterProfileManager) -> None:
        """Test updating profile."""
        await manager_without_db.create_profile(name="Diana")
        profile = manager_without_db.get_profile("Diana")
        assert profile is not None

        profile.current_status = CharacterStatus.MISSING
        profile.birth_chapter = 5
        profile.relationships = {"Alice": "sister"}

        updated = manager_without_db.update_profile(profile)
        assert updated is True

        stored = manager_without_db.get_profile("Diana")
        assert stored is not None
        assert stored.current_status == CharacterStatus.MISSING
        assert stored.birth_chapter == 5
        assert stored.relationships == {"Alice": "sister"}

    @pytest.mark.asyncio
    async def test_update_nonexistent_profile(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test updating nonexistent profile."""
        profile = CharacterProfile(name="Ghost")
        result = manager_without_db.update_profile(profile)
        assert result is False

    @pytest.mark.asyncio
    async def test_list_profiles(self, manager_without_db: CharacterProfileManager) -> None:
        """Test listing profiles."""
        await manager_without_db.create_profile(name="Alice")
        await manager_without_db.create_profile(name="Bob")
        await manager_without_db.create_profile(name="Charlie")

        profiles = manager_without_db.list_profiles()
        assert len(profiles) == 3
        names = [p.name for p in profiles]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" in names

    @pytest.mark.asyncio
    async def test_list_profiles_by_status(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test listing profiles by status."""
        await manager_without_db.create_profile(name="Alive1", current_status=CharacterStatus.ALIVE)
        await manager_without_db.create_profile(
            name="Deceased1", current_status=CharacterStatus.DECEASED
        )
        await manager_without_db.create_profile(
            name="Missing1", current_status=CharacterStatus.MISSING
        )

        alive = manager_without_db.list_profiles(status=CharacterStatus.ALIVE.value)
        assert len(alive) == 1
        assert alive[0].name == "Alive1"

        deceased = manager_without_db.list_profiles(status=CharacterStatus.DECEASED.value)
        assert len(deceased) == 1
        assert deceased[0].name == "Deceased1"

    @pytest.mark.asyncio
    async def test_delete_profile(self, manager_without_db: CharacterProfileManager) -> None:
        """Test deleting profile."""
        await manager_without_db.create_profile(name="ToDelete")

        assert manager_without_db.delete_profile("ToDelete") is True
        assert manager_without_db.get_profile("ToDelete") is None
        assert "ToDelete" not in manager_without_db._profiles

    @pytest.mark.asyncio
    async def test_delete_nonexistent_profile(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test deleting nonexistent profile."""
        result = manager_without_db.delete_profile("Nonexistent")
        assert result is False


# ========================================
# Timeline Event Extraction Tests
# ========================================


class TestCharacterProfileManagerEventExtraction:
    """Tests for timeline event extraction from chapter text."""

    @pytest.mark.asyncio
    async def test_extract_death_events(self, manager_without_db: CharacterProfileManager) -> None:
        """Test extracting death events from text."""
        text = """
        Alice drowned in the river.
        Bob was stabbed to death.
        Charlie was beheaded by the executioner.
        """

        events = manager_without_db.extract_events_from_chapter(text, 10)

        assert len(events) == 3

        # Check Alice's drowning
        alice_drown = None
        for e in events:
            if "Alice" in e.description:
                alice_drown = e
                break

        assert alice_drown is not None
        assert alice_drown.event_type == EventType.DEATH
        assert alice_drown.chapter == 10
        assert "drowned" in alice_drown.evidence.lower()

        # Check Bob's death
        bob_death = next((e for e in events if "Bob" in e.description), None)
        assert bob_death is not None
        assert bob_death.event_type == EventType.DEATH
        assert bob_death.chapter == 10
        assert "stabbed" in bob_death.evidence.lower()

    @pytest.mark.asyncio
    async def test_extract_injury_events(self, manager_without_db: CharacterProfileManager) -> None:
        """Test extracting injury events from text."""
        text = """
        Alice was wounded in the battle. She recovered after treatment.
        Bob suffered a severe injury to the leg.
        Charlie hurt his arm in the accident.
        """

        events = manager_without_db.extract_events_from_chapter(text, 15)

        assert len(events) >= 2

        # Check at least one injury event
        injury_events = [e for e in events if e.event_type == EventType.INJURY]
        assert len(injury_events) >= 1

    @pytest.mark.asyncio
    async def test_extract_relationship_changes(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test extracting relationship changes from text."""
        text = """
        Alice married Bob in a grand ceremony.
        Charlie betrayed his best friend during the battle.
        """

        events = manager_without_db.extract_events_from_chapter(text, 20)

        relationship_events = [e for e in events if e.event_type == EventType.RELATIONSHIP_CHANGE]
        assert len(relationship_events) >= 1

    @pytest.mark.asyncio
    async def test_extract_location_changes(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test extracting location changes from text."""
        text = """
        Alice arrived at the castle.
        Bob traveled to the mountains.
        """

        events = manager_without_db.extract_events_from_chapter(text, 5)

        location_events = [e for e in events if e.event_type == EventType.LOCATION_CHANGE]
        assert len(location_events) >= 1

    @pytest.mark.asyncio
    async def test_add_event(self, manager_without_db: CharacterProfileManager) -> None:
        """Test adding events to profile."""
        await manager_without_db.create_profile(name="EventCharacter")

        event = CharacterTimelineEvent(
            chapter=5,
            event_type=EventType.INJURY,
            description="Injured in battle",
            importance=EventImportance.MAJOR,
        )

        result = await manager_without_db.add_event("EventCharacter", event)
        assert result is True

        profile = manager_without_db.get_profile("EventCharacter")
        assert profile is not None
        assert len(profile.timeline) == 1
        assert profile.timeline[0].event_type == EventType.INJURY

    @pytest.mark.asyncio
    async def test_add_event_to_nonexistent_profile(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test adding event to nonexistent profile."""
        event = CharacterTimelineEvent(
            chapter=5,
            event_type=EventType.INJURY,
            description="Injured",
        )

        result = await manager_without_db.add_event("NonexistentCharacter", event)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_timeline(self, manager_without_db: CharacterProfileManager) -> None:
        """Test getting timeline events."""
        await manager_without_db.create_profile(name="TimelineCharacter")

        event1 = CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.BIRTH,
            description="Born",
            importance=EventImportance.CRITICAL,
        )
        event2 = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.INJURY,
            description="Injured",
            importance=EventImportance.MAJOR,
        )
        event3 = CharacterTimelineEvent(
            chapter=50,
            event_type=EventType.DEATH,
            description="Died",
            importance=EventImportance.CRITICAL,
        )

        await manager_without_db.add_event("TimelineCharacter", event1)
        await manager_without_db.add_event("TimelineCharacter", event2)
        await manager_without_db.add_event("TimelineCharacter", event3)

        # Get all events
        all_events = manager_without_db.get_timeline("TimelineCharacter")
        assert len(all_events) == 3

        # Get events by chapter range
        early_events = manager_without_db.get_timeline(
            "TimelineCharacter", start_chapter=1, end_chapter=20
        )
        assert len(early_events) == 2
        assert all(e.chapter <= 20 for e in early_events)


# ========================================
# Timeline Conflict Detection Tests
# ========================================


class TestCharacterProfileManagerConflictDetection:
    """Tests for timeline conflict detection."""

    @pytest.mark.asyncio
    async def test_detect_no_conflicts(self, manager_without_db: CharacterProfileManager) -> None:
        """Test detecting no conflicts in clean timeline."""
        await manager_without_db.create_profile(name="CleanCharacter")

        event1 = CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.BIRTH,
            description="Born",
            importance=EventImportance.CRITICAL,
        )
        event2 = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.INJURY,
            description="Injured",
            importance=EventImportance.MAJOR,
        )
        event3 = CharacterTimelineEvent(
            chapter=50,
            event_type=EventType.DEATH,
            description="Died peacefully",
            importance=EventImportance.CRITICAL,
        )

        await manager_without_db.add_event("CleanCharacter", event1)
        await manager_without_db.add_event("CleanCharacter", event2)
        await manager_without_db.add_event("CleanCharacter", event3)

        conflicts = await manager_without_db.detect_timeline_conflicts("CleanCharacter")
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_detect_multiple_deaths(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test detecting multiple death events (drowning twice)."""
        await manager_without_db.create_profile(name="DrowningCharacter")

        event1 = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.DEATH,
            description="Drowned in the river",
            importance=EventImportance.CRITICAL,
            evidence="Alice fell into the river and drowned",
        )
        event2 = CharacterTimelineEvent(
            chapter=20,
            event_type=EventType.DEATH,
            description="Drowned in the ocean",
            importance=EventImportance.CRITICAL,
            evidence="Alice drowned again in the ocean",
        )

        await manager_without_db.add_event("DrowningCharacter", event1)
        await manager_without_db.add_event("DrowningCharacter", event2)

        conflicts = await manager_without_db.detect_timeline_conflicts("DrowningCharacter")
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.MULTIPLE_DEATHS
        assert conflicts[0].character_name == "DrowningCharacter"
        assert conflicts[0].event1.chapter == 10
        assert conflicts[0].event2.chapter == 20

    @pytest.mark.asyncio
    async def test_detect_action_after_death(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test detecting actions after confirmed death."""
        await manager_without_db.create_profile(name="DeadCharacter")

        death_event = CharacterTimelineEvent(
            chapter=50,
            event_type=EventType.DEATH,
            description="Died in battle",
            importance=EventImportance.CRITICAL,
        )
        action_event = CharacterTimelineEvent(
            chapter=60,
            event_type=EventType.MAJOR_EVENT,
            description="Led the army to victory",
            importance=EventImportance.MAJOR,
        )

        await manager_without_db.add_event("DeadCharacter", death_event)
        await manager_without_db.add_event("DeadCharacter", action_event)

        conflicts = await manager_without_db.detect_timeline_conflicts("DeadCharacter")
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.ACTION_AFTER_DEATH

    @pytest.mark.asyncio
    async def test_detect_temporal_paradox(
        self, manager_without_db: CharacterProfileManager
    ) -> None:
        """Test detecting temporal paradox (birth after death)."""
        await manager_without_db.create_profile(name="ParadoxCharacter")

        birth_event = CharacterTimelineEvent(
            chapter=100,
            event_type=EventType.BIRTH,
            description="Born",
            importance=EventImportance.CRITICAL,
        )
        death_event = CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.DEATH,
            description="Died",
            importance=EventImportance.CRITICAL,
        )

        await manager_without_db.add_event("ParadoxCharacter", birth_event)
        await manager_without_db.add_event("ParadoxCharacter", death_event)

        conflicts = await manager_without_db.detect_timeline_conflicts("ParadoxCharacter")
        # Should detect temporal paradox in profile (birth_chapter > death_chapter)
        paradox_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.TEMPORAL_PARADOX
        ]
        assert len(paradox_conflicts) >= 1

    @pytest.mark.asyncio
    async def test_detect_all_conflicts(self, manager_without_db: CharacterProfileManager) -> None:
        """Test detecting all conflicts across all profiles."""
        await manager_without_db.create_profile(name="Conflict1")
        await manager_without_db.create_profile(name="Conflict2")

        # Profile 1: Multiple deaths
        death1 = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.DEATH,
            description="Died 1",
            importance=EventImportance.CRITICAL,
        )
        death2 = CharacterTimelineEvent(
            chapter=20,
            event_type=EventType.DEATH,
            description="Died 2",
            importance=EventImportance.CRITICAL,
        )
        await manager_without_db.add_event("Conflict1", death1)
        await manager_without_db.add_event("Conflict1", death2)

        # Profile 2: Action after death
        death = CharacterTimelineEvent(
            chapter=5,
            event_type=EventType.DEATH,
            description="Died",
            importance=EventImportance.CRITICAL,
        )
        action = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.MAJOR_EVENT,
            description="Acted",
            importance=EventImportance.MAJOR,
        )
        await manager_without_db.add_event("Conflict2", death)
        await manager_without_db.add_event("Conflict2", action)

        # Detect all conflicts
        all_conflicts = await manager_without_db.detect_all_conflicts()

        assert len(all_conflicts) >= 2


# ========================================
# Statistics and Helper Tests
# ========================================


class TestCharacterProfileManagerStatistics:
    """Tests for statistics and helper methods."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, manager_without_db: CharacterProfileManager) -> None:
        """Test getting statistics."""
        await manager_without_db.create_profile(name="Stat1")
        await manager_without_db.create_profile(name="Stat2")
        await manager_without_db.create_profile(name="Stat3")

        await manager_without_db.add_event(
            "Stat1",
            CharacterTimelineEvent(chapter=1, event_type=EventType.INJURY, description="Event 1"),
        )
        await manager_without_db.add_event(
            "Stat2",
            CharacterTimelineEvent(chapter=5, event_type=EventType.DEATH, description="Event 2"),
        )

        stats = manager_without_db.get_statistics()
        assert stats["total_profiles"] == 3
        assert stats["total_events"] == 2
