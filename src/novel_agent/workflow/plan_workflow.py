# src/agents/plan_workflow.py
"""Plan Workflow - Orchestrates the planning phase of novel generation.

This workflow coordinates:
- PlotAgent: Generate story outline
- CharacterAgent: Create main and supporting characters
- WorldbuildingAgent: Create world settings
- TimelineManager: Initialize story timeline
- Volume generation: Auto-create volumes based on chapter count
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.novel_agent.agents.base import AgentResult
from src.novel_agent.agents.character import CharacterAgent
from src.novel_agent.agents.plot import PlotAgent
from src.novel_agent.agents.worldbuilding import WorldbuildingAgent
from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.memory.base import BaseMemory
from src.novel_agent.novel.timeline_manager import TimelineManager, TimeUnit
from src.novel_agent.studio.core.state import ProjectStatus, get_studio_state
from src.novel_agent.utils.config import get_settings

logger = logging.getLogger(__name__)

# Default chapters per volume
CHAPTERS_PER_VOLUME = 10


@dataclass
class PlanResult:
    """Result of the planning workflow execution."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def outline(self) -> dict[str, Any] | None:
        """Get the generated outline if available."""
        return self.data.get("outline")

    @property
    def characters(self) -> list[dict[str, Any]]:
        """Get the generated characters if available."""
        return self.data.get("characters", [])

    @property
    def world(self) -> dict[str, Any] | None:
        """Get the generated world settings if available."""
        return self.data.get("world")

    @property
    def volumes(self) -> list[dict[str, Any]]:
        """Get the generated volumes if available."""
        return self.data.get("volumes", [])

    @property
    def timeline(self) -> dict[str, Any] | None:
        """Get the timeline data if available."""
        return self.data.get("timeline")


