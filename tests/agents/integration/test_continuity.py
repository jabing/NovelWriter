"""Integration tests for KG-to-chapter generation continuity flow.

Tests the integration between:
- GenerateWorkflow and fact_injector
- Fact injection into chapter generation prompts
- End-to-end continuity flow from workflow to writer
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.novel_agent.novel.continuity import PlotThread, StoryState
from src.novel_agent.novel.fact_database import Fact, FactType
from src.novel_agent.novel.fact_injector import RelevanceScore
from src.novel_agent.novel.outline_manager import ChapterSpec
from src.novel_agent.workflow.generate_workflow import ChapterGenerateWorkflow


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Create temporary storage path."""
    return tmp_path / "test_data"


@pytest.fixture
def mock_llm():
    """Create mock LLM with predictable responses."""
    llm = MagicMock()
    llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Test chapter content"))
    llm.generate = AsyncMock(return_value=MagicMock(content="Test chapter content"))
    return llm


@pytest.fixture
def mock_fact_injector(temp_storage: Path):
    """Create mock fact injector with test facts."""
    from src.novel_agent.novel.fact_injector import RelevantFactInjector

    injector = MagicMock(spec=RelevantFactInjector)

    # Create test facts
    test_facts = [
        (
            Fact(
                id="fact_1",
                fact_type=FactType.CHARACTER,
                content="Alice is a brilliant scientist",
                chapter_origin=1,
                importance=0.9,
                entities=["Alice"],
            ),
            RelevanceScore(
                fact_id="fact_1",
                recency_score=0.9,
                importance_score=0.9,
                narrative_significance_score=0.8,
                frequency_score=0.5,
                relationship_score=1.0,
                debt_urgency_score=0.0,
                total_score=0.8,
            ),
        ),
        (
            Fact(
                id="fact_2",
                fact_type=FactType.LOCATION,
                content="The laboratory is located in the mountains",
                chapter_origin=1,
                importance=0.7,
                entities=["Laboratory"],
            ),
            RelevanceScore(
                fact_id="fact_2",
                recency_score=0.8,
                importance_score=0.7,
                narrative_significance_score=0.6,
                frequency_score=0.3,
                relationship_score=0.5,
                debt_urgency_score=0.0,
                total_score=0.6,
            ),
        ),
    ]

    injector.get_relevant_facts.return_value = test_facts
    injector.get_context_string.return_value = "【相关事实】\n角色信息:\n  - Alice is a brilliant scientist\n地点信息:\n  - The laboratory is located in the mountains"
    injector.max_facts = 20

    return injector


@pytest.fixture
def mock_writer():
    """Create mock writer with tracked calls."""
    from src.novel_agent.agents.writers.base_writer import BaseWriter

    writer = MagicMock(spec=BaseWriter)
    writer.write_chapter_with_context = AsyncMock(
        return_value="Generated chapter content with fact context"
    )
    writer.GENRE = "fantasy"
    return writer


@pytest.fixture
def chapter_spec() -> ChapterSpec:
    """Create test chapter specification."""
    return ChapterSpec(
        number=5,
        title="The Discovery",
        summary="Alice makes a breakthrough discovery in her research.",
        characters=["Alice", "Bob"],
        location="Laboratory",
        key_events=["Alice discovers anomaly"],
    )


@pytest.fixture
def story_state() -> StoryState:
    """Create test story state."""
    return StoryState(
        chapter=4,
        location="Laboratory",
        active_characters=["Alice"],
        character_states={},
        plot_threads=[PlotThread(name="Main mystery", status="active")],
        key_events=["Previous chapter events"],
    )


# ============================================================================
# Test: Workflow has fact_injector attribute
# ============================================================================


