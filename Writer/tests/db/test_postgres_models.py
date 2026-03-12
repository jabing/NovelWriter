"""Unit tests for PostgreSQL models and client.

Tests all CRUD operations, relationships, and edge cases for:
- CharacterProfile
- TimelineEvent
- StoryFact
- Contradiction
"""
import os

import pytest

from src.db.postgres_client import PostgresClient
from src.db.postgres_models import (
    CharacterStatus,
    ContradictionType,
    EntityType,
    EventType,
    ImportanceLevel,
    SeverityLevel,
)

# Use in-memory SQLite for testing (faster than PostgreSQL for unit tests)
# In production, use actual PostgreSQL with test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)


@pytest.fixture
async def client():
    """Create test client with in-memory database."""
    # Use SQLite for testing (in-memory)
    client = PostgresClient(database_url=TEST_DATABASE_URL)
    await client.initialize()
    yield client
    await client.close()


class TestCharacterProfile:
    """Tests for CharacterProfile CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_character(self, client: PostgresClient) -> None:
        """Test creating a character."""
        character = await client.create_character(
            name="Alice",
            status=CharacterStatus.ACTIVE.value,
            birth_chapter=1,
            aliases=["Ally", "Alice Smith"],
            metadata={"role": "protagonist"},
        )

        assert character.id is not None
        assert character.name == "Alice"
        assert character.status == CharacterStatus.ACTIVE.value
        assert character.birth_chapter == 1
        assert character.death_chapter is None

    @pytest.mark.asyncio
    async def test_create_character_with_death(self, client: PostgresClient) -> None:
        """Test creating character with birth and death chapters."""
        character = await client.create_character(
            name="Bob",
            birth_chapter=5,
            death_chapter=20,
            status=CharacterStatus.DECEASED.value,
        )

        assert character.birth_chapter == 5
        assert character.death_chapter == 20
        assert character.status == CharacterStatus.DECEASED.value

    @pytest.mark.asyncio
    async def test_create_character_invalid_chapters(self, client: PostgresClient) -> None:
        """Test validation: death before birth."""
        with pytest.raises(ValueError, match="cannot be before"):
            await client.create_character(
                name="Invalid",
                birth_chapter=10,
                death_chapter=5,
            )

    @pytest.mark.asyncio
    async def test_get_character(self, client: PostgresClient) -> None:
        """Test retrieving character by ID."""
        created = await client.create_character(name="Charlie")
        retrieved = await client.get_character(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Charlie"

    @pytest.mark.asyncio
    async def test_get_character_not_found(self, client: PostgresClient) -> None:
        """Test retrieving non-existent character."""
        result = await client.get_character(9999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_character_by_name(self, client: PostgresClient) -> None:
        """Test retrieving character by name."""
        await client.create_character(name="Diana")
        character = await client.get_character_by_name("Diana")

        assert character is not None
        assert character.name == "Diana"

    @pytest.mark.asyncio
    async def test_list_characters(self, client: PostgresClient) -> None:
        """Test listing characters with filters."""
        await client.create_character(name="Eve", status=CharacterStatus.ACTIVE.value)
        await client.create_character(name="Frank", status=CharacterStatus.DECEASED.value)

        all_chars = await client.list_characters()
        assert len(all_chars) >= 2

        active_chars = await client.list_characters(status=CharacterStatus.ACTIVE.value)
        assert all(c.status == CharacterStatus.ACTIVE.value for c in active_chars)

    @pytest.mark.asyncio
    async def test_update_character(self, client: PostgresClient) -> None:
        """Test updating character."""
        character = await client.create_character(name="Grace")

        updated = await client.update_character(
            character.id,
            status=CharacterStatus.DECEASED.value,
            death_chapter=15,
        )

        assert updated is not None
        assert updated.status == CharacterStatus.DECEASED.value
        assert updated.death_chapter == 15

    @pytest.mark.asyncio
    async def test_delete_character(self, client: PostgresClient) -> None:
        """Test deleting character."""
        character = await client.create_character(name="Henry")
        deleted = await client.delete_character(character.id)
        assert deleted is True

        retrieved = await client.get_character(character.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_character_to_dict(self, client: PostgresClient) -> None:
        """Test serialization to dictionary."""
        character = await client.create_character(
            name="Ivy",
            aliases=["Ives"],
            metadata={"key": "value"},
        )
        data = character.to_dict()

        assert data["name"] == "Ivy"
        assert data["aliases"] == ["Ives"]
        assert data["metadata"] == {"key": "value"}


class TestTimelineEvent:
    """Tests for TimelineEvent CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_timeline_event(self, client: PostgresClient) -> None:
        """Test creating a timeline event."""
        character = await client.create_character(name="Jack")
        event = await client.create_timeline_event(
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Jack appears for the first time",
            character_id=character.id,
            importance=ImportanceLevel.HIGH.value,
        )

        assert event.id is not None
        assert event.chapter == 1
        assert event.character_id == character.id
        assert event.event_type == EventType.APPEARANCE.value

    @pytest.mark.asyncio
    async def test_get_character_timeline(self, client: PostgresClient) -> None:
        """Test retrieving character timeline."""
        character = await client.create_character(name="Karen")
        await client.create_timeline_event(
            chapter=1,
            event_type=EventType.BIRTH.value,
            description="Karen is born",
            character_id=character.id,
        )
        await client.create_timeline_event(
            chapter=10,
            event_type=EventType.MAJOR_EVENT.value,
            description="Karen saves the world",
            character_id=character.id,
        )

        events = await client.get_character_timeline(character.id)
        assert len(events) == 2
        assert events[0].chapter == 1
        assert events[1].chapter == 10

    @pytest.mark.asyncio
    async def test_get_chapter_events(self, client: PostgresClient) -> None:
        """Test retrieving events for a chapter."""
        character = await client.create_character(name="Leo")
        await client.create_timeline_event(
            chapter=5,
            event_type=EventType.APPEARANCE.value,
            description="Leo appears",
            character_id=character.id,
        )
        await client.create_timeline_event(
            chapter=5,
            event_type=EventType.RELATIONSHIP_CHANGE.value,
            description="Leo meets new ally",
            character_id=character.id,
        )

        events = await client.get_chapter_events(5)
        assert len(events) == 2

        # Filter by event type
        appearances = await client.get_chapter_events(
            5, event_type=EventType.APPEARANCE.value
        )
        assert len(appearances) == 1

    @pytest.mark.asyncio
    async def test_event_to_dict(self, client: PostgresClient) -> None:
        """Test event serialization."""
        event = await client.create_timeline_event(
            chapter=1,
            event_type=EventType.BIRTH.value,
            description="Test event",
            metadata={"custom": "data"},
        )
        data = event.to_dict()

        assert data["chapter"] == 1
        assert data["event_type"] == EventType.BIRTH.value
        assert data["metadata"] == {"custom": "data"}


