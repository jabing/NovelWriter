"""Tests for ContinuityValidator class."""

import pytest

from src.novel_agent.novel.continuity import CharacterState, PlotThread, StoryState
from src.novel_agent.novel.validators import ContinuityValidator, ValidationError, ValidationResult


class TestValidationError:
    """Test ValidationError dataclass."""

    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        error = ValidationError(
            severity="error", message="Test error message", chapter=5, details="Additional details"
        )

        assert error.severity == "error"
        assert error.message == "Test error message"
        assert error.chapter == 5
        assert error.details == "Additional details"

    def test_validation_error_defaults(self):
        """Test ValidationError with default details."""
        error = ValidationError(severity="warning", message="Test warning", chapter=3)

        assert error.details == ""


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test a valid result."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_validation_result_with_errors(self):
        """Test result with errors."""
        error = ValidationError(severity="error", message="Test error", chapter=1)
        result = ValidationResult(is_valid=False, errors=[error])

        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validation_result_with_warnings(self):
        """Test result with warnings."""
        warning = ValidationError(severity="warning", message="Test warning", chapter=1)
        result = ValidationResult(is_valid=True, warnings=[warning])

        assert result.is_valid is True
        assert len(result.warnings) == 1


class TestContinuityValidatorInit:
    """Test ContinuityValidator initialization."""

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = ContinuityValidator()

        assert isinstance(validator._death_keywords, list)
        assert "died" in validator._death_keywords
        assert "dead" in validator._death_keywords

        assert isinstance(validator._fusion_keywords, list)
        assert "fused" in validator._fusion_keywords

        assert isinstance(validator._location_transitions, list)
        assert "arrived at" in validator._location_transitions


class TestValidateChapter:
    """Test validate_chapter method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    @pytest.fixture
    def story_state(self):
        """Create a basic story state."""
        return StoryState(
            chapter=1,
            location="Test Location",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael", status="alive", location="Test Location", physical_form="human"
                )
            },
            plot_threads=[PlotThread(name="Main Quest", status="active")],
        )

    def test_validate_valid_chapter(self, validator, story_state):
        """Test validating a valid chapter."""
        content = "Kael walked through the forest. He was alive and well."

        result = validator.validate_chapter(
            chapter_content=content, chapter_number=2, story_state=story_state
        )

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    def test_validate_with_dead_character_error(self, validator):
        """Test detecting dead character appearing alive."""
        story_state = StoryState(
            chapter=3,
            location="Battlefield",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael", status="alive", location="Battlefield", physical_form="human"
                ),
                "Sylas": CharacterState(
                    name="Sylas", status="dead", location="Battlefield", physical_form="spirit"
                ),
            },
        )

        # Sylas appears alive without death context
        content = "Sylas walked into the room and spoke to Kael."

        result = validator.validate_chapter(
            chapter_content=content, chapter_number=4, story_state=story_state
        )

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Sylas" in err.message for err in result.errors)
        assert any("dead" in err.message.lower() for err in result.errors)

    def test_validate_dead_character_with_context(self, validator):
        """Test dead character with proper context is allowed."""
        story_state = StoryState(
            chapter=3,
            location="Battlefield",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael", status="alive", location="Battlefield", physical_form="human"
                ),
                "Sylas": CharacterState(
                    name="Sylas", status="dead", location="Battlefield", physical_form="spirit"
                ),
            },
        )

        # Sylas is mentioned in context of his death
        content = "Kael remembered how Sylas died bravely in battle."

        result = validator.validate_chapter(
            chapter_content=content, chapter_number=4, story_state=story_state
        )

        # Should be valid because death context is present
        assert result.is_valid is True


class TestCheckCharacterAppearances:
    """Test _check_character_appearances method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    def test_dead_character_appears_alive(self, validator):
        """Test detecting dead character appearing alive."""
        story_state = StoryState(
            chapter=1,
            location="Test",
            active_characters=[],
            character_states={
                "Villain": CharacterState(
                    name="Villain", status="dead", location="Test", physical_form="spirit"
                )
            },
        )

        content = "The Villain laughed and attacked the hero."
        errors = validator._check_character_appearances(content, story_state, 2)

        assert len(errors) > 0
        assert "Villain" in errors[0].message

    def test_alive_character_no_error(self, validator):
        """Test alive character doesn't trigger error."""
        story_state = StoryState(
            chapter=1,
            location="Test",
            active_characters=["Hero"],
            character_states={
                "Hero": CharacterState(
                    name="Hero", status="alive", location="Test", physical_form="human"
                )
            },
        )

        content = "The Hero walked into the room."
        errors = validator._check_character_appearances(content, story_state, 2)

        assert len(errors) == 0


