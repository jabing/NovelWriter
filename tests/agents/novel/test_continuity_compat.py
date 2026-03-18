"""Tests for backward compatibility with old project data.

This module tests:
- Loading old project data without role_id field
- Config switching (OFF → WARNING → STRICT)
- KG version compatibility
"""

import pytest

from src.novel_agent.novel.continuity import ContinuityManager, CharacterState, StoryState
from src.novel_agent.novel.continuity_config import ContinuityConfig, ContinuityStrictness
from src.novel_agent.novel.kg_transaction import KGTransactionManager


class TestOldDataCompatibility:
    """Tests for loading old project data without role_id."""

    def test_load_old_story_state(self) -> None:
        """Old format without role_id should load correctly."""
        manager = ContinuityManager()
        old_format = {
            "chapter": 1,
            "location": "北京",
            "character_states": {
                "林晓": {
                    "name": "林晓",
                    "status": "alive",
                    "location": "北京",
                    "physical_form": "human",
                    "relationships": {},
                    # NO role_id
                }
            },
            "plot_threads": [],
            "key_events": [],
        }

        state = manager.load(old_format)

        assert state.chapter == 1
        assert "林晓" in state.character_states
        assert state.character_states["林晓"].role_id is None

    def test_load_with_missing_optional_fields(self) -> None:
        """Should handle missing optional fields gracefully."""
        manager = ContinuityManager()
        minimal_format = {"chapter": 1, "location": "北京"}

        state = manager.load(minimal_format)

        assert state.chapter == 1
        assert len(state.character_states) == 0

    def test_load_old_character_without_role_id(self) -> None:
        """Test loading individual character state without role_id."""
        manager = ContinuityManager()
        old_char_dict = {
            "name": "Test Character",
            "status": "alive",
            "location": "Old Town",
            "physical_form": "human",
            "relationships": {},
            # Intentionally missing role_id
        }

        # This should work without role_id
        state = manager.load(
            {
                "chapter": 1,
                "location": "Old Town",
                "character_states": {"Test Character": old_char_dict},
            }
        )

        assert "Test Character" in state.character_states
        assert state.character_states["Test Character"].role_id is None

    def test_load_character_with_role_id(self) -> None:
        """Test loading character state with role_id (new format)."""
        manager = ContinuityManager()
        new_char_dict = {
            "name": "Test Character",
            "status": "alive",
            "location": "New Town",
            "physical_form": "human",
            "relationships": {},
            "role_id": "char_001",  # New field
        }

        state = manager.load(
            {
                "chapter": 1,
                "location": "New Town",
                "character_states": {"Test Character": new_char_dict},
            }
        )

        assert state.character_states["Test Character"].role_id == "char_001"

    def test_load_empty_character_states(self) -> None:
        """Test loading with empty character_states dict."""
        manager = ContinuityManager()
        format_with_empty_chars = {
            "chapter": 1,
            "location": "Nowhere",
            "character_states": {},
            "plot_threads": [],
            "key_events": [],
        }

        state = manager.load(format_with_empty_chars)

        assert state.chapter == 1
        assert len(state.character_states) == 0

    def test_load_with_none_role_id_explicit(self) -> None:
        """Test loading with explicit None role_id."""
        manager = ContinuityManager()
        char_with_none_role = {
            "name": "Anonymous",
            "status": "alive",
            "location": "Unknown",
            "physical_form": "spirit",
            "relationships": {},
            "role_id": None,  # Explicit None
        }

        state = manager.load(
            {
                "chapter": 1,
                "location": "Unknown",
                "character_states": {"Anonymous": char_with_none_role},
            }
        )

        assert state.character_states["Anonymous"].role_id is None


class TestStrictnessModes:
    """Tests for different strictness configurations."""

    def test_off_mode_allows_skip(self) -> None:
        """OFF mode should allow skipping checks."""
        config = ContinuityConfig(strictness=ContinuityStrictness.OFF)
        assert config.strictness == ContinuityStrictness.OFF

    def test_warning_mode_logs(self) -> None:
        """WARNING mode should log but continue."""
        config = ContinuityConfig(strictness=ContinuityStrictness.WARNING)
        assert config.strictness == ContinuityStrictness.WARNING

    def test_strict_mode_is_default(self) -> None:
        """STRICT should be the default mode."""
        config = ContinuityConfig()
        assert config.strictness == ContinuityStrictness.STRICT

    def test_config_from_dict(self) -> None:
        """Should create config from dictionary."""
        config = ContinuityConfig(**{"strictness": "warning"})
        assert config.strictness == ContinuityStrictness.WARNING

    def test_all_strictness_values(self) -> None:
        """Test all strictness values can be set."""
        for mode in ["off", "warning", "strict"]:
            config = ContinuityConfig(strictness=mode)
            assert config.strictness == mode

    def test_config_preserves_other_fields(self) -> None:
        """Config should preserve all fields when created from dict."""
        data = {
            "strictness": "off",
            "max_retries": 5,
            "min_chapter_words": 1000,
            "enable_character_id": True,
        }
        config = ContinuityConfig(**data)

        assert config.strictness == ContinuityStrictness.OFF
        assert config.max_retries == 5
        assert config.min_chapter_words == 1000
        assert config.enable_character_id is True


class TestKGVersionCompatibility:
    """Tests for KG version compatibility."""

    def test_kg_version_starts_at_zero(self) -> None:
        """New KG should start at version 0."""
        manager = KGTransactionManager()
        assert manager.get_version() == 0

    def test_kg_load_old_format(self) -> None:
        """Should handle old KG format without version."""
        manager = KGTransactionManager({"characters": {}, "locations": {}})
        assert manager.get_state()["characters"] == {}

    def test_kg_version_increments_on_commit(self) -> None:
        """Version should increment after successful commit."""
        manager = KGTransactionManager({"test": "value"})
        assert manager.get_version() == 0

        manager.begin_transaction()
        manager._transaction.changes = {"test": "updated"}
        manager.commit()

        assert manager.get_version() == 1

    def test_kg_rollback_does_not_increment_version(self) -> None:
        """Rollback should not increment version."""
        manager = KGTransactionManager({"test": "original"})
        manager.begin_transaction()
        manager._transaction.changes = {"test": "changed"}
        manager.rollback()

        assert manager.get_version() == 0
        assert manager.get_state()["test"] == "original"

    def test_kg_state_isolation(self) -> None:
        """KG state should be properly isolated between versions."""
        manager = KGTransactionManager({"characters": ["Alice"]})

        # First version
        manager.begin_transaction()
        manager._transaction.changes = {"characters": ["Alice", "Bob"]}
        manager.commit()

        # Second version
        manager.begin_transaction()
        manager._transaction.changes = {"locations": ["Gotham"]}
        manager.commit()

        state = manager.get_state()
        assert "characters" in state
        assert "locations" in state
        assert len(state["characters"]) == 2

    def test_kg_initial_state_empty(self) -> None:
        """KGTransactionManager with no initial state should have empty dict."""
        manager = KGTransactionManager()
        assert manager.get_state() == {}

    def test_kg_get_state_returns_copy(self) -> None:
        """get_state() should return a copy, not the original."""
        manager = KGTransactionManager({"test": "value"})
        state1 = manager.get_state()
        state1["test"] = "modified"

        state2 = manager.get_state()
        assert state2["test"] == "value"