class TestWorkflowFactInjectorAttribute:
    """Test that GenerateWorkflow properly initializes fact_injector."""

    def test_workflow_has_fact_injector_attribute(self, mock_llm):
        """Test that ChapterGenerateWorkflow has _fact_injector attribute."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Attribute should exist (initially None)
        assert hasattr(workflow, "_fact_injector")
        assert workflow._fact_injector is None

    def test_workflow_initializes_fact_injector(
        self,
        mock_llm,
        temp_storage: Path,
    ):
        """Test that _initialize_components creates fact_injector."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Initialize components
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Fact injector should be initialized
        assert workflow._fact_injector is not None
        from src.novel_agent.novel.fact_injector import RelevantFactInjector

        assert isinstance(workflow._fact_injector, RelevantFactInjector)

    def test_fact_injector_has_correct_settings(
        self,
        mock_llm,
        temp_storage: Path,
    ):
        """Test fact_injector is configured with correct settings."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Check configuration
        assert workflow._fact_injector is not None
        # Default max_facts from calculate_max_facts(30) = max(30, min(50, 45)) = 45
        assert workflow._fact_injector.max_facts >= 30


# ============================================================================
# Test: Facts are retrieved during chapter generation
# ============================================================================


class TestFactsRetrievedDuringGeneration:
    """Test that facts are retrieved when generating chapters."""

    @pytest.mark.asyncio
    async def test_get_relevant_facts_called_during_generation(
        self,
        mock_llm,
        mock_fact_injector,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that get_relevant_facts is called during _generate_single_chapter."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Initialize workflow components
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Replace fact_injector with mock
        workflow._fact_injector = mock_fact_injector
        workflow._story_state = story_state

        # Mock writer
        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(return_value="Test content")

        # Mock summary_manager to avoid validation
        workflow._summary_manager = None

        # Generate chapter
        result = await workflow._generate_single_chapter(
            chapter_spec=chapter_spec,
            characters=[],
            world_settings={},
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Verify get_relevant_facts was called
        mock_fact_injector.get_relevant_facts.assert_called_once()
        call_args = mock_fact_injector.get_relevant_facts.call_args

        # Verify call parameters
        assert call_args[1]["current_chapter"] == chapter_spec.number
        assert "active_entities" in call_args[1]

    @pytest.mark.asyncio
    async def test_fact_context_built_from_relevant_facts(
        self,
        mock_llm,
        mock_fact_injector,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that fact_context is built from retrieved facts."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )
        workflow._fact_injector = mock_fact_injector
        workflow._story_state = story_state

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(return_value="Test content")
        workflow._summary_manager = None

        # Generate chapter
        result = await workflow._generate_single_chapter(
            chapter_spec=chapter_spec,
            characters=[],
            world_settings={},
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Verify facts were retrieved
        assert mock_fact_injector.get_relevant_facts.called

        # Verify result exists
        assert result is not None
        assert result.content == "Test content"


# ============================================================================
# Test: fact_context is passed to writer
# ============================================================================


class TestFactContextPassedToWriter:
    """Test that fact_context parameter is used correctly."""

    @pytest.mark.asyncio
    async def test_write_chapter_with_context_accepts_fact_context(
        self,
        mock_llm,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that write_chapter_with_context accepts fact_context parameter."""
        from src.novel_agent.agents.writers.base_writer import BaseWriter

        # Create a concrete test writer
        class TestWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(
                self,
                chapter_number: int,
                chapter_outline: str,
                characters: list[dict],
                world_context: dict,
                **kwargs,
            ) -> str:
                return "Test chapter"

        writer = TestWriter(name="test_writer", llm=mock_llm)

        # Call with fact_context
        result = await writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=story_state,
            characters=[{"name": "Alice"}],
            world_context={},
            fact_context="Alice is a brilliant scientist",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_build_continuity_prompt_includes_fact_context(
        self,
        mock_llm,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that _build_continuity_prompt includes fact_context."""
        from src.novel_agent.agents.writers.base_writer import BaseWriter

        class TestWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(
                self,
                chapter_number: int,
                chapter_outline: str,
                characters: list[dict],
                world_context: dict,
                **kwargs,
            ) -> str:
                return "Test chapter"

        writer = TestWriter(name="test_writer", llm=mock_llm)

        # Build continuity prompt with fact_context
        prompt = writer._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Previous chapter summary",
            chapter_number=chapter_spec.number,
            fact_context="Alice is a brilliant scientist",
        )

        # Verify fact context is included
        assert "Alice is a brilliant scientist" in prompt
        assert "【相关事实】" in prompt

    @pytest.mark.asyncio
    async def test_build_continuity_prompt_without_fact_context(
        self,
        mock_llm,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that _build_continuity_prompt works without fact_context."""
        from src.novel_agent.agents.writers.base_writer import BaseWriter

        class TestWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(
                self,
                chapter_number: int,
                chapter_outline: str,
                characters: list[dict],
                world_context: dict,
                **kwargs,
            ) -> str:
                return "Test chapter"

        writer = TestWriter(name="test_writer", llm=mock_llm)

        # Build continuity prompt without fact_context
        prompt = writer._build_continuity_prompt(
            story_state=story_state,
            previous_summary="Previous chapter summary",
            chapter_number=chapter_spec.number,
            fact_context=None,
        )

        # Should still work, just without the fact section
        assert "【连续性上下文】" in prompt


# ============================================================================
# Test: End-to-end continuity flow
# ============================================================================


class TestEndToEndContinuityFlow:
    """End-to-end tests for the continuity flow."""

    @pytest.mark.asyncio
    async def test_full_flow_from_workflow_to_writer(
        self,
        mock_llm,
        temp_storage: Path,
    ):
        """Test complete flow: workflow -> fact_injector -> writer."""
        # Create workflow
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Track writer calls
        writer_calls = []

        async def track_write_chapter(**kwargs):
            writer_calls.append(kwargs)
            return "Generated content"

        # Mock writer
        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = track_write_chapter

        # Initialize with real fact_injector
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Add a test fact to the fact database
        workflow._fact_injector.add_fact(
            fact_type=FactType.CHARACTER,
            content="Alice discovered the ancient artifact in chapter 2",
            chapter_origin=2,
            importance=0.9,
            entities=["Alice", "ancient artifact"],
        )

        # Initialize story state
        from src.novel_agent.novel.continuity import StoryState

        workflow._story_state = StoryState(
            chapter=4,
            location="Mountain Laboratory",
            active_characters=["Alice"],
            character_states={},
            plot_threads=[PlotThread(name="Ancient mystery", status="active")],
            key_events=["Alice found the artifact"],
        )

        # Disable validation for simpler test
        workflow._summary_manager = None

        # Create chapter spec
        chapter_spec = ChapterSpec(
            number=5,
            title="The Revelation",
            summary="Alice studies the artifact",
            characters=["Alice"],
            location="Mountain Laboratory",
            key_events=["Artifact reveals secrets"],
        )

        # Generate chapter
        result = await workflow._generate_single_chapter(
            chapter_spec=chapter_spec,
            characters=[],
            world_settings={},
            project_id="test_novel",
            storage_path=temp_storage,
        )

        # Verify result
        assert result is not None
        assert result.chapter_number == 5
        assert result.title == "The Revelation"

        # Verify writer was called with story state
        assert len(writer_calls) == 1
        call_kwargs = writer_calls[0]
        assert "chapter_spec" in call_kwargs
        assert "story_state" in call_kwargs

    @pytest.mark.asyncio
    async def test_fact_injector_get_relevant_facts_returns_correct_entities(
        self,
        temp_storage: Path,
    ):
        """Test that get_relevant_facts filters by active entities."""
        from src.novel_agent.novel.fact_injector import RelevantFactInjector

        injector = RelevantFactInjector(
            storage_path=temp_storage,
            novel_id="test_novel",
            max_facts=20,
        )

        # Add facts for different entities
        injector.add_fact(
            fact_type=FactType.CHARACTER,
            content="Alice has blue eyes",
            chapter_origin=1,
            importance=0.5,
            entities=["Alice"],
        )
        injector.add_fact(
            fact_type=FactType.CHARACTER,
            content="Bob has red hair",
            chapter_origin=1,
            importance=0.5,
            entities=["Bob"],
        )
        injector.add_fact(
            fact_type=FactType.LOCATION,
            content="The castle is ancient",
            chapter_origin=1,
            importance=0.7,
            entities=["Castle"],
        )

        # Query for Alice only
        facts = injector.get_relevant_facts(
            current_chapter=5,
            active_entities=["Alice"],
        )

        # Should get facts related to Alice
        assert len(facts) > 0

        # Facts mentioning Alice should have higher relationship score
        alice_facts = [(f, s) for f, s in facts if "Alice" in f.entities]
        assert len(alice_facts) > 0

    @pytest.mark.asyncio
    async def test_continuity_with_multiple_chapters(
        self,
        mock_llm,
        temp_storage: Path,
    ):
        """Test continuity tracking across multiple chapter generations."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(return_value="Chapter content")
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )
        workflow._summary_manager = None

        # Set up initial story state
        from src.novel_agent.novel.continuity import StoryState

        workflow._story_state = StoryState(
            chapter=0,
            location="Starting Village",
            active_characters=["Hero"],
            character_states={},
            plot_threads=[],
            key_events=[],
        )

        # Generate multiple chapters
        for chapter_num in range(1, 4):
            chapter_spec = ChapterSpec(
                number=chapter_num,
                title=f"Chapter {chapter_num}",
                summary=f"Chapter {chapter_num} summary",
                characters=["Hero"],
                location="Various",
                key_events=[f"Event {chapter_num}"],
            )

            result = await workflow._generate_single_chapter(
                chapter_spec=chapter_spec,
                characters=[],
                world_settings={},
                project_id="test_novel",
                storage_path=temp_storage,
            )

            assert result is not None
            assert result.chapter_number == chapter_num

            # Update story state for next chapter
            if workflow._story_state:
                workflow._story_state.chapter = chapter_num

    @pytest.mark.asyncio
    async def test_fact_context_in_continuity_prompt(
        self,
        mock_llm,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that fact context appears in the continuity prompt."""
        from src.novel_agent.agents.writers.base_writer import BaseWriter

        class TestWriter(BaseWriter):
            GENRE = "test"

            async def write_chapter(
                self,
                chapter_number: int,
                chapter_outline: str,
                characters: list[dict],
                world_context: dict,
                **kwargs,
            ) -> str:
                # Verify fact context is in the outline
                assert "Alice is a brilliant scientist" in chapter_outline
                return "Generated content"

        writer = TestWriter(name="test_writer", llm=mock_llm)

        # Write with fact context
        await writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=story_state,
            characters=[{"name": "Alice"}],
            world_context={},
            fact_context="Alice is a brilliant scientist",
        )


