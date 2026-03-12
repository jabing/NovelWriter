"""Tests for shared data models."""

from novelwriter_shared.models import (
    CharacterProfile,
    CharacterStatus,
    CharacterTimelineEvent,
    ConflictType,
    EventImportance,
    EventType,
    Fact,
    FactType,
    TimelineConflict,
)
from novelwriter_shared.utils import generate_id


class TestCharacterTimelineEvent:
    """Tests for CharacterTimelineEvent model."""

    def test_create_event(self) -> None:
        """Test creating a timeline event."""
        event = CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.BIRTH,
            description="Character was born",
            importance=EventImportance.CRITICAL,
        )
        assert event.chapter == 1
        assert event.event_type == EventType.BIRTH
        assert event.importance == EventImportance.CRITICAL

    def test_event_from_dict(self) -> None:
        """Test creating event from dictionary."""
        data = {
            "chapter": 5,
            "event_type": "death",
            "description": "Character died",
            "importance": "critical",
        }
        event = CharacterTimelineEvent.from_dict(data)
        assert event.chapter == 5
        assert event.event_type == EventType.DEATH
        assert event.importance == EventImportance.CRITICAL

    def test_event_to_dict(self) -> None:
        """Test converting event to dictionary."""
        event = CharacterTimelineEvent(
            chapter=3,
            event_type=EventType.INJURY,
            description="Character was injured",
        )
        data = event.to_dict()
        assert data["chapter"] == 3
        assert data["event_type"] == "injury"
        assert data["description"] == "Character was injured"


class TestCharacterProfile:
    """Tests for CharacterProfile model."""

    def test_create_profile(self) -> None:
        """Test creating a character profile."""
        profile = CharacterProfile(
            name="Alice",
            tier=0,
            bio="Main protagonist",
        )
        assert profile.name == "Alice"
        assert profile.tier == 0
        assert profile.is_main is True
        assert profile.has_cognitive_graph is True

    def test_profile_token_budget(self) -> None:
        """Test token budget calculation."""
        profile_tier0 = CharacterProfile(name="Main", tier=0)
        profile_tier1 = CharacterProfile(name="Supporting", tier=1)
        profile_tier2 = CharacterProfile(name="Minor", tier=2)

        assert profile_tier0.get_token_budget() == 500
        assert profile_tier1.get_token_budget() == 300
        assert profile_tier2.get_token_budget() == 100

    def test_profile_status_properties(self) -> None:
        """Test status property methods."""
        profile = CharacterProfile(name="Test", current_status=CharacterStatus.ALIVE)
        assert profile.is_alive is True
        assert profile.is_deceased is False

        profile.current_status = CharacterStatus.DECEASED
        assert profile.is_alive is False
        assert profile.is_deceased is True

    def test_profile_from_dict(self) -> None:
        """Test creating profile from dictionary."""
        data = {
            "name": "Bob",
            "aliases": ["Bobby", "Robert"],
            "birth_chapter": 1,
            "tier": 1,
        }
        profile = CharacterProfile.from_dict(data)
        assert profile.name == "Bob"
        assert "Bobby" in profile.aliases
        assert profile.birth_chapter == 1

    def test_get_appearance_chapters(self) -> None:
        """Test getting chapters where character appears."""
        profile = CharacterProfile(name="Test")
        profile.timeline = [
            CharacterTimelineEvent(
                chapter=1,
                event_type=EventType.APPEARANCE,
                description="First appearance",
            ),
            CharacterTimelineEvent(
                chapter=5,
                event_type=EventType.MAJOR_EVENT,
                description="Important event",
            ),
            CharacterTimelineEvent(
                chapter=10,
                event_type=EventType.RELATIONSHIP_CHANGE,
                description="Met someone",
            ),
        ]
        chapters = profile.get_appearance_chapters()
        assert chapters == [1, 5, 10]


class TestFact:
    """Tests for Fact model."""

    def test_create_fact(self) -> None:
        """Test creating a fact."""
        fact = Fact(
            fact_type=FactType.CHARACTER,
            content="Alice is the protagonist",
            chapter_origin=1,
        )
        assert fact.fact_type == FactType.CHARACTER
        assert fact.chapter_origin == 1
        assert fact.id is not None

    def test_fact_from_dict(self) -> None:
        """Test creating fact from dictionary."""
        data = {
            "fact_type": "location",
            "content": "The castle is in the mountains",
            "chapter_origin": 3,
            "importance": 0.8,
        }
        fact = Fact.from_dict(data)
        assert fact.fact_type == FactType.LOCATION
        assert fact.importance == 0.8

    def test_fact_to_dict(self) -> None:
        """Test converting fact to dictionary."""
        fact = Fact(
            fact_type=FactType.EVENT,
            content="The battle occurred",
            chapter_origin=10,
        )
        data = fact.to_dict()
        assert data["fact_type"] == "event"
        assert data["content"] == "The battle occurred"
        assert "id" in data

    def test_fact_touch(self) -> None:
        """Test updating fact reference."""
        fact = Fact(content="Test fact", chapter_origin=1)
        assert fact.reference_count == 0
        assert fact.last_referenced == 0

        fact.touch(5)
        assert fact.reference_count == 1
        assert fact.last_referenced == 5

        fact.touch(10)
        assert fact.reference_count == 2
        assert fact.last_referenced == 10

    def test_fact_context_string(self) -> None:
        """Test generating context string."""
        fact = Fact(
            fact_type=FactType.CHARACTER,
            content="Alice is brave",
        )
        context = fact.get_context_string()
        assert "角色" in context
        assert "Alice is brave" in context


class TestTimelineConflict:
    """Tests for TimelineConflict model."""

    def test_create_conflict(self) -> None:
        """Test creating a timeline conflict."""
        event1 = CharacterTimelineEvent(
            chapter=5,
            event_type=EventType.DEATH,
            description="First death",
        )
        event2 = CharacterTimelineEvent(
            chapter=10,
            event_type=EventType.DEATH,
            description="Second death",
        )
        conflict = TimelineConflict(
            conflict_type=ConflictType.MULTIPLE_DEATHS,
            character_name="Test",
            event1=event1,
            event2=event2,
            description="Character died twice",
        )
        assert conflict.conflict_type == ConflictType.MULTIPLE_DEATHS
        assert conflict.character_name == "Test"
        assert conflict.severity == "major"

    def test_conflict_to_dict(self) -> None:
        """Test converting conflict to dictionary."""
        event1 = CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.BIRTH,
            description="Born",
        )
        event2 = CharacterTimelineEvent(
            chapter=5,
            event_type=EventType.DEATH,
            description="Died",
        )
        conflict = TimelineConflict(
            conflict_type=ConflictType.TEMPORAL_PARADOX,
            character_name="Test",
            event1=event1,
            event2=event2,
            description="Born after death",
            severity="critical",
        )
        data = conflict.to_dict()
        assert data["conflict_type"] == "temporal_paradox"
        assert data["severity"] == "critical"


class TestIDGenerator:
    """Tests for ID generation utilities."""

    def test_generate_id_no_prefix(self) -> None:
        """Test generating ID without prefix."""
        id1 = generate_id()
        id2 = generate_id()
        assert len(id1) == 8
        assert id1 != id2

    def test_generate_id_with_prefix(self) -> None:
        """Test generating ID with prefix."""
        id1 = generate_id("test")
        assert id1.startswith("test_")
        assert len(id1) == 13
