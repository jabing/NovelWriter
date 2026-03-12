#!/usr/bin/env python3
"""Complete novel generation script for Infini AI (Kimi K2.5)."""

import json
import os
from pathlib import Path

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

import asyncio

from src.agents.writers.fantasy import FantasyWriter
from src.llm.infini import InfiniAILLM

# Novel settings
PROJECT_ID = "novel_bdae7258"
NOVEL_DIR = Path(f"data/openviking/memory/novels/{PROJECT_ID}")
CHAPTERS_DIR = NOVEL_DIR / "chapters"


async def generate_characters(llm):
    """Generate character profiles."""
    print("\n=== Generating Characters ===")

    system_prompt = "You are an expert character developer for fantasy novels."

    user_prompt = """Create detailed character profiles for a fantasy novel about a mage named Kael who discovers an ancient dragon named Aurelion.

Characters needed:
1. Kael Vane - Young mage, protagonist
2. Lyra Ashford - Scholar of ancient magic, love interest
3. Malachar - Villain, wants to control the last magic
4. Aurelion - Ancient dragon, source of magic

For each character, provide in JSON format:
{
  "name": "Name",
  "role": "Role",
  "age": "Age",
  "appearance": "Description",
  "personality": {
    "traits": ["trait1", "trait2", "trait3"]
  },
  "background": "Description",
  "motivation": "Description"
}

Return a JSON array with all 4 characters. JSON ONLY, no markdown."""

    print("Requesting character profiles from Infini AI...")
    response = await llm.generate_with_system(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=1.0,
        max_tokens=4000,
    )

    content = response.content

    # Try to extract JSON
    json_start = content.find("[")
    json_end = content.rfind("]") + 1

    if json_start == -1 or json_end == 0:
        print("No JSON found in response")
        print(f"Response preview: {content[:500]}")

        # Fallback: Create basic character structure
        characters = [
            {
                "name": "Kael Vane",
                "role": "protagonist",
                "age": 22,
                "appearance": "Young man with dark hair and keen eyes",
                "personality": {"traits": ["curious", "determined", "brave"]},
                "background": "Junior archivist mage",
                "motivation": "Discover the truth about magic",
            },
            {
                "name": "Lyra Ashford",
                "role": "love_interest",
                "age": 24,
                "appearance": "Elegant scholar with reading glasses",
                "personality": {"traits": ["intelligent", "compassionate", "methodical"]},
                "background": "Archivist of forbidden lore",
                "motivation": "Help Kael uncover the truth",
            },
            {
                "name": "Malachar",
                "role": "antagonist",
                "age": 45,
                "appearance": "Tall imposing figure in dark robes",
                "personality": {"traits": ["ruthless", "ambitious", "cunning"]},
                "background": "High Council member",
                "motivation": "Control the last magic",
            },
            {
                "name": "Aurelion",
                "role": "dragon",
                "age": "Ancient",
                "appearance": "Crystalline dragon, imprisoned and emaciated",
                "personality": {"traits": ["wise", "mysterious", "ancient"]},
                "background": "Physical heart of magic itself",
                "motivation": "Restore natural magic flow",
            },
        ]
    else:
        json_str = content[json_start:json_end]
        try:
            characters = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"JSON string: {json_str[:500]}")
            # Use fallback
            characters = []

    # Save characters
    chars_path = NOVEL_DIR / "characters.json"
    with open(chars_path, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2)

    print(f"✓ Generated {len(characters)} characters")
    print(f"✓ Saved to {chars_path}")

    return characters


async def generate_outline(llm):
    """Generate novel outline."""
    print("\n=== Generating Novel Outline ===")

    system_prompt = "You are an expert fantasy novelist and story structure consultant."

    user_prompt = """Create a detailed 30-chapter outline for an English fantasy novel about a young mage named Kael who discovers an ancient dragon's secret in a world where magic is dying. The protagonist must choose between saving magic or letting it fade to restore balance to the world.

Structure:
- Act 1: Chapters 1-10 (The Awakening)
- Act 2: Chapters 11-20 (The Journey)
- Act 3: Chapters 21-30 (The Sacrifice)

For each chapter, provide:
Chapter N: [Title]
- Main plot points
- Characters involved
- Key conflicts
- Setting

Focus on creating compelling hooks and clear progression."""

    print("Requesting outline from Infini AI...")
    response = await llm.generate_with_system(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=1.0,
        max_tokens=8000,
    )

    outline = response.content

    # Save outline
    outline_path = NOVEL_DIR / "outline.md"
    with open(outline_path, "w", encoding="utf-8") as f:
        f.write(outline)

    print(f"✓ Generated outline ({len(outline)} characters)")
    print(f"✓ Saved to {outline_path}")

    return outline