class TestCheckCharacterStates:
    """Test _check_character_states method."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    def test_fused_character_with_physical_form(self, validator):
        """Test detecting fused character with physical actions."""
        story_state = StoryState(
            chapter=5,
            location="Inner Sanctum",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael", status="alive", location="Inner Sanctum", physical_form="human"
                ),
                "Spirit": CharacterState(
                    name="Spirit", status="fused", location="Kael", physical_form="spirit"
                ),
            },
        )

        # Fused character has physical action
        content = "The Spirit stood up and walked towards the door."
        errors = validator._check_character_states(content, story_state, 6)

        assert len(errors) > 0
        assert "Spirit" in errors[0].message
        assert "fused" in errors[0].message.lower()

    def test_fused_character_no_physical_action(self, validator):
        """Test fused character without physical action is OK."""
        story_state = StoryState(
            chapter=5,
            location="Inner Sanctum",
            active_characters=["Kael"],
            character_states={
                "Spirit": CharacterState(
                    name="Spirit", status="fused", location="Kael", physical_form="spirit"
                )
            },
        )

        # Fused character is mentioned but no physical action
        content = "Kael felt the Spirit's presence within him."
        errors = validator._check_character_states(content, story_state, 6)

        assert len(errors) == 0


class TestHelperMethods:
    """Test helper methods."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    def test_count_character_mentions(self, validator):
        """Test counting character mentions."""
        content = "Kael walked in. Kael sat down. Kael spoke."
        count = validator._count_character_mentions(content.lower(), "kael")

        assert count == 3

    def test_count_character_mentions_case_insensitive(self, validator):
        """Test counting is case insensitive."""
        content = "KAEL walked in. kael sat down. Kael spoke."
        count = validator._count_character_mentions(content.lower(), "kael")

        assert count == 3

    def test_extract_location_from_text(self, validator):
        """Test extracting location from text."""
        text = "They arrived at Hogwarts in the evening."
        location = validator._extract_location_from_text(text, "arrived at")

        assert location == "Hogwarts"

    def test_extract_location_no_match(self, validator):
        """Test extracting location when no match."""
        text = "They walked around for hours."
        location = validator._extract_location_from_text(text, "arrived at")

        assert location is None


class TestRelationshipValidation:
    """Test relationship consistency validation (new feature)."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    @pytest.fixture
    def story_state(self):
        """Create a basic story state."""
        return StoryState(
            chapter=1,
            location="Castle",
            active_characters=["张伟", "林轩"],
            character_states={
                "张伟": CharacterState(
                    name="张伟", status="alive", location="Castle", physical_form="human"
                ),
                "林轩": CharacterState(
                    name="林轩", status="alive", location="Castle", physical_form="human"
                ),
            },
        )

    def test_enemy_friendly_interaction_warning(self, validator, story_state):
        """Test that enemies showing friendly interaction triggers warning."""
        content = "张伟拥抱林轩，两人相视而笑。"
        relationships = [
            {
                "character1_name": "张伟",
                "character2_name": "林轩",
                "relationship_type": "enemy",
            }
        ]

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            relationships=relationships,
        )

        # Should have at least one warning or error about friendly interaction
        assert len(result.warnings) > 0 or len(result.errors) > 0
        # Check message mentions enemy relationship
        all_messages = [e.message for e in result.warnings] + [e.message for e in result.errors]
        assert any("敌对" in msg or "enemy" in msg.lower() for msg in all_messages)

    def test_enemy_kissing_triggers_warning(self, validator, story_state):
        """Test that enemies kissing triggers warning."""
        content = "张伟亲吻了林轩的脸颊。"
        relationships = [
            {
                "character1_name": "张伟",
                "character2_name": "林轩",
                "relationship_type": "enemy",
            }
        ]

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            relationships=relationships,
        )

        # Should have warnings or errors about friendly interaction
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_enemy_handshake_triggers_warning(self, validator, story_state):
        """Test that enemies shaking hands triggers warning."""
        content = "张伟和林轩握手言和。"
        relationships = [
            {
                "character1_name": "张伟",
                "character2_name": "林轩",
                "relationship_type": "enemy",
            }
        ]

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            relationships=relationships,
        )

        # Should have warnings or errors about friendly interaction
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_friend_friendly_interaction_no_warning(self, validator, story_state):
        """Test that friends with friendly interaction does not trigger warning."""
        content = "张伟拥抱林轩，两人相视而笑。"
        relationships = [
            {
                "character1_name": "张伟",
                "character2_name": "林轩",
                "relationship_type": "friend",
            }
        ]

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            relationships=relationships,
        )

        # Should not have warnings about friendly interaction for friends
        friend_warnings = [
            e for e in result.warnings if "敌对" in e.message or "enemy" in e.message.lower()
        ]
        assert len(friend_warnings) == 0

    def test_no_relationship_data_no_error(self, validator, story_state):
        """Test that missing relationship data doesn't cause errors."""
        content = "张伟拥抱林轩，两人相视而笑。"

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            relationships=None,
        )

        # Should still be valid without relationship checking
        assert result.is_valid is True

    def test_check_relationship_consistency_method(self, validator):
        """Test _check_relationship_consistency method directly."""
        relationships = [
            {"character1_name": "张伟", "character2_name": "林轩", "relationship_type": "enemy"}
        ]
        content = "张伟拥抱林轩，两人相视而笑。"

        errors = validator._check_relationship_consistency(content, relationships, 1)

        assert len(errors) > 0
        assert errors[0].severity == "warning"


