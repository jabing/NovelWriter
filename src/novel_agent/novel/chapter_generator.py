"""Chapter generator with continuity tracking and validation.

This module provides a high-level interface for generating chapters
with full continuity context and integrated validation through the
ValidationOrchestrator.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.novel_agent.agents.writers.base_writer import BaseWriter

from src.novel_agent.novel.continuity import ContinuityManager, StoryState
from src.novel_agent.novel.inventory_updater import InventoryUpdater
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.validation_orchestrator import (
    ValidationOrchestrator,
    ValidationResult,
)
from src.novel_agent.novel.validators import ContinuityValidator

logger = logging.getLogger(__name__)


class ChapterGenerator:
    """Generator for novel chapters with continuity tracking and validation.

    This class orchestrates the chapter generation process, including:
    - Managing story state across chapters
    - Validating continuity
    - Running comprehensive QA validation
    - Generating chapters with proper context
    """

    def __init__(
        self,
        writer: BaseWriter,
        continuity_manager: ContinuityManager | None = None,
        validator: ContinuityValidator | None = None,
        inventory_updater: InventoryUpdater | None = None,
        validation_orchestrator: ValidationOrchestrator | None = None,
    ) -> None:
        """Initialize the chapter generator.

        Args:
            writer: The writer agent to use for generation
            continuity_manager: Optional continuity manager
            validator: Optional continuity validator
            inventory_updater: Optional inventory updater
            validation_orchestrator: Optional validation orchestrator for comprehensive QA
        """
        self.writer = writer
        self.continuity = continuity_manager or ContinuityManager()
        self.validator = validator or ContinuityValidator()
        self.inventory_updater = inventory_updater or InventoryUpdater()
        self.validation_orchestrator = validation_orchestrator
        self._current_state: StoryState | None = None
        self._previous_chapter_content: str | None = None

    async def generate_chapter(
        self,
        chapter_spec: ChapterSpec,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        run_validation: bool = True,
        novel_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate a single chapter with continuity and validation.

        Args:
            chapter_spec: Chapter specification
            characters: Character profiles for this chapter
            world_context: World-building context
            run_validation: Whether to run validation orchestrator (default: True)
            novel_id: Optional novel ID for timeline validation
            **kwargs: Additional arguments passed to writer

        Returns:
            Dict with content, validation result, QA validation, and updated state
        """
        previous_summary = None
        if self._current_state and self._current_state.key_events:
            previous_summary = "; ".join(self._current_state.key_events[-3:])

        content = await self.writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=self._current_state
            or StoryState(
                chapter=0,
                location=chapter_spec.location,
                active_characters=[],
                character_states={},
                plot_threads=[],
                key_events=[],
            ),
            characters=characters,
            world_context=world_context,
            previous_chapter_summary=previous_summary,
            **kwargs,
        )

        self._current_state = self.continuity.update_from_chapter(
            self._current_state
            or StoryState(
                chapter=0,
                location=chapter_spec.location,
                active_characters=[],
                character_states={},
                plot_threads=[],
                key_events=[],
            ),
            content,
            chapter_spec.number,
        )

        try:
            inventory_stats = await self.inventory_updater.update_inventory(
                content,
                chapter_spec.number,
                self._current_state,
            )
        except Exception as e:
            logger.warning(f"Inventory update failed: {e}")
            inventory_stats = {"errors": [str(e)]}

        validation_result = self.validator.validate_chapter(
            chapter_content=content,
            chapter_number=chapter_spec.number,
            story_state=self._current_state,
            chapter_spec=chapter_spec,
        )

        qa_validation: ValidationResult | None = None
        if run_validation and self.validation_orchestrator:
            try:
                world_context_str = self._format_world_context(world_context)
                qa_validation = await self.validation_orchestrator.validate_chapter(
                    chapter_content=content,
                    chapter_num=chapter_spec.number,
                    world_context=world_context_str,
                    prev_chapter_content=self._previous_chapter_content,
                    novel_id=novel_id,
                )

                if not qa_validation.is_valid:
                    logger.warning(
                        f"QA validation failed for chapter {chapter_spec.number}: "
                        f"{qa_validation.summary}"
                    )
                else:
                    logger.info(f"QA validation passed for chapter {chapter_spec.number}")

            except Exception as e:
                logger.error(f"QA validation error: {e}")

        self._previous_chapter_content = content

        return {
            "content": content,
            "chapter_number": chapter_spec.number,
            "validation": validation_result,
            "qa_validation": qa_validation.to_dict() if qa_validation else None,
            "state": self._current_state,
            "inventory_stats": inventory_stats,
        }

    async def generate_novel(
        self,
        outline: DetailedOutline,
        world_context: dict[str, Any],
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        """Generate a complete novel from outline.

        Args:
            outline: Detailed outline with chapter specifications
            world_context: World-building context
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with chapters, validation results, and final state
        """
        chapters = []
        validation_results = []

        for chapter_spec in outline.chapters:
            characters = [{"name": char} for char in chapter_spec.characters]

            result = await self.generate_chapter(
                chapter_spec=chapter_spec,
                characters=characters,
                world_context=world_context,
            )

            chapters.append(result["content"])
            validation_results.append(result["validation"])

            if progress_callback:
                progress_callback(
                    chapter=chapter_spec.number,
                    total=len(outline.chapters),
                    valid=result["validation"].is_valid,
                )

        return {
            "chapters": chapters,
            "validations": validation_results,
            "final_state": self._current_state,
        }

    def get_current_state(self) -> StoryState | None:
        """Get the current story state.

        Returns:
            Current story state or None if no chapters generated
        """
        return self._current_state

    def set_initial_state(self, state: StoryState) -> None:
        """Set the initial story state.

        Args:
            state: Initial story state
        """
        self._current_state = state

    def _format_world_context(self, world_context: dict[str, Any]) -> str:
        context_parts = []
        if isinstance(world_context, dict):
            for key, value in world_context.items():
                if isinstance(value, str):
                    context_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    context_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    context_parts.append(f"{key}: {str(value)}")
        return "\n".join(context_parts)
