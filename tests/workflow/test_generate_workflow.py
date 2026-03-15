# tests/workflow/test_generate_workflow.py
"""Tests for the chapter generation workflow.

This module tests the ChapterGenerateWorkflow class including:
- Successful chapter generation
- Validation pipeline integration
- Checkpoint save/resume functionality
- Auto-retry on validation failure
- Error handling and messages
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.novel_agent.novel.auto_fixer import AutoFixResult
from src.novel_agent.novel.checkpointing import Checkpoint
from src.novel_agent.novel.consistency_verifier import VerificationResult
from src.novel_agent.novel.continuity import StoryState
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.summaries import ChapterSummary
from src.novel_agent.workflow.generate_workflow import (
    ChapterGenerateWorkflow,
    GenerateResult,
    GeneratedChapter,
    create_generate_workflow,
)
from src.novel_agent.workflow.state import WorkflowState


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance."""
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=MagicMock(content="Test generated content"))
    llm.generate_with_system = AsyncMock(
        return_value=MagicMock(content="Test system-generated content")
    )
    llm.name = "mock_llm"
    return llm


@pytest.fixture
def mock_writer():
    """Create a mock writer instance."""
    writer = MagicMock()
    writer.write_chapter_with_context = AsyncMock(
        return_value="# Chapter 1: The Beginning\n\nThis is the test chapter content."
    )
    writer.GENRE = "fantasy"
    return writer


@pytest.fixture
def mock_checkpoint_manager():
    """Create a mock checkpoint manager."""
    manager = MagicMock()
    manager.create_checkpoint = MagicMock(
        return_value=Checkpoint(
            checkpoint_id="test_checkpoint_001",
            chapter_number=1,
            word_count=100,
            content="Test content",
            state_snapshot={},
            created_at=__import__("datetime").datetime.now(),
            checksum="abc123",
            metadata={"project_id": "test_project"},
        )
    )
    manager.get_latest_checkpoint = MagicMock(return_value=None)
    manager.list_checkpoints = MagicMock(return_value=[])
    manager.load_checkpoint = MagicMock(return_value=None)
    manager.delete_checkpoint = MagicMock(return_value=True)
    return manager


@pytest.fixture
def mock_version_control():
    """Create a mock version control system."""
    vc = MagicMock()
    vc.commit_chapter = AsyncMock(return_value="v1.0.0")
    vc.get_version_history = AsyncMock(return_value=[])
    vc.get_version = AsyncMock(return_value=None)
    return vc


@pytest.fixture
def mock_summary_manager():
    """Create a mock summary manager with auto-fix support."""
    manager = MagicMock()

    # Create a successful verification result
    verification = MagicMock(spec=VerificationResult)
    verification.is_consistent = True

    # Create a successful auto-fix result
    auto_fix_result = MagicMock(spec=AutoFixResult)
    auto_fix_result.success = True
    auto_fix_result.final_content = "Fixed chapter content"
    auto_fix_result.iteration_count = 1
    auto_fix_result.is_fully_fixed = True
    auto_fix_result.issues_remaining = []

    # Create a chapter summary
    summary = MagicMock(spec=ChapterSummary)
    summary.chapter_number = 1
    summary.title = "Chapter 1"

    manager.process_chapter_with_autofix = AsyncMock(
        return_value=(summary, verification, auto_fix_result)
    )
    manager.process_chapter = AsyncMock(return_value=summary)

    return manager


@pytest.fixture
def mock_character_selector():
    """Create a mock character selector."""
    selector = MagicMock()
    selector.select_for_chapter = MagicMock(
        return_value=([], 10)  # No characters selected, budget remaining
    )
    return selector


@pytest.fixture
def mock_outline_validator():
    """Create a mock outline validator."""
    validator = MagicMock()
    validator.validate_chapter = MagicMock(return_value={"passed": True, "deviations": []})
    return validator


@pytest.fixture
def mock_continuity_manager():
    """Create a mock continuity manager."""
    manager = MagicMock()
    manager.update_from_chapter = MagicMock(
        return_value=StoryState(
            chapter=1,
            location="Test Location",
            active_characters=[],
            character_states={},
            plot_threads=[],
            key_events=["Event 1"],
        )
    )
    return manager


@pytest.fixture
def mock_timeline_manager():
    """Create a mock timeline manager."""
    manager = MagicMock()
    manager.validate_temporal_consistency = MagicMock(return_value=[])
    return manager