class TestStoryFact:
    """Tests for StoryFact CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_story_fact(self, client: PostgresClient) -> None:
        """Test creating a story fact."""
        character = await client.create_character(name="Mike")
        fact = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            entity_id=character.id,
            category="appearance",
            attribute="hair_color",
            value="brown",
            source_chapter=1,
            confidence=0.95,
            is_immutable=False,
        )

        assert fact.id is not None
        assert fact.entity_type == EntityType.CHARACTER.value
        assert fact.attribute == "hair_color"
        assert fact.value == "brown"
        assert fact.confidence == 0.95

    @pytest.mark.asyncio
    async def test_create_fact_invalid_confidence(self, client: PostgresClient) -> None:
        """Test validation: confidence out of range."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            await client.create_story_fact(
                entity_type=EntityType.CHARACTER.value,
                category="test",
                attribute="test",
                value="test",
                source_chapter=1,
                confidence=1.5,  # Invalid
            )

    @pytest.mark.asyncio
    async def test_get_entity_facts(self, client: PostgresClient) -> None:
        """Test retrieving facts for an entity."""
        character = await client.create_character(name="Nancy")
        await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            entity_id=character.id,
            category="appearance",
            attribute="eye_color",
            value="blue",
            source_chapter=1,
        )
        await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            entity_id=character.id,
            category="personality",
            attribute="trait",
            value="brave",
            source_chapter=2,
        )

        facts = await client.get_entity_facts(
            entity_type=EntityType.CHARACTER.value,
            entity_id=character.id,
        )
        assert len(facts) == 2

        # Filter by category
        appearance_facts = await client.get_entity_facts(
            entity_type=EntityType.CHARACTER.value,
            entity_id=character.id,
            category="appearance",
        )
        assert len(appearance_facts) == 1

    @pytest.mark.asyncio
    async def test_get_chapter_facts(self, client: PostgresClient) -> None:
        """Test retrieving facts from a chapter."""
        await client.create_story_fact(
            entity_type=EntityType.LOCATION.value,
            category="geography",
            attribute="name",
            value="Forest of Mystery",
            source_chapter=3,
        )

        facts = await client.get_chapter_facts(3)
        assert len(facts) == 1

    @pytest.mark.asyncio
    async def test_search_facts(self, client: PostgresClient) -> None:
        """Test searching facts."""
        await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="background",
            attribute="origin",
            value="born in the mystical village",
            source_chapter=1,
        )

        results = await client.search_facts("mystical")
        assert len(results) >= 1

        # Filter by entity type
        char_results = await client.search_facts(
            "mystical",
            entity_type=EntityType.CHARACTER.value,
        )
        assert len(char_results) >= 1

    @pytest.mark.asyncio
    async def test_fact_to_dict(self, client: PostgresClient) -> None:
        """Test fact serialization."""
        fact = await client.create_story_fact(
            entity_type=EntityType.ITEM.value,
            category="weapon",
            attribute="name",
            value="Sword of Light",
            source_chapter=1,
            metadata={"power": "holy"},
        )
        data = fact.to_dict()

        assert data["entity_type"] == EntityType.ITEM.value
        assert data["metadata"] == {"power": "holy"}


