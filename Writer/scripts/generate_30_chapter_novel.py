#!/usr/bin/env python3
"""Automated script to generate a 30-chapter fantasy novel using Infini AI."""

import os
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


import asyncio
import json
import logging
from typing import Any
from src.llm.infini import InfiniAILLM
from src.agents.writers.fantasy import FantasyWriter
from src.studio.core.state import get_studio_state, NovelProject, ProjectStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NovelGenerator:
    """Automated novel generation script."""

    def __init__(self, project_id: str = "novel_bdae7258"):
        """Initialize generator.

        Args:
            project_id: Project ID for the novel
        self.project_id = project_id
        self.state = get_studio_state()
        self.project = self.state.get_project(project_id)
        self.llm = InfiniAILLM()
        self.writer = FantasyWriter(name="FantasyWriter", llm=self.llm)

        # Output paths
        self.novel_dir = Path("data/openviking/memory/novels") / project_id
        self.chapters_dir = self.novel_dir / "chapters"
    def setup_directories(self) -> None:
        """Create necessary directories."""
        logger.info(f"Setting up directories in {self.novel_dir}")
        self.novel_dir.mkdir(parents=True, exist_ok=True)
        self.chapters_dir.mkdir(parents=True, exist_ok=True)

    async def generate_outline(self) -> str:
        """Generate novel outline with 3 acts, 30 chapters."""
        logger.info("Generating novel outline...")

        system_prompt = """You are an expert fantasy novelist and story structure consultant."""

        user_prompt = """Create a detailed 30-chapter outline for an English fantasy novel about a young mage who discovers an ancient dragon's secret in a world where magic is dying. The protagonist must choose between saving magic or letting it fade to restore balance to the world.

Structure:
- Act 1: Chapters 1-10 (The Awakening) - Introduction, discovery, first trials
- Act 2: Chapters 11-20 (The Journey) - Quest, challenges, character development
- Act 3: Chapters 21-30 (The Sacrifice) - Climax, final choice, resolution

For each chapter, provide:
1. Chapter number and title
2. Main plot points
3. Character appearances
4. Key conflicts
5. Setting locations

Main Characters:
- Kael Vane: Young protagonist mage, discovers dragon secret
- Lyra Ashford: Love interest, scholar of ancient magic
- Malachar: Antagonist, wants to control the last magic
- Ember: Ancient dragon, source of the dying magic

