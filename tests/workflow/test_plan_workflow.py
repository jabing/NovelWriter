# tests/workflow/test_plan_workflow.py
"""Tests for PlanWorkflow - orchestrates the planning phase of novel generation."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.novel_agent.agents.base import AgentResult
from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, StudioState
from src.novel_agent.workflow.plan_workflow import (
    CHAPTERS_PER_VOLUME,
    PlanResult,
    PlanWorkflow,
    Volume,
    create_plan_workflow,
)


class TestPlanResult:
    """Tests for PlanResult dataclass."""

    def test_plan_result_default_values(self) -> None:
        """Test PlanResult with default values."""
        result = PlanResult(success=True)
        assert result.success is True
        assert result.data == {}
        assert result.errors == []
        assert result.warnings == []

    def test_plan_result_properties(self) -> None:
        """Test PlanResult property accessors."""
        data = {
            "outline": {"title": "Test Novel"},
            "characters": [{"name": "Alice"}],
            "world": {"name": "Test World"},
            "volumes": [{"volume_number": 1}],
            "timeline": {"events": []},
        }
        result = PlanResult(success=True, data=data)

        assert result.outline == {"title": "Test Novel"}
        assert result.characters == [{"name": "Alice"}]
        assert result.world == {"name": "Test World"}
        assert result.volumes == [{"volume_number": 1}]
        assert result.timeline == {"events": []}

    def test_plan_result_properties_empty(self) -> None:
        """Test PlanResult properties with missing data."""
        result = PlanResult(success=True, data={})

        assert result.outline is None
        assert result.characters == []
        assert result.world is None
        assert result.volumes == []
        assert result.timeline is None


class TestVolume:
    """Tests for Volume dataclass."""

    def test_volume_creation(self) -> None:
        """Test Volume creation."""
        chapters = [{"chapter": 1, "title": "Chapter 1"}]
        volume = Volume(
            volume_number=1,
            title="Volume 1: The Beginning",
            chapters=chapters,
            start_chapter=1,
            end_chapter=10,
            summary="The story begins.",
        )

        assert volume.volume_number == 1
        assert volume.title == "Volume 1: The Beginning"
        assert volume.chapters == chapters
        assert volume.start_chapter == 1
        assert volume.end_chapter == 10
        assert volume.summary == "The story begins."

    def test_volume_to_dict(self) -> None:
        """Test Volume serialization."""
        volume = Volume(
            volume_number=2,
            title="Volume 2",
            chapters=[],
            start_chapter=11,
            end_chapter=20,
            summary="Continuation",
        )

        result = volume.to_dict()

        assert result["volume_number"] == 2
        assert result["title"] == "Volume 2"
        assert result["chapters"] == []
        assert result["start_chapter"] == 11
        assert result["end_chapter"] == 20
        assert result["summary"] == "Continuation"


class TestPlanWorkflowInit:
    """Tests for PlanWorkflow initialization."""

    def test_init_with_defaults(self, mock_llm: MagicMock) -> None:
        """Test PlanWorkflow initialization with default values."""
        workflow = PlanWorkflow(llm=mock_llm)

        assert workflow.llm == mock_llm
        assert workflow.memory is None
        assert workflow.chapters_per_volume == CHAPTERS_PER_VOLUME
        assert workflow.plot_agent is not None
        assert workflow.character_agent is not None
        assert workflow.worldbuilding_agent is not None

    def test_init_with_custom_chapters_per_volume(self, mock_llm: MagicMock) -> None:
        """Test PlanWorkflow with custom chapters per volume."""
        workflow = PlanWorkflow(llm=mock_llm, chapters_per_volume=5)

        assert workflow.chapters_per_volume == 5

    def test_init_with_memory(self, mock_llm: MagicMock) -> None:
        """Test PlanWorkflow with memory system."""
        mock_memory = MagicMock()
        workflow = PlanWorkflow(llm=mock_llm, memory=mock_memory)

        assert workflow.memory == mock_memory

    def test_create_plan_workflow_factory(self, mock_llm: MagicMock) -> None:
        """Test create_plan_workflow factory function."""
        workflow = create_plan_workflow(llm=mock_llm)

        assert isinstance(workflow, PlanWorkflow)
        assert workflow.llm == mock_llm


class TestPlanWorkflowExecute:
    """Tests for PlanWorkflow.execute method."""

    @pytest.fixture
    def mock_studio_state(self, mock_project: NovelProject) -> MagicMock:
        """Create a mock studio state."""
        state = MagicMock(spec=StudioState)
        state.get_project.return_value = mock_project
        state.update_project = MagicMock()
        return state

    @pytest.fixture
    def mock_outline_result(self) -> AgentResult:
        """Create a mock outline result from PlotAgent."""
        return AgentResult(
            success=True,
            data={
                "outline": {
                    "title": "Test Novel",
                    "genre": "science_fiction",
                    "main_arc": {
                        "acts": [
                            {
                                "name": "Act 1",
                                "chapters": "1-5",
                                "summary": "Setup",
                                "key_events": ["Event 1"],
                            },
                            {
                                "name": "Act 2",
                                "chapters": "6-10",
                                "summary": "Conflict",
                                "key_events": ["Event 2"],
                            },
                        ],
                        "climax": "Big battle",
                        "resolution": "Victory",
                    },
                    "chapters": [
                        {"chapter": i, "title": f"Chapter {i}", "summary": f"Summary {i}"}
                        for i in range(1, 21)
                    ],
                    "total_chapters": 20,
                }
            },
        )

    @pytest.fixture
    def mock_character_result(self) -> AgentResult:
        """Create a mock character result from CharacterAgent."""
        return AgentResult(
            success=True,
            data={
                "characters": [
                    {"id": "char_001", "name": "Alice", "role": "protagonist"},
                    {"id": "char_002", "name": "Bob", "role": "antagonist"},
                ],
                "relationships": [
                    {"character1": "Alice", "character2": "Bob", "relationship_type": "rivals"}
                ],
            },
        )

    @pytest.fixture
    def mock_world_result(self) -> AgentResult:
        """Create a mock world result from WorldbuildingAgent."""
        return AgentResult(
            success=True,
            data={
                "world": {
                    "name": "Test World",
                    "genre": "science_fiction",
                    "rules": {},
                    "locations": [],
                    "society": {},
                    "history": {},
                }
            },
        )

    @pytest.mark.asyncio
    async def test_execute_successful_planning(
        self,
        mock_llm: MagicMock,
        mock_studio_state: MagicMock,
        mock_outline_result: AgentResult,
        mock_character_result: AgentResult,
        mock_world_result: AgentResult,
        tmp_project_dir: Path,
    ) -> None:
        """Test successful planning workflow execution."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Mock agents
        workflow.plot_agent.execute = AsyncMock(return_value=mock_outline_result)
        workflow.character_agent.execute = AsyncMock(return_value=mock_character_result)
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=mock_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio_state,
        ):
            result = await workflow.execute("test_project_001")

        assert result.success is True
        assert result.outline is not None
        assert len(result.characters) == 2
        assert result.world is not None
        assert len(result.volumes) > 0
        assert result.timeline is not None
        assert len(result.errors) == 0

        # Verify project status was updated
        mock_studio_state.update_project.assert_called_once()
        updated_project = mock_studio_state.update_project.call_args[0][0]
        assert updated_project.status == ProjectStatus.WRITING

    @pytest.mark.asyncio
    async def test_execute_project_not_found(
        self,
        mock_llm: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test execute with non-existent project."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        mock_state = MagicMock(spec=StudioState)
        mock_state.get_project.return_value = None

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_state,
        ):
            result = await workflow.execute("nonexistent_project")

        assert result.success is False
        assert len(result.errors) == 1
        assert "not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_outline_failure(
        self,
        mock_llm: MagicMock,
        mock_studio_state: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test execute when outline generation fails."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Mock PlotAgent to fail
        failed_outline_result = AgentResult(
            success=False,
            data={},
            errors=["Failed to generate outline"],
        )
        workflow.plot_agent.execute = AsyncMock(return_value=failed_outline_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio_state,
        ):
            result = await workflow.execute("test_project_001")

        assert result.success is False
        assert "Failed to generate outline" in result.errors

    @pytest.mark.asyncio
    async def test_execute_character_failure_continues(
        self,
        mock_llm: MagicMock,
        mock_studio_state: MagicMock,
        mock_outline_result: AgentResult,
        mock_world_result: AgentResult,
        tmp_project_dir: Path,
    ) -> None:
        """Test execute continues when character creation fails (partial failure)."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Mock agents - CharacterAgent fails
        workflow.plot_agent.execute = AsyncMock(return_value=mock_outline_result)
        workflow.character_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                data={},
                errors=["Character creation failed"],
            )
        )
        workflow.worldbuilding_agent.execute = AsyncMock(return_value=mock_world_result)

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio_state,
        ):
            result = await workflow.execute("test_project_001")

        # Workflow should still succeed with warnings
        assert result.success is True
        assert len(result.characters) == 0  # Empty characters due to failure
        assert any("Character creation failed" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_execute_world_failure_continues(
        self,
        mock_llm: MagicMock,
        mock_studio_state: MagicMock,
        mock_outline_result: AgentResult,
        mock_character_result: AgentResult,
        tmp_project_dir: Path,
    ) -> None:
        """Test execute continues when worldbuilding fails (partial failure)."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Mock agents - WorldbuildingAgent fails
        workflow.plot_agent.execute = AsyncMock(return_value=mock_outline_result)
        workflow.character_agent.execute = AsyncMock(return_value=mock_character_result)
        workflow.worldbuilding_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                data={},
                errors=["Worldbuilding failed"],
            )
        )

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio_state,
        ):
            result = await workflow.execute("test_project_001")

        # Workflow should still succeed with warnings
        assert result.success is True
        assert result.world == {}  # Empty world due to failure
        assert any("Worldbuilding failed" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_execute_exception_handling(
        self,
        mock_llm: MagicMock,
        mock_studio_state: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test execute handles unexpected exceptions."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Mock PlotAgent to raise exception
        workflow.plot_agent.execute = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_studio_state,
        ):
            result = await workflow.execute("test_project_001")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Outline generation error" in result.errors[0]
        assert "Unexpected error" in result.errors[0]


class TestVolumeGeneration:
    """Tests for volume generation logic."""

    @pytest.fixture
    def workflow(self, mock_llm: MagicMock) -> PlanWorkflow:
        """Create a PlanWorkflow instance."""
        return PlanWorkflow(llm=mock_llm)

    def test_generate_volumes_basic(self, workflow: PlanWorkflow) -> None:
        """Test basic volume generation."""
        outline = {
            "chapters": [
                {"chapter": i, "title": f"Chapter {i}"} for i in range(1, 26)
            ]
        }
        total_chapters = 25

        volumes = workflow._generate_volumes(outline, total_chapters)

        assert len(volumes) == 3  # 25 chapters / 10 per volume = 3 volumes
        assert volumes[0].start_chapter == 1
        assert volumes[0].end_chapter == 10
        assert volumes[1].start_chapter == 11
        assert volumes[1].end_chapter == 20
        assert volumes[2].start_chapter == 21
        assert volumes[2].end_chapter == 25

    def test_generate_volumes_exact_multiple(self, workflow: PlanWorkflow) -> None:
        """Test volume generation when chapters are exact multiple."""
        outline = {
            "chapters": [
                {"chapter": i, "title": f"Chapter {i}"} for i in range(1, 21)
            ]
        }
        total_chapters = 20

        volumes = workflow._generate_volumes(outline, total_chapters)

        assert len(volumes) == 2
        assert volumes[0].end_chapter == 10
        assert volumes[1].end_chapter == 20

    def test_generate_volumes_single_chapter(self, workflow: PlanWorkflow) -> None:
        """Test volume generation with single chapter."""
        outline = {"chapters": [{"chapter": 1, "title": "Chapter 1"}]}
        total_chapters = 1

        volumes = workflow._generate_volumes(outline, total_chapters)

        assert len(volumes) == 1
        assert volumes[0].start_chapter == 1
        assert volumes[0].end_chapter == 1

    def test_generate_volumes_no_chapters_in_outline(self, workflow: PlanWorkflow) -> None:
        """Test volume generation when outline has no chapters."""
        outline: dict = {"chapters": []}
        total_chapters = 30

        volumes = workflow._generate_volumes(outline, total_chapters)

        # Should create placeholder volumes
        assert len(volumes) == 3  # 30 / 10 = 3
        assert volumes[0].title == "Volume 1"
        assert volumes[0].chapters == []

    def test_generate_volumes_custom_chapters_per_volume(self, mock_llm: MagicMock) -> None:
        """Test volume generation with custom chapters per volume."""
        workflow = PlanWorkflow(llm=mock_llm, chapters_per_volume=5)

        outline = {
            "chapters": [
                {"chapter": i, "title": f"Chapter {i}"} for i in range(1, 16)
            ]
        }
        total_chapters = 15

        volumes = workflow._generate_volumes(outline, total_chapters)

        assert len(volumes) == 3  # 15 / 5 = 3 volumes
        assert volumes[0].end_chapter == 5
        assert volumes[1].start_chapter == 6

    def test_generate_volume_title_with_key_events(self, workflow: PlanWorkflow) -> None:
        """Test volume title generation with key events."""
        chapters = [
            {"chapter": 1, "key_events": ["The Discovery"]},
            {"chapter": 2, "key_events": ["The Journey"]},
        ]

        title = workflow._generate_volume_title(chapters, 1)

        # Should include key event in title
        assert "Volume 1" in title

    def test_generate_volume_title_empty_chapters(self, workflow: PlanWorkflow) -> None:
        """Test volume title generation with empty chapters."""
        title = workflow._generate_volume_title([], 1)

        assert title == "Volume 1"

    def test_generate_volume_summary_with_summaries(self, workflow: PlanWorkflow) -> None:
        """Test volume summary generation with chapter summaries."""
        chapters = [
            {"chapter": 1, "summary": "The hero begins their journey."},
            {"chapter": 2, "summary": "They meet an unexpected ally."},
        ]

        summary = workflow._generate_volume_summary(chapters)

        assert "journey" in summary.lower()

    def test_generate_volume_summary_empty_chapters(self, workflow: PlanWorkflow) -> None:
        """Test volume summary generation with no chapter summaries."""
        chapters = [{"chapter": 1}, {"chapter": 2}]

        summary = workflow._generate_volume_summary(chapters)

        assert "chapters" in summary.lower()


class TestProjectDirectoryManagement:
    """Tests for project directory management."""

    @pytest.mark.asyncio
    async def test_ensure_project_dir_creates_structure(
        self, mock_llm: MagicMock, tmp_project_dir: Path
    ) -> None:
        """Test that _ensure_project_dir creates proper directory structure."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        project_dir = workflow._ensure_project_dir("new_project")

        assert project_dir.exists()
        assert (project_dir / "outline").exists()
        assert (project_dir / "characters").exists()
        assert (project_dir / "world").exists()
        assert (project_dir / "volumes").exists()
        assert (project_dir / "timeline").exists()


class TestArtifactSaving:
    """Tests for saving planning artifacts."""

    @pytest.mark.asyncio
    async def test_save_artifacts(
        self, mock_llm: MagicMock, tmp_project_dir: Path
    ) -> None:
        """Test that _save_artifacts saves all files correctly."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        project_dir = workflow._ensure_project_dir("test_project")

        outline = {"title": "Test Novel", "chapters": []}
        characters = [{"id": "char_001", "name": "Alice"}]
        relationships = [{"character1": "Alice", "character2": "Bob"}]
        world = {"name": "Test World"}
        volumes = [
            Volume(
                volume_number=1,
                title="Volume 1",
                chapters=[],
                start_chapter=1,
                end_chapter=10,
                summary="Test summary",
            )
        ]
        timeline = {"events": []}

        await workflow._save_artifacts(
            project_dir,
            outline=outline,
            characters=characters,
            relationships=relationships,
            world=world,
            volumes=volumes,
            timeline=timeline,
        )

        # Check all files were created
        assert (project_dir / "outline" / "main_outline.json").exists()
        assert (project_dir / "characters" / "characters.json").exists()
        assert (project_dir / "characters" / "relationships.json").exists()
        assert (project_dir / "world" / "world_settings.json").exists()
        assert (project_dir / "volumes" / "volumes.json").exists()
        assert (project_dir / "volumes" / "volume_01.json").exists()
        assert (project_dir / "timeline" / "timeline_summary.json").exists()
        assert (project_dir / "planning_metadata.json").exists()

        # Verify content
        with open(project_dir / "outline" / "main_outline.json") as f:
            saved_outline = json.load(f)
        assert saved_outline["title"] == "Test Novel"

        with open(project_dir / "characters" / "characters.json") as f:
            saved_characters = json.load(f)
        assert len(saved_characters) == 1
        assert saved_characters[0]["name"] == "Alice"


class TestTimelineInitialization:
    """Tests for timeline initialization."""

    @pytest.mark.asyncio
    async def test_initialize_timeline(
        self, mock_llm: MagicMock, tmp_project_dir: Path
    ) -> None:
        """Test timeline initialization with story events."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        project_dir = workflow._ensure_project_dir("test_project")

        outline = {
            "main_arc": {
                "acts": [
                    {
                        "name": "Act 1: Discovery",
                        "chapters": "1-10",
                        "summary": "The beginning",
                        "key_events": ["The Call", "First Challenge"],
                    },
                    {
                        "name": "Act 2: Journey",
                        "chapters": "11-20",
                        "summary": "The adventure",
                        "key_events": ["The Trial", "The Revelation"],
                    },
                ],
                "climax": "Final Battle",
                "resolution": "Victory and Peace",
            }
        }

        timeline_manager = await workflow._initialize_timeline(
            "test_project", outline, project_dir
        )

        # Check events were added
        timeline_data = timeline_manager.export_to_dict()
        assert len(timeline_data.get("events", [])) > 0


class TestStateUpdates:
    """Tests for project state updates."""

    @pytest.mark.asyncio
    async def test_project_status_updated_to_writing(
        self,
        mock_llm: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test that project status is updated to WRITING after planning."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        # Create mock project and state
        mock_project = NovelProject(
            id="test_project_001",
            title="Test Novel",
            genre="science_fiction",
            status=ProjectStatus.PLANNING,
            target_chapters=10,
        )
        mock_state = MagicMock(spec=StudioState)
        mock_state.get_project.return_value = mock_project
        mock_state.update_project = MagicMock()

        # Mock agents to return success
        workflow.plot_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=True,
                data={"outline": {"title": "Test", "chapters": [], "main_arc": {}}},
            )
        )
        workflow.character_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=True,
                data={"characters": [], "relationships": []},
            )
        )
        workflow.worldbuilding_agent.execute = AsyncMock(
            return_value=AgentResult(success=True, data={"world": {}})
        )

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_state,
        ):
            result = await workflow.execute("test_project_001")

        assert result.success is True
        mock_state.update_project.assert_called_once()

        # Verify the project was updated with WRITING status
        updated_project = mock_state.update_project.call_args[0][0]
        assert updated_project.status == ProjectStatus.WRITING


class TestErrorMessages:
    """Tests for error message handling."""

    @pytest.mark.asyncio
    async def test_error_message_for_missing_project(
        self,
        mock_llm: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test error message when project is not found."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        mock_state = MagicMock(spec=StudioState)
        mock_state.get_project.return_value = None

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_state,
        ):
            result = await workflow.execute("missing_project")

        assert result.success is False
        assert len(result.errors) == 1
        assert "missing_project" in result.errors[0]
        assert "not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_multiple_errors_collected(
        self,
        mock_llm: MagicMock,
        tmp_project_dir: Path,
    ) -> None:
        """Test that multiple errors are properly collected."""
        workflow = PlanWorkflow(llm=mock_llm, data_dir=tmp_project_dir.parent)

        mock_project = NovelProject(
            id="test_project",
            title="Test",
            genre="fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_state = MagicMock(spec=StudioState)
        mock_state.get_project.return_value = mock_project

        # Mock PlotAgent to fail with multiple errors
        workflow.plot_agent.execute = AsyncMock(
            return_value=AgentResult(
                success=False,
                data={},
                errors=["Error 1: Invalid genre", "Error 2: Missing premise"],
            )
        )

        with patch(
            "src.novel_agent.workflow.plan_workflow.get_studio_state",
            return_value=mock_state,
        ):
            result = await workflow.execute("test_project")

        assert result.success is False
        assert len(result.errors) == 2
        assert "Error 1: Invalid genre" in result.errors
        assert "Error 2: Missing premise" in result.errors