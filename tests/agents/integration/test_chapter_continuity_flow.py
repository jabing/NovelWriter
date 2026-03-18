"""Integration tests for chapter generation with continuity management.

Tests end-to-end chapter generation flow with:
- Chapter validation
- Knowledge Graph updates
- Character ID generation and registry
- Story state continuity
"""

import pytest
from pathlib import Path
import tempfile
import json
from src.novel_agent.novel.chapter_validator import ChapterValidator, ChapterValidationResult
from src.novel_agent.novel.continuity import (
    ContinuityManager,
    StoryState,
    CharacterState,
    PlotThread,
    StateChange,
)
from src.novel_agent.novel.character_registry import CharacterRegistry, CharacterEntry
from src.novel_agent.novel.kg_transaction import KGTransactionManager


class TestFullChapterGenerationFlow:
    """End-to-end tests for chapter generation with continuity."""

    @pytest.fixture
    def setup(self):
        """Set up test fixtures."""
        validator = ChapterValidator()
        registry = CharacterRegistry()
        kg_manager = KGTransactionManager()
        continuity = ContinuityManager()
        return {
            "validator": validator,
            "registry": registry,
            "kg_manager": kg_manager,
            "continuity": continuity,
        }

    def test_valid_chapter_passes_validation(self, setup):
        """Valid chapter content should pass all validation."""
        # Create a valid chapter with title, sufficient content, and ending
        content = "第一章 开端\n\n" + "这是第一章的内容，描述了一个新的开始。" * 100 + "\n\n完"

        result = setup["validator"].check_completeness(content)

        assert result.is_valid is True
        assert result.word_count >= 500
        assert result.has_title is True
        assert result.has_ending is True
        assert len(result.issues) == 0

    def test_valid_chapter_with_english_title(self, setup):
        """Valid chapter with English title should pass validation."""
        content = (
            "Chapter 1: The Beginning\n\n"
            + "This is the beginning of our story. " * 100
            + "\n\nTBC"
        )

        result = setup["validator"].check_completeness(content)

        assert result.is_valid is True
        assert result.has_title is True
        assert result.has_ending is True

    def test_invalid_chapter_fails_validation(self, setup):
        """Invalid chapter should fail validation."""
        # Too short, no title, no ending
        content = "短内容"

        result = setup["validator"].check_completeness(content)

        assert result.is_valid is False
        assert len(result.issues) > 0
        # Should have issues for: word count, title, ending
        assert any("字/词" in issue for issue in result.issues)  # word count issue
        assert any("标题" in issue for issue in result.issues)  # title issue
        assert any("结束标记" in issue for issue in result.issues)  # ending issue

    def test_chapter_without_title_fails(self, setup):
        """Chapter without title should fail validation."""
        content = "这是内容\n\n完"

        result = setup["validator"].check_completeness(content)

        assert result.is_valid is False
        assert result.has_title is False
        assert any("缺少章节标题" in issue for issue in result.issues)

    def test_chapter_without_ending_fails(self, setup):
        """Chapter without ending marker should fail validation."""
        # Has title but no ending
        content = "第一章 开端\n\n" + "内容内容" * 100

        result = setup["validator"].check_completeness(content)

        assert result.is_valid is False
        assert result.has_ending is False
        assert any("结束标记" in issue for issue in result.issues)

    def test_chapter_word_count_boundary(self, setup):
        """Test word count at exact boundary."""
        # Exactly 500 characters
        content = (
            "第一章 开端\n\n"
            + "文字" * 250  # 500 characters
            + "\n\n完"
        )

        result = setup["validator"].check_completeness(content)
        assert result.is_valid is True
        assert result.word_count >= 500

    def test_continuity_manager_state_update(self, setup):
        """Test continuity manager updating story state."""
        continuity = setup["continuity"]

        state = StoryState(
            chapter=1,
            location="Shanghai",
            character_states={
                "Alice": CharacterState(
                    name="Alice",
                    status="alive",
                    location="Shanghai",
                    physical_form="human",
                    role_id=None,
                ),
                "Bob": CharacterState(
                    name="Bob",
                    status="alive",
                    location="Shanghai",
                    physical_form="human",
                    role_id=None,
                ),
            },
            active_characters=["Alice"],
        )

        chapter_content = """
        Alice went to Boston. Bob was captured by enemies.
        """
        updated_state = continuity.update_from_chapter(state, chapter_content, 2)

        assert updated_state.chapter == 2
        # Alice is captured not in active_characters (only alive characters)
        assert "Alice" not in updated_state.active_characters
        # But Bob should be tracked with his status updated
        assert "Bob" in updated_state.character_states
        assert updated_state.character_states["Bob"].status == "captured"

    def test_continuity_manager_state_changes_detection(self, setup):
        """Test state change detection from chapter content."""
        continuity = setup["continuity"]

        content = """
        Alice died in the battle.
        Bob was captured by enemies.
        """

        changes = continuity._detect_state_changes(content)

        assert len(changes) == 2

        death_changes = [c for c in changes if c.new_state == "dead"]
        assert any(c.character == "Alice" for c in death_changes)

        capture_changes = [c for c in changes if c.new_state == "captured"]
        assert any(c.character == "Bob" for c in capture_changes)

    def test_continuity_manager_update_from_chapter_extraction(self):
        """Test character name extraction from chapter content."""
        continuity = ContinuityManager()

        state = StoryState(
            chapter=1,
            location="Beijing",
            character_states={},
            active_characters=[],
        )

        content = """
        Alice met Bob in Beijing.
        Alice said: Hello, Bob.
        Bob replied: Hello, Alice.
        They went to Boston.
        """

        updated = continuity.update_from_chapter(state, content, 2)

        assert "Alice" in updated.character_states
        assert "Bob" in updated.character_states
        assert "Alice" in updated.active_characters
        assert "Bob" in updated.active_characters

    def test_continuity_manager_character_state_preservation(self):
        """Test character state preservation across updates."""
        continuity = ContinuityManager()

        state = StoryState(
            chapter=1,
            location="Beijing",
            character_states={
                "LinXiao": CharacterState(
                    name="LinXiao",
                    status="alive",
                    location="Beijing",
                    physical_form="human",
                    role_id="char_LinXiao_001",
                    relationships={"ZhangSan": "friend"},
                )
            },
            active_characters=["LinXiao"],
        )

        content = "ZhangSan arrived in Shanghai."

        updated = continuity.update_from_chapter(state, content, 2)

        # The original LinXiao state should be preserved
        assert "LinXiao" in updated.character_states
        assert updated.character_states["LinXiao"].status == "alive"
        assert updated.character_states["LinXiao"].role_id == "char_LinXiao_001"
        # No new characters extracted since ZhangSan is treated as one word (no space)
        # and Shanghai is not recognized as a new character
        assert len(updated.character_states) == 1

    def test_continuity_integration_with_kg_manager(self):
        """Test integration between continuity and KG managers."""
        kg_manager = KGTransactionManager()

        # Simulate KG state from chapter processing
        def process_chapter(state):
            new_state = state.copy() if state else {}
            new_state["characters"] = state.get("characters", {}) if state else {}
            new_state["characters"]["林晓"] = {
                "name": "林晓",
                "status": "alive",
                "chapter_appeared": 1,
            }
            return new_state

        result = kg_manager.update_with_transaction(process_chapter)

        assert result is True
        state = kg_manager.get_state()
        assert "林晓" in state["characters"]
        assert kg_manager.get_version() == 1

    def test_full_workflow_integration(self):
        """Test complete workflow: validation -> registry -> continuity -> KG."""
        # Step 1: Validate chapter - need more content for 500 characters
        validator = ChapterValidator()
        content = "第一章 test\n\n" + "内容内容content " * 100 + "\n\n完"
        validation = validator.check_completeness(content)
        assert validation.is_valid is True

        # Step 2: Register characters
        registry = CharacterRegistry()
        role_id = registry.register("主角", role="protagonist", chapter=1)
        assert role_id == "char_主角_001"

        # Step 3: Update story state
        continuity = ContinuityManager()
        state = StoryState(
            chapter=1,
            location="Start",
            character_states={
                "主角": CharacterState(
                    name="主角",
                    status="alive",
                    location="Start",
                    physical_form="human",
                    role_id=role_id,
                )
            },
            active_characters=["主角"],
        )

        # Step 4: Update from chapter - use character that appears 3+ times
        chapter_content = "Zhang San moved to Boston. Zhang San saw Bob. Zhang San stayed."
        updated_state = continuity.update_from_chapter(state, chapter_content, 2)

        assert updated_state.chapter == 2
        assert "Zhang" in updated_state.character_states
        assert "San" in updated_state.character_states

        # Step 5: Update KG
        kg_manager = KGTransactionManager()
        kg_manager.update_with_transaction(lambda s: {"version": 1})

        assert kg_manager.get_version() == 1


