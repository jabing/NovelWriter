# tests/workflow/test_integration.py
"""Integration tests for end-to-end workflow: create → plan → generate.

This module tests the complete novel generation workflow including:
- Full pipeline from project creation to chapter generation
- Resume functionality across sessions
- State persistence and recovery
- Integration between all 6 core modules:
  1. PlotAgent (outline generation)
  2. CharacterAgent (character creation)
  3. WorldbuildingAgent (world building)
  4. TimelineManager (story timeline)
  5. Writer (chapter writing)
  6. Validation pipeline (continuity, consistency)
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.novel_agent.agents.base import AgentResult
from src.novel_agent.novel.auto_fixer import AutoFixResult
from src.novel_agent.novel.checkpointing import Checkpoint
from src.novel_agent.novel.consistency_verifier import VerificationResult
from src.novel_agent.novel.continuity import StoryState
from src.novel_agent.novel.summaries import ChapterSummary
from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, StudioState
from src.novel_agent.workflow.generate_workflow import (
    ChapterGenerateWorkflow,
    GenerateResult,
    create_generate_workflow,
)
from src.novel_agent.workflow.plan_workflow import (
    PlanResult,
    PlanWorkflow,
    create_plan_workflow,
)
from src.novel_agent.workflow.state import WorkflowState


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance for testing."""
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=MagicMock(content="Generated content from LLM"))
    llm.generate_with_system = AsyncMock(
        return_value=MagicMock(content="System-generated content from LLM")
    )
    llm.name = "mock_test_llm"
    return llm


@pytest.fixture
def integration_project():
    """Create a realistic project for integration testing."""
    return NovelProject(
        id="integration_test_001",
        title="The Chronicles of Integration",
        genre="fantasy",
        language="en",
        status=ProjectStatus.PLANNING,
        premise="A young wizard must save the realm from an ancient evil.",
        themes=["courage", "friendship", "sacrifice"],
        target_chapters=20,
        completed_chapters=0,
        target_words=50000,
        story_structure="heros_journey",
        tone="balanced",
    )


@pytest.fixture
def realistic_outline_result():
    """Create a realistic outline result from PlotAgent."""
    return AgentResult(
        success=True,
        data={
            "outline": {
                "title": "The Chronicles of Integration",
                "genre": "fantasy",
                "premise": "A young wizard must save the realm from an ancient evil.",
                "main_arc": {
                    "acts": [
                        {
                            "name": "Act 1: The Awakening",
                            "chapters": "1-5",
                            "summary": "The hero discovers their hidden powers.",
                            "key_events": [
                                "Discovery of magical ability",
                                "Meeting the mentor",
                                "First test of courage",
                            ],
                        },
                        {
                            "name": "Act 2: The Journey",
                            "chapters": "6-15",
                            "summary": "The hero gathers allies and faces challenges.",
                            "key_events": [
                                "Gathering the fellowship",
                                "Crossing the threshold",
                                "The dark night of the soul",
                            ],
                        },
                        {
                            "name": "Act 3: The Resolution",
                            "chapters": "16-20",
                            "summary": "The final confrontation and aftermath.",
                            "key_events": [
                                "The final battle",
                                "Sacrifice for the greater good",
                                "Return changed",
                            ],
                        },
                    ],
                    "climax": "The hero confronts the ancient evil in an epic battle.",
                    "resolution": "Peace is restored, but the hero is forever changed.",
                },
                "chapters": [
                    {
                        "chapter": i,
                        "title": f"Chapter {i}: {'The Beginning' if i == 1 else f'Event {i}'}",
                        "summary": f"Summary for chapter {i}",
                        "characters": ["Hero", "Mentor"] if i <= 5 else ["Hero", "Ally"],
                        "location": "Kingdom" if i <= 10 else "Dark Lands",
                        "key_events": [f"Event {i}"],
                    }
                    for i in range(1, 21)
                ],
                "total_chapters": 20,
            }
        },
    )


