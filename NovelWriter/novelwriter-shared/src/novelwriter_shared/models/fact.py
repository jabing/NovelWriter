"""Fact data model for tracking story facts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FactType(str, Enum):
    """Types of facts that can be tracked."""

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

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fact_type: FactType | str = FactType.EVENT
    content: str = ""
    chapter_origin: int = 0
    importance: float = 0.5
    last_referenced: int = 0
    reference_count: int = 0
    entities: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fact data."""
        if isinstance(self.fact_type, str):
            try:
                self.fact_type = FactType(self.fact_type)
            except ValueError:
                pass
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
            "fact_type": self.fact_type.value
            if isinstance(self.fact_type, FactType)
            else self.fact_type,
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
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        """Deserialize from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "fact_type" in data:
            try:
                data["fact_type"] = FactType(data["fact_type"])
            except ValueError:
                pass
        return cls(**data)

    def get_context_string(self) -> str:
        """Generate context string for LLM."""
        type_labels: dict[FactType, str] = {
            FactType.CHARACTER: "角色",
            FactType.LOCATION: "地点",
            FactType.EVENT: "事件",
            FactType.RELATIONSHIP: "关系",
            FactType.ITEM: "物品",
            FactType.WORLD_RULE: "世界规则",
            FactType.PLOT_THREAD: "剧情线",
        }
        fact_type = self.fact_type if isinstance(self.fact_type, FactType) else FactType.EVENT
        label = type_labels.get(fact_type, "事实")
        return f"[{label}] {self.content}"
