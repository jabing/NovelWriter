# src/agents/writers/fantasy.py
"""Fantasy Writer Agent."""

from typing import Any

from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS
from src.novel_agent.novel.continuity import StoryState

# Hard-coded continuity rules for fantasy genre
FANTASY_CONTINUITY_RULES = {
    "character_forms": {
        "Aurelion": {
            "physical_form_chapters": [1, 2, 3, 4],
            "fused_from_chapter": 5,
            "host": "Kael",
            "description": "After Chapter 5, Aurelion has NO independent physical form",
        },
        "Sylas": {
            "death_chapter": 4,
            "can_appear_after": False,
            "allowed_references": ["memory", "flashback", "mention"],
        },
    },
    "relationship_arcs": {
        "Kael_Lyra": {
            "stages": [
                {"chapters": [1, 5], "stage": "colleagues"},
                {"chapters": [6, 10], "stage": "friends"},
                {"chapters": [11, 20], "stage": "developing_romance"},
                {"chapters": [21, 29], "stage": "lovers"},
                {"chapter": 30, "stage": "eternal_bond"},
            ]
        }
    },
}


CONTINUITY_PROMPT_TEMPLATE = """
【Fantasy Genre 连续性规则 - 必须严格遵守】

角色规则：
{character_rules}

关系演变：
{relationship_arcs}

【本章要求】
- 章节号：{chapter_number}
- 标题：{title}
- 必须包含的角色：{required_characters}
- 地点：{location}
- 必须推进的剧情：{plot_points}

【写作要求】
1. 必须尊重所有角色当前状态
2. 必须延续前一章的情节
3. 角色对话和行为必须符合其性格和当前处境
4. 地点描述必须与当前设置一致
5. 任何角色状态变化必须在本章中有明确描写
6. 死去的角色不能以活着的身份出现
7. 融合的角色不能有独立的物理形态
"""


