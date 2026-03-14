"""Tests for BaseWriter class."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.agents.base import AgentResult
from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.novel.continuity import CharacterState, StoryState
from src.novel_agent.novel.outline_manager import ChapterSpec


class TestBaseWriter:
    """Test BaseWriter functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        mock = MagicMock()
        mock.generate_with_system = AsyncMock(return_value=MagicMock(content="Test content"))
        return mock

    @pytest.fixture
    def concrete_writer(self, mock_llm):
        """Create a concrete writer instance for testing."""

        class ConcreteWriter(BaseWriter):
            GENRE = "test"
            DOMAIN_KNOWLEDGE = "Test knowledge"

            async def write_chapter(self, **kwargs):
                return "Test chapter content"

        return ConcreteWriter(name="Test Writer", llm=mock_llm, memory=None)

    @pytest.mark.asyncio
    async def test_execute_with_basic_input(self, concrete_writer):
        """Test execute with basic input data."""
        input_data = {
            "chapter_number": 1,
            "chapter_outline": "Test outline",
            "characters": [{"name": "Test Character"}],
            "world_context": {"setting": "test"},
        }

        result = await concrete_writer.execute(input_data)

        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.data["content"] == "Test chapter content"
        assert result.data["chapter_number"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_continuity_params(self, concrete_writer):
        """Test execute with continuity parameters."""
        story_state = StoryState(
            chapter=1,
            location="Test Location",
            active_characters=["Character1"],
            character_states={
                "Character1": CharacterState(
                    name="Character1",
                    status="alive",
                    location="Test Location",
                    physical_form="human",
                )
            },
        )

        input_data = {
            "chapter_number": 2,
            "chapter_outline": "Test outline",
            "characters": [{"name": "Character1"}],
            "world_context": {"setting": "test"},
            "story_state": story_state,
            "previous_chapter_summary": "Previous events",
        }

        result = await concrete_writer.execute(input_data)

        assert isinstance(result, AgentResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_backward_compatible(self, concrete_writer):
        """Test execute is backward compatible without new params."""
        # Test with old-style input (no continuity params)
        input_data = {
            "chapter_number": 1,
            "chapter_outline": "Test outline",
            "characters": [],
            "world_context": {},
            "style_guide": "Test style",
            "learning_hints": ["hint1", "hint2"],
            "market_keywords": {"key": "value"},
            "language": "zh",
        }

        result = await concrete_writer.execute(input_data)

        assert isinstance(result, AgentResult)
        assert result.success is True


class TestBuildContinuityPrompt:
    """Test _build_continuity_prompt method."""

    @pytest.fixture
    def concrete_writer(self):
        """Create a concrete writer instance for testing."""

        class ConcreteWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(self, **kwargs):
                return "Test content"

        return ConcreteWriter(name="Test Writer", llm=MagicMock(), memory=None)

    def test_build_continuity_prompt_with_state(self, concrete_writer):
        """Test building continuity prompt with valid story state."""
        story_state = StoryState(
            chapter=5,
            location="Dragon's Keep",
            active_characters=["Kael", "Lyra"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Dragon's Keep",
                    physical_form="human",
                ),
                "Lyra": CharacterState(
                    name="Lyra",
                    status="injured",
                    location="Dragon's Keep",
                    physical_form="human",
                ),
            },
        )

        prompt = concrete_writer._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Kael and Lyra entered the keep.",
            chapter_number=6,
        )

        assert "Dragon's Keep" in prompt
        assert "Kael" in prompt
        assert "Lyra" in prompt
        assert "alive" in prompt
        assert "injured" in prompt
        assert "Kael and Lyra entered" in prompt

    def test_build_continuity_prompt_none_state(self, concrete_writer):
        """Test building continuity prompt with None state."""
        prompt = concrete_writer._build_continuity_prompt(
            story_state=None,
            previous_summary="Some summary",
            chapter_number=1,
        )

        assert prompt == ""

    def test_build_continuity_prompt_dead_character(self, concrete_writer):
        """Test that dead characters are marked appropriately."""
        story_state = StoryState(
            chapter=3,
            location="Battlefield",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Battlefield",
                    physical_form="human",
                ),
                "Sylas": CharacterState(
                    name="Sylas",
                    status="dead",
                    location="Battlefield",
                    physical_form="spirit",
                ),
            },
        )

        prompt = concrete_writer._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Sylas died.",
            chapter_number=4,
        )

        assert "dead" in prompt
        assert "已死亡" in prompt

    def test_build_continuity_prompt_fused_character(self, concrete_writer):
        """Test that fused characters are marked appropriately."""
        story_state = StoryState(
            chapter=5,
            location="Inner Sanctum",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Inner Sanctum",
                    physical_form="human",
                ),
                "Aurelion": CharacterState(
                    name="Aurelion",
                    status="fused",
                    location="Kael",
                    physical_form="spirit",
                ),
            },
        )

        prompt = concrete_writer._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Aurelion fused with Kael.",
            chapter_number=6,
        )

        assert "fused" in prompt
        assert "融合" in prompt