class TestContradiction:
    """Tests for Contradiction CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_contradiction(self, client: PostgresClient) -> None:
        """Test creating a contradiction."""
        fact1 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="appearance",
            attribute="age",
            value="25",
            source_chapter=1,
        )
        fact2 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="appearance",
            attribute="age",
            value="30",
            source_chapter=5,
        )

        contradiction = await client.create_contradiction(
            fact1_id=fact1.id,
            fact2_id=fact2.id,
            contradiction_type=ContradictionType.FACTUAL.value,
            severity=SeverityLevel.HIGH.value,
            description="Character age inconsistent between chapters",
        )

        assert contradiction.id is not None
        assert contradiction.fact1_id == fact1.id
        assert contradiction.fact2_id == fact2.id
        assert contradiction.resolved is False

    @pytest.mark.asyncio
    async def test_get_unresolved_contradictions(self, client: PostgresClient) -> None:
        """Test retrieving unresolved contradictions."""
        fact1 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value1",
            source_chapter=1,
        )
        fact2 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value2",
            source_chapter=2,
        )

        await client.create_contradiction(
            fact1_id=fact1.id,
            fact2_id=fact2.id,
            contradiction_type=ContradictionType.FACTUAL.value,
            severity=SeverityLevel.HIGH.value,
        )

        unresolved = await client.get_unresolved_contradictions()
        assert len(unresolved) >= 1

        # Filter by severity
        high_severity = await client.get_unresolved_contradictions(
            severity=SeverityLevel.HIGH.value
        )
        assert all(c.severity == SeverityLevel.HIGH.value for c in high_severity)

    @pytest.mark.asyncio
    async def test_resolve_contradiction(self, client: PostgresClient) -> None:
        """Test resolving a contradiction."""
        fact1 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value1",
            source_chapter=1,
        )
        fact2 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value2",
            source_chapter=2,
        )

        contradiction = await client.create_contradiction(
            fact1_id=fact1.id,
            fact2_id=fact2.id,
            contradiction_type=ContradictionType.FACTUAL.value,
        )

        resolved = await client.resolve_contradiction(
            contradiction.id,
            resolution_notes="Fixed by updating fact in chapter 3",
        )

        assert resolved is not None
        assert resolved.resolved is True
        assert resolved.resolution_notes == "Fixed by updating fact in chapter 3"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_contradiction_to_dict(self, client: PostgresClient) -> None:
        """Test contradiction serialization."""
        fact1 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value1",
            source_chapter=1,
        )
        fact2 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="value2",
            source_chapter=2,
        )

        contradiction = await client.create_contradiction(
            fact1_id=fact1.id,
            fact2_id=fact2.id,
            contradiction_type=ContradictionType.FACTUAL.value,
            description="Test contradiction",
        )
        data = contradiction.to_dict()

        assert data["fact1_id"] == fact1.id
        assert data["fact2_id"] == fact2.id
        assert data["resolved"] is False


class TestUtilityMethods:
    """Tests for utility methods."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, client: PostgresClient) -> None:
        """Test getting database statistics."""
        # Create some data
        character = await client.create_character(name="Oscar")
        await client.create_timeline_event(
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Oscar appears",
            character_id=character.id,
        )
        fact = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="test",
            source_chapter=1,
        )
        fact2 = await client.create_story_fact(
            entity_type=EntityType.CHARACTER.value,
            category="test",
            attribute="test",
            value="test2",
            source_chapter=2,
        )
        await client.create_contradiction(
            fact1_id=fact.id,
            fact2_id=fact2.id,
            contradiction_type=ContradictionType.FACTUAL.value,
        )

        stats = await client.get_statistics()
        assert stats["characters"] >= 1
        assert stats["timeline_events"] >= 1
        assert stats["story_facts"] >= 2
        assert stats["contradictions"] >= 1
        assert stats["unresolved_contradictions"] >= 1

    @pytest.mark.asyncio
    async def test_clear_all_data(self, client: PostgresClient) -> None:
        """Test clearing all data."""
        # Create some data
        await client.create_character(name="ToDelete")
        await client.create_timeline_event(
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Test",
        )

        # Clear data
        await client.clear_all_data()

        # Verify cleared
        stats = await client.get_statistics()
        assert stats["characters"] == 0
        assert stats["timeline_events"] == 0
        assert stats["story_facts"] == 0
        assert stats["contradictions"] == 0