The story should explore themes of sacrifice, choice, and the cost of power."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=1.0,  # Infini AI requires exactly 1.0
            max_tokens=8000,
        )

        outline = response.content
        logger.info(f"Generated outline ({len(outline)} characters)")

        # Save outline
        outline_path = self.novel_dir / "outline.md"
        with open(outline_path, "w", encoding="utf-8") as f:
            f.write(outline)
        logger.info(f"Saved outline to {outline_path}")

        return outline

    async def generate_characters(self) -> list[dict[str, Any]]:
        """Generate character profiles."""
        logger.info("Generating character profiles...")

        system_prompt = """You are an expert character developer for fantasy novels."""

        user_prompt = """Create detailed character profiles for the following fantasy novel characters:

1. Kael Vane (Protagonist) - Young mage who discovers an ancient dragon's secret
2. Lyra Ashford (Love Interest) - Scholar of ancient magic
3. Malachar (Antagonist) - Wants to control the last magic
4. Ember (Dragon) - Ancient dragon, source of the dying magic

For each character, provide:
- Name and role
- Age and appearance
- Personality traits (3-5 key traits)
- Background and history
- Motivation and goals
- Strengths and weaknesses
- Relationship to other characters

Format as JSON array of character objects."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=1.0,
            max_tokens=4000,
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            content = response.content
            start = content.find("[")
            end = content.rfind("]") + 1
            json_str = content[start:end]
            characters = json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse character JSON: {e}")
            # Fallback to manual structure
            characters = [
                {
                    "name": "Kael Vane",
                    "role": "protagonist",
                    "personality": {"traits": ["determined", "curious", "self-sacrificing"]},
                },
                {
                    "name": "Lyra Ashford",
                    "role": "love_interest",
                    "personality": {"traits": ["intelligent", "compassionate", "brave"]},
                },
                {
                    "name": "Malachar",
                    "role": "antagonist",
                    "personality": {"traits": ["ambitious", "ruthless", "manipulative"]},
                },
                {
                    "name": "Ember",
                    "role": "dragon",
                    "personality": {"traits": ["wise", "ancient", "mysterious"]},
                },
            ]

        logger.info(f"Generated {len(characters)} character profiles")

        # Save characters
        chars_path = self.novel_dir / "characters.json"
        with open(chars_path, "w", encoding="utf-8") as f:
            json.dump(characters, f, indent=2)
        logger.info(f"Saved characters to {chars_path}")

        return characters

    async def generate_chapter(
        self,
        chapter_number: int,
        outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
    ) -> str:
        """Generate a single chapter using FantasyWriter.

        Args:
            chapter_number: Chapter number to generate
            outline: Full novel outline
            characters: List of character profiles
            world_context: World-building context

        Returns:
            Generated chapter content
        """
        logger.info(f"Generating Chapter {chapter_number}/30...")

        # Extract chapter outline from full outline
        chapter_lines = []
        in_chapter = False
        for line in outline.split("\n"):
            if f"Chapter {chapter_number}" in line:
                in_chapter = True
                chapter_lines.append(line)
            elif in_chapter:
                if line.startswith("Chapter ") or line.startswith("Act "):
                    if f"Chapter {chapter_number}" not in line:
                        break
                chapter_lines.append(line)

        chapter_outline = "\n".join(chapter_lines)

        # Use FantasyWriter to generate content
        try:
            content = await self.writer.write_chapter(
                chapter_number=chapter_number,
                chapter_outline=chapter_outline,
                characters=characters,
                world_context=world_context,
                language="en",  # English language
            )
            logger.info(f"Chapter {chapter_number} generated ({len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"Failed to generate chapter {chapter_number}: {e}")
            raise

    async def generate_all_chapters(
        self,
        outline: str,
        characters: list[dict[str, Any]],
        start_chapter: int = 1,
        end_chapter: int = 30,
    ) -> None:
        """Generate all chapters with retry logic.

        Args:
            outline: Full novel outline
            characters: List of character profiles
            start_chapter: First chapter to generate (for resumability)
            end_chapter: Last chapter to generate
        """
        # World context for fantasy setting
        world_context = {
            "rules": {
                "name": "The Dying Magic",
                "core_rules": [
                    {
                        "rule": "Magic is Fading",
                        "description": "The world's magic is slowly disappearing, threatening all life",
                    },
                    {
                        "rule": "Dragon's Secret",
                        "description": "Ember holds the key to restoring or ending magic forever",
                    },
                ],
            },
            "locations": [
                {
                    "name": "The Academy",
                    "description": "Kael's school of magic, where he discovers the secret",
                },
                {"name": "Ember's Lair", "description": "Ancient dragon's hidden sanctuary"},
            ],
        }

        total_words = 0

        for chapter_num in range(start_chapter, end_chapter + 1):
            max_retries = 3
            retry_count = 0
            content = None

            while retry_count < max_retries:
                try:
                    content = await self.generate_chapter(
                        chapter_number=chapter_num,
                        outline=outline,
                        characters=characters,
                        world_context=world_context,
                    )
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(
                            f"Chapter {chapter_num} failed (attempt {retry_count}/{max_retries}): {e}. Retrying in 30s..."
                        )
                        await asyncio.sleep(30)
                    else:
                        logger.error(f"Chapter {chapter_num} failed after {max_retries} attempts")
                        raise

            if content:
                # Validate minimum word count
                MIN_WORDS = 500
                word_count = len(content.split())

                if word_count < MIN_WORDS:
                    logger.warning(
                        f"Chapter {chapter_num} content too short ({word_count} words). Retrying..."
                    )
                    if retry_count < max_retries:
                        retry_count += 1
                        await asyncio.sleep(30)
                        continue
                    else:
                        logger.error(f"Chapter {chapter_num} failed - max retries reached")
                        content = f"[Chapter {chapter_num} - Generation failed]"
                        word_count = 0

                # Save chapter
                chapter_filename = f"chapter_{chapter_num:03d}.md"
                chapter_path = self.chapters_dir / chapter_filename

                with open(chapter_path, "w", encoding="utf-8") as f:
                    f.write(content)

                total_words += word_count
                progress = (chapter_num / end_chapter) * 100

                logger.info(
                    f"✓ Chapter {chapter_num} saved ({word_count} words) "
                    f"Progress: {progress:.1f}% | Total: {total_words:,} words"
                )
        logger.info(f"Novel generation complete! Total words: {total_words:,}")

    async def run(self, start_chapter: int = 1) -> None:
        """Run the complete novel generation workflow.

        Args:
            start_chapter: Starting chapter (for resumability)
        """
        logger.info(f"Starting novel generation for project: {self.project_id}")

        if not self.project:
            logger.error(f"Project not found: {self.project_id}")
            return

        logger.info(f"Title: {self.project.title}")
        logger.info(f"Genre: {self.project.genre}")
        logger.info(f"Target: {self.project.target_chapters} chapters")

        # Setup directories
        self.setup_directories()

        # Generate outline
        outline = await self.generate_outline()

        # Generate characters
        characters = await self.generate_characters()

        # Generate chapters
        await self.generate_all_chapters(
            outline=outline,
            characters=characters,
            start_chapter=start_chapter,
            end_chapter=self.project.target_chapters,
        )

        # Update project status
        self.project.status = ProjectStatus.WRITING
        self.project.completed_chapters = self.project.target_chapters
        self.state.update_project(self.project)

        logger.info("Novel generation workflow complete!")


async def main():
    """Main entry point."""
    import sys

    start_chapter = 1
    if len(sys.argv) > 1:
        try:
            start_chapter = int(sys.argv[1])
        except ValueError:
            print(f"Invalid start chapter: {sys.argv[1]}")
            sys.exit(1)

    generator = NovelGenerator(project_id="novel_bdae7258")
    await generator.run(start_chapter=start_chapter)


if __name__ == "__main__":
    asyncio.run(main())
