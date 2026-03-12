"""SQLAlchemy models for PostgreSQL database.

This module defines the database schema for character profiles, timeline events,
story facts, and contradictions using SQLAlchemy 2.0 async ORM.

Tables:
    - character_profiles: Character information and status
    - timeline_events: Events in the story timeline
    - story_facts: Facts extracted from chapters
    - contradictions: Detected contradictions between facts
"""

import logging
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models with async attribute loading."""

    pass


class CharacterStatus(str, PyEnum):
    """Character status in the story."""

    ACTIVE = "active"
    DECEASED = "deceased"
    UNKNOWN = "unknown"
    MISSING = "missing"


class EventType(str, PyEnum):
    """Types of timeline events."""

    BIRTH = "birth"
    DEATH = "death"
    APPEARANCE = "appearance"
    DISAPPEARANCE = "disappearance"
    MAJOR_EVENT = "major_event"
    RELATIONSHIP_CHANGE = "relationship_change"
    LOCATION_CHANGE = "location_change"
    STATUS_CHANGE = "status_change"


class ImportanceLevel(str, PyEnum):
    """Importance levels for events and facts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EntityType(str, PyEnum):
    """Types of entities in story facts."""

    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    WORLD_RULE = "world_rule"
    PLOT_THREAD = "plot_thread"


class ContradictionType(str, PyEnum):
    """Types of contradictions."""

    TEMPORAL = "temporal"  # Time-based contradictions
    FACTUAL = "factual"  # Fact-based contradictions
    LOGICAL = "logical"  # Logical inconsistencies
    CHARACTER = "character"  # Character-related contradictions
    WORLD_BUILDING = "world_building"  # World rule violations


class SeverityLevel(str, PyEnum):
    """Severity levels for contradictions."""

    CRITICAL = "critical"  # Must be fixed before publication
    HIGH = "high"  # Should be fixed
    MEDIUM = "medium"  # Good to fix
    LOW = "low"  # Minor issue


