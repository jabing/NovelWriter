"""Unit tests for CharacterRegistry.

Tests cover:
- Character registration with unique IDs
- Same name different IDs (duplicate name handling)
- get_by_id and get_by_name lookups
- get_or_create behavior
- Save and load persistence
- Unicode name handling
"""

import logging
from pathlib import Path

import pytest

from src.novel_agent.novel.character_registry import CharacterEntry, CharacterRegistry

logger = logging.getLogger(__name__)


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def registry() -> CharacterRegistry:
    """Create a fresh CharacterRegistry for testing."""
    return CharacterRegistry()


@pytest.fixture
def temp_registry_path(tmp_path: Path) -> Path:
    """Create a temporary path for registry files."""
    path = tmp_path / "characters" / "registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# ========================================
# CharacterEntry Tests
# ========================================


class TestCharacterEntry:
    """Tests for CharacterEntry dataclass."""

    def test_creation(self) -> None:
        """Test creating a CharacterEntry."""
        entry = CharacterEntry(
            role_id="char_林晓_001",
            name="林晓",
            role="protagonist",
            first_appearance=1,
        )

        assert entry.role_id == "char_林晓_001"
        assert entry.name == "林晓"
        assert entry.role == "protagonist"
        assert entry.first_appearance == 1
        assert entry.aliases == []
        assert entry.metadata == {}

    def test_creation_with_all_fields(self) -> None:
        """Test creating entry with all fields."""
        entry = CharacterEntry(
            role_id="char_Alice_001",
            name="Alice",
            role="protagonist",
            first_appearance=1,
            aliases=["Ally", "Alicia"],
            metadata={"hair": "blonde", "age": 25},
        )

        assert entry.aliases == ["Ally", "Alicia"]
        assert entry.metadata == {"hair": "blonde", "age": 25}

    def test_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = CharacterEntry(
            role_id="char_张三_001",
            name="张三",
            role="supporting",
            first_appearance=5,
            aliases=["老张"],
            metadata={"profession": "teacher"},
        )

        data = entry.to_dict()

        assert data["role_id"] == "char_张三_001"
        assert data["name"] == "张三"
        assert data["role"] == "supporting"
        assert data["first_appearance"] == 5
        assert data["aliases"] == ["老张"]
        assert data["metadata"] == {"profession": "teacher"}

    def test_from_dict(self) -> None:
        """Test creating entry from dictionary."""
        data = {
            "role_id": "char_Bob_001",
            "name": "Bob",
            "role": "antagonist",
            "first_appearance": 10,
            "aliases": ["Robert"],
            "metadata": {"origin": "unknown"},
        }

        entry = CharacterEntry.from_dict(data)

        assert entry.role_id == "char_Bob_001"
        assert entry.name == "Bob"
        assert entry.role == "antagonist"
        assert entry.first_appearance == 10
        assert entry.aliases == ["Robert"]
        assert entry.metadata == {"origin": "unknown"}

    def test_from_dict_defaults(self) -> None:
        """Test creating entry with default values."""
        data = {
            "role_id": "char_Test_001",
            "name": "Test",
        }

        entry = CharacterEntry.from_dict(data)

        assert entry.role is None
        assert entry.first_appearance == 0
        assert entry.aliases == []
        assert entry.metadata == {}


# ========================================
# CharacterRegistry Registration Tests
# ========================================


class TestCharacterRegistryRegister:
    """Tests for character registration."""

    def test_register_returns_unique_id(self, registry: CharacterRegistry) -> None:
        """Test that register returns a unique ID."""
        role_id = registry.register("林晓")

        assert role_id == "char_林晓_001"
        assert role_id in registry

    def test_register_with_role_and_chapter(self, registry: CharacterRegistry) -> None:
        """Test registering with role and chapter."""
        role_id = registry.register("林晓", role="protagonist", chapter=1)

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.name == "林晓"
        assert entry.role == "protagonist"
        assert entry.first_appearance == 1

    def test_same_name_different_ids(self, registry: CharacterRegistry) -> None:
        """Test that same name gets different IDs."""
        id1 = registry.register("林晓")
        id2 = registry.register("林晓")

        assert id1 != id2
        assert id1 == "char_林晓_001"
        assert id2 == "char_林晓_002"

    def test_register_multiple_characters(self, registry: CharacterRegistry) -> None:
        """Test registering multiple different characters."""
        id1 = registry.register("Alice", role="protagonist")
        id2 = registry.register("Bob", role="antagonist")
        id3 = registry.register("Charlie", role="supporting")

        assert id1 == "char_Alice_001"
        assert id2 == "char_Bob_001"
        assert id3 == "char_Charlie_001"

        assert len(registry) == 3

    def test_register_with_aliases(self, registry: CharacterRegistry) -> None:
        """Test registering with aliases."""
        role_id = registry.register("张三", aliases=["老张", "张老师"])

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.aliases == ["老张", "张老师"]

    def test_register_with_metadata(self, registry: CharacterRegistry) -> None:
        """Test registering with metadata."""
        role_id = registry.register("李四", metadata={"age": 30, "profession": "医生"})

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.metadata == {"age": 30, "profession": "医生"}


