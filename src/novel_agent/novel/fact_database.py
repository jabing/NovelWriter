"""Fact database for tracking and retrieving story facts.

This module provides the Fact data model and FactDatabase for managing
facts extracted from chapter content. Facts are used to inject relevant
context during chapter generation.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FactType(str, Enum):
    """Types of facts that can be extracted."""

    CHARACTER = "character"
    LOCATION = "location"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    ITEM = "item"
    WORLD_RULE = "world_rule"
    PLOT_THREAD = "plot_thread"


@dataclass
class Fact:
    """A fact extracted from chapter content.

    Facts represent important pieces of information that should be
    tracked across the story for consistency and context injection.

    Attributes:
        id: Unique identifier for the fact
        fact_type: Type of fact (character, location, event, etc.)
        content: The actual fact content/description
        chapter_origin: Chapter number where this fact was introduced
        importance: Importance score (0.0 to 1.0)
        last_referenced: Chapter number where this was last referenced
        reference_count: Number of times this fact has been referenced
        entities: List of entity names mentioned in this fact
        created_at: When this fact was created
        metadata: Additional metadata
    """

    id: str
    fact_type: FactType
    content: str
    chapter_origin: int
    importance: float = 0.5
    last_referenced: int = 0
    reference_count: int = 0
    entities: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fact data."""
        if isinstance(self.fact_type, str):
            self.fact_type = FactType(self.fact_type)
        self.importance = max(0.0, min(1.0, self.importance))

    def touch(self, chapter: int) -> None:
        """Mark this fact as referenced in a chapter.

        Args:
            chapter: Chapter number where referenced
        """
        self.last_referenced = chapter
        self.reference_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "fact_type": self.fact_type.value,
            "content": self.content,
            "chapter_origin": self.chapter_origin,
            "importance": self.importance,
            "last_referenced": self.last_referenced,
            "reference_count": self.reference_count,
            "entities": self.entities,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Fact":
        """Deserialize from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "fact_type" in data:
            data["fact_type"] = FactType(data["fact_type"])
        return cls(**data)

    def get_context_string(self) -> str:
        """Generate context string for LLM."""
        type_labels = {
            FactType.CHARACTER: "角色",
            FactType.LOCATION: "地点",
            FactType.EVENT: "事件",
            FactType.RELATIONSHIP: "关系",
            FactType.ITEM: "物品",
            FactType.WORLD_RULE: "世界规则",
            FactType.PLOT_THREAD: "剧情线",
        }
        label = type_labels.get(self.fact_type, "事实")
        return f"【{label}】{self.content}"


class FactDatabase:
    """Database for storing and retrieving story facts.

    This class manages a collection of facts with support for:
    - Adding new facts
    - Querying facts by type, entity, chapter
    - Scoring fact relevance
    - Persistence to disk

    Attributes:
        storage_path: Path for storing fact database
        facts: Dictionary of all facts by ID
    """

    def __init__(self, storage_path: Path, novel_id: str) -> None:
        """Initialize the fact database.

        Args:
            storage_path: Base directory for storage
            novel_id: Novel identifier
        """
        self.storage_path = storage_path / novel_id
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "facts.json"

        # In-memory fact storage
        self.facts: dict[str, Fact] = {}

        # Index for quick lookups
        self._type_index: dict[FactType, list[str]] = {t: [] for t in FactType}
        self._entity_index: dict[str, list[str]] = {}
        self._chapter_index: dict[int, list[str]] = {}

        # Load existing facts
        self._load()

    def _load(self) -> None:
        """Load facts from disk."""
        if not self.db_path.exists():
            return

        try:
            with open(self.db_path, encoding="utf-8") as f:
                data = json.load(f)
                for fact_data in data.get("facts", []):
                    fact = Fact.from_dict(fact_data)
                    self.facts[fact.id] = fact
                    self._index_fact(fact)
            logger.info(f"Loaded {len(self.facts)} facts from disk")
        except Exception as e:
            logger.error(f"Failed to load facts: {e}")

    def save(self) -> None:
        """Save facts to disk."""
        data = {
            "facts": [f.to_dict() for f in self.facts.values()],
            "version": 1,
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved {len(self.facts)} facts to disk")

    def _index_fact(self, fact: Fact) -> None:
        """Add fact to indices for quick lookup.

        Args:
            fact: Fact to index
        """
        # Type index
        if fact.id not in self._type_index[fact.fact_type]:
            self._type_index[fact.fact_type].append(fact.id)

        # Entity index
        for entity in fact.entities:
            if entity not in self._entity_index:
                self._entity_index[entity] = []
            if fact.id not in self._entity_index[entity]:
                self._entity_index[entity].append(fact.id)

        # Chapter index
        if fact.chapter_origin not in self._chapter_index:
            self._chapter_index[fact.chapter_origin] = []
        if fact.id not in self._chapter_index[fact.chapter_origin]:
            self._chapter_index[fact.chapter_origin].append(fact.id)

    def add_fact(
        self,
        fact_type: FactType | str,
        content: str,
        chapter_origin: int,
        importance: float = 0.5,
        entities: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Fact:
        """Add a new fact to the database.

        Args:
            fact_type: Type of fact
            content: Fact content/description
            chapter_origin: Chapter where fact was introduced
            importance: Importance score (0.0 to 1.0)
            entities: Related entity names
            metadata: Additional metadata

        Returns:
            Created Fact object
        """
        if isinstance(fact_type, str):
            fact_type = FactType(fact_type)

        fact = Fact(
            id=str(uuid.uuid4()),
            fact_type=fact_type,
            content=content,
            chapter_origin=chapter_origin,
            importance=importance,
            entities=entities or [],
            metadata=metadata or {},
        )

        self.facts[fact.id] = fact
        self._index_fact(fact)
        self.save()

        logger.debug(f"Added fact: {fact_type.value} - {content[:50]}...")
        return fact

    def get_fact(self, fact_id: str) -> Fact | None:
        """Get a fact by ID.

        Args:
            fact_id: Fact identifier

        Returns:
            Fact if found, None otherwise
        """
        return self.facts.get(fact_id)

    def get_facts_by_type(self, fact_type: FactType) -> list[Fact]:
        """Get all facts of a specific type.

        Args:
            fact_type: Type of facts to retrieve

        Returns:
            List of matching facts
        """
        fact_ids = self._type_index.get(fact_type, [])
        return [self.facts[fid] for fid in fact_ids if fid in self.facts]

    def get_facts_by_entity(self, entity: str) -> list[Fact]:
        """Get all facts related to an entity.

        Args:
            entity: Entity name to search for

        Returns:
            List of matching facts
        """
        fact_ids = self._entity_index.get(entity, [])
        return [self.facts[fid] for fid in fact_ids if fid in self.facts]

    def get_facts_by_chapter(self, chapter: int) -> list[Fact]:
        """Get all facts from a specific chapter.

        Args:
            chapter: Chapter number

        Returns:
            List of matching facts
        """
        fact_ids = self._chapter_index.get(chapter, [])
        return [self.facts[fid] for fid in fact_ids if fid in self.facts]

    def get_all_facts(self) -> list[Fact]:
        """Get all facts in the database.

        Returns:
            List of all facts
        """
        return list(self.facts.values())

    def update_fact_reference(self, fact_id: str, chapter: int) -> None:
        """Update fact reference information.

        Args:
            fact_id: Fact identifier
            chapter: Chapter where referenced
        """
        fact = self.facts.get(fact_id)
        if fact:
            fact.touch(chapter)
            self.save()

    def delete_fact(self, fact_id: str) -> bool:
        """Delete a fact from the database.

        Args:
            fact_id: Fact identifier

        Returns:
            True if deleted, False if not found
        """
        if fact_id not in self.facts:
            return False

        fact = self.facts[fact_id]

        # Remove from indices
        if fact_id in self._type_index[fact.fact_type]:
            self._type_index[fact.fact_type].remove(fact_id)

        for entity in fact.entities:
            if entity in self._entity_index and fact_id in self._entity_index[entity]:
                self._entity_index[entity].remove(fact_id)

        if fact.chapter_origin in self._chapter_index:
            if fact_id in self._chapter_index[fact.chapter_origin]:
                self._chapter_index[fact.chapter_origin].remove(fact_id)

        # Remove fact
        del self.facts[fact_id]
        self.save()

        return True

    def get_fact_count(self) -> int:
        """Get total number of facts.

        Returns:
            Fact count
        """
        return len(self.facts)

    def get_fact_count_by_type(self) -> dict[FactType, int]:
        """Get fact counts by type.

        Returns:
            Dictionary of type to count
        """
        return {fact_type: len(fact_ids) for fact_type, fact_ids in self._type_index.items()}