class TestCharacterEntryDataclass:
    """Tests for CharacterEntry dataclass."""

    def test_character_entry_serialization(self):
        """Test character entry to_dict/from_dict."""
        entry = CharacterEntry(
            role_id="char_林晓_001",
            name="林晓",
            role="protagonist",
            first_appearance=1,
            aliases=["小林", "林"],
            metadata={"source": "outline"},
        )

        # Test to_dict
        data = entry.to_dict()
        assert data["role_id"] == "char_林晓_001"
        assert data["name"] == "林晓"
        assert data["role"] == "protagonist"

        # Test from_dict
        new_entry = CharacterEntry.from_dict(data)
        assert new_entry.role_id == entry.role_id
        assert new_entry.name == entry.name
        assert new_entry.role == entry.role
        assert new_entry.aliases == entry.aliases
        assert new_entry.metadata == entry.metadata

    def test_character_entry_defaults(self):
        """Test character entry with default values."""
        entry = CharacterEntry(
            role_id="char_test_001",
            name="Test",
        )

        assert entry.role is None
        assert entry.first_appearance == 0
        assert entry.aliases == []
        assert entry.metadata == {}

    def test_character_entry_is_alive(self):
        """Test CharacterState is_alive method."""
        alive = CharacterState(
            name="Alive",
            status="alive",
            location="here",
            physical_form="human",
        )
        dead = CharacterState(
            name="Dead",
            status="dead",
            location="grave",
            physical_form="human",
        )

        assert alive.is_alive() is True
        assert dead.is_alive() is False

    def test_character_state_has_physical_form(self):
        """Test CharacterState has_physical_form method."""
        human = CharacterState(
            name="Human",
            status="alive",
            location="here",
            physical_form="human",
        )
        spirit = CharacterState(
            name="Spirit",
            status="alive",
            location="spirit_world",
            physical_form="spirit",
        )
        ghost = CharacterState(
            name="Ghost",
            status="alive",
            location="nowhere",
            physical_form="ghost",
        )

        assert human.has_physical_form() is True
        assert spirit.has_physical_form() is False
        assert ghost.has_physical_form() is False


class TestChapterValidationResultDataclass:
    """Tests for ChapterValidationResult dataclass."""

    def test_result_with_issues(self):
        """Test validation result with issues."""
        result = ChapterValidationResult(
            is_valid=False,
            issues=["Word count too low", "Missing title"],
            suggestions=["Add more content", "Add a chapter title"],
            word_count=100,
            has_title=False,
            has_ending=False,
        )

        assert result.is_valid is False
        assert len(result.issues) == 2
        assert len(result.suggestions) == 2
        assert result.word_count == 100

    def test_result_without_issues(self):
        """Test validation result without issues."""
        result = ChapterValidationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            word_count=1000,
            has_title=True,
            has_ending=True,
        )

        assert result.is_valid is True
        assert result.issues == []

    def test_result_defaults(self):
        """Test validation result default values."""
        result = ChapterValidationResult(is_valid=True)

        assert result.issues == []
        assert result.suggestions == []
        assert result.word_count == 0
        assert result.has_title is False
        assert result.has_ending is False