class TestRelationships:
    """Tests for SQLAlchemy relationships."""

    @pytest.mark.asyncio
    async def test_character_timeline_events_relationship(
        self, client: PostgresClient
    ) -> None:
        """Test character-timeline relationship."""
        character = await client.create_character(name="Peter")
        await client.create_timeline_event(
            chapter=1,
            event_type=EventType.BIRTH.value,
            description="Peter is born",
            character_id=character.id,
        )
        await client.create_timeline_event(
            chapter=10,
            event_type=EventType.MAJOR_EVENT.value,
            description="Peter becomes king",
            character_id=character.id,
        )

        # Get character with events
        retrieved = await client.get_character(character.id)
        assert retrieved is not None
        assert len(retrieved.timeline_events) == 2

    @pytest.mark.asyncio
    async def test_cascade_delete(self, client: PostgresClient) -> None:
        """Test cascade delete of related records."""
        character = await client.create_character(name="Quinn")
        await client.create_timeline_event(
            chapter=1,
            event_type=EventType.APPEARANCE.value,
            description="Quinn appears",
            character_id=character.id,
        )

        # Delete character
        await client.delete_character(character.id)

        # Event should also be deleted
        events = await client.get_chapter_events(1)
        quinn_events = [e for e in events if e.character_id == character.id]
        assert len(quinn_events) == 0
