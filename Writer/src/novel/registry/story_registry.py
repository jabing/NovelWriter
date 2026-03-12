"""Centralized story registry for tracking all story elements.

This module provides the StoryRegistry class which serves as a single source
of truth for all story elements including chapters, characters, locations,
events, and titles. It prevents common issues like title duplication,
missing chapters, and orphaned references.
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChapterRecord:
    """Record of a completed chapter.

    Attributes:
        number: Chapter number (1-indexed)
        title: Full chapter title including format prefix
        content_hash: SHA256 hash of content for deduplication
        word_count: Total word count
        created_at: Timestamp when chapter was registered
        quality_score: Quality score from review (0-10)
        state_snapshot_id: Reference to story state checkpoint
    """

    number: int
    title: str
    content_hash: str
    word_count: int
    created_at: datetime
    quality_score: float
    state_snapshot_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChapterRecord":
        """Deserialize from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class EventRecord:
    """Record of a story event.

    Attributes:
        chapter: Chapter where event occurred
        description: Human-readable event description
        event_type: Type classification (character_death, location_change, etc.)
        entities: List of entity names involved
        importance: Importance level (critical, major, minor)
    """

    chapter: int
    description: str
    event_type: str
    entities: list[str] = field(default_factory=list)
    importance: str = "major"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventRecord":
        """Deserialize from dictionary."""
        return cls(**data)


