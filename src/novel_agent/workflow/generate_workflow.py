"""Workflow generation module for chapter generation.

This module provides the ChapterGenerateWorkflow class that orchestrates
the generation of novel chapters with validation, knowledge graph updates,
and checkpoint support.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.novel_agent.agents.writers.writer_factory import get_writer
from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.novel.chapter_validator import ChapterValidator
from src.novel_agent.novel.character_profile import CharacterProfile
from src.novel_agent.novel.character_selector import CharacterSelector
from src.novel_agent.novel.checkpointing import CheckpointManager, create_checkpoint_manager
from src.novel_agent.novel.continuity import ContinuityManager, StoryState
from src.novel_agent.novel.continuity_config import ContinuityConfig, ContinuityStrictness
from src.novel_agent.novel.continuity_validator import ContinuityContext, ContinuityValidator
from src.novel_agent.novel.fact_injector import RelevantFactInjector
from src.novel_agent.novel.language_checker import LanguageConsistencyChecker
from src.novel_agent.novel.perspective_checker import NarrativePerspectiveChecker
from src.novel_agent.novel.kg_transaction import KGTransactionManager
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.outline_validator import OutlineValidator
from src.novel_agent.novel.retry_policy import RetryManager, RetryPolicy
from src.novel_agent.novel.summary_manager import SummaryManager
from src.novel_agent.novel.timeline_manager import TimelineManager
from src.novel_agent.novel.version_control import VersionControlSystem, create_version_control
from src.novel_agent.workflow.state import WorkflowCheckpoint, WorkflowState

logger = logging.getLogger(__name__)


@dataclass
class ChapterVersion:
    """Represents a version snapshot for a specific chapter."""

    version_id: str
    chapter_number: int
    timestamp: datetime
    author: str
    message: str
    content: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GenerateWorkflow(ABC):
    """Base class for workflow generation with version control and checkpoint support.

    Provides checkpoint functionality to preserve generation progress during
    chapter writing, enabling recovery from failures and resumption of work.

    Checkpoint Lifecycle:
        1. Before each chapter: create checkpoint
        2. After each chapter: update checkpoint with completion
        3. On resume: load last checkpoint to continue
        4. On completion: cleanup all checkpoints
    """

    name: str
    description: str = ""
    checkpoint_dir: Path | None = None
    _version_control: VersionControlSystem | None = None
    _project_id: str | None = None
    _checkpoint_manager: CheckpointManager | None = None
    _storage_path: Path | None = None

    def _get_checkpoint_manager(self) -> CheckpointManager:
        if self._checkpoint_manager is None:
            self._checkpoint_manager = create_checkpoint_manager(self.checkpoint_dir)
        return self._checkpoint_manager

    def _create_checkpoint(
        self,
        chapter_number: int,
        content: str,
        project_id: str,
    ) -> WorkflowCheckpoint | None:
        manager = self._get_checkpoint_manager()

        state_snapshot: dict[str, Any] = {
            "project_id": project_id,
            "checkpoint_type": "workflow",
        }

        word_count = len(content.split()) if content else 0
        checkpoint = manager.create_checkpoint(
            chapter_number=chapter_number,
            word_count=word_count,
            content=content,
            state_snapshot=state_snapshot,
            metadata={"project_id": project_id},
        )

        if checkpoint is None:
            logger.warning(
                f"Failed to create checkpoint for project={project_id}, chapter={chapter_number}"
            )
            return None

        workflow_checkpoint = WorkflowCheckpoint(
            chapter_number=chapter_number,
            content=content,
            timestamp=checkpoint.created_at.isoformat(),
            project_id=project_id,
        )

        logger.info(f"Created workflow checkpoint: project={project_id}, chapter={chapter_number}")
        return workflow_checkpoint

    def _load_last_checkpoint(self, project_id: str) -> WorkflowCheckpoint | None:
        manager = self._get_checkpoint_manager()
        checkpoint = manager.get_latest_checkpoint()

        if checkpoint is None:
            logger.info(f"No checkpoints found for project={project_id}")
            return None

        checkpoint_project_id = checkpoint.metadata.get("project_id")
        if checkpoint_project_id and checkpoint_project_id != project_id:
            logger.info(
                f"Latest checkpoint belongs to different project: "
                f"{checkpoint_project_id} != {project_id}"
            )
            for cp_info in manager.list_checkpoints():
                cp = manager.load_checkpoint(cp_info["checkpoint_id"])
                if cp and cp.metadata.get("project_id") == project_id:
                    checkpoint = cp
                    break
            else:
                return None

        workflow_checkpoint = WorkflowCheckpoint(
            chapter_number=checkpoint.chapter_number,
            content=checkpoint.content,
            timestamp=checkpoint.created_at.isoformat(),
            project_id=project_id,
        )

        logger.info(
            f"Loaded last checkpoint: project={project_id}, chapter={checkpoint.chapter_number}, "
            f"words={checkpoint.word_count}"
        )
        return workflow_checkpoint

    def _cleanup_checkpoints(self, project_id: str) -> int:
        manager = self._get_checkpoint_manager()
        removed_count = 0

        for cp_info in manager.list_checkpoints():
            checkpoint = manager.load_checkpoint(cp_info["checkpoint_id"])
            if checkpoint and checkpoint.metadata.get("project_id") == project_id:
                if manager.delete_checkpoint(cp_info["checkpoint_id"]):
                    removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} checkpoints for project={project_id}")
        else:
            logger.debug(f"No checkpoints to clean up for project={project_id}")

        return removed_count

    def _get_version_control(
        self, project_id: str, base_path: Path | None = None
    ) -> VersionControlSystem:
        """Get or create version control system for a project.

        Args:
            project_id: Unique project/novel identifier
            base_path: Optional base path for version storage

        Returns:
            Initialized VersionControlSystem instance
        """
        if self._version_control is None or self._project_id != project_id:
            self._version_control = create_version_control(project_id, base_path)
            self._project_id = project_id
        return self._version_control

    async def _save_version(
        self,
        chapter_number: int,
        content: str,
        project_id: str,
        author: str = "workflow",
        message: str = "Chapter saved",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save a new version of a chapter.

        Creates a version snapshot before any modification, tracking
        the chapter content with timestamp and metadata.

        Args:
            chapter_number: Chapter number (1-indexed)
            content: Chapter content to save
            project_id: Project/novel identifier
            author: Author name (default: "workflow")
            message: Commit message describing the save
            tags: Optional version tags
            metadata: Optional additional metadata

        Returns:
            Version ID of the saved version
        """
        vc = self._get_version_control(project_id)
        version_id = await vc.commit_chapter(
            chapter_number=chapter_number,
            content=content,
            author=author,
            message=message,
            tags=tags,
            metadata=metadata,
        )

        if self._storage_path:
            content_dir = self._storage_path / "novels" / project_id / "content"
            content_dir.mkdir(parents=True, exist_ok=True)
            content_file = content_dir / f"chapter_{chapter_number:04d}.txt"
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Saved chapter {chapter_number} content to {content_file}")

        return version_id

    async def _list_versions(
        self,
        chapter_number: int,
        project_id: str,
        limit: int = 50,
    ) -> list[ChapterVersion]:
        """List all versions for a specific chapter.

        Returns version history for a chapter, sorted by timestamp
        (most recent first), with optional content retrieval.

        Args:
            chapter_number: Chapter number to query
            project_id: Project/novel identifier
            limit: Maximum number of versions to return

        Returns:
            List of ChapterVersion objects for the chapter
        """
        vc = self._get_version_control(project_id)
        all_versions = await vc.get_version_history(limit=limit)

        chapter_versions: list[ChapterVersion] = []
        chapter_key = f"chapter_{chapter_number}"

        for version in all_versions:
            if chapter_key in version.chapter_contents:
                content = version.chapter_contents.get(chapter_key)
                chapter_version = ChapterVersion(
                    version_id=version.version_id,
                    chapter_number=chapter_number,
                    timestamp=version.timestamp,
                    author=version.author,
                    message=version.message,
                    content=content,
                    tags=version.tags,
                    metadata=version.metadata,
                )
                chapter_versions.append(chapter_version)

        return chapter_versions

    async def _rollback_to_version(
        self,
        chapter_number: int,
        version_id: str,
        project_id: str,
    ) -> str:
        """Rollback a chapter to a previous version.

        Retrieves the chapter content from a specific version and
        optionally creates a new version for the rollback.

        Args:
            chapter_number: Chapter number to rollback
            version_id: Version ID to rollback to
            project_id: Project/novel identifier

        Returns:
            Chapter content from the specified version

        Raises:
            ValueError: If version or chapter content not found
        """
        vc = self._get_version_control(project_id)
        version = await vc.get_version(version_id)

        if version is None:
            raise ValueError(f"Version {version_id} not found")

        chapter_key = f"chapter_{chapter_number}"
        content = version.chapter_contents.get(chapter_key)

        if content is None:
            raise ValueError(f"Chapter {chapter_number} not found in version {version_id}")

        return content

    @abstractmethod
    async def generate_content(self, plan: dict[str, Any]) -> dict[str, Any]:
        pass

    @abstractmethod
    async def validate_output(self, output: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def finalize(self, output: dict[str, Any]) -> WorkflowState:
        pass


@dataclass
class GeneratedChapter:
    chapter_number: int
    title: str
    content: str
    word_count: int
    version_id: str | None = None
    validation_passed: bool = True
    auto_fix_iterations: int = 0
    validation_issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "version_id": self.version_id,
            "validation_passed": self.validation_passed,
            "auto_fix_iterations": self.auto_fix_iterations,
            "validation_issues": self.validation_issues,
            "metadata": self.metadata,
        }


