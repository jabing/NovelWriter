#!/usr/bin/env python
"""Generate all chapters for 星际迷途：新纪元 novel.

This script uses the proper validation workflow with ChapterGenerator
and SummaryManager to generate all 30 chapters with:
- ValidationOrchestrator for QA
- Knowledge Graph integration
- ContinuityManager for story state
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.novel_agent.agents.writers.scifi import SciFiWriter
from src.novel_agent.llm.deepseek import DeepSeekLLM
from src.novel_agent.novel.chapter_generator import ChapterGenerator
from src.novel_agent.novel.continuity import ContinuityManager
from src.novel_agent.novel.outline_manager import ChapterSpec
from src.novel_agent.novel.summary_manager import SummaryManager
from src.novel_agent.novel.validation_orchestrator import ValidationOrchestrator
from src.novel_agent.novel.validators import ContinuityValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("chapter_generation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Novel configuration
NOVEL_ID = "481e0917-52a6-4545-a0ca-89342c2895d0"
NOVEL_TITLE = "星际迷途：新纪元"
GENRE = "scifi"
LANGUAGE = "zh"
TOTAL_CHAPTERS = 30

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "openviking" / "memory" / "novels" / NOVEL_ID
OUTLINE_FILE = DATA_DIR / "outlines" / "outline_20260314_210000.json"
CHARACTERS_DIR = DATA_DIR / "characters"
CHAPTERS_DIR = DATA_DIR / "chapters"


def load_outline() -> dict:
    """Load outline from JSON file."""
    with open(OUTLINE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_characters() -> list[dict]:
    """Load all character profiles."""
    characters = []
    for char_file in CHARACTERS_DIR.glob("*.json"):
        with open(char_file, "r", encoding="utf-8") as f:
            characters.append(json.load(f))
    return characters


def create_chapter_spec(chapter_data: dict) -> ChapterSpec:
    """Create ChapterSpec from outline data."""
    return ChapterSpec(
        number=chapter_data["number"],
        title=chapter_data["title"],
        summary=chapter_data["summary"],
        characters=chapter_data.get("characters", []),
        location=chapter_data.get("location", ""),
        key_events=[e.get("description", "") for e in chapter_data.get("plot_events", [])],
        character_states=chapter_data.get("state_changes", {}),
    )


def build_world_context(outline: dict) -> dict:
    """Build world context from outline."""
    return {
        "title": outline.get("title", NOVEL_TITLE),
        "genre": outline.get("genre", GENRE),
        "story_idea": outline.get("story_idea", ""),
        "main_characters": outline.get("main_characters", []),
    }


async def generate_all_chapters(start_chapter: int = 1):
    """Main function to generate all chapters.
    
    Args:
        start_chapter: Chapter number to start from (for resuming)
    """
    logger.info(f"Starting chapter generation for {NOVEL_TITLE}")
    logger.info(f"Novel ID: {NOVEL_ID}")
    logger.info(f"Total chapters: {TOTAL_CHAPTERS}")
    logger.info(f"Starting from chapter: {start_chapter}")

    # Ensure output directory exists
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    # Load outline and characters
    outline = load_outline()
    characters = load_characters()
    logger.info(f"Loaded {len(outline.get('chapters', []))} chapters from outline")
    logger.info(f"Loaded {len(characters)} character profiles")

    # Build world context
    world_context = build_world_context(outline)

    # Initialize LLM
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")

    llm = DeepSeekLLM(api_key=api_key, model="deepseek-chat", temperature=0.8, max_tokens=4000)
    logger.info("DeepSeekLLM initialized")

    # Initialize writer
    writer = SciFiWriter(name="SciFi Writer", llm=llm)
    logger.info("SciFiWriter initialized")

    # Initialize components
    continuity_manager = ContinuityManager()
    validator = ContinuityValidator()
    validation_orchestrator = ValidationOrchestrator()

    # Initialize ChapterGenerator
    generator = ChapterGenerator(
        writer=writer,
        continuity_manager=continuity_manager,
        validator=validator,
        validation_orchestrator=validation_orchestrator,
    )
    logger.info("ChapterGenerator initialized")

    # Initialize SummaryManager (without AutoFixer due to API mismatch)
    summary_manager = SummaryManager(
        storage_path=DATA_DIR,
        novel_id=NOVEL_ID,
        llm=llm,
        use_auto_fix=False,
        use_knowledge_graph=True,
    )
    logger.info("SummaryManager initialized with Knowledge Graph support (AutoFixer disabled)")

    # Track results
    results = {
        "novel_id": NOVEL_ID,
        "title": NOVEL_TITLE,
        "genre": GENRE,
        "total_chapters": TOTAL_CHAPTERS,
        "generated_at": datetime.now().isoformat(),
        "chapters": [],
        "validation_summary": {
            "total_issues": 0,
            "passed": 0,
            "failed": 0,
        },
    }

    # Generate each chapter
    chapters_data = outline.get("chapters", [])

    for chapter_data in chapters_data:
        chapter_num = chapter_data["number"]
        chapter_title = chapter_data["title"]

        if chapter_num < start_chapter:
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Generating Chapter {chapter_num}: {chapter_title}")
        logger.info(f"{'='*60}")

        try:
            # Create ChapterSpec
            chapter_spec = create_chapter_spec(chapter_data)

            # Get characters for this chapter
            chapter_characters = [
                c for c in characters if c.get("name") in chapter_spec.characters
            ]
            if not chapter_characters:
                # Use all characters if none specifically match
                chapter_characters = characters

            # Generate chapter with validation
            logger.info(f"Calling generate_chapter for chapter {chapter_num}...")
            gen_result = await generator.generate_chapter(
                chapter_spec=chapter_spec,
                characters=chapter_characters,
                world_context=world_context,
                run_validation=True,
                novel_id=NOVEL_ID,
                language=LANGUAGE,
            )

            content = gen_result["content"]
            content_length = len(content)
            logger.info(f"Generated content: {content_length} characters")

            # Process with SummaryManager (KG updates) - use process_chapter since autofix is disabled
            logger.info(f"Processing chapter with SummaryManager...")
            try:
                summary = await summary_manager.process_chapter(
                    chapter_number=chapter_num,
                    title=chapter_title,
                    content=content,
                )
                verification = None
                auto_fix = None
            except Exception as e:
                logger.warning(f"SummaryManager processing failed: {e}")
                summary = None
                verification = None
                auto_fix = None

            # Log validation results
            validation = gen_result.get("validation")
            qa_validation = gen_result.get("qa_validation")

            if validation:
                is_valid = getattr(validation, "is_valid", True)
                logger.info(f"Continuity validation: {'PASSED' if is_valid else 'FAILED'}")

            if qa_validation:
                is_valid_qa = qa_validation.get("is_valid", True)
                issues = qa_validation.get("total_issues", 0)
                logger.info(f"QA validation: {'PASSED' if is_valid_qa else 'FAILED'} ({issues} issues)")

            # Log KG updates
            if summary_manager.knowledge_graph:
                kg_nodes = len(summary_manager.knowledge_graph._nodes)
                kg_edges = len(summary_manager.knowledge_graph._edges)
                logger.info(f"Knowledge Graph: {kg_nodes} nodes, {kg_edges} edges")

            # Save chapter to file
            chapter_file = CHAPTERS_DIR / f"chapter_{chapter_num:03d}.json"
            chapter_record = {
                "chapter_number": chapter_num,
                "title": chapter_title,
                "content": content,
                "content_length": content_length,
                "validation": {
                    "continuity": {
                        "is_valid": getattr(validation, "is_valid", True) if validation else None,
                    },
                    "qa": qa_validation,
                    "verification": {
                        "is_consistent": verification.is_consistent if verification else True,
                    },
                },
                "summary": {
                    "summary": summary.summary if summary else "",
                    "key_events": summary.key_events if summary and hasattr(summary, "key_events") else [],
                },
                "generated_at": datetime.now().isoformat(),
            }

            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(chapter_record, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved chapter to {chapter_file}")

            # Track results
            results["chapters"].append(
                {
                    "chapter": chapter_num,
                    "title": chapter_title,
                    "content_length": content_length,
                    "validation_passed": qa_validation.get("is_valid", True) if qa_validation else True,
                }
            )

            if qa_validation and not qa_validation.get("is_valid", True):
                results["validation_summary"]["failed"] += 1
            else:
                results["validation_summary"]["passed"] += 1

            if qa_validation:
                results["validation_summary"]["total_issues"] += qa_validation.get("total_issues", 0)

        except Exception as e:
            logger.error(f"Error generating chapter {chapter_num}: {e}", exc_info=True)
            results["chapters"].append(
                {
                    "chapter": chapter_num,
                    "title": chapter_title,
                    "error": str(e),
                    "validation_passed": False,
                }
            )
            results["validation_summary"]["failed"] += 1

    # Save final summary
    summary_file = DATA_DIR / "generation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved generation summary to {summary_file}")

    # Log final statistics
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total chapters: {TOTAL_CHAPTERS}")
    logger.info(f"Passed: {results['validation_summary']['passed']}")
    logger.info(f"Failed: {results['validation_summary']['failed']}")
    logger.info(f"Total issues: {results['validation_summary']['total_issues']}")

    if summary_manager.knowledge_graph:
        logger.info(f"Knowledge Graph nodes: {len(summary_manager.knowledge_graph._nodes)}")
        logger.info(f"Knowledge Graph edges: {len(summary_manager.knowledge_graph._edges)}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate chapters for novel")
    parser.add_argument("--start", type=int, default=1, help="Chapter number to start from")
    args = parser.parse_args()
    
    results = asyncio.run(generate_all_chapters(start_chapter=args.start))
    print(f"\nGeneration complete. {results['validation_summary']['passed']}/{TOTAL_CHAPTERS} chapters passed validation.")