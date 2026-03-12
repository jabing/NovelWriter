"""Character profile data models with timeline tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CharacterStatus(str, Enum):
    """Character status in the story."""

    ALIVE = "alive"
    DECEASED = "deceased"
    MISSING = "missing"
    FUSED = "fused"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """Types of timeline events for characters."""

    BIRTH = "birth"
    DEATH = "death"
    INJURY = "injury"
    RECOVERY = "recovery"
    APPEARANCE = "appearance"
    DISAPPEARANCE = "disappearance"
    RELATIONSHIP_CHANGE = "relationship_change"
    LOCATION_CHANGE = "location_change"
    STATUS_CHANGE = "status_change"
    SKILL_ACQUISITION = "skill_acquisition"
    ITEM_ACQUISITION = "item_acquisition"
    ITEM_LOSS = "item_loss"
    MAJOR_EVENT = "major_event"


class EventImportance(str, Enum):
    """Importance level of timeline events."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ConflictType(str, Enum):
    """Types of timeline conflicts."""

    MULTIPLE_DEATHS = "multiple_deaths"
    ACTION_AFTER_DEATH = "action_after_death"
    TEMPORAL_PARADOX = "temporal_paradox"
    DUPLICATE_MAJOR_EVENT = "duplicate_major_event"
    STATUS_INCONSISTENCY = "status_inconsistency"


@dataclass
class CharacterTimelineEvent:
    """A single event in a character's timeline.

    Attributes:
        chapter: Chapter number where event occurred
        event_type: Type of event (birth, death, injury, etc.)
        description: Human-readable description of the event
        importance: Importance level (critical, major, minor)
        timestamp: Optional precise timestamp within the story
        metadata: Additional event metadata
        evidence: Text evidence from chapter
        id: Database ID if persisted
    """

    chapter: int
    event_type: EventType | str
    description: str
    importance: EventImportance | str = EventImportance.MINOR
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        """Normalize event type and importance to enum values."""
        if isinstance(self.event_type, str):
            try:
                self.event_type = EventType(self.event_type)
            except ValueError:
                pass
        if isinstance(self.importance, str):
            try:
                self.importance = EventImportance(self.importance)
            except ValueError:
                self.importance = EventImportance.MINOR

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chapter": self.chapter,
            "event_type": self.event_type.value
            if isinstance(self.event_type, EventType)
            else self.event_type,
            "description": self.description,
            "importance": self.importance.value
            if isinstance(self.importance, EventImportance)
            else self.importance,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
            "evidence": self.evidence,
            "id": self.id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterTimelineEvent:
        """Create from dictionary."""
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            chapter=data["chapter"],
            event_type=data.get("event_type", EventType.APPEARANCE.value),
            description=data.get("description", ""),
            importance=data.get("importance", EventImportance.MINOR.value),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
            evidence=data.get("evidence", ""),
            id=data.get("id"),
        )