class CharacterProfile(Base):
    """Character profile information.

    Stores comprehensive information about characters in the story,
    including their status, lifespan, and metadata.

    Attributes:
        id: Primary key (auto-increment)
        name: Character name (required, indexed)
        status: Character status (active/deceased/unknown/missing)
        birth_chapter: Chapter where character was born/introduced
        death_chapter: Chapter where character died (if applicable)
        aliases: JSON-serialized list of character aliases
        metadata: Additional character metadata (JSON)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
        timeline_events: Relationship to timeline events
    """

    __tablename__ = "character_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CharacterStatus.ACTIVE.value,
        index=True,
    )
    birth_chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    death_chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        "TimelineEvent",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    story_facts: Mapped[list["StoryFact"]] = relationship(
        "StoryFact",
        back_populates="character",
        cascade="all, delete-orphan",
        foreign_keys="StoryFact.entity_id",
        primaryjoin="and_(CharacterProfile.id == foreign(StoryFact.entity_id), "
        "StoryFact.entity_type == 'character')",
    )

    # Constraints
    __table_args__ = (
        Index("idx_character_status", "status"),
        Index("idx_character_name_status", "name", "status"),
        # Ensure death_chapter is after birth_chapter if both exist
        # Note: This will be enforced in application logic
    )

    def __repr__(self) -> str:
        return f"<CharacterProfile(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "birth_chapter": self.birth_chapter,
            "death_chapter": self.death_chapter,
            "aliases": json.loads(self.aliases) if self.aliases else [],
            "metadata": json.loads(self.meta_data) if self.meta_data else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TimelineEvent(Base):
    """Timeline event for tracking story progression.

    Stores events that occur in the story timeline, associated with
    characters, chapters, and importance levels.

    Attributes:
        id: Primary key (auto-increment)
        character_id: Foreign key to character_profiles (indexed)
        chapter: Chapter number where event occurred (indexed)
        event_type: Type of event (indexed)
        description: Event description
        importance: Importance level (indexed)
        metadata: Additional event metadata (JSON)
        created_at: Record creation timestamp
        character: Relationship to CharacterProfile
    """

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("character_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    chapter: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=EventType.APPEARANCE.value,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=ImportanceLevel.MEDIUM.value,
        index=True,
    )
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    character: Mapped["CharacterProfile | None"] = relationship(
        "CharacterProfile",
        back_populates="timeline_events",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_timeline_chapter", "chapter"),
        Index("idx_timeline_character_chapter", "character_id", "chapter"),
        Index("idx_timeline_type_importance", "event_type", "importance"),
    )

    def __repr__(self) -> str:
        return (
            f"<TimelineEvent(id={self.id}, chapter={self.chapter}, "
            f"type='{self.event_type}')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        import json

        return {
            "id": self.id,
            "character_id": self.character_id,
            "chapter": self.chapter,
            "event_type": self.event_type,
            "description": self.description,
            "importance": self.importance,
            "metadata": json.loads(self.meta_data) if self.meta_data else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StoryFact(Base):
    """Story fact extracted from chapter content.

    Stores facts extracted from the story for consistency checking
    and context injection during generation.

    Attributes:
        id: Primary key (auto-increment)
        entity_type: Type of entity (character/location/item/etc) (indexed)
        entity_id: ID of the related entity (indexed, nullable)
        category: Fact category (indexed)
        attribute: Fact attribute name
        value: Fact value
        source_chapter: Chapter where fact was introduced (indexed)
        confidence: Confidence score (0.0 to 1.0)
        is_immutable: Whether fact can be changed
        metadata: Additional metadata (JSON)
        created_at: Record creation timestamp
        character: Relationship to CharacterProfile (conditional)
    """

    __tablename__ = "story_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    attribute: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source_chapter: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    is_immutable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    character: Mapped["CharacterProfile | None"] = relationship(
        "CharacterProfile",
        back_populates="story_facts",
        foreign_keys=[entity_id],
        primaryjoin="and_(CharacterProfile.id == foreign(StoryFact.entity_id), "
        "StoryFact.entity_type == 'character')",
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_fact_entity", "entity_type", "entity_id"),
        Index("idx_fact_category", "category"),
        Index("idx_fact_chapter", "source_chapter"),
        Index("idx_fact_entity_attr", "entity_type", "entity_id", "attribute"),
        # Check constraint for confidence
        # Note: PostgreSQL check constraint will be added via migration
    )

    def __repr__(self) -> str:
        return (
            f"<StoryFact(id={self.id}, entity_type='{self.entity_type}', "
            f"category='{self.category}')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        import json

        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "category": self.category,
            "attribute": self.attribute,
            "value": self.value,
            "source_chapter": self.source_chapter,
            "confidence": self.confidence,
            "is_immutable": self.is_immutable,
            "metadata": json.loads(self.meta_data) if self.meta_data else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Contradiction(Base):
    """Detected contradiction between story facts.

    Stores information about contradictions detected between
    different facts in the story for quality assurance.

    Attributes:
        id: Primary key (auto-increment)
        fact1_id: Foreign key to first conflicting fact
        fact2_id: Foreign key to second conflicting fact
        contradiction_type: Type of contradiction (indexed)
        severity: Severity level (indexed)
        description: Human-readable description
        detected_at: Detection timestamp
        resolved: Whether contradiction is resolved (indexed)
        resolution_notes: Notes on how contradiction was resolved
        resolved_at: Resolution timestamp
        fact1: Relationship to first StoryFact
        fact2: Relationship to second StoryFact
    """

    __tablename__ = "contradictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact1_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("story_facts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fact2_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("story_facts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contradiction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default=SeverityLevel.MEDIUM.value,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    fact1: Mapped["StoryFact"] = relationship(
        "StoryFact",
        foreign_keys=[fact1_id],
    )
    fact2: Mapped["StoryFact"] = relationship(
        "StoryFact",
        foreign_keys=[fact2_id],
    )

    # Constraints and indexes
    __table_args__ = (
        Index("idx_contradiction_type", "contradiction_type"),
        Index("idx_contradiction_severity", "severity"),
        Index("idx_contradiction_resolved", "resolved"),
        Index(
            "idx_contradiction_facts",
            "fact1_id",
            "fact2_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Contradiction(id={self.id}, type='{self.contradiction_type}', "
            f"severity='{self.severity}', resolved={self.resolved})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "fact1_id": self.fact1_id,
            "fact2_id": self.fact2_id,
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "description": self.description,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