# ========================================
# CharacterRegistry Lookup Tests
# ========================================


class TestCharacterRegistryLookup:
    """Tests for character lookup methods."""

    def test_get_by_id(self, registry: CharacterRegistry) -> None:
        """Test getting character by ID."""
        role_id = registry.register("林晓", role="protagonist", chapter=1)

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.name == "林晓"
        assert entry.role == "protagonist"
        assert entry.first_appearance == 1

    def test_get_by_id_not_found(self, registry: CharacterRegistry) -> None:
        """Test getting non-existent ID returns None."""
        entry = registry.get_by_id("char_nonexistent_001")
        assert entry is None

    def test_get_by_name(self, registry: CharacterRegistry) -> None:
        """Test getting characters by name."""
        registry.register("林晓", role="protagonist")
        registry.register("林晓", role="antagonist")

        entries = registry.get_by_name("林晓")
        assert len(entries) == 2

        roles = {e.role for e in entries}
        assert roles == {"protagonist", "antagonist"}

    def test_get_by_name_not_found(self, registry: CharacterRegistry) -> None:
        """Test getting non-existent name returns empty list."""
        entries = registry.get_by_name("Nonexistent")
        assert entries == []

    def test_get_all(self, registry: CharacterRegistry) -> None:
        """Test getting all characters."""
        registry.register("Alice", role="protagonist")
        registry.register("Bob", role="antagonist")
        registry.register("Charlie", role="supporting")

        all_entries = registry.get_all()
        assert len(all_entries) == 3

        names = {e.name for e in all_entries}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_get_by_role(self, registry: CharacterRegistry) -> None:
        """Test getting characters by role."""
        registry.register("Alice", role="protagonist")
        registry.register("Bob", role="protagonist")
        registry.register("Charlie", role="antagonist")

        protagonists = registry.get_by_role("protagonist")
        assert len(protagonists) == 2

        names = {e.name for e in protagonists}
        assert names == {"Alice", "Bob"}

    def test_get_statistics(self, registry: CharacterRegistry) -> None:
        """Test getting registry statistics."""
        registry.register("Alice", role="protagonist")
        registry.register("Bob", role="protagonist")
        registry.register("Charlie", role="antagonist")
        registry.register("林晓", role="protagonist")
        registry.register("林晓", role="antagonist")

        stats = registry.get_statistics()

        assert stats["total_characters"] == 5
        assert stats["unique_names"] == 4  # Alice, Bob, Charlie, 林晓
        assert stats["duplicate_names"] == 1  # 林晓 appears twice
        assert stats["by_role"]["protagonist"] == 3
        assert stats["by_role"]["antagonist"] == 2


# ========================================
# CharacterRegistry get_or_create Tests
# ========================================


class TestCharacterRegistryGetOrCreate:
    """Tests for get_or_create method."""

    def test_get_or_create_returns_existing(self, registry: CharacterRegistry) -> None:
        """Test that get_or_create returns existing ID when only one exists."""
        id1 = registry.register("林晓", role="protagonist")
        id2 = registry.get_or_create("林晓")

        assert id1 == id2
        assert len(registry) == 1

    def test_get_or_create_creates_new_when_none(self, registry: CharacterRegistry) -> None:
        """Test that get_or_create creates new when none exists."""
        role_id = registry.get_or_create("Alice", role="protagonist")

        assert role_id == "char_Alice_001"
        assert len(registry) == 1

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.role == "protagonist"

    def test_get_or_create_creates_new_when_multiple(self, registry: CharacterRegistry) -> None:
        """Test that get_or_create creates new when multiple exist."""
        id1 = registry.register("林晓", role="protagonist")
        id2 = registry.register("林晓", role="antagonist")

        # Now there are 2 characters named 林晓
        assert len(registry.get_by_name("林晓")) == 2

        # get_or_create should create a new one (ambiguous)
        id3 = registry.get_or_create("林晓")

        assert id3 != id1
        assert id3 != id2
        assert id3 == "char_林晓_003"
        assert len(registry) == 3


