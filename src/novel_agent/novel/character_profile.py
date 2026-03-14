"""Character profile management with timeline tracking.

This module provides comprehensive character profile management including:
- Character profile data models with timeline events
- Timeline event extraction from chapter text
- Timeline conflict detection (e.g., multiple drowning incidents)
- PostgreSQL storage integration

Usage:
    manager = CharacterProfileManager(postgres_client)
    profile = manager.create_profile("Alice")
    manager.add_event("Alice", CharacterTimelineEvent(...))
    conflicts = manager.detect_timeline_conflicts("Alice")
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.novel_agent.db.postgres_client import PostgresClient

logger = logging.getLogger(__name__)


# === 简化的Token预算表 (固定值) ===
TIER_TOKEN_BUDGET = {
    0: 500,  # 核心主角
    1: 300,  # 重要配角
    2: 100,  # 普通配角
    3: 0,    # 社会公众 (模板不计入)
}

# === 认知图谱自动推断规则 ===
TIER_COGNITIVE_GRAPH = {
    0: True,   # 完整认知图谱
    1: True,   # 完整认知图谱
    2: "simplified",  # 简化认知图谱
    3: False,  # 无认知图谱
}


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

    CRITICAL = "critical"  # Death, birth, major transformation
    MAJOR = "major"  # Important events affecting story
    MINOR = "minor"  # Minor events, appearances


class ConflictType(str, Enum):
    """Types of timeline conflicts."""

    MULTIPLE_DEATHS = "multiple_deaths"  # Character dies multiple times
    ACTION_AFTER_DEATH = "action_after_death"  # Actions after confirmed death
    TEMPORAL_PARADOX = "temporal_paradox"  # Impossible sequence
    DUPLICATE_MAJOR_EVENT = "duplicate_major_event"  # Same major event twice
    STATUS_INCONSISTENCY = "status_inconsistency"  # Contradictory statuses


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
    """

    chapter: int
    event_type: EventType | str
    description: str
    importance: EventImportance | str = EventImportance.MINOR
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    id: int | None = None  # Database ID if persisted

    def __post_init__(self) -> None:
        """Normalize event type and importance to enum values."""
        if isinstance(self.event_type, str):
            try:
                self.event_type = EventType(self.event_type)
            except ValueError:
                pass  # Keep as custom string
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
        immutable_facts: Facts that cannot change (e.g., birth date, lineage)
        relationships: Mapping of other character names to relationship types
        metadata: Additional character metadata
        tier: Character tier (0=核心主角, 1=重要配角, 2=普通配角, 3=社会公众)
        has_cognitive_graph: Whether character has cognitive graph (auto-inferred)
        cognitive_graph_id: ID of the character's cognitive graph
        bio: Character biography (tier 0-1 complete, tier 2 simplified, tier 3 empty)
        persona: Character personality traits (tier 0-1 only)
        mbti: MBTI personality type (tier 0 only)
        profession: Character's profession or role
        interested_topics: List of topics the character is interested in
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
    bio: str = ""  # 人设信息 (tier 0-1 完整，tier 2 简化，tier 3 无)
    persona: str = ""  # 仅 tier 0-1
    mbti: str = ""  # 仅 tier 0
    profession: str = ""
    interested_topics: list[str] = field(default_factory=list)
    id: int | None = None  # Database ID if persisted
    tier: int = 1  # Default to important supporting character
    has_cognitive_graph: bool = field(init=False)
    cognitive_graph_id: str | None = None
    is_main: bool = field(init=False)
    is_supporting: bool = field(init=False)

    def __post_init__(self) -> None:
        """Normalize status to enum value and auto-inference."""
        if isinstance(self.current_status, str):
            try:
                self.current_status = CharacterStatus(self.current_status)
            except ValueError:
                self.current_status = CharacterStatus.UNKNOWN

        # 自动设置认知图谱
        self.has_cognitive_graph = bool(TIER_COGNITIVE_GRAPH.get(self.tier, False))
        self.cognitive_graph_id = None if not self.has_cognitive_graph else f"cg_{self.name}"

        # 向后兼容: tier映射到is_main/is_supporting
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

    def get_token_budget(self) -> int:
        """获取该角色的Token预算"""
        return TIER_TOKEN_BUDGET.get(self.tier, 0)

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
        severity: How severe the conflict is (critical, major, minor)
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