class StoryRegistry:
    """Centralized registry for story elements.

    This class serves as the single source of truth for all story elements
    and prevents common issues:

    - Title duplication: Tracks all used titles and rejects duplicates
    - Missing chapters: Validates chapter sequence on registration
    - Orphaned references: Tracks all entities for reference validation

    Example:
        >>> registry = StoryRegistry("my_novel", Path("data/novels"))
        >>> registry.register_character("Alice")
        >>> registry.register_chapter(1, "Chapter 1: The Beginning", content, 8.5, "snap_001")
        True
    """

    def __init__(self, novel_id: str, storage_path: Path):
        """Initialize the story registry.

        Args:
            novel_id: Unique identifier for the novel
            storage_path: Base path for storing registry data
        """
        self.novel_id = novel_id
        self.storage_path = storage_path / novel_id
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory indices for fast lookup
        self._chapters: dict[int, ChapterRecord] = {}
        self._events: list[EventRecord] = []
        self._characters: set[str] = set()
        self._locations: set[str] = set()
        self._items: set[str] = set()
        self._abilities: set[str] = set()
        self._titles: dict[int, str] = {}  # chapter -> title
        self._content_hashes: set[str] = set()

        # Load existing data
        self._load_registry()

        logger.info(f"StoryRegistry initialized for '{novel_id}'")

    def register_chapter(
        self,
        number: int,
        title: str,
        content: str,
        quality_score: float,
        state_snapshot_id: str,
    ) -> bool:
        """Register a completed chapter.

        Validates:
        1. Chapter doesn't already exist
        2. No sequence gaps (previous chapter must exist)
        3. Title is unique
        4. Content is not a duplicate

        Args:
            number: Chapter number
            title: Full chapter title
            content: Chapter content
            quality_score: Quality score from review
            state_snapshot_id: Reference to state checkpoint

        Returns:
            True if registration successful, False otherwise
        """
        # Validate chapter number
        if number in self._chapters:
            logger.error(f"Chapter {number} already exists in registry")
            return False

        # Check for sequence gap (except chapter 1)
        if number > 1 and (number - 1) not in self._chapters:
            logger.error(f"Cannot register chapter {number}: chapter {number - 1} does not exist")
            return False

        # Extract title text and check uniqueness
        title_text = self._extract_title_text(title)
        for ch, existing_title in self._titles.items():
            existing_text = self._extract_title_text(existing_title)
            if existing_text.lower() == title_text.lower():
                logger.error(f"Title '{title_text}' already used in chapter {ch}")
                return False

        # Check for duplicate content
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        if content_hash in self._content_hashes:
            logger.error(f"Content appears to be duplicate (hash: {content_hash})")
            return False

        # Register chapter
        record = ChapterRecord(
            number=number,
            title=title,
            content_hash=content_hash,
            word_count=len(content.split()),
            created_at=datetime.now(),
            quality_score=quality_score,
            state_snapshot_id=state_snapshot_id,
        )

        self._chapters[number] = record
        self._titles[number] = title
        self._content_hashes.add(content_hash)

        self._save_registry()
        logger.info(f"Registered chapter {number}: {title}")
        return True

    def unregister_chapter(self, number: int) -> bool:
        """Remove a chapter from the registry.

        Args:
            number: Chapter number to remove

        Returns:
            True if removed, False if not found
        """
        if number not in self._chapters:
            return False

        record = self._chapters.pop(number)
        self._titles.pop(number, None)
        self._content_hashes.discard(record.content_hash)

        self._save_registry()
        logger.info(f"Unregistered chapter {number}")
        return True

    def register_event(
        self,
        chapter: int,
        description: str,
        event_type: str,
        entities: list[str] | None = None,
        importance: str = "major",
    ) -> None:
        """Register a story event.

        Args:
            chapter: Chapter where event occurred
            description: Human-readable description
            event_type: Type classification
            entities: Entities involved
            importance: Importance level
        """
        event = EventRecord(
            chapter=chapter,
            description=description,
            event_type=event_type,
            entities=entities or [],
            importance=importance,
        )
        self._events.append(event)
        self._save_registry()
        logger.debug(f"Registered event: {description[:50]}...")

    def register_character(self, name: str) -> None:
        """Register a character in the story.

        Args:
            name: Character name
        """
        if name not in self._characters:
            self._characters.add(name)
            self._save_registry()
            logger.debug(f"Registered character: {name}")

    def register_location(self, name: str) -> None:
        """Register a location in the story.

        Args:
            name: Location name
        """
        if name not in self._locations:
            self._locations.add(name)
            self._save_registry()
            logger.debug(f"Registered location: {name}")

    def register_item(self, name: str) -> None:
        """Register an item in the story.

        Args:
            name: Item name
        """
        if name not in self._items:
            self._items.add(name)
            self._save_registry()
            logger.debug(f"Registered item: {name}")

    def register_ability(self, name: str) -> None:
        """Register an ability in the story.

        Args:
            name: Ability name
        """
        if name not in self._abilities:
            self._abilities.add(name)
            self._save_registry()
            logger.debug(f"Registered ability: {name}")

    def chapter_exists(self, number: int) -> bool:
        """Check if chapter exists.

        Args:
            number: Chapter number

        Returns:
            True if chapter exists
        """
        return number in self._chapters

    def get_chapter(self, number: int) -> ChapterRecord | None:
        """Get chapter record.

        Args:
            number: Chapter number

        Returns:
            ChapterRecord if found, None otherwise
        """
        return self._chapters.get(number)

    def get_chapters(self, start: int, end: int) -> list[ChapterRecord]:
        """Get chapters in range.

        Args:
            start: Start chapter (inclusive)
            end: End chapter (inclusive)

        Returns:
            List of chapter records in order
        """
        return [self._chapters[n] for n in range(start, end + 1) if n in self._chapters]

    def get_missing_chapters(self, up_to: int) -> list[int]:
        """Find gaps in chapter sequence.

        Args:
            up_to: Maximum chapter number to check

        Returns:
            List of missing chapter numbers
        """
        existing = set(self._chapters.keys())
        expected = set(range(1, up_to + 1))
        return sorted(expected - existing)

    def get_latest_chapter(self) -> int:
        """Get the latest chapter number.

        Returns:
            Latest chapter number, or 0 if no chapters
        """
        if not self._chapters:
            return 0
        return max(self._chapters.keys())

    def get_events(
        self,
        chapter: int | None = None,
        event_type: str | None = None,
        min_importance: str | None = None,
    ) -> list[EventRecord]:
        """Get events with optional filtering.

        Args:
            chapter: Filter by chapter (events up to this chapter)
            event_type: Filter by event type
            min_importance: Filter by minimum importance

        Returns:
            List of matching events
        """
        events = self._events

        if chapter is not None:
            events = [e for e in events if e.chapter <= chapter]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if min_importance is not None:
            importance_order = {"critical": 3, "major": 2, "minor": 1}
            min_level = importance_order.get(min_importance, 0)
            events = [e for e in events if importance_order.get(e.importance, 0) >= min_level]

        return events

    def character_exists(self, name: str) -> bool:
        """Check if character is registered.

        Args:
            name: Character name

        Returns:
            True if character exists
        """
        return name in self._characters

    def location_exists(self, name: str) -> bool:
        """Check if location is registered.

        Args:
            name: Location name

        Returns:
            True if location exists
        """
        return name in self._locations

    def item_exists(self, name: str) -> bool:
        """Check if item is registered.

        Args:
            name: Item name

        Returns:
            True if item exists
        """
        return name in self._items

    def ability_exists(self, name: str) -> bool:
        """Check if ability is registered.

        Args:
            name: Ability name

        Returns:
            True if ability exists
        """
        return name in self._abilities

    def get_all_characters(self) -> list[str]:
        """Get all registered characters."""
        return sorted(self._characters)

    def get_all_locations(self) -> list[str]:
        """Get all registered locations."""
        return sorted(self._locations)

    def get_all_titles(self) -> dict[int, str]:
        """Get all registered titles."""
        return self._titles.copy()

    def is_title_used(self, title: str, exclude_chapter: int | None = None) -> bool:
        """Check if title is already used.

        Args:
            title: Title to check
            exclude_chapter: Chapter to exclude from check

        Returns:
            True if title is used
        """
        title_text = self._extract_title_text(title).lower()
        for ch, existing in self._titles.items():
            if exclude_chapter is not None and ch == exclude_chapter:
                continue
            if self._extract_title_text(existing).lower() == title_text:
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "novel_id": self.novel_id,
            "total_chapters": len(self._chapters),
            "latest_chapter": self.get_latest_chapter(),
            "total_events": len(self._events),
            "total_characters": len(self._characters),
            "total_locations": len(self._locations),
            "total_items": len(self._items),
            "total_abilities": len(self._abilities),
            "average_quality": (
                sum(c.quality_score for c in self._chapters.values()) / len(self._chapters)
                if self._chapters
                else 0
            ),
            "total_words": sum(c.word_count for c in self._chapters.values()),
        }

    def _extract_title_text(self, full_title: str) -> str:
        """Extract title text from full title.

        Removes chapter number prefix.

        Args:
            full_title: Full title with prefix

        Returns:
            Title text only
        """
        import re

        # Match common title patterns
        patterns = [
            r"第\d+章[：:\s]*(.+)",  # Chinese: 第1章：Title
            r"Chapter\s+\d+[：:\s]*(.+)",  # English: Chapter 1: Title
        ]

        for pattern in patterns:
            match = re.match(pattern, full_title)
            if match:
                return match.group(1).strip()

        return full_title.strip()

    def _load_registry(self) -> None:
        """Load registry from storage."""
        registry_path = self.storage_path / "registry.json"
        if not registry_path.exists():
            return

        try:
            with open(registry_path, encoding="utf-8") as f:
                data = json.load(f)

            # Load chapters
            for ch_data in data.get("chapters", []):
                record = ChapterRecord.from_dict(ch_data)
                self._chapters[record.number] = record
                self._titles[record.number] = record.title
                self._content_hashes.add(record.content_hash)

            # Load events
            for ev_data in data.get("events", []):
                self._events.append(EventRecord.from_dict(ev_data))

            # Load entity sets
            self._characters = set(data.get("characters", []))
            self._locations = set(data.get("locations", []))
            self._items = set(data.get("items", []))
            self._abilities = set(data.get("abilities", []))

            logger.info(
                f"Loaded registry: {len(self._chapters)} chapters, "
                f"{len(self._events)} events, {len(self._characters)} characters"
            )

        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

    def _save_registry(self) -> None:
        """Save registry to storage."""
        registry_path = self.storage_path / "registry.json"

        data = {
            "novel_id": self.novel_id,
            "chapters": [
                c.to_dict() for c in sorted(self._chapters.values(), key=lambda x: x.number)
            ],
            "events": [e.to_dict() for e in self._events],
            "characters": list(self._characters),
            "locations": list(self._locations),
            "items": list(self._items),
            "abilities": list(self._abilities),
        }

        # Atomic write
        temp_path = registry_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            temp_path.rename(registry_path)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise
