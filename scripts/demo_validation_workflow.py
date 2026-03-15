#!/usr/bin/env python
"""Demonstration script for the NovelWriter validation workflow.

This script demonstrates the complete validation workflow using:
- ChapterGenerator: Generates chapters with full validation
- SummaryManager: Manages rolling summaries with knowledge graph updates

Usage:
    python scripts/demo_validation_workflow.py --help
    python scripts/demo_validation_workflow.py --genre fantasy --chapters 1
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Any

# Core imports from learnings.md
from src.novel_agent.novel.continuity import ContinuityManager, StoryState
from src.novel_agent.novel.inventory_updater import InventoryUpdater
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.validation_orchestrator import ValidationOrchestrator, ValidationResult
from src.novel_agent.novel.validators import ContinuityValidator
from src.novel_agent.novel.chapter_generator import ChapterGenerator
from src.novel_agent.novel.summary_manager import SummaryManager
from src.novel_agent.agents.writers.base_writer import BaseWriter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("demo_validation_workflow")


# ============================================================================
# PLACEHOLDER FUNCTIONS - Complete validation workflow steps
# ============================================================================


async def create_project(novel_id: str, genre: str) -> dict[str, Any]:
    """Create a new novel project with initial configuration.

    Args:
        novel_id: Unique identifier for the novel
        genre: Genre of the novel (fantasy, sci-fi, romance, etc.)

    Returns:
        Project configuration dictionary
    """
    logger.info("create_project: Creating project")
    # TODO: Implement project creation logic
    return {
        "novel_id": novel_id,
        "genre": genre,
        "status": "initialized",
        "storage_path": f"data/novels/{novel_id}",
    }


async def generate_outline(project: dict[str, Any], num_chapters: int) -> DetailedOutline:
    """Generate a detailed chapter outline for the novel.

    Args:
        project: Project configuration dictionary
        num_chapters: Number of chapters to generate

    Returns:
        DetailedOutline with ChapterSpec objects
    """
    logger.info("generate_outline: Generating outline")
    # TODO: Implement outline generation logic
    chapters = [
        ChapterSpec(
            number=i,
            title=f"Chapter {i}",
            summary=f"Summary for chapter {i}",
            characters=[],
            location="Starting Location",
        )
        for i in range(1, num_chapters + 1)
    ]
    return DetailedOutline(chapters=chapters)


async def create_characters(project: dict[str, Any]) -> list[dict[str, Any]]:
    """Create character profiles for the novel.

    Args:
        project: Project configuration dictionary

    Returns:
        List of character dictionaries
    """
    logger.info("create_characters: Creating characters")
    # TODO: Implement character creation logic
    return [
        {
            "name": "Main Character",
            "role": "protagonist",
            "description": "The main protagonist of the story",
        }
    ]


async def generate_chapters_with_validation(
    project: dict[str, Any],
    outline: DetailedOutline,
    characters: list[dict[str, Any]],
    writer: BaseWriter,
    continuity_manager: ContinuityManager,
    validator: ContinuityValidator,
    inventory_updater: InventoryUpdater,
    validation_orchestrator: ValidationOrchestrator | None = None,
) -> list[dict[str, Any]]:
    """Generate chapters with full validation using ChapterGenerator.

    Args:
        project: Project configuration dictionary
        outline: DetailedOutline with chapter specifications
        characters: List of character profiles
        writer: BaseWriter instance for content generation
        continuity_manager: ContinuityManager for state tracking
        validator: ContinuityValidator for validation
        inventory_updater: InventoryUpdater for knowledge graph updates
        validation_orchestrator: Optional ValidationOrchestrator for QA validation

    Returns:
        List of generated chapter results with validation data
    """
    logger.info("generate_chapters_with_validation: Starting chapter generation")

    generator = ChapterGenerator(
        writer=writer,
        continuity_manager=continuity_manager,
        validator=validator,
        inventory_updater=inventory_updater,
        validation_orchestrator=validation_orchestrator,
    )

    results = []
    for chapter_spec in outline.chapters:
        logger.info(f"Generating chapter {chapter_spec.number}")

        # Generate chapter with validation
        result = await generator.generate_chapter(
            chapter_spec=chapter_spec,
            characters=characters,
            world_context={"location": chapter_spec.location},
            run_validation=True,
            novel_id=project.get("novel_id"),
        )

        results.append(result)

        # Log validation results
        if validation_result := result.get("validation"):
            logger.info(f"Chapter {chapter_spec.number}: Validation passed={validation_result.get('passed')}")

    return results


async def verify_knowledge_graph(
    project: dict[str, Any],
    summary_manager: SummaryManager,
    generated_chapters: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify the knowledge graph state after chapter generation.

    Args:
        project: Project configuration dictionary
        summary_manager: SummaryManager instance
        generated_chapters: List of generated chapter results

    Returns:
        Verification result dictionary
    """
    logger.info("verify_knowledge_graph: Verifying knowledge graph")

    # Process each chapter through SummaryManager
    for chapter_result in generated_chapters:
        content = chapter_result.get("content", "")
        chapter_number = chapter_result.get("chapter_number", 0)

        if isinstance(content, str) and content:
            logger.info(f"Processing chapter {chapter_number} through SummaryManager")
            # TODO: Call summary_manager.process_chapter_with_autofix()

    # Verify knowledge graph integrity
    verification = {
        "entities_extracted": 0,
        "relations_inferred": 0,
        "consistency_checked": True,
        "status": "verified",
    }

    logger.info("verify_knowledge_graph: Verification complete")
    return verification


# ============================================================================
# MAIN ASYNC ENTRY POINT
# ============================================================================


async def main_async(args: argparse.Namespace) -> int:
    """Main async entry point for the validation workflow demo.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("=" * 60)
    logger.info("NovelWriter Validation Workflow Demo")
    logger.info("=" * 60)

    # Create project
    project = await create_project(
        novel_id=args.novel_id,
        genre=args.genre,
    )
    logger.info(f"Created project: {project['novel_id']}")

    # Generate outline
    outline = await generate_outline(project, args.chapters)
    logger.info(f"Generated {len(outline.chapters)} chapter(s)")

    # Create characters
    characters = await create_characters(project)
    logger.info(f"Created {len(characters)} character(s)")

    # TODO: Initialize writer, continuity manager, validator, inventory updater
    # These would typically be created with proper LLM connections
    # For now, we log what would be created

    logger.info("Initializing validation components (placeholder)")
    logger.info("  - Writer: BaseWriter (requires LLM)")
    logger.info("  - ContinuityManager: ContinuityManager")
    logger.info("  - Validator: ContinuityValidator")
    logger.info("  - InventoryUpdater: InventoryUpdater")

    # Placeholder for actual component initialization
    # writer = create_writer(args.genre, llm)
    # continuity_manager = ContinuityManager()
    # validator = ContinuityValidator()
    # inventory_updater = InventoryUpdater()
    # validation_orchestrator = ValidationOrchestrator()

    # Generate chapters with validation
    # chapters = await generate_chapters_with_validation(
    #     project, outline, characters, writer, continuity_manager,
    #     validator, inventory_updater, validation_orchestrator
    # )

    logger.info("Chapter generation with validation: SKIPPED (components not initialized)")

    # Initialize SummaryManager for knowledge graph updates
    logger.info("Initializing SummaryManager")
    storage_path = Path(project.get("storage_path", "data/novels"))
    storage_path.mkdir(parents=True, exist_ok=True)

    # TODO: Initialize LLM and SummaryManager
    # llm = create_llm()
    # summary_manager = SummaryManager(storage_path, project["novel_id"], llm)

    # Verify knowledge graph
    # verification = await verify_knowledge_graph(project, summary_manager, chapters)

    logger.info("Knowledge graph verification: SKIPPED (components not initialized)")

    logger.info("=" * 60)
    logger.info("Demo complete")
    logger.info("=" * 60)

    return 0


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


def main() -> int:
    """CLI entry point with argument parsing.

    Returns:
        Exit code from main_async
    """
    parser = argparse.ArgumentParser(
        description="Demonstrate the complete NovelWriter validation workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_validation_workflow.py --genre fantasy --chapters 1
  python scripts/demo_validation_workflow.py --novel-id test_novel --genre sci-fi
        """,
    )

    parser.add_argument(
        "--novel-id",
        type=str,
        default="demo",
        help="Unique identifier for the novel (default: demo)",
    )
    parser.add_argument(
        "--genre",
        type=str,
        default="fantasy",
        choices=["fantasy", "sci-fi", "romance", "history", "military"],
        help="Genre of the novel (default: fantasy)",
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=1,
        help="Number of chapters to generate (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