class CharacterProfileManager:
    """Manager for character profiles with timeline tracking.

    This class provides:
    - CRUD operations for character profiles
    - Timeline event management
    - Event extraction from chapter text
    - Timeline conflict detection
    - PostgreSQL storage integration

    Example:
        >>> from src.novel_agent.db.postgres_client import PostgresClient
        >>> client = PostgresClient("postgresql+asyncpg://...")
        >>> manager = CharacterProfileManager(client)
        >>> profile = await manager.create_profile("Alice")
        >>> events = manager.extract_events_from_chapter(chapter_text, 1)
        >>> for event in events:
        ...     await manager.add_event("Alice", event)
        >>> conflicts = await manager.detect_timeline_conflicts("Alice")
    """

    # Event extraction patterns for English text
    EVENT_PATTERNS_EN = {
        EventType.DEATH: [
            r"(?i)\b([A-Z][a-z]+)\s+(?:was\s+)?(?:drowned|died|killed|slain|perished)\b",
            r"(?i)\b([A-Z][a-z]+)\s+(?:was\s+)?(?:beheaded|executed)\b",
            r"(?i)\b([A-Z][a-z]+)\s+(?:was\s+)?(?:stabbed|shot|poisoned)\s+to\s+death\b",
            r"(?i)\b([A-Z][a-z]+)'s\s+(?:lifeless|dead)\s+body\b",
            r"(?i)\bdeath\s+of\s+([A-Z][a-z]+)\b",
        ],
        EventType.INJURY: [
            r"(?i)\b([A-Z][a-z]+)\s+(?:was\s+)?(?:wounded|injured|hurt|maimed)\b",
            r"(?i)\b([A-Z][a-z]+)\s+suffered\s+(?:a\s+)?(?:wound|injury)\b",
        ],
        EventType.RELATIONSHIP_CHANGE: [
            r"(?i)\b([A-Z][a-z]+)\s+(?:married|wed|became\s+friends\s+with|befriended)\s+([A-Z][a-z]+)\b",
            r"(?i)\b([A-Z][a-z]+)\s+(?:betrayed|killed|murdered)\s+([A-Z][a-z]+)\b",
        ],
        EventType.STATUS_CHANGE: [
            r"(?i)\b([A-Z][a-z]+)\s+(?:was\s+)?(?:crowned|promoted|exiled|imprisoned|freed)\b",
            r"(?i)\b([A-Z][a-z]+)\s+(?:became|transformed\s+into)\s+(?:a\s+)?(?:king|queen|dragon|spirit)\b",
        ],
        EventType.LOCATION_CHANGE: [
            r"(?i)\b([A-Z][a-z]+)\s+(?:arrived\s+(?:at|in)|traveled\s+to|entered)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
        ],
    }

    # Event extraction patterns for Chinese text
    EVENT_PATTERNS_ZH = {
        EventType.DEATH: [
            r"([^\s，。！？]{2,4})(?:溺水|淹死|死亡|牺牲|战死|被杀|自缢身亡)",
            r"([^\s，。！？]{2,4})的生命终结",
            r"([^\s，。！？]{2,4})的尸体",
        ],
        EventType.INJURY: [
            r"([^\s，。！？]{2,4})(?:受伤|负伤|被伤)",
            r"([^\s，。！？]{2,4})(?:断|失)了(?:左|右)?(?:手|脚|臂|腿)",
        ],
        EventType.RELATIONSHIP_CHANGE: [
            r"([^\s，。！？]{2,4})(?:与|和)([^\s，。！？]{2,4})(?:结婚|成为朋友|结为|背叛)",
        ],
        EventType.STATUS_CHANGE: [
            r"([^\s，。！？]{2,4})(?:登基|称王|被封|晋升|被囚|被流放)",
            r"([^\s，。！？]{2,4})变成了(?:龙|灵体|魔物)",
        ],
        EventType.LOCATION_CHANGE: [
            r"([^\s，。！？]{2,4})(?:到达|来到|进入)([^\s，。！？]{2,8})",
        ],
    }

    def __init__(
        self,
        postgres_client: PostgresClient | None = None,
        storage_path: Path | None = None,
    ) -> None:
        """Initialize the character profile manager.

        Args:
            postgres_client: Optional PostgreSQL client for persistence
            storage_path: Optional file path for JSON-based storage
        """
        self._postgres = postgres_client
        self._storage_path = storage_path
        self._profiles: dict[str, CharacterProfile] = {}
        self._profile_id_map: dict[int, str] = {}  # db_id -> name

        # Load from storage if path exists
        if storage_path and storage_path.exists():
            self._load_from_storage()

        logger.info(f"CharacterProfileManager initialized with {len(self._profiles)} profiles")

    def _load_from_storage(self) -> None:
        """Load profiles from JSON storage."""
        if not self._storage_path:
            return

        try:
            profiles_file = self._storage_path / "profiles.json"
            if profiles_file.exists():
                with open(profiles_file, encoding="utf-8") as f:
                    data = json.load(f)

                for profile_data in data.get("profiles", []):
                    profile = CharacterProfile.from_dict(profile_data)
                    self._profiles[profile.name] = profile
                    if profile.id:
                        self._profile_id_map[profile.id] = profile.name

                logger.info(f"Loaded {len(self._profiles)} profiles from {self._storage_path}")

        except Exception as e:
            logger.error(f"Failed to load profiles from {self._storage_path}: {e}")

    def _save_to_storage(self) -> None:
        """Save profiles to JSON storage."""
        if not self._storage_path:
            return

        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            profiles_file = self._storage_path / "profiles.json"

            data = {
                "profiles": [p.to_dict() for p in self._profiles.values()],
                "updated_at": datetime.now().isoformat(),
            }

            with open(profiles_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self._profiles)} profiles to {self._storage_path}")

        except Exception as e:
            logger.error(f"Failed to save profiles to {self._storage_path}: {e}")

    # ========================================
    # CRUD Operations
    # ========================================

    async def create_profile(
        self,
        name: str,
        aliases: list[str] | None = None,
        birth_chapter: int | None = None,
        death_chapter: int | None = None,
        current_status: str | CharacterStatus = CharacterStatus.ALIVE,
        metadata: dict[str, Any] | None = None,
    ) -> CharacterProfile:
        """Create a new character profile.

        Args:
            name: Character name
            aliases: List of alternative names
            birth_chapter: Chapter where character was introduced
            current_status: Initial character status
            metadata: Additional metadata

        Returns:
            Created CharacterProfile

        Raises:
            ValueError: If profile with same name already exists
        """
        if name in self._profiles:
            raise ValueError(f"Character profile '{name}' already exists")

        profile = CharacterProfile(
            name=name,
            aliases=aliases or [],
            birth_chapter=birth_chapter,
            death_chapter=death_chapter,
            current_status=current_status,
            metadata=metadata or {},
        )

        # Add birth/appearance event
        if birth_chapter is not None:
            birth_event = CharacterTimelineEvent(
                chapter=birth_chapter,
                event_type=EventType.BIRTH if birth_chapter == 1 else EventType.APPEARANCE,
                description=f"{name} was introduced" if birth_chapter > 1 else f"{name} was born",
                importance=EventImportance.CRITICAL,
            )
            profile.timeline.append(birth_event)

        # Persist to PostgreSQL if available
        if self._postgres:
            try:
                db_profile = await self._postgres.create_character(
                    name=name,
                    status=current_status.value
                    if isinstance(current_status, CharacterStatus)
                    else current_status,
                    birth_chapter=birth_chapter,
                    aliases=aliases,
                    metadata=metadata,
                )
                profile.id = db_profile.id
                self._profile_id_map[db_profile.id] = name
                logger.info(f"Created profile '{name}' in database (ID: {db_profile.id})")
            except Exception as e:
                logger.warning(f"Failed to persist profile to database: {e}")

        # Store in memory
        self._profiles[name] = profile

        # Save to file storage
        self._save_to_storage()

        logger.info(f"Created character profile: {name}")
        return profile

    def get_profile(self, name: str) -> CharacterProfile | None:
        """Get a character profile by name.

        Args:
            name: Character name

        Returns:
            CharacterProfile if found, None otherwise
        """
        # Check by primary name
        if name in self._profiles:
            return self._profiles[name]

        # Check by alias
        for profile in self._profiles.values():
            if name in profile.aliases:
                return profile

        return None

    async def get_profile_by_id(self, profile_id: int) -> CharacterProfile | None:
        """Get a character profile by database ID.

        Args:
            profile_id: Database ID

        Returns:
            CharacterProfile if found, None otherwise
        """
        # Check local cache first
        if profile_id in self._profile_id_map:
            name = self._profile_id_map[profile_id]
            return self._profiles.get(name)

        # Query database if available
        if self._postgres:
            try:
                db_profile = await self._postgres.get_character(profile_id)
                if db_profile:
                    profile = self._convert_db_to_profile(db_profile)
                    self._profiles[profile.name] = profile
                    self._profile_id_map[profile_id] = profile.name
                    return profile
            except Exception as e:
                logger.warning(f"Failed to get profile from database: {e}")

        return None

    def update_profile(self, profile: CharacterProfile) -> bool:
        """Update an existing character profile.

        Args:
            profile: Profile to update

        Returns:
            True if updated, False if not found
        """
        if profile.name not in self._profiles:
            logger.warning(f"Cannot update non-existent profile: {profile.name}")
            return False

        self._profiles[profile.name] = profile

        # Update in database if available
        if self._postgres and profile.id:
            try:
                asyncio.create_task(
                    self._postgres.update_character(
                        profile.id,
                        status=profile.current_status.value
                        if isinstance(profile.current_status, CharacterStatus)
                        else profile.current_status,
                        birth_chapter=profile.birth_chapter,
                        death_chapter=profile.death_chapter,
                        aliases=profile.aliases,
                        metadata=profile.metadata,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to update profile in database: {e}")

        self._save_to_storage()
        logger.debug(f"Updated profile: {profile.name}")
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete a character profile.

        Args:
            name: Character name to delete

        Returns:
            True if deleted, False if not found
        """
        if name not in self._profiles:
            return False

        profile = self._profiles[name]

        # Delete from database if available
        if self._postgres and profile.id:
            try:
                asyncio.create_task(self._postgres.delete_character(profile.id))
                del self._profile_id_map[profile.id]
            except Exception as e:
                logger.warning(f"Failed to delete profile from database: {e}")

        del self._profiles[name]
        self._save_to_storage()

        logger.info(f"Deleted profile: {name}")
        return True

    def list_profiles(
        self,
        status: CharacterStatus | str | None = None,
    ) -> list[CharacterProfile]:
        """List all character profiles with optional filtering.

        Args:
            status: Filter by status

        Returns:
            List of matching profiles
        """
        profiles = list(self._profiles.values())

        if status is not None:
            target_status = status.value if isinstance(status, CharacterStatus) else status
            profiles = [
                p
                for p in profiles
                if (
                    p.current_status.value
                    if isinstance(p.current_status, CharacterStatus)
                    else p.current_status
                )
                == target_status
            ]

        return profiles

    # ========================================
    # Timeline Event Operations
    # ========================================

    async def add_event(
        self,
        character_name: str,
        event: CharacterTimelineEvent,
    ) -> bool:
        """Add a timeline event to a character's profile.

        Args:
            character_name: Character name
            event: Event to add

        Returns:
            True if added, False if profile not found
        """
        profile = self.get_profile(character_name)
        if profile is None:
            logger.warning(f"Cannot add event to non-existent profile: {character_name}")
            return False

        profile.timeline.append(event)

        # Update status and chapter info based on event type
        if event.event_type == EventType.BIRTH:
            profile.birth_chapter = event.chapter
        if event.event_type == EventType.DEATH:
            profile.current_status = CharacterStatus.DECEASED
            profile.death_chapter = event.chapter

        # Persist to database if available
        if self._postgres and profile.id:
            try:
                await self._postgres.create_timeline_event(
                    chapter=event.chapter,
                    event_type=event.event_type.value
                    if isinstance(event.event_type, EventType)
                    else event.event_type,
                    description=event.description,
                    character_id=profile.id,
                    importance=event.importance.value
                    if isinstance(event.importance, EventImportance)
                    else event.importance,
                    metadata=event.metadata,
                )
            except Exception as e:
                logger.warning(f"Failed to persist event to database: {e}")

        self._save_to_storage()
        logger.debug(f"Added event to {character_name}: {event.event_type}")
        return True

    def get_timeline(
        self,
        character_name: str,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
    ) -> list[CharacterTimelineEvent]:
        """Get timeline events for a character.

        Args:
            character_name: Character name
            start_chapter: Optional start chapter filter
            end_chapter: Optional end chapter filter

        Returns:
            List of timeline events
        """
        profile = self.get_profile(character_name)
        if profile is None:
            return []

        events = profile.timeline

        if start_chapter is not None:
            events = [e for e in events if e.chapter >= start_chapter]
        if end_chapter is not None:
            events = [e for e in events if e.chapter <= end_chapter]

        return sorted(events, key=lambda e: e.chapter)

    # ========================================
    # Event Extraction
    # ========================================

    def extract_events_from_chapter(
        self,
        chapter_content: str,
        chapter_num: int,
        language: str = "auto",
    ) -> list[CharacterTimelineEvent]:
        """Extract timeline events from chapter text.

        Detects events like deaths, injuries, relationship changes, etc.
        from the chapter content.

        Args:
            chapter_content: Full chapter text
            chapter_num: Chapter number
            language: Language of text ("en", "zh", or "auto" for detection)

        Returns:
            List of extracted CharacterTimelineEvent objects
        """
        events: list[CharacterTimelineEvent] = []

        # Detect language if auto
        if language == "auto":
            # Simple heuristic: if >30% Chinese characters, use Chinese patterns
            chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", chapter_content))
            total_chars = len(chapter_content)
            language = "zh" if total_chars > 0 and chinese_chars / total_chars > 0.3 else "en"

        patterns = self.EVENT_PATTERNS_ZH if language == "zh" else self.EVENT_PATTERNS_EN

        # Extract death events
        for pattern in patterns.get(EventType.DEATH, []):
            for match in re.finditer(pattern, chapter_content):
                character_name = match.group(1)
                evidence = match.group(0)

                # Check if we already have a death event for this character
                existing_deaths = [
                    e
                    for e in events
                    if e.event_type == EventType.DEATH
                    and e.metadata.get("character_name") == character_name
                ]

                if not existing_deaths:
                    # Extract specific verb from evidence for better description
                    verb = "died"
                    evidence_lower = evidence.lower()
                    for v in ["drowned", "killed", "slain", "perished", "beheaded", "executed", "stabbed", "shot", "poisoned"]:
                        if v in evidence_lower:
                            verb = v
                            break

                    event = CharacterTimelineEvent(
                        chapter=chapter_num,
                        event_type=EventType.DEATH,
                        description=f"{character_name} {verb}",
                        importance=EventImportance.CRITICAL,
                        evidence=evidence,
                        metadata={"character_name": character_name},
                    )
                    events.append(event)
                    logger.debug(
                        f"Extracted death event: {character_name} in chapter {chapter_num}"
                    )

        # Extract injury events
        for pattern in patterns.get(EventType.INJURY, []):
            for match in re.finditer(pattern, chapter_content):
                character_name = match.group(1)
                evidence = match.group(0)

                event = CharacterTimelineEvent(
                    chapter=chapter_num,
                    event_type=EventType.INJURY,
                    description=f"{character_name} was injured",
                    importance=EventImportance.MAJOR,
                    evidence=evidence,
                    metadata={"character_name": character_name},
                )
                events.append(event)

        # Extract relationship changes
        for pattern in patterns.get(EventType.RELATIONSHIP_CHANGE, []):
            for match in re.finditer(pattern, chapter_content):
                try:
                    character1 = match.group(1)
                    character2 = match.group(2)
                    evidence = match.group(0)

                    # Determine relationship type from evidence
                    rel_type = "related"
                    if any(w in evidence.lower() for w in ["married", "wed", "结婚"]):
                        rel_type = "married"
                    elif any(w in evidence.lower() for w in ["friend", "朋友", "盟友"]):
                        rel_type = "friend"
                    elif any(w in evidence.lower() for w in ["betrayed", "背叛"]):
                        rel_type = "enemy"
                    elif any(w in evidence.lower() for w in ["killed", "murdered", "杀"]):
                        rel_type = "killer"

                    event = CharacterTimelineEvent(
                        chapter=chapter_num,
                        event_type=EventType.RELATIONSHIP_CHANGE,
                        description=f"{character1} relationship changed with {character2}",
                        importance=EventImportance.MAJOR,
                        evidence=evidence,
                        metadata={
                            "character1": character1,
                            "character2": character2,
                            "relationship_type": rel_type,
                        },
                    )
                    events.append(event)
                except (IndexError, AttributeError):
                    continue

        # Extract status changes
        for pattern in patterns.get(EventType.STATUS_CHANGE, []):
            for match in re.finditer(pattern, chapter_content):
                character_name = match.group(1)
                evidence = match.group(0)

                # Determine new status from evidence
                new_status = "unknown"
                if any(w in evidence.lower() for w in ["crowned", "称王", "登基"]):
                    new_status = "crowned"
                elif any(w in evidence.lower() for w in ["exiled", "流放"]):
                    new_status = "exiled"
                elif any(w in evidence.lower() for w in ["imprisoned", "被囚"]):
                    new_status = "imprisoned"

                event = CharacterTimelineEvent(
                    chapter=chapter_num,
                    event_type=EventType.STATUS_CHANGE,
                    description=f"{character_name} status changed to {new_status}",
                    importance=EventImportance.MAJOR,
                    evidence=evidence,
                    metadata={"character_name": character_name, "new_status": new_status},
                )
                events.append(event)

        # Extract location changes
        for pattern in patterns.get(EventType.LOCATION_CHANGE, []):
            for match in re.finditer(pattern, chapter_content):
                try:
                    character_name = match.group(1)
                    location = match.group(2)
                    evidence = match.group(0)

                    event = CharacterTimelineEvent(
                        chapter=chapter_num,
                        event_type=EventType.LOCATION_CHANGE,
                        description=f"{character_name} arrived at {location}",
                        importance=EventImportance.MINOR,
                        evidence=evidence,
                        metadata={"character_name": character_name, "location": location},
                    )
                    events.append(event)
                except (IndexError, AttributeError):
                    continue

        logger.info(f"Extracted {len(events)} events from chapter {chapter_num}")
        return events

    # ========================================
    # Conflict Detection
    # ========================================

    async def detect_timeline_conflicts(
        self,
        character_name: str,
    ) -> list[TimelineConflict]:
        """Detect timeline conflicts for a character.

        Checks for:
        - Multiple deaths (e.g., drowning twice)
        - Actions after confirmed death
        - Temporal paradoxes
        - Duplicate major events
        - Status inconsistencies

        Args:
            character_name: Character name to check

        Returns:
            List of detected TimelineConflict objects
        """
        profile = self.get_profile(character_name)
        if profile is None:
            return []

        conflicts: list[TimelineConflict] = []

        # 1. Check for multiple deaths
        death_events = profile.get_death_events()
        if len(death_events) > 1:
            for i in range(len(death_events) - 1):
                conflict = TimelineConflict(
                    conflict_type=ConflictType.MULTIPLE_DEATHS,
                    character_name=character_name,
                    event1=death_events[i],
                    event2=death_events[i + 1],
                    description=f"{character_name} died in chapter {death_events[i].chapter} "
                    f"but appears to die again in chapter {death_events[i + 1].chapter}",
                    severity="critical",
                    suggested_resolution=f"Verify if {character_name} truly died in chapter "
                    f"{death_events[i].chapter} or if the death in chapter "
                    f"{death_events[i + 1].chapter} is a flashback/visions",
                )
                conflicts.append(conflict)

        # 2. Check for actions after confirmed death
        if death_events:
            first_death = min(death_events, key=lambda e: e.chapter)
            events_after_death = [
                e
                for e in profile.timeline
                if e.chapter > first_death.chapter
                and e.event_type
                not in [
                    EventType.DEATH,
                    EventType.DISAPPEARANCE,
                ]
            ]

            for event in events_after_death:
                conflict = TimelineConflict(
                    conflict_type=ConflictType.ACTION_AFTER_DEATH,
                    character_name=character_name,
                    event1=first_death,
                    event2=event,
                    description=f"{character_name} has event '{event.description}' in chapter "
                    f"{event.chapter} after confirmed death in chapter {first_death.chapter}",
                    severity="critical",
                    suggested_resolution=f"Verify if {character_name} was resurrected, "
                    f"if the event is a flashback, or if the death was faked",
                )
                conflicts.append(conflict)

        # 3. Check for duplicate major events (e.g., drowning twice)
        major_events_by_type: dict[str, list[CharacterTimelineEvent]] = {}
        for event in profile.timeline:
            if event.importance in [EventImportance.CRITICAL, EventImportance.MAJOR]:
                event_key = f"{event.event_type}_{event.metadata.get('character_name', '')}"
                if event_key not in major_events_by_type:
                    major_events_by_type[event_key] = []
                major_events_by_type[event_key].append(event)

        for event_key, events in major_events_by_type.items():
            if len(events) > 1:
                # Check if this is a unique event type that shouldn't repeat
                event_type_str = (
                    events[0].event_type.value
                    if isinstance(events[0].event_type, EventType)
                    else str(events[0].event_type)
                )

                # Deaths and births should only happen once
                if event_type_str in ["death", "birth"]:
                    continue  # Already handled above

                # Check for similar descriptions (potential duplicate)
                for i in range(len(events) - 1):
                    for j in range(i + 1, len(events)):
                        # Check if events are similar (e.g., both drowning)
                        if self._events_are_similar(events[i], events[j]):
                            conflict = TimelineConflict(
                                conflict_type=ConflictType.DUPLICATE_MAJOR_EVENT,
                                character_name=character_name,
                                event1=events[i],
                                event2=events[j],
                                description=f"{character_name} experienced similar events: "
                                f"'{events[i].description}' (ch{events[i].chapter}) and "
                                f"'{events[j].description}' (ch{events[j].chapter})",
                                severity="major",
                                suggested_resolution="Verify if both events are intended or if "
                                "one is a mistake/flashback",
                            )
                            conflicts.append(conflict)

        # 4. Check for status inconsistencies
        profile.get_events_by_type(EventType.STATUS_CHANGE)
        current_status = profile.current_status

        # Check if current status aligns with timeline
        if current_status == CharacterStatus.DECEASED and not death_events:
            conflict = TimelineConflict(
                conflict_type=ConflictType.STATUS_INCONSISTENCY,
                character_name=character_name,
                event1=profile.timeline[0]
                if profile.timeline
                else CharacterTimelineEvent(
                    chapter=0,
                    event_type=EventType.STATUS_CHANGE,
                    description="Profile status",
                ),
                event2=CharacterTimelineEvent(
                    chapter=999,
                    event_type=EventType.STATUS_CHANGE,
                    description=f"Current status: {current_status.value}",
                ),
                description=f"{character_name} is marked as deceased but has no death event",
                severity="major",
                suggested_resolution="Add death event to timeline or update character status",
            )
            conflicts.append(conflict)

        # 5. Check temporal paradoxes (birth after death)
        if profile.birth_chapter and profile.death_chapter:
            if profile.birth_chapter > profile.death_chapter:
                conflict = TimelineConflict(
                    conflict_type=ConflictType.TEMPORAL_PARADOX,
                    character_name=character_name,
                    event1=CharacterTimelineEvent(
                        chapter=profile.birth_chapter,
                        event_type=EventType.BIRTH,
                        description=f"{character_name} was born",
                    ),
                    event2=CharacterTimelineEvent(
                        chapter=profile.death_chapter,
                        event_type=EventType.DEATH,
                        description=f"{character_name} died",
                    ),
                    description=f"{character_name} birth chapter ({profile.birth_chapter}) "
                    f"is after death chapter ({profile.death_chapter})",
                    severity="critical",
                    suggested_resolution="Correct birth or death chapter numbers",
                )
                conflicts.append(conflict)

        if conflicts:
            logger.warning(f"Detected {len(conflicts)} conflicts for {character_name}")
        else:
            logger.debug(f"No conflicts detected for {character_name}")

        return conflicts

    async def detect_all_conflicts(self) -> dict[str, list[TimelineConflict]]:
        """Detect conflicts for all character profiles.

        Returns:
            Dictionary mapping character names to their conflicts
        """
        all_conflicts: dict[str, list[TimelineConflict]] = {}

        for profile_name in self._profiles:
            conflicts = await self.detect_timeline_conflicts(profile_name)
            if conflicts:
                all_conflicts[profile_name] = conflicts

        return all_conflicts

    def _events_are_similar(
        self,
        event1: CharacterTimelineEvent,
        event2: CharacterTimelineEvent,
    ) -> bool:
        """Check if two events are similar enough to be potential duplicates.

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if events appear similar
        """
        # Same event type is a strong indicator
        if event1.event_type == event2.event_type:
            # Check for similar keywords in description
            keywords = ["drown", "溺水", "fall", "掉", "injury", "伤", "wound", "受伤"]
            desc1_lower = event1.description.lower()
            desc2_lower = event2.description.lower()

            for keyword in keywords:
                if keyword in desc1_lower and keyword in desc2_lower:
                    return True

        return False

    def _convert_db_to_profile(self, db_profile) -> CharacterProfile:
        """Convert database model to CharacterProfile dataclass.

        Args:
            db_profile: SQLAlchemy CharacterProfile model

        Returns:
            CharacterProfile dataclass instance
        """
        timeline_events = []
        for db_event in db_profile.timeline_events:
            event = CharacterTimelineEvent(
                chapter=db_event.chapter,
                event_type=db_event.event_type,
                description=db_event.description,
                importance=db_event.importance,
                metadata=json.loads(db_event.meta_data) if db_event.meta_data else {},
                id=db_event.id,
            )
            timeline_events.append(event)

        return CharacterProfile(
            name=db_profile.name,
            aliases=json.loads(db_profile.aliases) if db_profile.aliases else [],
            birth_chapter=db_profile.birth_chapter,
            death_chapter=db_profile.death_chapter,
            current_status=db_profile.status,
            timeline=timeline_events,
            metadata=json.loads(db_profile.meta_data) if db_profile.meta_data else {},
            id=db_profile.id,
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about character profiles.

        Returns:
            Dictionary with profile statistics
        """
        stats = {
            "total_profiles": len(self._profiles),
            "by_status": {},
            "total_events": 0,
            "profiles_with_conflicts": 0,
        }

        for profile in self._profiles.values():
            status = (
                profile.current_status.value
                if isinstance(profile.current_status, CharacterStatus)
                else profile.current_status
            )
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["total_events"] += len(profile.timeline)

        return stats


__all__ = [
    "CharacterProfile",
    "CharacterTimelineEvent",
    "CharacterProfileManager",
    "CharacterStatus",
    "EventType",
    "EventImportance",
    "ConflictType",
    "TimelineConflict",
]