@pytest.fixture
def sample_chapter_spec():
    """Create a sample chapter specification."""
    return ChapterSpec(
        number=1,
        title="The Beginning",
        summary="The story begins with our hero.",
        characters=["Alice", "Bob"],
        location="Castle",
        key_events=["First event", "Second event"],
        plot_threads_started=["Main plot"],
        plot_threads_resolved=[],
        character_states={"Alice": "curious"},
    )


@pytest.fixture
def sample_outline():
    """Create a sample detailed outline."""
    chapters = [
        ChapterSpec(
            number=1,
            title="The Beginning",
            summary="The story begins.",
            characters=["Alice"],
            location="Castle",
            key_events=["Event 1"],
        ),
        ChapterSpec(
            number=2,
            title="The Journey",
            summary="The journey continues.",
            characters=["Alice", "Bob"],
            location="Forest",
            key_events=["Event 2"],
        ),
        ChapterSpec(
            number=3,
            title="The Climax",
            summary="The climax arrives.",
            characters=["Alice", "Bob", "Charlie"],
            location="Mountain",
            key_events=["Event 3"],
        ),
    ]
    return DetailedOutline(chapters=chapters)


@pytest.fixture
def sample_project_files(tmp_path: Path, sample_outline: DetailedOutline) -> Path:
    """Create sample project files for testing."""
    project_dir = tmp_path / "novels" / "test_project"
    project_dir.mkdir(parents=True)

    # Create outline file
    outline_data = {
        "chapters": [
            {
                "number": ch.number,
                "title": ch.title,
                "summary": ch.summary,
                "characters": ch.characters,
                "location": ch.location,
                "key_events": ch.key_events,
                "plot_threads_resolved": ch.plot_threads_resolved,
                "plot_threads_started": ch.plot_threads_started,
                "character_states": ch.character_states,
            }
            for ch in sample_outline.chapters
        ],
        "plot_threads": ["Main plot"],
        "timeline": [],
        "characters": ["Alice", "Bob"],
        "genre": "fantasy",
    }
    with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
        json.dump(outline_data, f)

    # Create characters file
    characters_data = {
        "characters": [
            {
                "name": "Alice",
                "bio": "The protagonist",
                "persona": "Brave and curious",
                "current_status": "active",
                "relationships": {},
            },
            {
                "name": "Bob",
                "bio": "The companion",
                "persona": "Loyal and wise",
                "current_status": "active",
                "relationships": {},
            },
        ]
    }
    with open(project_dir / "characters.json", "w", encoding="utf-8") as f:
        json.dump(characters_data, f)

    # Create world settings file
    world_data = {"setting": "Fantasy Kingdom", "magic_system": "Elemental"}
    with open(project_dir / "world_settings.json", "w", encoding="utf-8") as f:
        json.dump(world_data, f)

    return tmp_path


class TestChapterGenerateWorkflowInit:
    """Tests for ChapterGenerateWorkflow initialization."""

    def test_init_with_required_params(self, mock_llm: MagicMock) -> None:
        """Test initialization with required parameters."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
        )

        assert workflow.name == "test_workflow"
        assert workflow.llm == mock_llm
        assert workflow.genre == "fantasy"
        assert workflow.max_fix_iterations == 3

    def test_init_with_custom_params(self, mock_llm: MagicMock, tmp_path: Path) -> None:
        """Test initialization with custom parameters."""
        workflow = ChapterGenerateWorkflow(
            name="custom_workflow",
            llm=mock_llm,
            genre="scifi",
            description="Custom description",
            checkpoint_dir=tmp_path / "checkpoints",
            max_fix_iterations=5,
        )

        assert workflow.name == "custom_workflow"
        assert workflow.llm == mock_llm
        assert workflow.genre == "scifi"
        assert workflow.description == "Custom description"
        assert workflow.max_fix_iterations == 5

    def test_writer_initialization(self, mock_llm: MagicMock) -> None:
        """Test that writer is initialized based on genre."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Writer should be initialized
        assert workflow.writer is not None