class TestWriteChapterWithContext:
    """Test write_chapter_with_context method."""

    @pytest.fixture
    def concrete_writer(self):
        """Create a concrete writer instance for testing."""

        class ConcreteWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(self, **kwargs):
                return f"Chapter {kwargs.get('chapter_number')} content"

        return ConcreteWriter(name="Test Writer", llm=MagicMock(), memory=None)

    @pytest.fixture
    def chapter_spec(self):
        """Create a chapter spec."""
        return ChapterSpec(
            number=1,
            title="Test Chapter",
            summary="Test summary",
            characters=["Kael"],
            location="Test Location",
        )

    @pytest.fixture
    def story_state(self):
        """Create a story state."""
        return StoryState(
            chapter=0,
            location="Test Location",
            active_characters=["Kael"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Test Location",
                    physical_form="human",
                )
            },
        )

    @pytest.mark.asyncio
    async def test_write_chapter_with_context_basic(
        self, concrete_writer, chapter_spec, story_state
    ):
        """Test writing chapter with context."""
        content = await concrete_writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=story_state,
            characters=[{"name": "Kael"}],
            world_context={"setting": "fantasy"},
        )

        assert "Chapter 1 content" in content

    @pytest.mark.asyncio
    async def test_write_chapter_with_context_and_previous_summary(
        self, concrete_writer, chapter_spec, story_state
    ):
        """Test writing chapter with previous summary."""
        content = await concrete_writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=story_state,
            characters=[{"name": "Kael"}],
            world_context={},
            previous_chapter_summary="Previous events occurred.",
        )

        assert "Chapter 1 content" in content


class TestGetLanguageInstruction:
    """Test get_language_instruction function."""

    def test_chinese_language(self):
        """Test Chinese language instruction."""
        instruction = get_language_instruction("zh")
        assert "中文" in instruction
        assert "必须使用中文写作" in instruction

    def test_english_language(self):
        """Test English language returns empty."""
        instruction = get_language_instruction("en")
        assert instruction == ""

    def test_none_language(self):
        """Test None language returns empty."""
        instruction = get_language_instruction(None)
        assert instruction == ""

    def test_unknown_language(self):
        """Test unknown language returns empty."""
        instruction = get_language_instruction("fr")
        assert instruction == ""


class TestTokenBudgetIntegration:
    """Test token budget integration in BaseWriter."""

    @pytest.fixture
    def concrete_writer_with_budget(self):
        """Create a concrete writer with custom token budget."""
        from src.novel_agent.utils.token_budget import TokenBudgetConfig, TokenBudgetManager

        class ConcreteWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(self, **kwargs):
                return "Test content"

        config = TokenBudgetConfig(
            max_context_tokens=1000,  # Small budget for testing
        )
        budget_manager = TokenBudgetManager(config)
        return ConcreteWriter(
            name="Test Writer",
            llm=MagicMock(),
            memory=None,
            token_budget_manager=budget_manager,
        )

    @pytest.fixture
    def concrete_writer_default_budget(self):
        """Create a concrete writer with default budget."""
        class ConcreteWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(self, **kwargs):
                return "Test content"

        return ConcreteWriter(
            name="Test Writer",
            llm=MagicMock(),
            memory=None,
        )

    def test_token_budget_manager_initialized(self, concrete_writer_default_budget):
        """Test that token budget manager is initialized by default."""
        assert hasattr(concrete_writer_default_budget, "_token_budget")
        assert concrete_writer_default_budget._token_budget is not None

    def test_token_budget_manager_custom(self, concrete_writer_with_budget):
        """Test that custom token budget manager is used."""
        assert concrete_writer_with_budget._token_budget is not None
        assert concrete_writer_with_budget._token_budget.config.max_context_tokens == 1000

    def test_build_continuity_prompt_uses_token_budget(self, concrete_writer_with_budget, caplog):
        """Test that continuity prompt respects token budget and truncates previous_summary."""
        import logging
        caplog.set_level(logging.INFO)

        story_state = StoryState(
            chapter=5,
            location="Dragon's Keep",
            active_characters=["Kael", "Lyra"],
            character_states={
                "Kael": CharacterState(
                    name="Kael",
                    status="alive",
                    location="Dragon's Keep",
                    physical_form="human",
                ),
            },
        )

        long_summary = "A" * 5000  # Large summary to trigger truncation

        # Use a very small max_tokens to trigger truncation
        prompt = concrete_writer_with_budget._build_continuity_prompt(
            story_state=story_state,
            previous_summary=long_summary,
            chapter_number=6,
            max_tokens=50,  # Very small budget
        )

        # Essential info should still be present
        assert "Dragon's Keep" in prompt
        assert "Kael" in prompt or "Lyra" in prompt

        # The long summary should have been truncated
        # Original would be ~5000+ chars, truncated should be much shorter
        assert len(prompt) < len(long_summary)

        # Verify truncation was logged
        assert any("[TokenBudget]" in record.message for record in caplog.records)
        assert any("truncated=True" in record.message or "truncated=False" in record.message for record in caplog.records)
    def test_build_continuity_prompt_logs_token_usage(self, concrete_writer_with_budget, caplog):
        """Test that token usage is logged (T5)."""
        import logging
        caplog.set_level(logging.INFO)

        story_state = StoryState(
            chapter=5,
            location="Dragon's Keep",
            active_characters=["Kael"],
            character_states={},
        )

        concrete_writer_with_budget._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Previous events.",
            chapter_number=6,
        )

        # Check that token budget log was created
        assert any("[TokenBudget]" in record.message for record in caplog.records)

    def test_build_continuity_prompt_within_budget(self, concrete_writer_with_budget):
        """Test that prompt stays within budget when content is small."""
        story_state = StoryState(
            chapter=1,
            location="Village",
            active_characters=["Hero"],
            character_states={},
        )

        prompt = concrete_writer_with_budget._build_continuity_prompt(
            story_state=story_state,
            previous_summary="",
            chapter_number=2,
            max_tokens=500,
        )

        # Small content should fit within budget
        assert "Village" in prompt
        assert "Hero" in prompt