class TestPlotValidation:
    """Test plot consistency validation (new feature)."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    @pytest.fixture
    def story_state(self):
        """Create a basic story state."""
        return StoryState(
            chapter=1,
            location="Castle",
            active_characters=["主角"],
            character_states={
                "主角": CharacterState(
                    name="主角", status="alive", location="Castle", physical_form="human"
                ),
            },
        )

    def test_missing_foreshadowing_warning(self, validator, story_state):
        """Test that missing foreshadowing triggers warning."""
        content = "这是一章普通的内容，没有提到伏笔。"
        outline_data = {"required_foreshadowing": ["神秘戒指", "古老预言"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=5,
            story_state=story_state,
            outline_data=outline_data,
        )

        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_foreshadowing_present_no_warning(self, validator, story_state):
        """Test that present foreshadowing doesn't trigger warning."""
        content = "主角发现了神秘戒指，想起了古老预言。"
        outline_data = {"required_foreshadowing": ["神秘戒指", "古老预言"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=5,
            story_state=story_state,
            outline_data=outline_data,
        )

        # Should not have foreshadowing warnings
        foreshadow_warnings = [
            e for e in result.warnings if "伏笔" in e.message or "foreshadow" in e.message.lower()
        ]
        assert len(foreshadow_warnings) == 0

    def test_partial_foreshadowing_warning(self, validator, story_state):
        """Test that missing some foreshadowing triggers warning."""
        content = "主角发现了神秘戒指。"
        outline_data = {"required_foreshadowing": ["神秘戒指", "古老预言", "宝藏地图"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=5,
            story_state=story_state,
            outline_data=outline_data,
        )

        # Should have warnings or errors for missing foreshadowing
        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_no_outline_data_no_error(self, validator, story_state):
        """Test that missing outline data doesn't cause errors."""
        content = "这是一章普通的内容。"

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=5,
            story_state=story_state,
            outline_data=None,
        )

        assert result.is_valid is True

    def test_check_plot_consistency_method(self, validator):
        """Test _check_plot_consistency method directly."""
        outline_data = {"required_foreshadowing": ["神秘戒指", "古老预言"]}
        content = "这是一章没有伏笔的内容。"

        errors = validator._check_plot_consistency(content, outline_data, 5)

        assert len(errors) > 0
        assert errors[0].severity == "warning"


class TestWorldSettingsValidation:
    """Test world settings consistency validation (new feature)."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ContinuityValidator()

    @pytest.fixture
    def story_state(self):
        """Create a basic story state."""
        return StoryState(
            chapter=1,
            location="Castle",
            active_characters=["法师"],
            character_states={
                "法师": CharacterState(
                    name="法师", status="alive", location="Castle", physical_form="human"
                ),
            },
        )

    def test_forbidden_element_error(self, validator, story_state):
        """Test that forbidden elements trigger error."""
        content = "角色使用了魔法火球攻击敌人。"
        world_settings = {"forbidden_elements": ["魔法火球"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            world_settings=world_settings,
        )

        assert len(result.errors) > 0

    def test_forbidden_element_not_present_no_error(self, validator, story_state):
        """Test that allowed elements don't trigger error."""
        content = "角色使用了冰霜法术攻击敌人。"
        world_settings = {"forbidden_elements": ["魔法火球"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            world_settings=world_settings,
        )

        # Should not have forbidden element errors
        forbidden_errors = [
            e for e in result.errors if "禁止" in e.message or "forbidden" in e.message.lower()
        ]
        assert len(forbidden_errors) == 0

    def test_multiple_forbidden_elements(self, validator, story_state):
        """Test detection of multiple forbidden elements."""
        content = "角色使用了魔法火球和传送术。"
        world_settings = {"forbidden_elements": ["魔法火球", "传送术"]}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            world_settings=world_settings,
        )

        # Should have errors for forbidden elements
        assert len(result.errors) >= 2

    def test_no_world_settings_no_error(self, validator, story_state):
        """Test that missing world settings doesn't cause errors."""
        content = "角色使用了魔法火球攻击敌人。"

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            world_settings=None,
        )

        assert result.is_valid is True

    def test_check_world_settings_consistency_method(self, validator):
        """Test _check_world_settings_consistency method directly."""
        world_settings = {"forbidden_elements": ["魔法火球"]}
        content = "角色使用了魔法火球攻击敌人。"

        errors = validator._check_world_settings_consistency(content, world_settings, 1)

        assert len(errors) > 0
        assert errors[0].severity == "error"

    def test_empty_forbidden_elements_no_error(self, validator, story_state):
        """Test that empty forbidden elements list doesn't cause errors."""
        content = "角色使用了魔法火球攻击敌人。"
        world_settings = {"forbidden_elements": []}

        result = validator.validate_chapter(
            chapter_content=content,
            chapter_number=1,
            story_state=story_state,
            world_settings=world_settings,
        )

        assert result.is_valid is True