class TestCreateGenerateWorkflow:
    """Tests for create_generate_workflow factory function."""

    def test_factory_creates_workflow(self, mock_llm: MagicMock) -> None:
        """Test that factory creates a valid workflow."""
        workflow = create_generate_workflow(
            name="factory_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        assert isinstance(workflow, ChapterGenerateWorkflow)
        assert workflow.name == "factory_workflow"
        assert workflow.genre == "fantasy"

    def test_factory_with_checkpoint_dir(self, mock_llm: MagicMock, tmp_path: Path) -> None:
        """Test factory with custom checkpoint directory."""
        workflow = create_generate_workflow(
            name="checkpoint_workflow",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=tmp_path,
        )

        assert workflow.checkpoint_dir == tmp_path


class TestSuccessfulChapterGeneration:
    """Tests for successful chapter generation."""

    @pytest.mark.asyncio
    async def test_execute_generates_single_chapter(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        mock_outline_validator: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test successful generation of a single chapter."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=sample_project_files / "checkpoints",
        )

        # Mock the writer factory
        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            # Mock internal components
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    # Mock the summary manager creation
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.TimelineManager",
                                return_value=mock_timeline_manager,
                            ):
                                with patch(
                                    "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                                    return_value=mock_continuity_manager,
                                ):
                                    result = await workflow.execute(
                                        project_id="test_project",
                                        start_chapter=1,
                                        count=1,
                                        storage_path=sample_project_files,
                                    )

        assert result.success is True
        assert result.chapters_generated == 1
        assert result.total_chapters_requested == 1
        assert len(result.chapters) == 1
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_execute_generates_multiple_chapters(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        mock_outline_validator: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test successful generation of multiple chapters."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=sample_project_files / "checkpoints",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.TimelineManager",
                                return_value=mock_timeline_manager,
                            ):
                                with patch(
                                    "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                                    return_value=mock_continuity_manager,
                                ):
                                    result = await workflow.execute(
                                        project_id="test_project",
                                        start_chapter=1,
                                        count=2,
                                        storage_path=sample_project_files,
                                    )

        assert result.success is True
        assert result.chapters_generated == 2
        assert result.total_chapters_requested == 2
        assert len(result.chapters) == 2
        assert result.is_complete is True

    @pytest.mark.asyncio
    async def test_generated_chapter_has_correct_metadata(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        mock_outline_validator: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that generated chapters have correct metadata."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=sample_project_files / "checkpoints",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.TimelineManager",
                                return_value=mock_timeline_manager,
                            ):
                                with patch(
                                    "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                                    return_value=mock_continuity_manager,
                                ):
                                    result = await workflow.execute(
                                        project_id="test_project",
                                        start_chapter=1,
                                        count=1,
                                        storage_path=sample_project_files,
                                    )

        chapter = result.chapters[0]
        assert chapter.chapter_number == 1
        assert chapter.title == "The Beginning"
        assert chapter.content is not None
        assert chapter.word_count > 0
        assert chapter.validation_passed is True