# ========================================
# CharacterRegistry Update Tests
# ========================================


class TestCharacterRegistryUpdate:
    """Tests for update and delete methods."""

    def test_update_role(self, registry: CharacterRegistry) -> None:
        """Test updating character role."""
        role_id = registry.register("Alice", role="supporting")

        result = registry.update(role_id, role="protagonist")
        assert result is True

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.role == "protagonist"

    def test_update_chapter(self, registry: CharacterRegistry) -> None:
        """Test updating first appearance chapter."""
        role_id = registry.register("Alice", chapter=5)

        result = registry.update(role_id, chapter=1)
        assert result is True

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.first_appearance == 1

    def test_update_metadata_merge(self, registry: CharacterRegistry) -> None:
        """Test that metadata update merges with existing."""
        role_id = registry.register("Alice", metadata={"age": 25})

        result = registry.update(role_id, metadata={"hair": "blonde"})
        assert result is True

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.metadata == {"age": 25, "hair": "blonde"}

    def test_update_nonexistent(self, registry: CharacterRegistry) -> None:
        """Test updating non-existent entry returns False."""
        result = registry.update("char_nonexistent_001", role="protagonist")
        assert result is False

    def test_delete(self, registry: CharacterRegistry) -> None:
        """Test deleting character entry."""
        role_id = registry.register("Alice")

        result = registry.delete(role_id)
        assert result is True
        assert registry.get_by_id(role_id) is None
        assert len(registry) == 0

    def test_delete_nonexistent(self, registry: CharacterRegistry) -> None:
        """Test deleting non-existent entry returns False."""
        result = registry.delete("char_nonexistent_001")
        assert result is False

    def test_delete_updates_name_index(self, registry: CharacterRegistry) -> None:
        """Test that delete updates the name index."""
        id1 = registry.register("林晓", role="protagonist")
        id2 = registry.register("林晓", role="antagonist")

        # Both exist
        entries = registry.get_by_name("林晓")
        assert len(entries) == 2

        # Delete one
        registry.delete(id1)

        # Only one remains
        entries = registry.get_by_name("林晓")
        assert len(entries) == 1
        assert entries[0].role == "antagonist"


# ========================================
# CharacterRegistry Persistence Tests
# ========================================


class TestCharacterRegistryPersistence:
    """Tests for save and load methods."""

    def test_save_and_load(self, registry: CharacterRegistry, temp_registry_path: Path) -> None:
        """Test saving and loading registry."""
        registry.register("林晓", role="protagonist", chapter=1)
        registry.register("张三", role="supporting", chapter=5)

        # Save
        registry.save(temp_registry_path)
        assert temp_registry_path.exists()

        # Load into new registry
        new_registry = CharacterRegistry()
        new_registry.load(temp_registry_path)

        assert len(new_registry) == 2
        assert new_registry.get_by_name("林晓")[0].role == "protagonist"
        assert new_registry.get_by_name("张三")[0].first_appearance == 5

    def test_save_and_load_with_duplicates(
        self, registry: CharacterRegistry, temp_registry_path: Path
    ) -> None:
        """Test saving and loading registry with duplicate names."""
        registry.register("林晓", role="protagonist")
        registry.register("林晓", role="antagonist")

        # Save
        registry.save(temp_registry_path)

        # Load into new registry
        new_registry = CharacterRegistry()
        new_registry.load(temp_registry_path)

        entries = new_registry.get_by_name("林晓")
        assert len(entries) == 2

        roles = {e.role for e in entries}
        assert roles == {"protagonist", "antagonist"}

    def test_load_nonexistent_file(self, registry: CharacterRegistry, tmp_path: Path) -> None:
        """Test loading from non-existent file."""
        nonexistent_path = tmp_path / "nonexistent.json"

        # Should not raise, just log warning
        registry.load(nonexistent_path)
        assert len(registry) == 0

    def test_save_creates_directory(self, registry: CharacterRegistry, tmp_path: Path) -> None:
        """Test that save creates parent directories."""
        path = tmp_path / "nested" / "dir" / "registry.json"

        registry.register("Alice")
        registry.save(path)

        assert path.exists()
        assert path.parent.exists()

    def test_load_preserves_counter(
        self, registry: CharacterRegistry, temp_registry_path: Path
    ) -> None:
        """Test that loading preserves ID counter."""
        # Register some characters
        registry.register("林晓")
        registry.register("林晓")
        registry.save(temp_registry_path)

        # Load into new registry
        new_registry = CharacterRegistry()
        new_registry.load(temp_registry_path)

        # Next registration should continue the counter
        id3 = new_registry.register("林晓")
        assert id3 == "char_林晓_003"


