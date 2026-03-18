"""Tests for role_id field in CharacterState."""

from src.novel_agent.novel.continuity import (
    CharacterState,
    ContinuityManager,
    StoryState,
)


class TestCharacterStateRoleId:
    """Test role_id field in CharacterState."""

    def test_character_state_has_role_id_field_with_default_none(self) -> None:
        """Test that CharacterState has role_id field defaulting to None."""
        state = CharacterState(
            name="林晓",
            status="alive",
            location="北京",
            physical_form="human",
        )
        assert state.role_id is None

    def test_character_state_with_role_id(self) -> None:
        """Test that CharacterState can have role_id set."""
        state = CharacterState(
            name="林晓",
            status="alive",
            location="北京",
            physical_form="human",
            role_id="char_林晓_001",
        )
        assert state.role_id == "char_林晓_001"

    def test_character_state_role_id_optional(self) -> None:
        """Test that role_id is truly optional."""
        state_without = CharacterState(
            name="测试角色",
            status="alive",
            location="测试地点",
            physical_form="human",
        )
        state_with = CharacterState(
            name="测试角色",
            status="alive",
            location="测试地点",
            physical_form="human",
            role_id="char_test_001",
        )
        assert state_without.role_id is None
        assert state_with.role_id == "char_test_001"


class TestSerializationWithRoleId:
    """Test serialization/deserialization with role_id."""

    def test_serialization_includes_role_id(self) -> None:
        """Test that save() includes role_id in output."""
        manager = ContinuityManager()
        state = StoryState(
            chapter=1,
            location="北京",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="北京",
                    physical_form="human",
                    role_id="char_林晓_001",
                )
            },
        )

        saved = manager.save(state)
        assert saved["character_states"]["林晓"]["role_id"] == "char_林晓_001"

    def test_serialization_includes_none_role_id(self) -> None:
        """Test that save() includes role_id even when None."""
        manager = ContinuityManager()
        state = StoryState(
            chapter=1,
            location="北京",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="北京",
                    physical_form="human",
                )
            },
        )

        saved = manager.save(state)
        assert saved["character_states"]["林晓"]["role_id"] is None

    def test_deserialization_with_role_id(self) -> None:
        """Test that load() correctly deserializes role_id."""
        manager = ContinuityManager()
        state_dict = {
            "chapter": 1,
            "location": "北京",
            "character_states": {
                "林晓": {
                    "name": "林晓",
                    "status": "alive",
                    "location": "北京",
                    "physical_form": "human",
                    "relationships": {},
                    "role_id": "char_林晓_001",
                }
            },
            "plot_threads": [],
            "key_events": [],
        }

        state = manager.load(state_dict)
        assert state.character_states["林晓"].role_id == "char_林晓_001"


class TestBackwardCompatibility:
    """Test backward compatibility with old format without role_id."""

    def test_deserialization_backward_compatible(self) -> None:
        """Old format without role_id should still work."""
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
                }
            },
            "plot_threads": [],
            "key_events": [],
        }

        state = manager.load(old_format)
        assert state.character_states["林晓"].name == "林晓"
        assert state.character_states["林晓"].role_id is None

    def test_mixed_format_deserialization(self) -> None:
        """Test loading with some characters having role_id, others not."""
        manager = ContinuityManager()
        mixed_format = {
            "chapter": 1,
            "location": "北京",
            "character_states": {
                "林晓": {
                    "name": "林晓",
                    "status": "alive",
                    "location": "北京",
                    "physical_form": "human",
                    "relationships": {},
                    "role_id": "char_林晓_001",
                },
                "王刚": {
                    "name": "王刚",
                    "status": "alive",
                    "location": "上海",
                    "physical_form": "human",
                    "relationships": {},
                },
            },
            "plot_threads": [],
            "key_events": [],
        }

        state = manager.load(mixed_format)
        assert state.character_states["林晓"].role_id == "char_林晓_001"
        assert state.character_states["王刚"].role_id is None


class TestNameRemainsDictionaryKey:
    """Test that name remains as dictionary key (critical for backward compat)."""

    def test_name_remains_dictionary_key(self) -> None:
        """Critical: name must remain as dictionary key, not role_id."""
        state = StoryState(
            chapter=1,
            location="北京",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="北京",
                    physical_form="human",
                    role_id="char_林晓_001",
                )
            },
        )

        assert "林晓" in state.character_states
        assert "char_林晓_001" not in state.character_states

    def test_get_character_state_by_name(self) -> None:
        """Test that get_character_state works by name."""
        state = StoryState(
            chapter=1,
            location="北京",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="北京",
                    physical_form="human",
                    role_id="char_林晓_001",
                )
            },
        )

        char_state = state.get_character_state("林晓")
        assert char_state is not None
        assert char_state.role_id == "char_林晓_001"

    def test_multiple_characters_same_name_different_role_id(self) -> None:
        """Test that multiple characters with same name can have different role_ids."""
        state = StoryState(
            chapter=1,
            location="北京",
            character_states={
                "林晓(主角)": CharacterState(
                    name="林晓",
                    status="alive",
                    location="北京",
                    physical_form="human",
                    role_id="char_林晓_001",
                ),
                "林晓(反派)": CharacterState(
                    name="林晓",
                    status="alive",
                    location="上海",
                    physical_form="human",
                    role_id="char_林晓_002",
                ),
            },
        )

        assert state.character_states["林晓(主角)"].role_id == "char_林晓_001"
        assert state.character_states["林晓(反派)"].role_id == "char_林晓_002"


class TestRoundTrip:
    """Test save/load round-trip preserves role_id."""

    def test_round_trip_preserves_role_id(self) -> None:
        """Test that save -> load preserves role_id."""
        manager = ContinuityManager()
        original_state = StoryState(
            chapter=5,
            location="杭州",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="杭州",
                    physical_form="human",
                    role_id="char_林晓_001",
                )
            },
        )

        saved = manager.save(original_state)
        loaded_state = manager.load(saved)

        assert loaded_state.character_states["林晓"].role_id == "char_林晓_001"

    def test_round_trip_with_none_role_id(self) -> None:
        """Test that save -> load preserves None role_id."""
        manager = ContinuityManager()
        original_state = StoryState(
            chapter=5,
            location="杭州",
            character_states={
                "林晓": CharacterState(
                    name="林晓",
                    status="alive",
                    location="杭州",
                    physical_form="human",
                )
            },
        )

        saved = manager.save(original_state)
        loaded_state = manager.load(saved)

        assert loaded_state.character_states["林晓"].role_id is None