async def generate_chapters(llm, writer, outline, characters, start_chapter=1, end_chapter=30):
    """Generate all chapters."""
    print(f"\n=== Generating Chapters {start_chapter}-{end_chapter} ===")

    # World context
    world_context = {
        "rules": {
            "name": "The Dying Magic",
            "core_rules": [
                {
                    "rule": "Magic is Fading",
                    "description": "The world's magic is slowly disappearing",
                },
                {
                    "rule": "Dragon's Secret",
                    "description": "Aurelion holds the key to restoring magic",
                },
            ],
        },
        "locations": [
            {"name": "The Academy", "description": "Kael's school of magic"},
            {"name": "Caverns of Echoing Stone", "description": "Where Aurelion is imprisoned"},
            {"name": "Capital City", "description": "Built atop magical wells"},
        ],
    }

    total_words = 0

    for chapter_num in range(start_chapter, end_chapter + 1):
        # Extract chapter outline
        chapter_lines = []
        in_chapter = False
        for line in outline.split("\n"):
            if f"Chapter {chapter_num}" in line:
                in_chapter = True
                chapter_lines.append(line)
            elif in_chapter:
                if line.startswith("Chapter ") and f"Chapter {chapter_num}" not in line:
                    break
                chapter_lines.append(line)

        chapter_outline = "\n".join(chapter_lines)

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(
                    f"\nGenerating Chapter {chapter_num}/30 (Attempt {attempt + 1}/{max_retries})..."
                )

                content = await writer.write_chapter(
                    chapter_number=chapter_num,
                    chapter_outline=chapter_outline,
                    characters=characters,
                    world_context=world_context,
                    language="en",
                )

                # Validate content has minimum words
                word_count = len(content.split())
                MIN_WORDS = 500  # Minimum words for a valid chapter

                if word_count < MIN_WORDS:
                    # Content too short - don't save, retry
                    print(f"  ✗ Content too short ({word_count} words, need {MIN_WORDS})")
                    if attempt < max_retries - 1:
                        print("  Retrying in 30s...")
                        await asyncio.sleep(30)
                        continue
                    else:
                        print(f"  ✗ Failed after {max_retries} attempts - skipping chapter")
                        # Save placeholder to avoid completely empty file
                        content = f"[Chapter {chapter_num} - Generation failed, needs manual regeneration]"
                        word_count = 0

                # Save chapter
                CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
                chapter_path = CHAPTERS_DIR / f"chapter_{chapter_num:03d}.md"

                with open(chapter_path, "w", encoding="utf-8") as f:
                    f.write(content)

                total_words += word_count
                progress = (chapter_num / end_chapter) * 100

                print(f"✓ Chapter {chapter_num} completed ({word_count} words)")
                print(f"  Progress: {progress:.1f}% | Total: {total_words:,} words")
                print(f"  Saved to {chapter_path}")

                break

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ✗ Failed: {e}. Retrying in 30s...")
                    await asyncio.sleep(30)
                else:
                    print(f"  ✗ Failed after {max_retries} attempts")
                    raise

    print("\n=== Generation Complete ===")
    print(f"Total chapters: {end_chapter - start_chapter + 1}")
    print(f"Total words: {total_words:,}")


async def main():
    """Main execution."""
    print("=" * 60)
    print("NOVEL GENERATION - The Last Dragon Mage")
    print("LLM: Infini AI (Kimi K2.5)")
    print("=" * 60)

    # Create directories
    NOVEL_DIR.mkdir(parents=True, exist_ok=True)
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize LLM and writer
    llm = InfiniAILLM()
    writer = FantasyWriter(name="FantasyWriter", llm=llm)

    # Check if outline already exists
    outline_path = NOVEL_DIR / "outline.md"
    if outline_path.exists():
        print("✓ Outline already exists, loading...")
        with open(outline_path) as f:
            outline = f.read()
    else:
        outline = await generate_outline(llm)

    # Check if characters already exist
    chars_path = NOVEL_DIR / "characters.json"
    if chars_path.exists():
        print("✓ Characters already exist, loading...")
        with open(chars_path) as f:
            characters = json.load(f)
    else:
        characters = await generate_characters(llm)

    # Generate chapters
    print("\n" + "=" * 60)
    print("Starting chapter generation...")
    print("Note: Each chapter may take 30-60 seconds")
    print("=" * 60)

    await generate_chapters(llm, writer, outline, characters, start_chapter=1, end_chapter=30)

    print("\n" + "=" * 60)
    print("NOVEL GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