@pytest.fixture
def realistic_character_result():
    """Create a realistic character result from CharacterAgent."""
    return AgentResult(
        success=True,
        data={
            "characters": [
                {
                    "id": "char_hero",
                    "name": "Aria",
                    "role": "protagonist",
                    "bio": "A young orphan who discovers she has powerful magic.",
                    "persona": "Brave, curious, and fiercely loyal to friends.",
                    "current_status": "alive",
                    "relationships": {"Mentor Marcus": "student"},
                },
                {
                    "id": "char_mentor",
                    "name": "Marcus",
                    "role": "mentor",
                    "bio": "An aged wizard who guides the protagonist.",
                    "persona": "Wise, patient, and haunted by past failures.",
                    "current_status": "alive",
                    "relationships": {"Aria": "mentor"},
                },
                {
                    "id": "char_ally",
                    "name": "Theron",
                    "role": "supporting",
                    "bio": "A skilled warrior who joins the quest.",
                    "persona": "Stoic, honorable, and secretly seeks redemption.",
                    "current_status": "alive",
                    "relationships": {"Aria": "friend"},
                },
                {
                    "id": "char_villain",
                    "name": "Lord Vexar",
                    "role": "antagonist",
                    "bio": "An ancient evil sorcerer seeking to plunge the world into darkness.",
                    "persona": "Cunning, patient, and utterly ruthless.",
                    "current_status": "alive",
                    "relationships": {"Aria": "enemy"},
                },
            ],
            "relationships": [
                {"character1": "Aria", "character2": "Marcus", "relationship_type": "mentor-student"},
                {"character1": "Aria", "character2": "Theron", "relationship_type": "allies"},
                {"character1": "Aria", "character2": "Lord Vexar", "relationship_type": "enemies"},
            ],
        },
    )


@pytest.fixture
def realistic_world_result():
    """Create a realistic world result from WorldbuildingAgent."""
    return AgentResult(
        success=True,
        data={
            "world": {
                "name": "Eldoria",
                "genre": "fantasy",
                "magic_system": {
                    "name": "Elemental Weaving",
                    "rules": "Magic is drawn from the four elements",
                    "limitations": "Overuse leads to corruption",
                },
                "locations": [
                    {"name": "Crystal Spire Academy", "type": "school", "importance": "major"},
                    {"name": "Shadowfell Mountains", "type": "wilderness", "importance": "major"},
                    {"name": "Golden City of Valoria", "type": "city", "importance": "major"},
                ],
                "society": {
                    "government": "Magical Council",
                    "culture": "Magic users are respected but feared",
                },
                "history": {
                    "ancient_war": "The War of Shadows 1000 years ago",
                    "current_era": "Age of Fragile Peace",
                },
            }
        },
    )


@pytest.fixture
def mock_writer():
    """Create a mock writer for testing."""
    writer = MagicMock()
    writer.write_chapter_with_context = AsyncMock(
        return_value="""# Chapter 1: The Awakening

Aria stood at the edge of the Crystal Spire, watching the sun set over the Golden City of Valoria. She had always known she was different, but today had changed everything.

The ancient tome had chosen her. Its pages, written in a language she somehow understood, spoke of elemental weaving—a magic long thought lost to time.

"You have a gift, young one," Master Marcus said, appearing beside her. "But with great power comes great responsibility."

The wind whispered secrets of a coming darkness, and Aria knew her life would never be the same."""
    )
    writer.GENRE = "fantasy"
    return writer


@pytest.fixture
def mock_summary_manager():
    """Create a mock summary manager with validation support."""
    manager = MagicMock()

    verification = MagicMock(spec=VerificationResult)
    verification.is_consistent = True

    auto_fix_result = MagicMock(spec=AutoFixResult)
    auto_fix_result.success = True
    auto_fix_result.final_content = "Validated and fixed chapter content"
    auto_fix_result.iteration_count = 1
    auto_fix_result.is_fully_fixed = True
    auto_fix_result.issues_remaining = []

    summary = MagicMock(spec=ChapterSummary)
    summary.chapter_number = 1
    summary.title = "The Awakening"

    manager.process_chapter_with_autofix = AsyncMock(
        return_value=(summary, verification, auto_fix_result)
    )
    manager.process_chapter = AsyncMock(return_value=summary)

    return manager


