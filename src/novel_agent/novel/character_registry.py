"""Character registry for managing unique character IDs.

This module provides a registry system for tracking characters with unique IDs,
solving the problem of multiple characters with the same name (e.g., "三个林晓").

Usage:
    registry = CharacterRegistry()
    role_id = registry.register("林晓", role="protagonist", chapter=1)
    entry = registry.get_by_id(role_id)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CharacterEntry:
    """Entry in the character registry.

    Attributes:
        role_id: Unique identifier for this character (e.g., "char_林晓_001")
        name: Character's name
        role: Character's role in the story (protagonist, antagonist, supporting, etc.)
        first_appearance: Chapter number where character first appears
        aliases: Alternative names for this character
        metadata: Additional character metadata
    """

    role_id: str
    name: str
    role: str | None = None
    first_appearance: int = 0
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterEntry:
        """Create from dictionary."""
        return cls(
            role_id=data["role_id"],
            name=data["name"],
            role=data.get("role"),
            first_appearance=data.get("first_appearance", 0),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {}),
        )


class CharacterRegistry:
    """Registry for managing unique character IDs.

    Allows same-named characters to have different role_ids,
    solving the "三个林晓" problem where multiple characters
    share the same name.

    Example:
        >>> registry = CharacterRegistry()
        >>> id1 = registry.register("林晓", role="protagonist")
        >>> id2 = registry.register("林晓", role="antagonist")
        >>> assert id1 != id2
        >>> assert id1 == "char_林晓_001"
        >>> assert id2 == "char_林晓_002"
    """

    def __init__(self) -> None:
        """Initialize the character registry."""
        self._entries: dict[str, CharacterEntry] = {}  # role_id -> entry
        self._name_index: dict[str, list[str]] = {}  # name -> [role_ids]
        self._counter: dict[str, int] = {}  # sanitized_name -> next sequence

    def register(
        self,
        name: str,
        role: str | None = None,
        chapter: int = 0,
        aliases: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Register a new character, returns unique role_id.

        Args:
            name: Character name
            role: Optional role (protagonist, antagonist, etc.)
            chapter: Chapter where character first appears
            aliases: Optional list of alternative names
            metadata: Optional additional metadata

        Returns:
            Unique role_id like "char_林晓_001"
        """
        role_id = self._generate_role_id(name)

        entry = CharacterEntry(
            role_id=role_id,
            name=name,
            role=role,
            first_appearance=chapter,
            aliases=aliases or [],
            metadata=metadata or {},
        )

        # Store entry
        self._entries[role_id] = entry

        # Update name index
        if name not in self._name_index:
            self._name_index[name] = []
        self._name_index[name].append(role_id)

        logger.debug(f"Registered character: {name} -> {role_id}")
        return role_id

    def get_or_create(
        self,
        name: str,
        role: str | None = None,
        chapter: int = 0,
        aliases: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Get existing role_id or create new entry.

        If characters with this name already exist:
        - Return first match if only one exists
        - Create new entry if multiple exist (ambiguous case)

        Args:
            name: Character name
            role: Optional role
            chapter: Chapter where character first appears
            aliases: Optional list of alternative names
            metadata: Optional additional metadata

        Returns:
            Unique role_id
        """
        existing_ids = self._name_index.get(name, [])

        # If exactly one exists, return it
        if len(existing_ids) == 1:
            return existing_ids[0]

        # If none exist, create new
        if len(existing_ids) == 0:
            return self.register(name, role, chapter, aliases, metadata)

        # Multiple exist - ambiguous, create new
        logger.warning(
            f"Ambiguous get_or_create for '{name}': {len(existing_ids)} entries exist, "
            "creating new entry"
        )
        return self.register(name, role, chapter, aliases, metadata)

    def get_by_id(self, role_id: str) -> CharacterEntry | None:
        """Get character by role_id.

        Args:
            role_id: The unique role identifier

        Returns:
            CharacterEntry if found, None otherwise
        """
        return self._entries.get(role_id)

    def get_by_name(self, name: str) -> list[CharacterEntry]:
        """Get all characters with given name (may be multiple).

        Args:
            name: Character name to search for

        Returns:
            List of CharacterEntry objects with matching name
        """
        role_ids = self._name_index.get(name, [])
        entries = []
        for role_id in role_ids:
            entry = self._entries.get(role_id)
            if entry:
                entries.append(entry)
        return entries

    def get_all(self) -> list[CharacterEntry]:
        """Get all registered characters.

        Returns:
            List of all CharacterEntry objects
        """
        return list(self._entries.values())

    def update(
        self,
        role_id: str,
        role: str | None = None,
        chapter: int | None = None,
        aliases: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Update an existing character entry.

        Args:
            role_id: The unique role identifier
            role: Optional new role
            chapter: Optional new first appearance chapter
            aliases: Optional new aliases list
            metadata: Optional metadata to merge

        Returns:
            True if updated, False if not found
        """
        entry = self._entries.get(role_id)
        if entry is None:
            return False

        if role is not None:
            entry.role = role
        if chapter is not None:
            entry.first_appearance = chapter
        if aliases is not None:
            entry.aliases = aliases
        if metadata is not None:
            entry.metadata.update(metadata)

        return True

    def delete(self, role_id: str) -> bool:
        """Delete a character entry.

        Args:
            role_id: The unique role identifier

        Returns:
            True if deleted, False if not found
        """
        entry = self._entries.get(role_id)
        if entry is None:
            return False

        # Remove from entries
        del self._entries[role_id]

        # Remove from name index
        if entry.name in self._name_index:
            try:
                self._name_index[entry.name].remove(role_id)
                if not self._name_index[entry.name]:
                    del self._name_index[entry.name]
            except ValueError:
                pass

        logger.debug(f"Deleted character entry: {role_id}")
        return True

    def get_by_role(self, role: str) -> list[CharacterEntry]:
        """Get all characters with a specific role.

        Args:
            role: Role to filter by (e.g., "protagonist", "antagonist")

        Returns:
            List of CharacterEntry objects with matching role
        """
        return [e for e in self._entries.values() if e.role == role]

    def get_statistics(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with statistics
        """
        role_counts: dict[str, int] = {}
        for entry in self._entries.values():
            role_key = entry.role or "unassigned"
            role_counts[role_key] = role_counts.get(role_key, 0) + 1

        return {
            "total_characters": len(self._entries),
            "unique_names": len(self._name_index),
            "duplicate_names": sum(1 for ids in self._name_index.values() if len(ids) > 1),
            "by_role": role_counts,
        }

    def save(self, path: Path) -> None:
        """Save registry to JSON file.

        Args:
            path: Path to save the registry file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "entries": [e.to_dict() for e in self._entries.values()],
            "counter": self._counter,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved character registry to {path}")

    def load(self, path: Path) -> None:
        """Load registry from JSON file.

        Args:
            path: Path to load the registry file from
        """
        if not path.exists():
            logger.warning(f"Registry file not found: {path}")
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Clear existing data
        self._entries.clear()
        self._name_index.clear()
        self._counter.clear()

        # Load counter first (needed for generating new IDs)
        self._counter = data.get("counter", {})

        # Load entries
        for entry_data in data.get("entries", []):
            entry = CharacterEntry.from_dict(entry_data)
            self._entries[entry.role_id] = entry

            # Rebuild name index
            if entry.name not in self._name_index:
                self._name_index[entry.name] = []
            self._name_index[entry.name].append(entry.role_id)

        logger.info(f"Loaded {len(self._entries)} character entries from {path}")

    def _generate_role_id(self, name: str) -> str:
        """Generate unique role_id for name.

        Generates IDs like "char_林晓_001", "char_林晓_002", etc.
        Handles Unicode names correctly.

        Args:
            name: Character name

        Returns:
            Unique role_id
        """
        safe_name = self._sanitize_name(name)
        sequence = self._counter.get(safe_name, 0) + 1
        self._counter[safe_name] = sequence
        return f"char_{safe_name}_{sequence:03d}"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use in ID.

        Keeps alphanumeric characters and CJK characters.
        Removes special characters that could cause issues.

        Args:
            name: Original character name

        Returns:
            Sanitized name safe for use in IDs
        """
        # Keep alphanumeric and CJK characters (U+4E00 to U+9FFF)
        safe_chars = []
        for c in name:
            if c.isalnum() or "\u4e00" <= c <= "\u9fff":
                safe_chars.append(c)

        safe_name = "".join(safe_chars)

        # Fallback if name becomes empty
        if not safe_name:
            safe_name = "unknown"

        return safe_name

    def __len__(self) -> int:
        """Return number of registered characters."""
        return len(self._entries)

    def __contains__(self, role_id: str) -> bool:
        """Check if role_id exists in registry."""
        return role_id in self._entries


__all__ = [
    "CharacterEntry",
    "CharacterRegistry",
]