# ========================================
# Unicode Name Handling Tests
# ========================================


class TestCharacterRegistryUnicode:
    """Tests for Unicode name handling."""

    def test_chinese_names(self, registry: CharacterRegistry) -> None:
        """Test handling of Chinese character names."""
        id1 = registry.register("林晓")
        id2 = registry.register("张三丰")
        id3 = registry.register("李小龙")

        assert "林晓" in id1
        assert "张三丰" in id2
        assert "李小龙" in id3

    def test_japanese_names(self, registry: CharacterRegistry) -> None:
        """Test handling of Japanese character names."""
        id1 = registry.register("田中")
        id2 = registry.register("山田太郎")

        assert "田中" in id1
        assert "山田太郎" in id2

    def test_mixed_names(self, registry: CharacterRegistry) -> None:
        """Test handling of mixed character names."""
        id1 = registry.register("Alice")
        id2 = registry.register("林晓")
        id3 = registry.register("田中Bob")

        assert id1 == "char_Alice_001"
        assert "林晓" in id2
        assert "田中Bob" in id3

    def test_special_characters_in_name(self, registry: CharacterRegistry) -> None:
        """Test handling of special characters in names."""
        # Special characters should be stripped
        id1 = registry.register("Alice@#$%")
        id2 = registry.register("Bob!*&^")

        # Special chars stripped
        assert id1 == "char_Alice_001"
        assert id2 == "char_Bob_001"

    def test_empty_name_after_sanitize(self, registry: CharacterRegistry) -> None:
        """Test handling of name that becomes empty after sanitization."""
        role_id = registry.register("@#$%^&*")

        # Falls back to "unknown"
        assert role_id == "char_unknown_001"


# ========================================
# Additional Edge Cases Tests
# ========================================


class TestCharacterRegistryEdgeCases:
    """Tests for edge cases."""

    def test_contains(self, registry: CharacterRegistry) -> None:
        """Test __contains__ method."""
        role_id = registry.register("Alice")

        assert role_id in registry
        assert "char_nonexistent_001" not in registry

    def test_len(self, registry: CharacterRegistry) -> None:
        """Test __len__ method."""
        assert len(registry) == 0

        registry.register("Alice")
        assert len(registry) == 1

        registry.register("Bob")
        assert len(registry) == 2

    def test_multiple_roles_same_name(self, registry: CharacterRegistry) -> None:
        """Test multiple characters with same name but different roles."""
        id1 = registry.register("林晓", role="protagonist")
        id2 = registry.register("林晓", role="antagonist")
        id3 = registry.register("林晓", role="supporting")

        assert id1 != id2 != id3

        protagonist = registry.get_by_id(id1)
        antagonist = registry.get_by_id(id2)
        supporting = registry.get_by_id(id3)

        assert protagonist is not None and protagonist.role == "protagonist"
        assert antagonist is not None and antagonist.role == "antagonist"
        assert supporting is not None and supporting.role == "supporting"

    def test_none_role(self, registry: CharacterRegistry) -> None:
        """Test registering character with None role."""
        role_id = registry.register("Alice", role=None)

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.role is None

    def test_zero_chapter(self, registry: CharacterRegistry) -> None:
        """Test registering character with chapter 0."""
        role_id = registry.register("Alice", chapter=0)

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.first_appearance == 0

    def test_large_chapter_number(self, registry: CharacterRegistry) -> None:
        """Test registering character with large chapter number."""
        role_id = registry.register("Alice", chapter=9999)

        entry = registry.get_by_id(role_id)
        assert entry is not None
        assert entry.first_appearance == 9999