@pytest.fixture
def mock_checkpoint_manager():
    """Create a mock checkpoint manager for testing."""
    manager = MagicMock()
    manager.create_checkpoint = MagicMock(
        return_value=Checkpoint(
            checkpoint_id="test_checkpoint_001",
            chapter_number=1,
            word_count=100,
            content="Test checkpoint content",
            state_snapshot={},
            created_at=datetime.now(),
            checksum="abc123",
            metadata={"project_id": "integration_test_001"},
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
def mock_character_selector():
    """Create a mock character selector."""
    selector = MagicMock()
    selector.select_for_chapter = MagicMock(return_value=([], 10))
    return selector


@pytest.fixture
def mock_continuity_manager():
    """Create a mock continuity manager."""
    manager = MagicMock()
    manager.update_from_chapter = MagicMock(
        return_value=StoryState(
            chapter=1,
            location="Crystal Spire Academy",
            active_characters=["Aria", "Marcus"],
            character_states={"Aria": "awakened"},
            plot_threads=["Main quest"],
            key_events=["Discovery of magic"],
        )
    )
    return manager


@pytest.fixture
def mock_timeline_manager():
    """Create a mock timeline manager."""
    manager = MagicMock()
    manager.validate_temporal_consistency = MagicMock(return_value=[])
    manager.export_to_dict = MagicMock(return_value={"events": []})
    return manager


@pytest.fixture
def integration_test_dir(tmp_path: Path) -> Path:
    """Create a test directory structure for integration tests."""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir(parents=True)
    return test_dir


# =============================================================================
# Test Classes
# =============================================================================


class TestCompleteWorkflowEndToEnd:
    """Test the complete workflow from project creation to chapter generation."""

    @pytest.mark.asyncio
    async def test_create_plan_generate_pipeline(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_character_result: AgentResult,
        realistic_world_result: AgentResult,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test the complete pipeline: create project → plan → generate chapters."""
        from src.novel_agent.novel.character_profile import CharacterProfile, CharacterStatus

        # Setup project directory
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        # Create mock studio state
        mock_studio = MagicMock(spec=StudioState)
        mock_studio.get_project.return_value = integration_project
        mock_studio.update_project = MagicMock()

        # Initialize PlanWorkflow
        plan_workflow = PlanWorkflow(
            llm=mock_llm,
            data_dir=integration_test_dir,
        )

        # Mock agent executions
        plan_workflow.plot_agent.execute = AsyncMock(return_value=realistic_outline_result)
        plan_workflow.character_agent.execute = AsyncMock(return_value=realistic_character_result)
        plan_workflow.worldbuilding_agent.execute = AsyncMock(return_value=realistic_world_result)

        # Execute Plan Workflow
        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio,
        ):
            plan_result = await plan_workflow.execute(integration_project.id)

        # Verify planning succeeded
        assert plan_result.success is True
        assert plan_result.outline is not None
        assert len(plan_result.characters) == 4
        assert plan_result.world is not None
        assert len(plan_result.volumes) > 0

        # Verify artifacts were saved
        assert (project_dir / "outline" / "main_outline.json").exists()
        assert (project_dir / "characters" / "characters.json").exists()
        assert (project_dir / "world" / "world_settings.json").exists()

        # Verify project status updated to WRITING
        mock_studio.update_project.assert_called()
        updated_project = mock_studio.update_project.call_args[0][0]
        assert updated_project.status == ProjectStatus.WRITING

        # Now setup for GenerateWorkflow
        # Create project files for generation
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "The Awakening",
                    "summary": "Aria discovers her magical powers.",
                    "characters": ["Aria", "Marcus"],
                    "location": "Crystal Spire Academy",
                    "key_events": ["Discovery of magic"],
                    "plot_threads_started": ["Main quest"],
                    "plot_threads_resolved": [],
                    "character_states": {"Aria": "awakened"},
                },
                {
                    "number": 2,
                    "title": "The Mentor's Lesson",
                    "summary": "Marcus begins training Aria.",
                    "characters": ["Aria", "Marcus"],
                    "location": "Crystal Spire Academy",
                    "key_events": ["First lesson"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {"Aria": "learning"},
                },
            ],
            "plot_threads": ["Main quest"],
            "timeline": [],
            "characters": ["Aria", "Marcus"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        # Create characters with proper CharacterStatus enum value
        characters_data = {
            "characters": [
                {
                    "name": "Aria",
                    "bio": "A young orphan with magical powers.",
                    "persona": "Brave and curious",
                    "current_status": CharacterStatus.ALIVE.value,  # Use enum value
                    "relationships": {"Marcus": "student"},
                },
                {
                    "name": "Marcus",
                    "bio": "An aged wizard mentor.",
                    "persona": "Wise and patient",
                    "current_status": CharacterStatus.ALIVE.value,  # Use enum value
                    "relationships": {"Aria": "mentor"},
                },
            ]
        }
        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump(characters_data, f)

        world_data = realistic_world_result.data["world"]
        with open(novels_dir / "world_settings.json", "w", encoding="utf-8") as f:
            json.dump(world_data, f)

        # Create mock character selector that returns CharacterProfile objects
        mock_selector = MagicMock()
        aria_profile = CharacterProfile(
            name="Aria",
            bio="A young orphan with magical powers.",
            persona="Brave and curious",
            current_status=CharacterStatus.ALIVE,
            relationships={"Marcus": "student"},
        )
        marcus_profile = CharacterProfile(
            name="Marcus",
            bio="An aged wizard mentor.",
            persona="Wise and patient",
            current_status=CharacterStatus.ALIVE,
            relationships={"Aria": "mentor"},
        )
        mock_selector.select_for_chapter = MagicMock(
            return_value=([aria_profile, marcus_profile], 10)
        )

        generate_workflow = ChapterGenerateWorkflow(
            name="integration_generate",
            llm=mock_llm,
            genre="fantasy",
            checkpoint_dir=integration_test_dir / "checkpoints",
        )

        with patch(
            "src.novel_agent.workflow.generate_workflow.get_writer",
            return_value=mock_writer,
        ):
            with patch.object(
                generate_workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
            ):
                with patch.object(
                    generate_workflow, "_get_version_control", return_value=mock_version_control
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch.object(
                            generate_workflow, "_character_selector", mock_selector
                        ):
                            with patch.object(
                                generate_workflow, "_timeline_manager", mock_timeline_manager
                            ):
                                with patch.object(
                                    generate_workflow, "_continuity_manager", mock_continuity_manager
                                ):
                                    generate_result = await generate_workflow.execute(
                                        project_id=integration_project.id,
                                        start_chapter=1,
                                        count=2,
                                        storage_path=integration_test_dir,
                                    )

        # Verify generation succeeded
        assert generate_result.success is True
        assert generate_result.chapters_generated == 2
        assert len(generate_result.chapters) == 2
        assert generate_result.is_complete is True

        # Verify chapter content
        chapter_1 = generate_result.chapters[0]
        assert chapter_1.chapter_number == 1
        assert chapter_1.title == "The Awakening"
        assert chapter_1.content is not None
        assert chapter_1.word_count > 0
        assert chapter_1.validation_passed is True

    @pytest.mark.asyncio
    async def test_workflow_integration_with_all_modules(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_character_result: AgentResult,
        realistic_world_result: AgentResult,
        integration_test_dir: Path,
    ) -> None:
        """Test that all 6 core modules work together correctly."""
        # Setup
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        mock_studio = MagicMock(spec=StudioState)
        mock_studio.get_project.return_value = integration_project
        mock_studio.update_project = MagicMock()

        workflow = PlanWorkflow(llm=mock_llm, data_dir=integration_test_dir)

        # Track which agents were called
        plot_called = False
        character_called = False
        world_called = False

        async def track_plot_call(data):
            nonlocal plot_called
            plot_called = True
            return realistic_outline_result

        async def track_character_call(data):
            nonlocal character_called
            character_called = True
            return realistic_character_result

        async def track_world_call(data):
            nonlocal world_called
            world_called = True
            return realistic_world_result

        workflow.plot_agent.execute = AsyncMock(side_effect=track_plot_call)
        workflow.character_agent.execute = AsyncMock(side_effect=track_character_call)
        workflow.worldbuilding_agent.execute = AsyncMock(side_effect=track_world_call)

        # Execute
        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio,
        ):
            result = await workflow.execute(integration_project.id)

        # Verify all modules were called
        assert plot_called is True, "PlotAgent was not called"
        assert character_called is True, "CharacterAgent was not called"
        assert world_called is True, "WorldbuildingAgent was not called"

        # Verify integration results
        assert result.success is True

        # Verify volumes were generated from outline
        assert len(result.volumes) >= 2  # 20 chapters / 10 per volume

        # Verify timeline was initialized
        assert result.timeline is not None

        # Verify characters and world data are integrated
        assert len(result.characters) == 4
        assert result.world["name"] == "Eldoria"


class TestResumeAcrossSessions:
    """Test resume functionality for workflows interrupted mid-execution."""

    @pytest.mark.asyncio
    async def test_resume_generation_from_checkpoint(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that generation can resume from a checkpoint after interruption."""
        # Setup project files
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": i,
                    "title": f"Chapter {i}",
                    "summary": f"Summary {i}",
                    "characters": ["Aria"],
                    "location": "Test Location",
                    "key_events": [f"Event {i}"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
                for i in range(1, 6)
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Aria"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        # Create a checkpoint indicating chapter 2 was completed
        existing_checkpoint = Checkpoint(
            checkpoint_id="checkpoint_chapter_2",
            chapter_number=2,
            word_count=500,
            content="Content for chapter 2",
            state_snapshot={},
            created_at=datetime.now(),
            checksum="existing_abc123",
            metadata={"project_id": integration_project.id},
        )
        mock_checkpoint_manager.get_latest_checkpoint = MagicMock(
            return_value=existing_checkpoint
        )
        mock_checkpoint_manager.load_checkpoint = MagicMock(
            return_value=existing_checkpoint
        )

        # Initialize workflow
        workflow = ChapterGenerateWorkflow(
            name="resume_test",
            llm=mock_llm,
            genre="fantasy",
        )

        # Execute with resume=True
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
                                        project_id=integration_project.id,
                                        start_chapter=1,
                                        count=3,
                                        storage_path=integration_test_dir,
                                        resume=True,
                                    )

        # Verify resumption
        assert result.resumed_from_checkpoint is True
        assert result.start_chapter == 3  # Should start from chapter 3 (after checkpoint at 2)

    @pytest.mark.asyncio
    async def test_resume_without_existing_checkpoint(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that workflow starts fresh when no checkpoint exists."""
        # Setup project files
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "summary": "First chapter",
                    "characters": ["Aria"],
                    "location": "Test",
                    "key_events": ["Event"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Aria"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        # No existing checkpoint
        mock_checkpoint_manager.get_latest_checkpoint = MagicMock(return_value=None)

        workflow = ChapterGenerateWorkflow(
            name="no_checkpoint_test",
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
                                project_id=integration_project.id,
                                start_chapter=1,
                                count=1,
                                storage_path=integration_test_dir,
                                resume=True,
                            )

        # Should start fresh from chapter 1
        assert result.resumed_from_checkpoint is False
        assert result.start_chapter == 1


class TestStatePersistence:
    """Test state persistence across workflow execution."""

    @pytest.mark.asyncio
    async def test_project_state_persists_after_planning(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_character_result: AgentResult,
        realistic_world_result: AgentResult,
        integration_test_dir: Path,
    ) -> None:
        """Test that project state is properly saved and can be loaded."""
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        # Use real StudioState for persistence testing
        real_state = StudioState(data_dir=integration_test_dir)
        real_state.add_project(integration_project)

        workflow = PlanWorkflow(llm=mock_llm, data_dir=integration_test_dir)
        workflow.plot_agent.execute = AsyncMock(return_value=realistic_outline_result)
        workflow.character_agent.execute = AsyncMock(return_value=realistic_character_result)
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=realistic_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=real_state,
        ):
            result = await workflow.execute(integration_project.id)

        assert result.success is True

        # Verify project status was updated
        updated_project = real_state.get_project(integration_project.id)
        assert updated_project is not None
        assert updated_project.status == ProjectStatus.WRITING

        # Simulate a new session by creating a new StudioState
        new_state = StudioState(data_dir=integration_test_dir)
        loaded_project = new_state.get_project(integration_project.id)

        # Verify state persisted
        assert loaded_project is not None
        assert loaded_project.title == integration_project.title
        assert loaded_project.status == ProjectStatus.WRITING

    @pytest.mark.asyncio
    async def test_artifact_files_persist_correctly(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_character_result: AgentResult,
        realistic_world_result: AgentResult,
        integration_test_dir: Path,
    ) -> None:
        """Test that all artifact files are correctly saved and loadable."""
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        mock_studio = MagicMock(spec=StudioState)
        mock_studio.get_project.return_value = integration_project
        mock_studio.update_project = MagicMock()

        workflow = PlanWorkflow(llm=mock_llm, data_dir=integration_test_dir)
        workflow.plot_agent.execute = AsyncMock(return_value=realistic_outline_result)
        workflow.character_agent.execute = AsyncMock(return_value=realistic_character_result)
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=realistic_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio,
        ):
            await workflow.execute(integration_project.id)

        # Verify and load each artifact file
        # 1. Outline
        outline_file = project_dir / "outline" / "main_outline.json"
        assert outline_file.exists()
        with open(outline_file, encoding="utf-8") as f:
            outline_data = json.load(f)
        assert outline_data["title"] == "The Chronicles of Integration"
        assert len(outline_data["chapters"]) == 20

        # 2. Characters
        characters_file = project_dir / "characters" / "characters.json"
        assert characters_file.exists()
        with open(characters_file, encoding="utf-8") as f:
            characters_data = json.load(f)
        assert len(characters_data) == 4
        assert characters_data[0]["name"] == "Aria"

        # 3. Relationships
        relationships_file = project_dir / "characters" / "relationships.json"
        assert relationships_file.exists()
        with open(relationships_file, encoding="utf-8") as f:
            relationships_data = json.load(f)
        assert len(relationships_data) == 3

        # 4. World settings
        world_file = project_dir / "world" / "world_settings.json"
        assert world_file.exists()
        with open(world_file, encoding="utf-8") as f:
            world_data = json.load(f)
        assert world_data["name"] == "Eldoria"

        # 5. Volumes
        volumes_file = project_dir / "volumes" / "volumes.json"
        assert volumes_file.exists()
        with open(volumes_file, encoding="utf-8") as f:
            volumes_data = json.load(f)
        assert len(volumes_data) >= 2

        # 6. Timeline
        timeline_file = project_dir / "timeline" / "timeline_summary.json"
        assert timeline_file.exists()

        # 7. Planning metadata
        metadata_file = project_dir / "planning_metadata.json"
        assert metadata_file.exists()
        with open(metadata_file, encoding="utf-8") as f:
            metadata = json.load(f)
        assert "planning_completed_at" in metadata
        assert metadata["total_chapters"] == 20
        assert metadata["total_characters"] == 4

    @pytest.mark.asyncio
    async def test_workflow_state_persistence_in_result(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that WorkflowState is properly returned in GenerateResult."""
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": i,
                    "title": f"Chapter {i}",
                    "summary": f"Summary {i}",
                    "characters": ["Aria"],
                    "location": "Test",
                    "key_events": ["Event"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
                for i in range(1, 4)
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Aria"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        workflow = ChapterGenerateWorkflow(
            name="state_test",
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
                                project_id=integration_project.id,
                                start_chapter=1,
                                count=2,
                                storage_path=integration_test_dir,
                            )

        # Verify WorkflowState
        assert result.workflow_state is not None
        assert result.workflow_state.planning_complete is True
        assert result.workflow_state.last_generated_chapter == 2
        assert result.workflow_state.validation_enabled is True

        # Test serialization
        state_dict = result.workflow_state.to_dict()
        assert state_dict["planning_complete"] is True
        assert state_dict["last_generated_chapter"] == 2

        # Test deserialization
        restored_state = WorkflowState.from_dict(state_dict)
        assert restored_state.planning_complete is True
        assert restored_state.last_generated_chapter == 2


class TestErrorRecoveryIntegration:
    """Test error handling and recovery in the integrated workflow."""

    @pytest.mark.asyncio
    async def test_partial_failure_continues_workflow(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_world_result: AgentResult,
        integration_test_dir: Path,
    ) -> None:
        """Test that workflow continues even when some agents fail."""
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        mock_studio = MagicMock(spec=StudioState)
        mock_studio.get_project.return_value = integration_project
        mock_studio.update_project = MagicMock()

        workflow = PlanWorkflow(llm=mock_llm, data_dir=integration_test_dir)

        # PlotAgent succeeds
        workflow.plot_agent.execute = AsyncMock(return_value=realistic_outline_result)

        # CharacterAgent fails
        workflow.character_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                data={},
                errors=["Character generation failed: API error"],
            )
        )

        # WorldbuildingAgent succeeds
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=realistic_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio,
        ):
            result = await workflow.execute(integration_project.id)

        # Workflow should still succeed with warnings
        assert result.success is True
        assert len(result.characters) == 0  # Empty due to failure
        assert result.world is not None  # World should be present
        assert any("Character" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_validation_failures_recorded_in_result(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that validation failures are properly recorded."""
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "summary": "First chapter",
                    "characters": ["Aria"],
                    "location": "Test",
                    "key_events": ["Event"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Aria"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        # Create summary manager with failed validation
        mock_summary = MagicMock()
        verification = MagicMock()
        verification.is_consistent = False

        auto_fix_result = MagicMock(spec=AutoFixResult)
        auto_fix_result.success = False
        auto_fix_result.final_content = "Content with issues"
        auto_fix_result.iteration_count = 3
        auto_fix_result.is_fully_fixed = False
        auto_fix_result.issues_remaining = [MagicMock(severity=5)]

        mock_summary.process_chapter_with_autofix = AsyncMock(
            return_value=(None, verification, auto_fix_result)
        )

        workflow = ChapterGenerateWorkflow(
            name="validation_test",
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
                                project_id=integration_project.id,
                                start_chapter=1,
                                count=1,
                                storage_path=integration_test_dir,
                            )

        # Chapter should be generated but marked as failed validation
        assert result.success is True
        assert len(result.chapters) == 1
        assert result.chapters[0].validation_passed is False
        assert result.chapters[0].auto_fix_iterations == 3
        assert any("validation failed" in e.lower() for e in result.errors)


class TestModuleIntegrationValidation:
    """Test that all 6 modules integrate correctly."""

    @pytest.mark.asyncio
    async def test_character_data_used_in_chapter_generation(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that character data from planning is used in generation."""
        from src.novel_agent.novel.character_profile import CharacterProfile, CharacterStatus

        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        # Create outline with specific characters
        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "The Test",
                    "summary": "A test chapter",
                    "characters": ["Aria", "Marcus"],
                    "location": "Academy",
                    "key_events": ["Test event"],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Aria", "Marcus"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        # Create character profiles with proper enum values
        characters_data = {
            "characters": [
                {
                    "name": "Aria",
                    "bio": "A powerful young wizard",
                    "persona": "Brave and determined",
                    "current_status": CharacterStatus.ALIVE.value,
                    "relationships": {},
                },
                {
                    "name": "Marcus",
                    "bio": "An aged mentor wizard",
                    "persona": "Wise and patient",
                    "current_status": CharacterStatus.ALIVE.value,
                    "relationships": {},
                },
            ]
        }
        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump(characters_data, f)

        # Track characters passed to writer
        characters_received = []

        async def capture_writer_call(**kwargs):
            if "characters" in kwargs:
                characters_received.extend(kwargs["characters"])
            return "Generated chapter content"

        mock_writer.write_chapter_with_context = AsyncMock(side_effect=capture_writer_call)

        # Create CharacterProfile objects for the selector to return
        aria_profile = CharacterProfile(
            name="Aria",
            bio="A powerful young wizard",
            persona="Brave and determined",
            current_status=CharacterStatus.ALIVE,
        )
        marcus_profile = CharacterProfile(
            name="Marcus",
            bio="An aged mentor wizard",
            persona="Wise and patient",
            current_status=CharacterStatus.ALIVE,
        )

        mock_selector = MagicMock()
        mock_selector.select_for_chapter = MagicMock(
            return_value=([aria_profile, marcus_profile], 10)
        )

        workflow = ChapterGenerateWorkflow(
            name="character_integration_test",
            llm=mock_llm,
            genre="fantasy",
        )
        workflow.writer = mock_writer

        with patch(
            "src.novel_agent.workflow.generate_workflow.CharacterSelector",
            return_value=mock_selector,
        ):
            with patch(
                "src.novel_agent.workflow.generate_workflow.TimelineManager",
                return_value=mock_timeline_manager,
            ):
                with patch(
                    "src.novel_agent.workflow.generate_workflow.ContinuityManager",
                    return_value=mock_continuity_manager,
                ):
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch.object(
                            workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
                        ):
                            with patch.object(
                                workflow, "_get_version_control", return_value=mock_version_control
                            ):
                                await workflow.execute(
                                    project_id=integration_project.id,
                                    start_chapter=1,
                                    count=1,
                                    storage_path=integration_test_dir,
                                )

        # Verify characters were passed to writer
        assert len(characters_received) == 2
        character_names = [c["name"] for c in characters_received]
        assert "Aria" in character_names
        assert "Marcus" in character_names

    @pytest.mark.asyncio
    async def test_world_context_used_in_generation(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        mock_continuity_manager: MagicMock,
        mock_timeline_manager: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that world building data is passed to chapter generation."""
        from src.novel_agent.novel.character_profile import CharacterStatus

        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "summary": "First chapter",
                    "characters": [],
                    "location": "Crystal Spire",
                    "key_events": [],
                    "plot_threads_started": [],
                    "plot_threads_resolved": [],
                    "character_states": {},
                }
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": [],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        # Create world settings
        world_data = {
            "name": "Eldoria",
            "magic_system": {"name": "Elemental Weaving"},
            "locations": [{"name": "Crystal Spire", "type": "academy"}],
        }
        with open(novels_dir / "world_settings.json", "w", encoding="utf-8") as f:
            json.dump(world_data, f)

        # Track world context passed to writer
        world_context_received = {}

        async def capture_world_context(**kwargs):
            if "world_context" in kwargs:
                world_context_received.update(kwargs["world_context"])
            return "Generated content"

        mock_writer.write_chapter_with_context = AsyncMock(side_effect=capture_world_context)

        workflow = ChapterGenerateWorkflow(
            name="world_integration_test",
            llm=mock_llm,
            genre="fantasy",
        )
        workflow.writer = mock_writer

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
                    with patch(
                        "src.novel_agent.workflow.generate_workflow.SummaryManager",
                        return_value=mock_summary_manager,
                    ):
                        with patch.object(
                            workflow, "_get_checkpoint_manager", return_value=mock_checkpoint_manager
                        ):
                            with patch.object(
                                workflow, "_get_version_control", return_value=mock_version_control
                            ):
                                await workflow.execute(
                                    project_id=integration_project.id,
                                    start_chapter=1,
                                    count=1,
                                    storage_path=integration_test_dir,
                                )

        # Verify world context was passed
        assert world_context_received.get("name") == "Eldoria"
        assert "magic_system" in world_context_received

    @pytest.mark.asyncio
    async def test_timeline_events_from_outline_used(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        realistic_outline_result: AgentResult,
        realistic_character_result: AgentResult,
        realistic_world_result: AgentResult,
        integration_test_dir: Path,
    ) -> None:
        """Test that timeline events from outline are initialized correctly."""
        project_dir = integration_test_dir / integration_project.id
        project_dir.mkdir(parents=True)

        mock_studio = MagicMock(spec=StudioState)
        mock_studio.get_project.return_value = integration_project
        mock_studio.update_project = MagicMock()

        workflow = PlanWorkflow(llm=mock_llm, data_dir=integration_test_dir)
        workflow.plot_agent.execute = AsyncMock(return_value=realistic_outline_result)
        workflow.character_agent.execute = AsyncMock(return_value=realistic_character_result)
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=realistic_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio,
        ):
            result = await workflow.execute(integration_project.id)

        # Verify timeline was initialized with events from outline
        assert result.timeline is not None
        events = result.timeline.get("events", [])
        assert len(events) > 0

        # Check that acts are in timeline
        event_types = [e.get("event_type") for e in events]
        assert "act" in event_types


class TestFactoryFunctions:
    """Test factory functions for workflow creation."""

    def test_plan_workflow_factory(self, mock_llm: MagicMock) -> None:
        """Test that create_plan_workflow creates a valid workflow."""
        workflow = create_plan_workflow(llm=mock_llm)

        assert isinstance(workflow, PlanWorkflow)
        assert workflow.llm == mock_llm
        assert workflow.plot_agent is not None
        assert workflow.character_agent is not None
        assert workflow.worldbuilding_agent is not None

    def test_generate_workflow_factory(self, mock_llm: MagicMock) -> None:
        """Test that create_generate_workflow creates a valid workflow."""
        workflow = create_generate_workflow(
            name="factory_test",
            llm=mock_llm,
            genre="fantasy",
        )

        assert isinstance(workflow, ChapterGenerateWorkflow)
        assert workflow.name == "factory_test"
        assert workflow.genre == "fantasy"

    def test_workflow_factory_with_memory(self, mock_llm: MagicMock) -> None:
        """Test that workflow factories accept memory parameter."""
        mock_memory = MagicMock()

        plan_workflow = create_plan_workflow(llm=mock_llm, memory=mock_memory)
        assert plan_workflow.memory == mock_memory


class TestGeneratedChapterMetadata:
    """Test that generated chapters have correct metadata."""

    @pytest.mark.asyncio
    async def test_chapter_metadata_populated(
        self,
        mock_llm: MagicMock,
        integration_project: NovelProject,
        mock_writer: MagicMock,
        mock_summary_manager: MagicMock,
        mock_checkpoint_manager: MagicMock,
        mock_version_control: MagicMock,
        mock_character_selector: MagicMock,
        integration_test_dir: Path,
    ) -> None:
        """Test that chapter metadata is correctly populated."""
        novels_dir = integration_test_dir / "novels" / integration_project.id
        novels_dir.mkdir(parents=True)

        outline_data = {
            "chapters": [
                {
                    "number": 1,
                    "title": "The First Adventure",
                    "summary": "An exciting beginning",
                    "characters": ["Hero"],
                    "location": "The Ancient Temple",
                    "key_events": ["Discovery", "First Challenge"],
                    "plot_threads_started": ["Main Quest"],
                    "plot_threads_resolved": [],
                    "character_states": {"Hero": "determined"},
                }
            ],
            "plot_threads": [],
            "timeline": [],
            "characters": ["Hero"],
            "genre": "fantasy",
        }
        with open(novels_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        with open(novels_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": []}, f)

        workflow = ChapterGenerateWorkflow(
            name="metadata_test",
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
                                project_id=integration_project.id,
                                start_chapter=1,
                                count=1,
                                storage_path=integration_test_dir,
                            )

        chapter = result.chapters[0]

        # Verify all metadata fields
        assert chapter.chapter_number == 1
        assert chapter.title == "The First Adventure"
        assert chapter.content is not None
        assert len(chapter.content) > 0
        assert chapter.word_count > 0
        assert chapter.validation_passed is True
        assert chapter.version_id is not None

        # Verify to_dict serialization
        chapter_dict = chapter.to_dict()
        assert chapter_dict["chapter_number"] == 1
        assert chapter_dict["title"] == "The First Adventure"
        assert "content" in chapter_dict
        assert "word_count" in chapter_dict