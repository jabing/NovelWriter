"""Tests for ContinuityValidator class."""

import pytest

from src.novel.continuity import CharacterState, PlotThread, StoryState
from src.novel.validators import ContinuityValidator, ValidationError, ValidationResult


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
