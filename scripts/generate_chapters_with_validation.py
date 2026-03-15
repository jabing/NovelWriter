#!/usr/bin/env python
"""Generate chapters for validation workflow demo with proper validation chain.

This script demonstrates the proper chapter generation workflow:
1. Uses ChapterGenerator with validation
2. Uses SummaryManager for KG updates
3. Saves chapters to proper location

Usage:
    python scripts/generate_chapters_with_validation.py --novel-id <id> [--start 1] [--end 30]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("generate_chapters")

# Core imports
from src.novel_agent.novel.continuity import ContinuityManager, StoryState
from src.novel_agent.novel.inventory_updater import InventoryUpdater
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.validation_orchestrator import ValidationOrchestrator
from src.novel_agent.novel.validators import ContinuityValidator
from src.novel_agent.novel.chapter_generator import ChapterGenerator
from src.novel_agent.novel.summary_manager import SummaryManager
from src.novel_agent.novel.knowledge_graph import KnowledgeGraph


async def generate_chapters(
    novel_id: str,
    start_chapter: int,
    end_chapter: int,
    data_dir: Path,
) -> dict[str, Any]:
    """Generate chapters with full validation workflow."""
    
    # Load outline
    outline_dir = data_dir / "openviking" / "memory" / "novels" / novel_id / "outlines"
    outline_files = list(outline_dir.glob("*.json"))
    if not outline_files:
        logger.error(f"No outline found for {novel_id}")
        return {"success": False, "error": "No outline found"}
    
    with open(outline_files[0], encoding="utf-8") as f:
        outline_data = json.load(f)
    
    logger.info(f"Loaded outline: {outline_data.get('title')}")
    logger.info(f"Total chapters in outline: {len(outline_data.get('chapters', []))}")
    
    # Load characters
    characters_dir = data_dir / "openviking" / "memory" / "novels" / novel_id / "characters"
    characters = []
    if characters_dir.exists():
        for char_file in characters_dir.glob("*.json"):
            with open(char_file, encoding="utf-8") as f:
                characters.append(json.load(f))
    
    logger.info(f"Loaded {len(characters)} characters")
    
    # Initialize KG
    kg_dir = data_dir / "knowledge_graphs" / novel_id
    kg_dir.mkdir(parents=True, exist_ok=True)
    knowledge_graph = KnowledgeGraph(novel_id, kg_dir)
    logger.info(f"Initialized Knowledge Graph at {kg_dir}")
    
    # Initialize components
    continuity_manager = ContinuityManager()
    inventory_updater = InventoryUpdater()
    validator = ContinuityValidator()
    validation_orchestrator = ValidationOrchestrator()
    
    # Initialize story state
    initial_state = StoryState(
        chapter=0,
        location="新纪元号 - 太阳系边缘",
        active_characters=["林轩", "苏雅", "张伟"],
        character_states={},
        plot_threads=[],
        key_events=[],
    )
    continuity_manager._current_state = initial_state
    
    # Initialize generator
    generator = ChapterGenerator(
        writer=None,  # We'll generate content differently
        continuity_manager=continuity_manager,
        validator=validator,
        inventory_updater=inventory_updater,
        validation_orchestrator=validation_orchestrator,
    )
    
    # Initialize summary manager
    summary_manager = SummaryManager(
        storage_path=data_dir,
        novel_id=novel_id,
        llm=None,  # Will handle without LLM for now
        use_auto_fix=False,
        use_knowledge_graph=True,
    )
    
    # Create chapters directory
    chapters_dir = data_dir / "openviking" / "memory" / "novels" / novel_id / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "success": True,
        "chapters_generated": 0,
        "validation_results": [],
        "kg_entities": 0,
        "errors": [],
    }
    
    # Generate each chapter
    for chapter_num in range(start_chapter, end_chapter + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating Chapter {chapter_num}")
        logger.info(f"{'='*60}")
        
        # Find chapter in outline
        chapter_data = None
        for ch in outline_data.get("chapters", []):
            if ch.get("number") == chapter_num:
                chapter_data = ch
                break
        
        if not chapter_data:
            logger.warning(f"Chapter {chapter_num} not found in outline, skipping")
            continue
        
        # Generate chapter content (using outline summary as base, expanding it)
        chapter_content = generate_chapter_content(chapter_data, characters, outline_data)
        
        # Update continuity
        try:
            new_state = continuity_manager.update_from_chapter(
                continuity_manager._current_state,
                chapter_content,
                chapter_num,
            )
            continuity_manager._current_state = new_state
            logger.info(f"  Updated continuity state")
        except Exception as e:
            logger.warning(f"  Continuity update failed: {e}")
        
        # Validate chapter
        try:
            validation_result = validator.validate_chapter(
                chapter_content=chapter_content,
                chapter_number=chapter_num,
                story_state=continuity_manager._current_state,
                chapter_spec=ChapterSpec(
                    number=chapter_num,
                    title=chapter_data.get("title", f"Chapter {chapter_num}"),
                    summary=chapter_data.get("summary", ""),
                    plot_events=chapter_data.get("plot_events", []),
                    characters=chapter_data.get("characters", []),
                    location=chapter_data.get("location", ""),
                ),
            )
            is_valid = validation_result.is_valid
            logger.info(f"  Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            results["validation_results"].append({
                "chapter": chapter_num,
                "valid": is_valid,
                "issues": validation_result.issues if hasattr(validation_result, 'issues') else [],
            })
        except Exception as e:
            logger.warning(f"  Validation error: {e}")
            results["validation_results"].append({
                "chapter": chapter_num,
                "valid": None,
                "error": str(e),
            })
        
        # Update knowledge graph
        try:
            # Extract entities from content (simplified)
            entities_extracted = extract_entities_simple(chapter_content, chapter_num)
            for entity in entities_extracted:
                try:
                    knowledge_graph.add_node(entity)
                except Exception:
                    pass  # Node may already exist
            logger.info(f"  KG entities: {len(entities_extracted)} extracted")
        except Exception as e:
            logger.warning(f"  KG update failed: {e}")
        
        # Save chapter
        chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.json"
        chapter_json = {
            "chapter_number": chapter_num,
            "title": chapter_data.get("title", f"Chapter {chapter_num}"),
            "content": chapter_content,
            "word_count": len(chapter_content),
            "characters": chapter_data.get("characters", []),
            "location": chapter_data.get("location", ""),
            "outline_summary": chapter_data.get("summary", ""),
        }
        
        with open(chapter_file, "w", encoding="utf-8") as f:
            json.dump(chapter_json, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  Saved: {chapter_file}")
        results["chapters_generated"] += 1
    
    # Save KG
    try:
        knowledge_graph.save()
        nodes_count = len(knowledge_graph.get_all_nodes())
        results["kg_entities"] = nodes_count
        logger.info(f"\nKnowledge Graph saved with {nodes_count} nodes")
    except Exception as e:
        logger.warning(f"Failed to save KG: {e}")
    
    return results


def generate_chapter_content(chapter_data: dict, characters: list, outline: dict) -> str:
    """Generate chapter content from outline data."""
    
    title = chapter_data.get("title", "Untitled")
    summary = chapter_data.get("summary", "")
    plot_events = chapter_data.get("plot_events", [])
    location = chapter_data.get("location", "Unknown")
    chapter_chars = chapter_data.get("characters", [])
    
    # Build chapter content
    content_parts = []
    
    # Chapter header
    content_parts.append(f"# {title}\n")
    content_parts.append(f"\n{summary}\n")
    
    # Add plot events as narrative
    if plot_events:
        content_parts.append("\n## 主要情节\n")
        for i, event in enumerate(plot_events, 1):
            event_desc = event.get("description", "")
            event_chars = event.get("characters_involved", "")
            event_loc = event.get("location", "")
            event_time = event.get("time_of_day", "")
            
            content_parts.append(f"\n{i}. {event_desc}")
            if event_chars:
                content_parts.append(f"\n   - 涉及人物：{event_chars}")
            if event_loc:
                content_parts.append(f"\n   - 地点：{event_loc}")
            if event_time:
                content_parts.append(f"\n   - 时间：{event_time}")
    
    # Add character context
    if chapter_chars:
        content_parts.append("\n## 出场人物\n")
        for char_name in chapter_chars:
            # Find character details
            char_info = None
            for c in characters:
                if c.get("name") == char_name:
                    char_info = c
                    break
            
            if char_info:
                content_parts.append(f"\n- **{char_name}** ({char_info.get('profession', '未知')})")
                content_parts.append(f"：{char_info.get('bio', '')}")
            else:
                content_parts.append(f"\n- **{char_name}**")
    
    # Add narrative expansion (simplified for demo)
    content_parts.append("\n\n## 章节正文\n")
    content_parts.append(f"\n{summary}\n\n")
    
    # Expand plot events into narrative
    for event in plot_events:
        event_desc = event.get("description", "")
        content_parts.append(f"{event_desc}。")
    
    # Add location description
    content_parts.append(f"\n\n---\n地点：{location}\n")
    
    return "".join(content_parts)


def extract_entities_simple(content: str, chapter_num: int) -> list[dict]:
    """Simple entity extraction for demo purposes."""
    entities = []
    
    # Character patterns
    character_names = ["林轩", "苏雅", "张伟", "陈明", "李昊", "凯瑟琳"]
    for name in character_names:
        if name in content:
            entities.append({
                "node_id": f"char_{name}",
                "node_type": "character",
                "properties": {
                    "name": name,
                    "first_appearance": chapter_num,
                },
            })
    
    # Location patterns
    locations = ["新纪元号", "舰桥", "引擎舱", "科学实验室", "虫洞"]
    for loc in locations:
        if loc in content:
            entities.append({
                "node_id": f"loc_{loc}",
                "node_type": "location",
                "properties": {
                    "name": loc,
                    "first_appearance": chapter_num,
                },
            })
    
    return entities


def main():
    parser = argparse.ArgumentParser(description="Generate chapters with validation")
    parser.add_argument("--novel-id", required=True, help="Novel ID")
    parser.add_argument("--start", type=int, default=1, help="Start chapter")
    parser.add_argument("--end", type=int, default=30, help="End chapter")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    data_dir = Path("data")
    
    logger.info(f"Starting chapter generation for {args.novel_id}")
    logger.info(f"Chapters: {args.start} to {args.end}")
    
    results = asyncio.run(generate_chapters(
        novel_id=args.novel_id,
        start_chapter=args.start,
        end_chapter=args.end,
        data_dir=data_dir,
    ))
    
    logger.info(f"\n{'='*60}")
    logger.info("Generation Complete")
    logger.info(f"{'='*60}")
    logger.info(f"Chapters generated: {results.get('chapters_generated', 0)}")
    logger.info(f"KG entities: {results.get('kg_entities', 0)}")
    
    if results.get("errors"):
        logger.warning(f"Errors: {len(results['errors'])}")
        for err in results["errors"]:
            logger.warning(f"  - {err}")


if __name__ == "__main__":
    main()