@dataclass
class CharacterProfile:
    """Complete character profile with timeline and relationships.

    Attributes:
        name: Character's primary name
        aliases: Alternative names or nicknames
        birth_chapter: Chapter where character was born/introduced
        death_chapter: Chapter where character died (if applicable)
        current_status: Current character status
        timeline: List of timeline events
        immutable_facts: Facts that cannot change
        relationships: Mapping of other character names to relationship types
        metadata: Additional character metadata
        tier: Character tier (0=核心主角，1=重要配角，2=普通配角，3=社会公众)
        has_cognitive_graph: Whether character has cognitive graph
        cognitive_graph_id: ID of the character's cognitive graph
        bio: Character biography
        persona: Character personality traits
        mbti: MBTI personality type
        profession: Character's profession or role
        interested_topics: List of topics the character is interested in
        id: Database ID if persisted
    """

    name: str
    aliases: list[str] = field(default_factory=list)
    birth_chapter: int | None = None
    death_chapter: int | None = None
    current_status: CharacterStatus | str = CharacterStatus.ALIVE
    timeline: list[CharacterTimelineEvent] = field(default_factory=list)
    immutable_facts: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    bio: str = ""
    persona: str = ""
    mbti: str = ""
    profession: str = ""
    interested_topics: list[str] = field(default_factory=list)
    id: int | None = None
    tier: int = 1
    has_cognitive_graph: bool = field(init=False)
    cognitive_graph_id: str | None = None
    is_main: bool = field(init=False)
    is_supporting: bool = field(init=False)

    TIER_COGNITIVE_GRAPH: dict[int, Any] = field(
        default_factory=lambda: {0: True, 1: True, 2: "simplified", 3: False}
    )

    def __post_init__(self) -> None:
        """Normalize status and auto-inference cognitive graph."""
        if isinstance(self.current_status, str):
            try:
                self.current_status = CharacterStatus(self.current_status)
            except ValueError:
                self.current_status = CharacterStatus.UNKNOWN

        self.has_cognitive_graph = bool(self.TIER_COGNITIVE_GRAPH.get(self.tier, False))
        self.cognitive_graph_id = None if not self.has_cognitive_graph else f"cg_{self.name}"

        if self.tier == 0:
            self.is_main = True
            self.is_supporting = False
        else:
            self.is_main = False
            self.is_supporting = True

    @property
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.current_status == CharacterStatus.ALIVE

    @property
    def is_deceased(self) -> bool:
        """Check if character is deceased."""
        return self.current_status == CharacterStatus.DECEASED

    TIER_TOKEN_BUDGET: dict[int, int] = field(default_factory=lambda: {0: 500, 1: 300, 2: 100, 3: 0})

    def get_token_budget(self) -> int:
        """Get token budget for this character."""
        return self.TIER_TOKEN_BUDGET.get(self.tier, 0)

    def get_events_by_type(self, event_type: EventType | str) -> list[CharacterTimelineEvent]:
        """Get all events of a specific type."""
        target_type = event_type.value if isinstance(event_type, EventType) else event_type
        return [
            e
            for e in self.timeline
            if (e.event_type.value if isinstance(e.event_type, EventType) else e.event_type)
            == target_type
        ]

    def get_death_events(self) -> list[CharacterTimelineEvent]:
        """Get all death-related events."""
        return self.get_events_by_type(EventType.DEATH)

    def get_appearance_chapters(self) -> list[int]:
        """Get list of chapters where character appears."""
        return sorted(
            {
                e.chapter
                for e in self.timeline
                if e.event_type
                in [EventType.APPEARANCE, EventType.MAJOR_EVENT, EventType.RELATIONSHIP_CHANGE]
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "aliases": self.aliases,
            "birth_chapter": self.birth_chapter,
            "death_chapter": self.death_chapter,
            "current_status": self.current_status.value
            if isinstance(self.current_status, CharacterStatus)
            else self.current_status,
            "timeline": [e.to_dict() for e in self.timeline],
            "immutable_facts": self.immutable_facts,
            "relationships": self.relationships,
            "metadata": self.metadata,
            "bio": self.bio,
            "persona": self.persona,
            "mbti": self.mbti,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "id": self.id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterProfile:
        """Create from dictionary."""
        timeline = [CharacterTimelineEvent.from_dict(e) for e in data.get("timeline", [])]

        return cls(
            name=data["name"],
            aliases=data.get("aliases", []),
            birth_chapter=data.get("birth_chapter"),
            death_chapter=data.get("death_chapter"),
            current_status=data.get("current_status", CharacterStatus.ALIVE.value),
            timeline=timeline,
            immutable_facts=data.get("immutable_facts", {}),
            relationships=data.get("relationships", {}),
            metadata=data.get("metadata", {}),
            bio=data.get("bio", ""),
            persona=data.get("persona", ""),
            mbti=data.get("mbti", ""),
            profession=data.get("profession", ""),
            interested_topics=data.get("interested_topics", []),
            id=data.get("id"),
        )


@dataclass
class TimelineConflict:
    """Detected timeline conflict for a character.

    Attributes:
        conflict_type: Type of conflict detected
        character_name: Character with the conflict
        event1: First conflicting event
        event2: Second conflicting event
        description: Human-readable conflict description
        severity: How severe the conflict is
        suggested_resolution: Optional suggestion for resolving the conflict
    """

    conflict_type: ConflictType
    character_name: str
    event1: CharacterTimelineEvent
    event2: CharacterTimelineEvent
    description: str
    severity: str = "major"
    suggested_resolution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conflict_type": self.conflict_type.value,
            "character_name": self.character_name,
            "event1": self.event1.to_dict(),
            "event2": self.event2.to_dict(),
            "description": self.description,
            "severity": self.severity,
            "suggested_resolution": self.suggested_resolution,
        }