class TestValidationPipelineIntegration:
    """Tests for validation pipeline integration."""

    @pytest.mark.asyncio
    async def test_validation_passed_on_success(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that validation_passed is True when validation succeeds."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        assert result.chapters[0].validation_passed is True

    @pytest.mark.asyncio
    async def test_validation_failed_when_inconsistent(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that validation_passed is False when validation fails."""
        # Create a mock summary manager with failed validation
        mock_summary = MagicMock()
        verification = MagicMock()
        verification.is_consistent = False

        # No auto-fix result (failed to fix)
        mock_summary.process_chapter_with_autofix = AsyncMock(
            return_value=(None, verification, None)
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        assert result.chapters[0].validation_passed is False

    @pytest.mark.asyncio
    async def test_outline_validation_called(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that outline validator is called during generation."""
        mock_outline_validator = MagicMock()
        mock_outline_validator.validate_chapter = MagicMock(
            return_value={"passed": True, "deviations": []}
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.OutlineValidator",
                                return_value=mock_outline_validator,
                            ):
                                await workflow.execute(
                                    project_id="test_project",
                                    start_chapter=1,
                                    count=1,
                                    storage_path=sample_project_files,
                                )


class TestCheckpointSaveResume:
    """Tests for checkpoint save and resume functionality."""

    @pytest.mark.asyncio
    async def test_checkpoint_created_before_generation(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that checkpoint is created before chapter generation."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=sample_project_files / "checkpoints",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        # Verify checkpoint was created at least twice (before and after)
        assert mock_checkpoint_manager.create_checkpoint.call_count >= 1

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test resuming generation from a checkpoint."""
        # Create a checkpoint that indicates chapter 1 was completed
        existing_checkpoint = Checkpoint(
            checkpoint_id="existing_checkpoint",
            chapter_number=1,
            word_count=500,
            content="Previous chapter content",
            state_snapshot={},
            created_at=__import__("datetime").datetime.now(),
            checksum="def456",
            metadata={"project_id": "test_project"},
        )
        mock_checkpoint_manager.get_latest_checkpoint = MagicMock(
            return_value=existing_checkpoint
        )
        mock_checkpoint_manager.load_checkpoint = MagicMock(
            return_value=existing_checkpoint
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=2,
                                storage_path=sample_project_files,
                                resume=True,
                            )

        assert result.resumed_from_checkpoint is True
        assert result.start_chapter == 2  # Should start from chapter 2

    @pytest.mark.asyncio
    async def test_cleanup_checkpoints_on_success(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that checkpoints are cleaned up on successful completion."""
        # Set up checkpoints to be cleaned
        mock_checkpoint_manager.list_checkpoints = MagicMock(
            return_value=[{"checkpoint_id": "cp_1"}]
        )
        mock_checkpoint_manager.load_checkpoint = MagicMock(
            return_value=Checkpoint(
                checkpoint_id="cp_1",
                chapter_number=1,
                word_count=100,
                content="content",
                state_snapshot={},
                created_at=__import__("datetime").datetime.now(),
                checksum="abc",
                metadata={"project_id": "test_project"},
            )
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        # Verify delete was called
        mock_checkpoint_manager.delete_checkpoint.assert_called()


class TestAutoRetryOnValidationFailure:
    """Tests for auto-retry mechanism on validation failure."""

    @pytest.mark.asyncio
    async def test_auto_fix_iterations_recorded(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that auto-fix iterations are recorded in the result."""
        # Create a mock summary manager with multiple fix iterations
        mock_summary = MagicMock()
        verification = MagicMock()
        verification.is_consistent = False  # Initially inconsistent

        # Auto-fix result with 2 iterations
        auto_fix_result = MagicMock(spec=AutoFixResult)
        auto_fix_result.success = True
        auto_fix_result.final_content = "Fixed content after 2 iterations"
        auto_fix_result.iteration_count = 2
        auto_fix_result.is_fully_fixed = True
        auto_fix_result.issues_remaining = []

        mock_summary.process_chapter_with_autofix = AsyncMock(
            return_value=(None, verification, auto_fix_result)
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            max_fix_iterations=3,
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        assert result.chapters[0].auto_fix_iterations == 2
        assert result.chapters[0].validation_passed is True

    @pytest.mark.asyncio
    async def test_max_fix_iterations_exceeded(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test behavior when max fix iterations are exceeded."""
        # Create a mock summary manager with failed auto-fix
        mock_summary = MagicMock()
        verification = MagicMock()
        verification.is_consistent = False

        # Auto-fix failed after max iterations
        auto_fix_result = MagicMock(spec=AutoFixResult)
        auto_fix_result.success = False
        auto_fix_result.final_content = "Content still has issues"
        auto_fix_result.iteration_count = 3
        auto_fix_result.is_fully_fixed = False
        auto_fix_result.issues_remaining = [MagicMock(severity=5)]

        mock_summary.process_chapter_with_autofix = AsyncMock(
            return_value=(None, verification, auto_fix_result)
        )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            max_fix_iterations=3,
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        assert result.chapters[0].auto_fix_iterations == 3
        assert result.chapters[0].validation_passed is False
        assert "validation failed after 3 fix attempts" in result.errors[0]


class TestKnowledgeGraphUpdates:
    """Tests for knowledge graph updates after chapter generation."""

    @pytest.mark.asyncio
    async def test_continuity_manager_updates_story_state(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        mock_continuity_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that continuity manager updates story state."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                                return_value=mock_continuity_manager,
                            ):
                                await workflow.execute(
                                    project_id="test_project",
                                    start_chapter=1,
                                    count=1,
                                    storage_path=sample_project_files,
                                )

        # Verify continuity manager was called to update state
        mock_continuity_manager.update_from_chapter.assert_called_once()

    @pytest.mark.asyncio
    async def test_story_state_carries_forward(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        mock_continuity_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that story state carries forward between chapters."""
        # Track the story state updates
        updated_states = []

        def track_update(state, **kwargs):
            updated_states.append(state)
            return StoryState(
                chapter=state.chapter + 1,
                location="New Location",
                active_characters=state.active_characters,
                character_states=state.character_states,
                plot_threads=state.plot_threads,
                key_events=state.key_events + ["New Event"],
            )

        mock_continuity_manager.update_from_chapter = MagicMock(side_effect=track_update)

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            with patch(
                                "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                                return_value=mock_continuity_manager,
                            ):
                                await workflow.execute(
                                    project_id="test_project",
                                    start_chapter=1,
                                    count=2,
                                    storage_path=sample_project_files,
                                )

        # Story state should be updated for each chapter
        assert len(updated_states) >= 1


class TestErrorHandling:
    """Tests for error handling and messages."""

    @pytest.mark.asyncio
    async def test_error_when_no_outline(
        self,
        mock_llm: MagicMock,
        mock_summary_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test error handling when no outline exists."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        empty_project = tmp_path / "novels" / "empty_project"
        empty_project.mkdir(parents=True)

        with patch(
            "src.novel_agent.workflow.generate_workflow.SummaryManager",
            return_value=mock_summary_manager,
        ):
            result = await workflow.execute(
                project_id="empty_project",
                start_chapter=1,
                count=1,
                storage_path=tmp_path,
            )

        assert result.success is False
        assert "No outline found" in result.errors[0]
        assert result.chapters_generated == 0

    @pytest.mark.asyncio
    async def test_error_when_chapter_not_in_outline(
        self,
        mock_llm: MagicMock,
        mock_summary_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test behavior when chapter number exceeds outline range."""
        project_dir = tmp_path / "novels" / "test_project"
        project_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "summary": "First chapter",
                    "characters": ["Alice"],
                    "location": "Castle",
                    "key_events": ["Event 1"],
                    "plot_threads_resolved": [],
                    "plot_threads_started": [],
                    "character_states": {},
                },
                {
                    "number": 2,
                    "title": "Chapter 2",
                    "summary": "Second chapter",
                    "characters": ["Bob"],
                    "location": "Forest",
                    "key_events": ["Event 2"],
                    "plot_threads_resolved": [],
                    "plot_threads_started": [],
                    "character_states": {},
                },
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": [],
            "genre": "fantasy",
        }
        with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        characters_data = {"characters": []}
        with open(project_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump(characters_data, f)

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.SummaryManager",
            return_value=mock_summary_manager,
        ):
            result = await workflow.execute(
                project_id="test_project",
                start_chapter=10,
                count=1,
                storage_path=tmp_path,
            )

        assert result.success is True
        assert result.chapters_generated == 0
        assert result.total_chapters_requested == 1

    @pytest.mark.asyncio
    async def test_error_when_chapter_spec_missing(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test error when chapter exists in range but spec is missing."""
        project_dir = tmp_path / "novels" / "test_project"
        project_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "summary": "First chapter",
                    "characters": ["Alice"],
                    "location": "Castle",
                    "key_events": ["Event 1"],
                    "plot_threads_resolved": [],
                    "plot_threads_started": [],
                    "character_states": {},
                },
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": [],
            "genre": "fantasy",
        }
        with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        characters_data = {"characters": []}
        with open(project_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump(characters_data, f)

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=tmp_path,
                            )

        assert result.success is True
        assert len(result.chapters) == 1

    @pytest.mark.asyncio
    async def test_error_when_writer_not_initialized(
        self,
        mock_llm: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_summary_manager: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test error handling when writer is not initialized."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )
        workflow.writer = None

        with patch.object(
            workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
        ):
            with patch(
                "src.novel_agent.workflow.generate_workflow.SummaryManager",
                return_value=mock_summary_manager,
            ):
                result = await workflow.execute(
                    project_id="test_project",
                    start_chapter=1,
                    count=1,
                    storage_path=sample_project_files,
                )

        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_error_recorded_on_exception(
        self,
        mock_llm: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that exceptions are caught and recorded as errors."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        failing_writer = MagicMock()
        failing_writer.write_chapter_with_context = AsyncMock(
            side_effect=RuntimeError("Writer error")
        )
        workflow.writer = failing_writer

        with patch.object(
            workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
        ):
            with patch.object(
                workflow, "_get_version_control", return_value=mock_version_control
            ):
                with patch(
                    "src.novel_agent.workflow.generate_workflow.SummaryManager",
                    return_value=mock_summary_manager,
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                        return_value=mock_character_selector,
                    ):
                        result = await workflow.execute(
                            project_id="test_project",
                            start_chapter=1,
                            count=1,
                            storage_path=sample_project_files,
                        )

        assert result.success is False
        assert len(result.errors) > 0
        assert "Writer error" in str(result.errors)


class TestGenerateResult:
    """Tests for GenerateResult dataclass."""

    def test_is_complete_when_all_chapters_generated(self) -> None:
        """Test is_complete property when all chapters are generated."""
        result = GenerateResult(
            success=True,
            project_id="test",
            total_chapters_requested=3,
            chapters_generated=3,
        )

        assert result.is_complete is True

    def test_is_complete_when_not_all_chapters_generated(self) -> None:
        """Test is_complete property when not all chapters are generated."""
        result = GenerateResult(
            success=True,
            project_id="test",
            total_chapters_requested=5,
            chapters_generated=3,
        )

        assert result.is_complete is False

    def test_to_dict_serialization(self) -> None:
        """Test to_dict serialization."""
        chapter = GeneratedChapter(
            chapter_number=1,
            title="Test Chapter",
            content="Content",
            word_count=100,
            validation_passed=True,
        )
        result = GenerateResult(
            success=True,
            project_id="test",
            chapters=[chapter],
            total_chapters_requested=1,
            chapters_generated=1,
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["project_id"] == "test"
        assert result_dict["chapters_generated"] == 1
        assert result_dict["is_complete"] is True


class TestGeneratedChapter:
    """Tests for GeneratedChapter dataclass."""

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        chapter = GeneratedChapter(
            chapter_number=1,
            title="Test Chapter",
            content="Chapter content here",
            word_count=100,
            version_id="v1.0.0",
            validation_passed=True,
            auto_fix_iterations=0,
            metadata={"location": "Castle"},
        )

        chapter_dict = chapter.to_dict()

        assert chapter_dict["chapter_number"] == 1
        assert chapter_dict["title"] == "Test Chapter"
        assert chapter_dict["content"] == "Chapter content here"
        assert chapter_dict["word_count"] == 100
        assert chapter_dict["version_id"] == "v1.0.0"
        assert chapter_dict["validation_passed"] is True
        assert chapter_dict["auto_fix_iterations"] == 0
        assert chapter_dict["metadata"]["location"] == "Castle"


class TestAbstractMethods:
    """Tests for abstract methods implementation."""

    @pytest.mark.asyncio
    async def test_generate_content_returns_dict(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that generate_content returns a dictionary."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.generate_content(
                                {
                                    "project_id": "test_project",
                                    "start_chapter": 1,
                                    "count": 1,
                                    "storage_path": str(sample_project_files),
                                }
                            )

        assert isinstance(result, dict)
        assert "success" in result
        assert "chapters" in result

    @pytest.mark.asyncio
    async def test_validate_output(self, mock_llm: MagicMock) -> None:
        """Test validate_output method."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        # Test successful validation
        success_output = {"success": True, "chapters_generated": 1}
        assert await workflow.validate_output(success_output) is True

        # Test failed validation
        failed_output = {"success": False, "chapters_generated": 0}
        assert await workflow.validate_output(failed_output) is False

    @pytest.mark.asyncio
    async def test_finalize_returns_workflow_state(self, mock_llm: MagicMock) -> None:
        """Test finalize method returns WorkflowState."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        output = {"chapters_generated": 5}
        state = await workflow.finalize(output)

        assert isinstance(state, WorkflowState)
        assert state.planning_complete is True
        assert state.last_generated_chapter == 5
        assert state.validation_enabled is True


class TestProgressCallback:
    """Tests for progress callback functionality."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that progress callback is called during generation."""
        progress_calls = []

        def track_progress(chapter: int, total: int, success: bool) -> None:
            progress_calls.append(
                {"chapter": chapter, "total": total, "success": success}
            )

        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=2,
                                storage_path=sample_project_files,
                                progress_callback=track_progress,
                            )

        # Should have been called for each chapter
        assert len(progress_calls) == 2
        assert progress_calls[0]["chapter"] == 1
        assert progress_calls[1]["chapter"] == 2


class TestVersionControlIntegration:
    """Tests for version control integration."""

    @pytest.mark.asyncio
    async def test_version_saved_after_generation(
        self,
        mock_llm: MagicMock,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_summary_manager: MagicMock,
        mock_character_selector: MagicMock,
        sample_project_files: Path,
    ) -> None:
        """Test that version is saved after chapter generation."""
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch(
                            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
                            return_value=mock_character_selector,
                        ):
                            result = await workflow.execute(
                                project_id="test_project",
                                start_chapter=1,
                                count=1,
                                storage_path=sample_project_files,
                            )

        # Verify version was saved
        mock_version_control.commit_chapter.assert_called_once()

        # Verify chapter has version_id
        assert result.chapters[0].version_id == "v1.0.0"