# ============================================================================
# Test: Fact injection error handling
# ============================================================================


class TestFactInjectionErrorHandling:
    """Test error handling in fact injection flow."""

    @pytest.mark.asyncio
    async def test_generation_continues_if_fact_injector_fails(
        self,
        mock_llm,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that chapter generation continues even if fact injector fails."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(return_value="Test content")
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )
        workflow._story_state = story_state
        workflow._summary_manager = None

        # Patch get_relevant_facts to raise an error
        with patch.object(
            workflow._fact_injector,
            "get_relevant_facts",
            side_effect=Exception("Database error"),
        ):
            # Generation should still succeed
            result = await workflow._generate_single_chapter(
                chapter_spec=chapter_spec,
                characters=[],
                world_settings={},
                project_id="test_novel",
                storage_path=temp_storage,
            )

        # Result should still be generated
        assert result is not None
        assert result.content == "Test content"

    @pytest.mark.asyncio
    async def test_generation_works_without_fact_injector(
        self,
        mock_llm,
        temp_storage: Path,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
    ):
        """Test that generation works when fact_injector is None."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(return_value="Test content")
        workflow._initialize_components(
            project_id="test_novel",
            storage_path=temp_storage,
        )
        workflow._fact_injector = None  # No fact injector
        workflow._story_state = story_state
        workflow._summary_manager = None

        result = await workflow._generate_single_chapter(
            chapter_spec=chapter_spec,
            characters=[],
            world_settings={},
            project_id="test_novel",
            storage_path=temp_storage,
        )

        assert result is not None
        assert result.content == "Test content"