@dataclass
class Volume:
    """A volume containing multiple chapters."""

    volume_number: int
    title: str
    chapters: list[dict[str, Any]]
    start_chapter: int
    end_chapter: int
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert volume to dictionary."""
        return {
            "volume_number": self.volume_number,
            "title": self.title,
            "chapters": self.chapters,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "summary": self.summary,
        }


class PlanWorkflow:
    """Orchestrates the planning phase of novel generation.

    This workflow:
    1. Generates story outline using PlotAgent
    2. Creates characters using CharacterAgent
    3. Creates world settings using WorldbuildingAgent
    4. Auto-generates volumes based on chapter count
    5. Initializes TimelineManager with story timeline
    6. Saves all artifacts to project directory
    7. Updates project status to WRITING
    """

    def __init__(
        self,
        llm: BaseLLM,
        memory: BaseMemory | None = None,
        chapters_per_volume: int = CHAPTERS_PER_VOLUME,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize the planning workflow.

        Args:
            llm: LLM instance for agent generation
            memory: Optional memory system for context storage
            chapters_per_volume: Number of chapters per volume (default: 10)
            data_dir: Base directory for project data
        """
        self.llm = llm
        self.memory = memory
        self.chapters_per_volume = chapters_per_volume

        # Set up data directory
        settings = get_settings()
        self.data_dir = data_dir or Path(settings.openviking_data_dir) / "memory" / "novels"

        # Initialize agents
        self.plot_agent = PlotAgent(name="Plot Agent", llm=llm, memory=memory)
        self.character_agent = CharacterAgent(name="Character Agent", llm=llm, memory=memory)
        self.worldbuilding_agent = WorldbuildingAgent(
            name="Worldbuilding Agent", llm=llm, memory=memory
        )

        logger.info(f"PlanWorkflow initialized with chapters_per_volume={chapters_per_volume}")

    def _get_project_dir(self, project_id: str) -> Path:
        """Get the project directory path.

        Args:
            project_id: Unique project identifier

        Returns:
            Path to the project directory
        """
        return self.data_dir / project_id

    def _ensure_project_dir(self, project_id: str) -> Path:
        """Ensure project directory exists and return its path.

        Args:
            project_id: Unique project identifier

        Returns:
            Path to the project directory
        """
        project_dir = self._get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for artifacts
        (project_dir / "outline").mkdir(exist_ok=True)
        (project_dir / "characters").mkdir(exist_ok=True)
        (project_dir / "world").mkdir(exist_ok=True)
        (project_dir / "volumes").mkdir(exist_ok=True)
        (project_dir / "timeline").mkdir(exist_ok=True)

        return project_dir

    async def execute(self, project_id: str) -> PlanResult:
        """Execute the planning workflow for a project.

        Args:
            project_id: Unique project identifier

        Returns:
            PlanResult with planning artifacts or errors
        """
        logger.info(f"Starting PlanWorkflow for project: {project_id}")
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Get project state
            studio_state = get_studio_state()
            project = studio_state.get_project(project_id)

            if project is None:
                return PlanResult(
                    success=False,
                    errors=[f"Project '{project_id}' not found"],
                )

            # Ensure project directory exists
            project_dir = self._ensure_project_dir(project_id)

            # Build input data for agents
            input_data = {
                "genre": project.genre,
                "language": project.language,
                "target_chapters": project.target_chapters,
                "premise": project.premise,
                "structure": project.story_structure,
                "context": {
                    "title": project.title,
                    "tone": project.tone,
                    "target_audience": project.target_audience,
                    "themes": project.themes,
                    "premise": project.premise,
                    "content_rating": project.content_rating,
                },
            }

            # Step 1: Generate outline using PlotAgent
            logger.info("Step 1: Generating story outline...")
            outline_result = await self._generate_outline(input_data)

            if not outline_result.success:
                errors.extend(outline_result.errors)
                return PlanResult(success=False, errors=errors)

            outline = outline_result.data.get("outline", {})
            warnings.extend(outline_result.warnings)

            # Step 2: Create characters using CharacterAgent
            logger.info("Step 2: Creating characters...")
            character_input = {
                **input_data,
                "outline": outline,
                "num_main_characters": 3,  # Default: protagonist, antagonist, one main
                "num_supporting": 5,  # Default: 5 supporting characters
            }
            character_result = await self._create_characters(character_input)

            if not character_result.success:
                warnings.extend(character_result.errors)
                logger.warning(f"Character creation had issues: {character_result.errors}")
                characters = []
                relationships = []
            else:
                characters = character_result.data.get("characters", [])
                relationships = character_result.data.get("relationships", [])
                warnings.extend(character_result.warnings)

            # Step 3: Create world settings using WorldbuildingAgent
            logger.info("Step 3: Creating world settings...")
            world_input = {
                **input_data,
                "outline": outline,
            }
            world_result = await self._create_world(world_input)

            if not world_result.success:
                warnings.extend(world_result.errors)
                logger.warning(f"Worldbuilding had issues: {world_result.errors}")
                world = {}
            else:
                world = world_result.data.get("world", {})
                warnings.extend(world_result.warnings)

            # Step 4: Generate volumes based on chapter count
            logger.info("Step 4: Generating volumes...")
            volumes = self._generate_volumes(outline, project.target_chapters)

            # Step 5: Initialize TimelineManager
            logger.info("Step 5: Initializing timeline...")
            timeline_manager = await self._initialize_timeline(
                project_id, outline, project_dir
            )
            timeline_data = timeline_manager.export_to_dict()

            # Step 6: Save all artifacts
            logger.info("Step 6: Saving planning artifacts...")
            await self._save_artifacts(
                project_dir,
                outline=outline,
                characters=characters,
                relationships=relationships,
                world=world,
                volumes=volumes,
                timeline=timeline_data,
            )

            # Step 7: Update project status to WRITING
            logger.info("Step 7: Updating project status to WRITING...")
            project.status = ProjectStatus.WRITING
            studio_state.update_project(project)

            # Build result data
            result_data = {
                "outline": outline,
                "characters": characters,
                "relationships": relationships,
                "world": world,
                "volumes": [v.to_dict() if isinstance(v, Volume) else v for v in volumes],
                "timeline": timeline_data,
                "project_id": project_id,
                "project_dir": str(project_dir),
            }

            logger.info(f"PlanWorkflow completed successfully for project: {project_id}")

            return PlanResult(
                success=True,
                data=result_data,
                warnings=warnings,
            )

        except Exception as e:
            error_msg = f"Planning workflow failed: {str(e)}"
            logger.exception(error_msg)
            errors.append(error_msg)
            return PlanResult(success=False, errors=errors)

    async def _generate_outline(self, input_data: dict[str, Any]) -> AgentResult:
        """Generate story outline using PlotAgent.

        Args:
            input_data: Input data for outline generation

        Returns:
            AgentResult with outline data
        """
        try:
            result = await self.plot_agent.execute(input_data)

            if result.success:
                logger.info("Story outline generated successfully")
            else:
                logger.error(f"Failed to generate outline: {result.errors}")

            return result

        except Exception as e:
            logger.exception("Error generating outline")
            return AgentResult(
                success=False,
                data={},
                errors=[f"Outline generation error: {str(e)}"],
            )

    async def _create_characters(self, input_data: dict[str, Any]) -> AgentResult:
        """Create characters using CharacterAgent.

        Args:
            input_data: Input data for character creation

        Returns:
            AgentResult with character data
        """
        try:
            result = await self.character_agent.execute(input_data)

            if result.success:
                char_count = len(result.data.get("characters", []))
                logger.info(f"Created {char_count} characters successfully")
            else:
                logger.error(f"Failed to create characters: {result.errors}")

            return result

        except Exception as e:
            logger.exception("Error creating characters")
            return AgentResult(
                success=False,
                data={},
                errors=[f"Character creation error: {str(e)}"],
            )

    async def _create_world(self, input_data: dict[str, Any]) -> AgentResult:
        """Create world settings using WorldbuildingAgent.

        Args:
            input_data: Input data for worldbuilding

        Returns:
            AgentResult with world data
        """
        try:
            result = await self.worldbuilding_agent.execute(input_data)

            if result.success:
                logger.info("World settings created successfully")
            else:
                logger.error(f"Failed to create world: {result.errors}")

            return result

        except Exception as e:
            logger.exception("Error creating world settings")
            return AgentResult(
                success=False,
                data={},
                errors=[f"Worldbuilding error: {str(e)}"],
            )

    def _generate_volumes(
        self, outline: dict[str, Any], total_chapters: int
    ) -> list[Volume]:
        """Generate volumes based on chapter count.

        Creates volumes with approximately CHAPTERS_PER_VOLUME chapters each.

        Args:
            outline: Story outline with chapter information
            total_chapters: Total number of chapters in the story

        Returns:
            List of Volume objects
        """
        volumes: list[Volume] = []
        chapters = outline.get("chapters", [])

        # If no chapters in outline, create placeholder volumes
        if not chapters:
            logger.warning("No chapters in outline, creating placeholder volumes")
            num_volumes = max(1, total_chapters // self.chapters_per_volume)
            for i in range(num_volumes):
                start = i * self.chapters_per_volume + 1
                end = min((i + 1) * self.chapters_per_volume, total_chapters)
                volumes.append(
                    Volume(
                        volume_number=i + 1,
                        title=f"Volume {i + 1}",
                        chapters=[],
                        start_chapter=start,
                        end_chapter=end,
                        summary=f"Chapters {start}-{end}",
                    )
                )
            return volumes

        # Distribute chapters across volumes
        num_volumes = max(1, (total_chapters + self.chapters_per_volume - 1) // self.chapters_per_volume)

        for vol_num in range(num_volumes):
            start_idx = vol_num * self.chapters_per_volume
            end_idx = min(start_idx + self.chapters_per_volume, len(chapters))

            volume_chapters = chapters[start_idx:end_idx]

            # Generate volume title based on content
            volume_title = self._generate_volume_title(volume_chapters, vol_num + 1)

            # Generate volume summary
            volume_summary = self._generate_volume_summary(volume_chapters)

            volumes.append(
                Volume(
                    volume_number=vol_num + 1,
                    title=volume_title,
                    chapters=volume_chapters,
                    start_chapter=start_idx + 1,
                    end_chapter=end_idx,
                    summary=volume_summary,
                )
            )

        logger.info(f"Generated {len(volumes)} volumes for {total_chapters} chapters")
        return volumes

    def _generate_volume_title(
        self, chapters: list[dict[str, Any]], volume_num: int
    ) -> str:
        """Generate a title for a volume based on its chapters.

        Args:
            chapters: List of chapters in the volume
            volume_num: Volume number

        Returns:
            Generated volume title
        """
        if not chapters:
            return f"Volume {volume_num}"

        # Try to extract key themes/events from chapters
        key_events = []
        for ch in chapters[:3]:  # Look at first 3 chapters
            if ch.get("key_events"):
                key_events.extend(ch["key_events"][:1])

        # For now, use a simple format
        # Could be enhanced with LLM-based title generation
        if key_events:
            first_event = key_events[0]
            if isinstance(first_event, str) and len(first_event) < 50:
                return f"Volume {volume_num}: {first_event[:30]}..."

        return f"Volume {volume_num}"

    def _generate_volume_summary(self, chapters: list[dict[str, Any]]) -> str:
        """Generate a summary for a volume based on its chapters.

        Args:
            chapters: List of chapters in the volume

        Returns:
            Generated volume summary
        """
        if not chapters:
            return "No chapters in this volume."

        summaries = []
        for ch in chapters:
            if ch.get("summary"):
                summaries.append(ch["summary"])

        if summaries:
            # Combine first and last summaries
            if len(summaries) == 1:
                return summaries[0]
            return f"{summaries[0][:100]}... to {summaries[-1][:50]}..."

        return f"Contains chapters {chapters[0].get('chapter', 1)} through {chapters[-1].get('chapter', len(chapters))}."

    async def _initialize_timeline(
        self, project_id: str, outline: dict[str, Any], project_dir: Path
    ) -> TimelineManager:
        """Initialize TimelineManager with story timeline.

        Args:
            project_id: Project identifier
            outline: Story outline with events
            project_dir: Project directory for timeline storage

        Returns:
            Initialized TimelineManager
        """
        timeline_path = project_dir / "timeline"
        timeline_manager = TimelineManager(
            timeline_id=f"{project_id}_timeline",
            storage_path=timeline_path,
        )

        # Add main story arc events from outline
        main_arc = outline.get("main_arc", {})
        acts = main_arc.get("acts", [])

        for act_idx, act in enumerate(acts):
            act_name = act.get("name", f"Act {act_idx + 1}")
            act_summary = act.get("summary", "")

            # Add act as a major timeline event
            event_id = f"act_{act_idx + 1}"
            try:
                timeline_manager.add_event(
                    event_id=event_id,
                    timestamp=f"Act {act_idx + 1}",
                    description=act_summary or act_name,
                    event_type="act",
                    metadata={
                        "name": act_name,
                        "chapters": act.get("chapters", ""),
                        "focus": act.get("focus", ""),
                    },
                    start_order=act_idx * 10,
                    time_unit=TimeUnit.ARC,
                )
            except ValueError:
                # Event already exists, skip
                pass

            # Add key events from the act
            key_events = act.get("key_events", [])
            for event_idx, event in enumerate(key_events):
                if isinstance(event, str):
                    event_description = event
                else:
                    event_description = event.get("description", str(event))

                try:
                    timeline_manager.add_event(
                        event_id=f"event_{act_idx}_{event_idx}",
                        timestamp=f"Act {act_idx + 1}",
                        description=event_description,
                        event_type="plot_point",
                        metadata={"act": act_name},
                        start_order=act_idx * 10 + event_idx,
                        time_unit=TimeUnit.CHAPTER,
                    )
                except ValueError:
                    pass

        # Add climax event
        climax = main_arc.get("climax", "")
        if climax:
            try:
                timeline_manager.add_event(
                    event_id="climax",
                    timestamp="Climax",
                    description=climax,
                    event_type="climax",
                    metadata={"importance": "critical"},
                    start_order=90,
                    time_unit=TimeUnit.ARC,
                )
            except ValueError:
                pass

        # Add resolution event
        resolution = main_arc.get("resolution", "")
        if resolution:
            try:
                timeline_manager.add_event(
                    event_id="resolution",
                    timestamp="Resolution",
                    description=resolution,
                    event_type="resolution",
                    metadata={"importance": "critical"},
                    start_order=99,
                    time_unit=TimeUnit.ARC,
                )
            except ValueError:
                pass

        logger.info(f"Timeline initialized with {len(timeline_manager._events)} events")
        return timeline_manager

    async def _save_artifacts(
        self,
        project_dir: Path,
        outline: dict[str, Any],
        characters: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        world: dict[str, Any],
        volumes: list[dict[str, Any] | Volume],
        timeline: dict[str, Any],
    ) -> None:
        """Save all planning artifacts to project directory.

        Args:
            project_dir: Path to project directory
            outline: Story outline data
            characters: List of character profiles
            relationships: List of character relationships
            world: World settings data
            volumes: List of volumes
            timeline: Timeline data
        """
        # Save outline
        outline_file = project_dir / "outline" / "main_outline.json"
        with open(outline_file, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved outline to {outline_file}")

        # Save characters
        characters_file = project_dir / "characters" / "characters.json"
        with open(characters_file, "w", encoding="utf-8") as f:
            json.dump(characters, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {len(characters)} characters to {characters_file}")

        # Save relationships
        if relationships:
            relationships_file = project_dir / "characters" / "relationships.json"
            with open(relationships_file, "w", encoding="utf-8") as f:
                json.dump(relationships, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved relationships to {relationships_file}")

        # Save world settings
        world_file = project_dir / "world" / "world_settings.json"
        with open(world_file, "w", encoding="utf-8") as f:
            json.dump(world, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved world settings to {world_file}")

        # Save volumes
        volumes_data = [v.to_dict() if isinstance(v, Volume) else v for v in volumes]
        volumes_file = project_dir / "volumes" / "volumes.json"
        with open(volumes_file, "w", encoding="utf-8") as f:
            json.dump(volumes_data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {len(volumes)} volumes to {volumes_file}")

        # Save individual volumes
        for vol in volumes:
            vol_data = vol.to_dict() if isinstance(vol, Volume) else vol
            vol_num = vol_data.get("volume_number", 1)
            vol_file = project_dir / "volumes" / f"volume_{vol_num:02d}.json"
            with open(vol_file, "w", encoding="utf-8") as f:
                json.dump(vol_data, f, indent=2, ensure_ascii=False)

        # Save timeline summary
        timeline_file = project_dir / "timeline" / "timeline_summary.json"
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved timeline to {timeline_file}")

        # Save planning metadata
        metadata = {
            "planning_completed_at": datetime.now().isoformat(),
            "total_chapters": outline.get("total_chapters", 0),
            "total_characters": len(characters),
            "total_volumes": len(volumes),
            "total_timeline_events": len(timeline.get("events", [])),
        }
        metadata_file = project_dir / "planning_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved planning metadata to {metadata_file}")

        logger.info(f"All planning artifacts saved to {project_dir}")


# Factory function
def create_plan_workflow(
    llm: BaseLLM,
    memory: BaseMemory | None = None,
    chapters_per_volume: int = CHAPTERS_PER_VOLUME,
) -> PlanWorkflow:
    """Create a PlanWorkflow instance.

    Args:
        llm: LLM instance for generation
        memory: Optional memory system
        chapters_per_volume: Number of chapters per volume

    Returns:
        Initialized PlanWorkflow
    """
    return PlanWorkflow(
        llm=llm,
        memory=memory,
        chapters_per_volume=chapters_per_volume,
    )


__all__ = [
    "PlanWorkflow",
    "PlanResult",
    "Volume",
    "create_plan_workflow",
    "CHAPTERS_PER_VOLUME",
]