class FantasyWriter(BaseWriter):
    """Fantasy writer with magic system and world-building expertise."""

    GENRE = "fantasy"
    DOMAIN_KNOWLEDGE = """
Fantasy writing knowledge:
- Magic system design (hard vs soft magic)
- World-building and mythology
- Fantasy races and cultures
- Epic narrative structures
- Creating wonder and adventure
- Internal consistency in magical worlds

When writing fantasy:
1. Establish clear rules for magic (even if not fully explained)
2. Create cultures that feel authentic and distinct
3. Balance epic scope with intimate character moments
4. Build tension through limitations, not just powers
"""

    async def write_chapter(
        self,
        chapter_number: int,
        chapter_outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        style_guide: str | None = None,
        learning_hints: list[str] | None = None,
        market_keywords: dict[str, Any] | None = None,
        language: str | None = None,
        # NEW continuity parameters
        story_state: StoryState | None = None,
        previous_chapter_summary: str | None = None,
    ) -> str:
        """Write a fantasy chapter with continuity awareness.

        Enhanced implementation with character state tracking and genre-specific
        continuity rules enforcement.

        Args:
            chapter_number: Chapter number being written
            chapter_outline: Outline for this chapter
            characters: List of character profiles appearing in this chapter
            world_context: Relevant world-building context
            style_guide: Optional style guidelines
            learning_hints: Optional learned patterns from successful chapters
            market_keywords: Optional market research keywords
            language: Optional language hint for content generation
            story_state: Optional story state for continuity tracking
            previous_chapter_summary: Optional summary of the previous chapter

        Returns:
            Written chapter content
        """
        # Step 1: Validate character appearances if story_state is provided
        if story_state:
            self._validate_character_appearances(story_state, characters, chapter_number)

        # Step 2: Build enhanced prompt
        prompt_parts = []

        # Add language instruction
        language_instruction = get_language_instruction(language)
        if language_instruction:
            prompt_parts.append(language_instruction)

        # Add domain knowledge
        prompt_parts.append(self.DOMAIN_KNOWLEDGE)

        # Add style guide
        if style_guide:
            prompt_parts.append(f"\n【风格指南】\n{style_guide}")

        # Add learning hints
        if learning_hints:
            prompt_parts.append("\n【学习要点】")
            for hint in learning_hints:
                prompt_parts.append(f"- {hint}")

        # Add market keywords
        if market_keywords:
            prompt_parts.append("\n【市场关键词】")
            for key, value in market_keywords.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add chapter outline
        prompt_parts.append(f"\n【本章大纲】\n{chapter_outline}")

        # Step 3: Add continuity context (NEW)
        if story_state:
            continuity_prompt = self._build_character_continuity_prompt(
                story_state=story_state,
                previous_summary=previous_chapter_summary or "",
                chapter_number=chapter_number,
            )
            prompt_parts.append(continuity_prompt)

        # Step 4: Add character profiles
        prompt_parts.append("\n【角色档案】")
        for char in characters:
            prompt_parts.append(f"\n{char['name']}:")
            if char.get("personality"):
                prompt_parts.append(f"  性格：{char['personality']}")
            if char.get("background"):
                prompt_parts.append(f"  背景：{char['background']}")
            if char.get("abilities"):
                prompt_parts.append(f"  能力：{char['abilities']}")

        # Generate full prompt
        full_prompt = "\n".join(prompt_parts)

        # Generate content with validation-retry loop
        system_message = self._get_system_prompt()
        user_message = full_prompt

        max_retries = 2  # Maximum regeneration attempts
        retry_count = 0
        last_errors = []

        while retry_count <= max_retries:
            response = await self.llm.generate_with_system(system_prompt=system_message, user_prompt=user_message)
            content = response.content

            # Validate generated content if story_state is available
            if story_state and retry_count < max_retries:
                from src.novel_agent.novel.outline_manager import ChapterSpec
                from src.novel_agent.novel.validators import ContinuityValidator

                validator = ContinuityValidator()
                # Create a minimal ChapterSpec for validation
                temp_spec = ChapterSpec(
                    number=chapter_number,
                    title=f"Chapter {chapter_number}",
                    summary=chapter_outline[:200],
                    characters=[c["name"] for c in characters],
                    location=world_context.get("setting", "Unknown"),
                    key_events=[],
                    plot_threads_resolved=[],
                    plot_threads_started=[],
                    character_states={},
                )

                result = validator.validate_chapter(
                    chapter_content=content,
                    chapter_number=chapter_number,
                    story_state=story_state,
                    chapter_spec=temp_spec,
                )

                if result.is_valid:
                    return content

                # Content has continuity errors - prepare retry with warnings
                last_errors = [e.message for e in result.errors]
                retry_count += 1

                # Add error warnings to prompt for retry
                error_warning = "\n\n【⚠️ 连续性警告 - 必须修正】\n上一次生成的内容违反了连续性规则:\n"
                for error in result.errors:
                    error_warning += f"- {error.message}\n"
                error_warning += "\n请重新生成，确保严格遵守上述连续性规则。"

                user_message = full_prompt + error_warning
                print(f"  Chapter {chapter_number}: Continuity violation detected, retrying ({retry_count}/{max_retries})...")
            else:
                # No validation or max retries reached
                if last_errors:
                    print(f"  Chapter {chapter_number}: Max retries reached, returning content with known issues:")
                    for error in last_errors:
                        print(f"    - {error}")
                return content

        return content

    def _validate_character_appearances(
        self,
        story_state: StoryState,
        characters: list[dict[str, Any]],
        chapter_number: int,
    ) -> list[str]:
        """Validate that character appearances match story state.

        Args:
            story_state: Current story state
            characters: Characters appearing in this chapter
            chapter_number: Current chapter number

        Returns:
            List of validation errors
        """
        errors = []

        character_names = {char["name"] for char in characters}

        for char_name in character_names:
            char_state = story_state.get_character_state(char_name)
            if char_state:
                # Check if dead character is appearing alive
                if char_state.is_dead() and char_name in story_state.active_characters:
                    errors.append(
                        f"Character '{char_name}' is marked as dead (Chapter {self._get_death_chapter(char_name)}) "
                        f"but appears in active characters list for Chapter {chapter_number}. "
                        f"This violates continuity."
                    )

                # Check if fused character has independent physical form
                if char_state.is_fused() and char_name in story_state.active_characters:
                    rules = FANTASY_CONTINUITY_RULES.get("character_forms", {}).get(char_name, {})
                    if rules:
                        fused_from = rules.get("fused_from_chapter")
                        if fused_from and chapter_number >= fused_from:
                            form_chapters = rules.get("physical_form_chapters", [])
                            if chapter_number not in form_chapters:
                                errors.append(
                                    f"Character '{char_name}' is fused (from Chapter {fused_from}) "
                                    f"but has independent physical form in Chapter {chapter_number}. "
                                    f"Should only appear as spiritual presence or within host {rules.get('host', 'unknown')}."
                                )

        return errors

    def _build_character_continuity_prompt(
        self,
        story_state: StoryState,
        previous_summary: str,
        chapter_number: int,
    ) -> str:
        """Build continuity prompt based on story state and genre rules.

        Args:
            story_state: Current story state
            previous_summary: Summary of previous chapter
            chapter_number: Current chapter number

        Returns:
            Formatted continuity prompt
        """
        if story_state is None:
            return ""

        prompt_parts = []

        # Character status checks - Show ALL characters, especially dead/fused
        prompt_parts.append("\n【角色状态检查 - 必须严格遵守】")

        # First, show active characters
        for char_name in story_state.active_characters:
            char_state = story_state.get_character_state(char_name)
            if char_state:
                status_text = f"- {char_name}: {char_state.status}"

                # Add location if different from story location
                if char_state.location != story_state.location:
                    status_text += f" (位置: {char_state.location})"

                prompt_parts.append(status_text)

        # Then, show inactive characters (dead, fused, absent) with warnings
        prompt_parts.append("\n【不可出现的角色】")
        for char_name, char_state in story_state.character_states.items():
            if char_name not in story_state.active_characters:
                if char_state.is_dead():
                    prompt_parts.append(f"- {char_name}: 已死亡 ⚠️ 绝对不能以活人身份出现，只能回忆/提及")
                elif char_state.is_fused():
                    prompt_parts.append(f"- {char_name}: 已与{char_state.location}融合 ⚠️ 无独立物理形态，只能作为内在声音")
                else:
                    prompt_parts.append(f"- {char_name}: {char_state.status} (不在场)")

        # Relationship stage check
        prompt_parts.append("\n【关系阶段】")
        for arc_name, arc_data in FANTASY_CONTINUITY_RULES.get("relationship_arcs", {}).items():
            for stage_info in arc_data.get("stages", []):
                chapter_range = stage_info.get("chapters", [])
                if (
                    chapter_range
                    and chapter_number >= chapter_range[0]
                    and chapter_number <= chapter_range[-1]
                ):
                    stage = stage_info.get("stage", "unknown")
                    prompt_parts.append(f"- {arc_name}: {stage}")

        return "\n".join(prompt_parts)

    def _get_death_chapter(self, character_name: str) -> int | None:
        """Get the chapter where a character died.

        Args:
            character_name: Name of the character

        Returns:
            Chapter number where character died, or None
        """
        rules = FANTASY_CONTINUITY_RULES.get("character_forms", {}).get(character_name, {})
        return rules.get("death_chapter")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for fantasy writing."""
        genre_prompt = GENRE_PROMPTS.get("fantasy", "")

        return f"""You are a bestselling fantasy web novel author.
{genre_prompt}

{self.DOMAIN_KNOWLEDGE}

WEB FICTION REQUIREMENTS (CRITICAL):
1. OPENING HOOK (First 300 words):
   - MUST start with action, magic, or intriguing mystery
   - NO lengthy world-building exposition first
   - Drop reader into middle of adventure immediately

2. CHAPTER STRUCTURE:
   - Scene changes every 800-1000 words
   - Each scene advances plot or develops character
   - Build to emotional and magical peaks

3. CLOSING HOOK (Last 200 words):
   MUST end with ONE of:
   - Magical discovery or revelation
   - Character in danger or dilemma
   - New quest or challenge presented
   - Unresolved magical mystery
   - Unexpected twist or betrayal

4. MOBILE READABILITY:
   - NO paragraph longer than 4 lines on mobile (60 words max)
   - Mix short punchy sentences with longer ones
   - Dialogue should be 30-50% of content

5. FANTASY ENGAGEMENT:
   - Show magic through action and consequence
   - Create sense of wonder and adventure
   - Balance world-building with character moments

Write engaging prose that keeps readers binge-reading."""