@dataclass
class GenerateResult:
    success: bool
    project_id: str
    chapters: list[GeneratedChapter] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_chapters_requested: int = 0
    chapters_generated: int = 0
    resumed_from_checkpoint: bool = False
    start_chapter: int = 1
    workflow_state: WorkflowState | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return self.success and self.chapters_generated == self.total_chapters_requested

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "chapters": [c.to_dict() for c in self.chapters],
            "errors": self.errors,
            "total_chapters_requested": self.total_chapters_requested,
            "chapters_generated": self.chapters_generated,
            "resumed_from_checkpoint": self.resumed_from_checkpoint,
            "start_chapter": self.start_chapter,
            "is_complete": self.is_complete,
            "metadata": self.metadata,
        }


@dataclass
class ProjectData:
    outline: DetailedOutline | None = None
    characters: list[CharacterProfile] = field(default_factory=list)
    world_settings: dict[str, Any] = field(default_factory=dict)
    genre: str = "fantasy"
    metadata: dict[str, Any] = field(default_factory=dict)


class ChapterGenerateWorkflow(GenerateWorkflow):
    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        genre: str = "fantasy",
        description: str = "",
        checkpoint_dir: Path | None = None,
        max_fix_iterations: int = 3,
        continuity_config: ContinuityConfig | None = None,
    ) -> None:
        self.name = name
        self.llm = llm
        self.genre = genre
        self.description = description
        self.checkpoint_dir = checkpoint_dir
        self.max_fix_iterations = max_fix_iterations
        self.writer = get_writer(genre, llm)

        self._version_control: VersionControlSystem | None = None
        self._project_id: str | None = None
        self._checkpoint_manager: CheckpointManager | None = None
        self._summary_manager: SummaryManager | None = None
        self._character_selector: CharacterSelector | None = None
        self._outline_validator: OutlineValidator | None = None
        self._timeline_manager: TimelineManager | None = None
        self._continuity_manager: ContinuityManager | None = None
        self._story_state: StoryState | None = None
        self._fact_injector: RelevantFactInjector | None = None
        self._continuity_config: ContinuityConfig = continuity_config or ContinuityConfig()
        self._chapter_validator: ChapterValidator = ChapterValidator()
        self._retry_manager: RetryManager = RetryManager(RetryPolicy())
        self._kg_transaction: KGTransactionManager | None = None
        # Continuity validation
        self._continuity_validator: ContinuityValidator = ContinuityValidator()
        self._language_checker: LanguageConsistencyChecker = LanguageConsistencyChecker()
        self._perspective_checker: NarrativePerspectiveChecker = NarrativePerspectiveChecker()
        self._previous_chapter_content: str | None = None
        self._expected_language: str | None = None  # Detected from chapter 1
        self._expected_perspective: str | None = None  # Detected from chapter 1

    def _initialize_components(
        self,
        project_id: str,
        storage_path: Path,
    ) -> None:
        self._summary_manager = SummaryManager(
            storage_path=storage_path,
            novel_id=project_id,
            llm=self.llm,
            use_auto_fix=True,
            use_knowledge_graph=True,
        )
        self._character_selector = CharacterSelector()
        self._timeline_manager = TimelineManager(
            timeline_id=f"{project_id}_timeline",
            storage_path=storage_path / "timeline",
        )
        self._continuity_manager = ContinuityManager()
        self._story_state = StoryState(
            chapter=0,
            location="",
            active_characters=[],
            character_states={},
            plot_threads=[],
            key_events=[],
        )
        # Initialize fact injector with default chapter count
        # Will be updated when outline is loaded if available
        self._fact_injector = RelevantFactInjector(
            storage_path=storage_path,
            novel_id=project_id,
            chapter_count=30,  # default, will be updated when outline is loaded
        )

    def _load_project_data(
        self,
        project_id: str,
        storage_path: Path,
    ) -> ProjectData:
        project_data = ProjectData()
        project_dir = storage_path / "novels" / project_id

        # Check multiple possible outline locations
        outline_file = project_dir / "outline.json"
        outline_alt_file = project_dir / "outline" / "main_outline.json"

        outline_path = None
        if outline_file.exists():
            outline_path = outline_file
        elif outline_alt_file.exists():
            outline_path = outline_alt_file

        if outline_path:
            try:
                with open(outline_path, encoding="utf-8") as f:
                    outline_data = json.load(f)
                chapters = []
                for ch_data in outline_data.get("chapters", []):
                    ch_num = ch_data.get("chapter") or ch_data.get("number", 0)
                    chapters.append(
                        ChapterSpec(
                            number=ch_num,
                            title=ch_data.get("title", f"Chapter {ch_num}"),
                            summary=ch_data.get("summary", ""),
                            characters=ch_data.get("characters", []),
                            location=ch_data.get("location", ""),
                            key_events=ch_data.get("key_events", []),
                            plot_threads_resolved=ch_data.get("plot_threads_resolved", []),
                            plot_threads_started=ch_data.get("plot_threads_started", []),
                            character_states=ch_data.get("character_states", {}),
                        )
                    )
                project_data.outline = DetailedOutline(chapters=chapters)
                project_data.genre = outline_data.get("genre", self.genre)

                outline_for_validator = {
                    "chapters": outline_data.get("chapters", []),
                    "plot_threads": outline_data.get("plot_threads", []),
                    "timeline": outline_data.get("timeline", []),
                    "characters": outline_data.get("characters", []),
                }
                self._outline_validator = OutlineValidator(outline_for_validator)
                logger.info(f"Loaded outline with {len(chapters)} chapters")
            except Exception as e:
                logger.error(f"Failed to load outline: {e}")

        characters_file = project_dir / "characters.json"
        characters_alt_file = project_dir / "characters" / "characters.json"
        characters_path = characters_file if characters_file.exists() else characters_alt_file

        if characters_path.exists():
            try:
                with open(characters_path, encoding="utf-8") as f:
                    characters_data = json.load(f)
                char_list = (
                    characters_data
                    if isinstance(characters_data, list)
                    else characters_data.get("characters", [])
                )
                for char_data in char_list:
                    profile = CharacterProfile.from_dict(char_data)
                    project_data.characters.append(profile)
                logger.info(f"Loaded {len(project_data.characters)} characters")
            except Exception as e:
                logger.error(f"Failed to load characters: {e}")

        world_file = project_dir / "world_settings.json"
        world_alt_file = project_dir / "world" / "world_settings.json"
        world_path = world_file if world_file.exists() else world_alt_file

        if world_path.exists():
            try:
                with open(world_path, encoding="utf-8") as f:
                    project_data.world_settings = json.load(f)
                logger.info("Loaded world settings")
            except Exception as e:
                logger.error(f"Failed to load world settings: {e}")

        if project_data.outline is None:
            project_data.outline = DetailedOutline(chapters=[])

        return project_data

    async def execute(
        self,
        project_id: str,
        start_chapter: int = 1,
        count: int = 1,
        storage_path: Path | None = None,
        resume: bool = False,
        progress_callback: Any | None = None,
    ) -> GenerateResult:
        if storage_path is None:
            storage_path = Path("data/openviking/memory")

        self._storage_path = storage_path
        self._initialize_components(project_id, storage_path)
        project_data = self._load_project_data(project_id, storage_path)

        if project_data.outline is None or not project_data.outline.chapters:
            return GenerateResult(
                success=False,
                project_id=project_id,
                errors=["No outline found for project"],
                total_chapters_requested=count,
            )

        result = GenerateResult(
            success=True,
            project_id=project_id,
            total_chapters_requested=count,
            start_chapter=start_chapter,
        )

        if resume:
            checkpoint = self._load_last_checkpoint(project_id)
            if checkpoint:
                start_chapter = checkpoint.chapter_number + 1
                result.resumed_from_checkpoint = True
                result.start_chapter = start_chapter
                logger.info(f"Resuming from chapter {start_chapter}")

        end_chapter = min(start_chapter + count - 1, project_data.outline.get_total_chapters())

        for chapter_num in range(start_chapter, end_chapter + 1):
            try:
                checkpoint = self._create_checkpoint(
                    chapter_number=chapter_num,
                    content="",
                    project_id=project_id,
                )

                chapter_spec = project_data.outline.get_chapter_spec(chapter_num)
                if chapter_spec is None:
                    result.errors.append(f"Chapter {chapter_num} not found in outline")
                    if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                        result.success = False
                        break  # STRICT mode: stop generation
                    continue  # Non-STRICT mode: skip and continue

                chapter_result = await self._generate_single_chapter(
                    chapter_spec=chapter_spec,
                    characters=project_data.characters,
                    world_settings=project_data.world_settings,
                    project_id=project_id,
                    storage_path=storage_path,
                )

                if chapter_result:
                    result.chapters.append(chapter_result)
                    result.chapters_generated += 1

                    if not chapter_result.validation_passed:
                        result.errors.append(
                            f"Chapter {chapter_num} validation failed after "
                            f"{chapter_result.auto_fix_iterations} fix attempts"
                        )
                        if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                            result.success = False
                            break  # STRICT mode: stop generation on validation failure

                    version_id = await self._save_version(
                        chapter_number=chapter_num,
                        content=chapter_result.content,
                        project_id=project_id,
                        author=self.name,
                        message=f"Generated chapter {chapter_num}: {chapter_spec.title}",
                        tags=[self.genre, "generated"],
                        metadata={"validation_passed": chapter_result.validation_passed},
                    )
                    chapter_result.version_id = version_id

                    self._create_checkpoint(
                        chapter_number=chapter_num,
                        content=chapter_result.content,
                        project_id=project_id,
                    )

                    if progress_callback:
                        progress_callback(
                            chapter=chapter_num,
                            total=end_chapter,
                            success=chapter_result.validation_passed,
                        )
                else:
                    result.errors.append(f"Failed to generate chapter {chapter_num}")
                    result.success = False
                    if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                        break  # STRICT mode: stop generation

            except Exception as e:
                logger.error(f"Error generating chapter {chapter_num}: {e}")
                result.errors.append(f"Chapter {chapter_num}: {str(e)}")
                result.success = False
                if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                    break  # STRICT mode: stop generation

        result.workflow_state = WorkflowState(
            planning_complete=True,
            last_generated_chapter=end_chapter
            if result.chapters_generated > 0
            else start_chapter - 1,
            validation_enabled=True,
        )

        if result.success and result.chapters_generated == count:
            self._cleanup_checkpoints(project_id)

        return result

    async def _generate_single_chapter(
        self,
        chapter_spec: ChapterSpec,
        characters: list[CharacterProfile],
        world_settings: dict[str, Any],
        project_id: str,
        storage_path: Path,
    ) -> GeneratedChapter | None:
        """Generate a single chapter with retry support."""
        if self.writer is None:
            logger.error("Writer not initialized")
            return None

        async def generate_operation() -> GeneratedChapter:
            return await self._generate_single_chapter_internal(
                chapter_spec=chapter_spec,
                characters=characters,
                world_settings=world_settings,
                project_id=project_id,
                storage_path=storage_path,
            )

        result = await self._retry_manager.execute_with_retry(generate_operation)

        if result.success:
            return result.result
        else:
            logger.error(
                f"Chapter {chapter_spec.number} generation failed after {result.attempts} attempts"
            )
            return None

    async def _generate_single_chapter_internal(
        self,
        chapter_spec: ChapterSpec,
        characters: list[CharacterProfile],
        world_settings: dict[str, Any],
        project_id: str,
        storage_path: Path,
    ) -> GeneratedChapter:

        chapter_spec_dict = {
            "characters": chapter_spec.characters,
            "location": chapter_spec.location,
            "key_events": chapter_spec.key_events,
        }
        selected_characters, remaining_budget = self._character_selector.select_for_chapter(
            all_characters=characters,
            chapter_spec=chapter_spec_dict,
        )

        characters_for_chapter = [
            {
                "name": char.name,
                "bio": char.bio,
                "persona": char.persona,
                "status": char.current_status.value
                if hasattr(char.current_status, "value")
                else str(char.current_status),
                "relationships": char.relationships,
            }
            for char in selected_characters
        ]

        previous_summary = None
        if self._story_state and self._story_state.key_events:
            previous_summary = "; ".join(self._story_state.key_events[-3:])

        fact_context = ""
        if self._fact_injector:
            try:
                active_entities = [char.name for char in selected_characters]
                relevant_facts = self._fact_injector.get_relevant_facts(
                    current_chapter=chapter_spec.number,
                    active_entities=active_entities,
                )
                if relevant_facts:
                    fact_context = "\n".join(
                        [f"- {fact.content}" for fact, _ in relevant_facts[:10]]
                    )
                    logger.info(
                        f"Injected {len(relevant_facts)} relevant facts for chapter {chapter_spec.number}"
                    )
            except Exception as e:
                logger.warning(f"Failed to get relevant facts: {e}")

        if fact_context:
            logger.debug(f"Facts prepared for chapter {chapter_spec.number}")

        content = await self.writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=self._story_state
            or StoryState(
                chapter=0,
                location=chapter_spec.location,
                active_characters=[],
                character_states={},
                plot_threads=[],
                key_events=[],
            ),
            characters=characters_for_chapter,
            world_context=world_settings,
            previous_chapter_summary=previous_summary,
            fact_context=fact_context if fact_context else None,
        )

        validation_passed = True
        auto_fix_iterations = 0

        if self._summary_manager:
            try:
                (
                    summary,
                    verification,
                    auto_fix_result,
                ) = await self._summary_manager.process_chapter_with_autofix(
                    chapter_number=chapter_spec.number,
                    title=chapter_spec.title,
                    content=content,
                    max_fix_iterations=self.max_fix_iterations,
                )

                if auto_fix_result and auto_fix_result.success:
                    content = auto_fix_result.final_content
                    auto_fix_iterations = auto_fix_result.iteration_count
                    validation_passed = auto_fix_result.is_fully_fixed
                elif verification and not verification.is_consistent:
                    validation_passed = False
                    auto_fix_iterations = self.max_fix_iterations

                logger.info(
                    f"Chapter {chapter_spec.number}: validation_passed={validation_passed}, "
                    f"fix_iterations={auto_fix_iterations}"
                )
            except Exception as e:
                logger.error(f"Validation failed for chapter {chapter_spec.number}: {e}")
                validation_passed = False

        # ChapterValidator integration - check completeness
        validation_issues: list[str] = []
        if self._continuity_config.strictness != ContinuityStrictness.OFF:
            chapter_validation = self._chapter_validator.check_completeness(
                content=content, min_words=self._continuity_config.min_chapter_words
            )
            if not chapter_validation.is_valid:
                validation_issues = chapter_validation.issues
                logger.warning(
                    f"Chapter {chapter_spec.number} validation issues: {validation_issues}"
                )
                if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                    validation_passed = False

        if self._outline_validator:
            try:
                validation_result = self._outline_validator.validate_chapter(
                    chapter_content=content,
                    chapter_number=chapter_spec.number,
                )
                if not validation_result.get("passed", True):
                    logger.warning(
                        f"Outline validation issues for chapter {chapter_spec.number}: "
                        f"{validation_result.get('deviations', [])}"
                    )
            except Exception as e:
                logger.error(f"Outline validation error: {e}")

        if self._timeline_manager:
            try:
                issues = self._timeline_manager.validate_temporal_consistency()
                if issues:
                    logger.warning(f"Timeline issues detected: {issues}")
            except Exception as e:
                logger.error(f"Timeline validation error: {e}")

        if self._continuity_manager and self._story_state:
            try:
                if self._kg_transaction is None:
                    self._kg_transaction = KGTransactionManager()

                known_characters = [c.name for c in characters]

                def update_kg_state(state: dict[str, Any]) -> dict[str, Any]:
                    new_story_state = self._continuity_manager.update_from_chapter(
                        state=state.get("story_state", self._story_state),
                        chapter_content=content,
                        chapter_number=chapter_spec.number,
                        known_characters=known_characters,
                    )
                    return {"story_state": new_story_state}

                success = self._kg_transaction.update_with_transaction(update_kg_state)

                if not success:
                    logger.error("KG transaction failed, rolled back")
                    if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                        validation_passed = False
                else:
                    new_state = self._kg_transaction.get_state().get("story_state")
                    if new_state:
                        self._story_state = new_state
                        logger.debug(f"KG updated to version {self._kg_transaction.get_version()}")
            except Exception as e:
                logger.error(f"Continuity update error: {e}")
                if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                    validation_passed = False

        if self._continuity_config.strictness != ContinuityStrictness.OFF:
            if self._previous_chapter_content is None:
                detected_lang = self._language_checker.detect_language(content)
                self._expected_language = detected_lang.value
                detected_persp = self._perspective_checker.detect_perspective(content)
                self._expected_perspective = detected_persp.value
                logger.info(
                    f"Chapter {chapter_spec.number}: Detected language={self._expected_language}, "
                    f"perspective={self._expected_perspective}"
                )
            else:
                known_character_names = [c.name for c in characters]
                continuity_context = ContinuityContext(
                    chapter_number=chapter_spec.number,
                    character_names=known_character_names,
                    expected_language=self._expected_language,
                    expected_perspective=self._expected_perspective,
                    block_on_character_mismatch=self._continuity_config.block_on_character_mismatch,
                )
                continuity_result = self._continuity_validator.validate_chapter(
                    current=content,
                    previous=self._previous_chapter_content,
                    context=continuity_context,
                )
                if not continuity_result.is_valid:
                    error_msg = f"连续性验证失败: {'; '.join(continuity_result.issues)}"
                    logger.error(f"Chapter {chapter_spec.number}: {error_msg}")
                    validation_issues.extend(continuity_result.issues)
                    if self._continuity_config.strictness == ContinuityStrictness.STRICT:
                        validation_passed = False
                elif continuity_result.warnings:
                    logger.warning(
                        f"Chapter {chapter_spec.number} continuity warnings: "
                        f"{continuity_result.warnings}"
                    )
            self._previous_chapter_content = content

        word_count = len(content.split()) if content else 0

        return GeneratedChapter(
            chapter_number=chapter_spec.number,
            title=chapter_spec.title,
            content=content,
            word_count=word_count,
            validation_passed=validation_passed,
            auto_fix_iterations=auto_fix_iterations,
            validation_issues=validation_issues,
            metadata={
                "location": chapter_spec.location,
                "characters": chapter_spec.characters,
            },
        )

    async def generate_content(self, plan: dict[str, Any]) -> dict[str, Any]:
        project_id = plan.get("project_id", "default")
        start_chapter = plan.get("start_chapter", 1)
        count = plan.get("count", 1)
        storage_path = Path(plan.get("storage_path", "data/openviking/memory"))
        resume = plan.get("resume", False)

        result = await self.execute(
            project_id=project_id,
            start_chapter=start_chapter,
            count=count,
            storage_path=storage_path,
            resume=resume,
        )

        return result.to_dict()

    async def validate_output(self, output: dict[str, Any]) -> bool:
        return output.get("success", False) and output.get("chapters_generated", 0) > 0

    async def finalize(self, output: dict[str, Any]) -> WorkflowState:
        return WorkflowState(
            planning_complete=True,
            last_generated_chapter=output.get("chapters_generated", 0),
            validation_enabled=True,
        )


def create_generate_workflow(
    name: str,
    llm: BaseLLM,
    genre: str = "fantasy",
    checkpoint_dir: Path | None = None,
) -> ChapterGenerateWorkflow:
    return ChapterGenerateWorkflow(
        name=name,
        llm=llm,
        genre=genre,
        checkpoint_dir=checkpoint_dir,
    )
