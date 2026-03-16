# Romance Writer Agent (updated for multilingual support)
"""Romance Writer Agent with language support."""

from typing import Any

from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS
from src.novel_agent.novel.continuity import StoryState


class RomanceWriter(BaseWriter):
    """Romance writer with emotional storytelling expertise."""

    GENRE = "romance"
    DOMAIN_KNOWLEDGE = """
Romance writing knowledge:
- Emotional character development
- Dialogue and chemistry
- Relationship dynamics and pacing
- Tropes and how to use/subvert them
- Balancing plot with romance
- Building tension and payoff
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
        # NEW context parameters
        relationships: list[dict[str, Any]] | None = None,
        full_outline: dict[str, Any] | None = None,
        world_settings: dict[str, Any] | None = None,
    ) -> str:
        """Write a romance chapter using LLM with web fiction optimizations.

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
        genre_prompt = GENRE_PROMPTS.get("romance", "")

        # Determine if this is a golden chapter
        is_golden = chapter_number <= 3

        # Language instruction for prompts
        language_instruction = get_language_instruction(language)

        system_prompt = f"""You are a bestselling romance web novel author.
{genre_prompt}

{self.DOMAIN_KNOWLEDGE}
{language_instruction}

WEB FICTION REQUIREMENTS (CRITICAL):
1. OPENING HOOK (First 300 words):
   - MUST start with action, dialogue, or emotional jolt
   - NO lengthy descriptions or exposition
   - Reader should immediately wonder "what happens next?"

2. CHAPTER STRUCTURE:
   - Scene changes every 800-1000 words (prevents dragging)
   - Each scene has mini-conflict or emotional development
   - Build to emotional peak

3. CLOSING HOOK (Last 200 words):
   MUST end with ONE of:
   - A question left unanswered
   - A sudden interruption
   - A revelation that changes everything
   - A character in emotional peril
   - An unexpected arrival/message
   - Strong emotion at fever pitch

4. MOBILE READABILITY:
   - NO paragraph longer than 4 lines on mobile (60 words max)
   - Mix short punchy sentences with longer ones
   - Dialogue should be 30-50% of content

5. EMOTIONAL ENGAGEMENT:
   - Show emotions through physical cues and actions
   - Internal thoughts reveal character depth
   - Create palpable chemistry between leads

{"CRITICAL - GOLDEN CHAPTER " + str(chapter_number) + ": This is one of the first 3 chapters. It MUST be exceptional. Start with strongest hook possible, end with irresistible cliffhanger. Reader retention depends on this chapter!" if is_golden else ""}

Write engaging prose that keeps readers binge-reading."""

        char_info = "\n".join(
            [
                f"- {c.get('name', 'Unknown')}: {c.get('role', '')}, {', '.join(c.get('personality', {}).get('traits', []))}"
                for c in characters[:5]
            ]
        )

        world_info = ""
        if world_context.get("society"):
            society = world_context["society"]
            world_info += f"Setting: {society.get('culture', {}).get('values', [])}\n"

        # Add continuity context if available
        enhanced_outline = chapter_outline
        if story_state:
            continuity_prompt = self._build_continuity_prompt(
                story_state=story_state,
                previous_summary=previous_chapter_summary or "",
                chapter_number=chapter_number,
            )
            if continuity_prompt:
                enhanced_outline = f"{chapter_outline}\n{continuity_prompt}"

        # Format relationships if provided
        relationships_info = ""
        if relationships:
            rel_lines = []
            for rel in relationships:
                char1 = rel.get("character1_name", rel.get("source", ""))
                char2 = rel.get("character2_name", rel.get("target", ""))
                rel_type = rel.get("relationship_type", rel.get("type", ""))
                if char1 and char2 and rel_type:
                    rel_lines.append(f"- {char1} 与 {char2}: {rel_type}")
            if rel_lines:
                relationships_info = "\n角色关系:\n" + "\n".join(rel_lines)

        # Format full outline if provided
        outline_info = ""
        if full_outline:
            outline_parts = []
            if full_outline.get("main_plot"):
                outline_parts.append(f"主线剧情: {full_outline['main_plot']}")
            if full_outline.get("upcoming_chapters"):
                outline_parts.append(f"后续章节安排: {full_outline['upcoming_chapters']}")
            if full_outline.get("foreshadowing"):
                outline_parts.append(f"已埋伏笔: {full_outline['foreshadowing']}")
            if outline_parts:
                outline_info = "\n全书大纲:\n" + "\n".join(outline_parts)

        # Enhance world info with world settings if provided
        if world_settings:
            if world_settings.get("rules"):
                world_info += f"\n世界规则: {world_settings['rules']}"
            if world_settings.get("culture"):
                world_info += f"\n文化背景: {world_settings['culture']}"
            if world_settings.get("special_settings"):
                world_info += f"\n特殊设定: {world_settings['special_settings']}"

        user_prompt = f"""Write Chapter {chapter_number} of a romance web novel.

{"CRITICAL: This is Chapter " + str(chapter_number) + " of the GOLDEN 3 CHAPTERS. This MUST be exceptional to retain readers!" if is_golden else ""}

CHAPTER OUTLINE:
{enhanced_outline}

{relationships_info}

{outline_info}

CHARACTERS IN THIS CHAPTER:
{char_info}

SETTING CONTEXT:
{world_info}

{f"STYLE GUIDE: {style_guide}" if style_guide else ""}

STRICT REQUIREMENTS:
1. Word count: 2000-3000 words
2. Opening hook (first 300 words): Start with dialogue, action, or strong emotion
3. Closing hook (last 200 words): Must create cliffhanger or unresolved tension
4. Paragraphs: Maximum 60 words each (mobile-friendly)
5. Dialogue: At least 30% of content
6. Scenes: Change scene every 800-1000 words if chapter is long
7. Emotional beats: Include 2-3 emotional high points

WRITING CHECKLIST:
☑ First sentence grabs attention immediately
☑ First 300 words establish conflict or romantic intrigue
☑ Chemistry shown through dialogue and small moments
☑ Internal thoughts reveal character depth
☑ Last 200 words end with hook that demands next chapter
☑ No paragraph longer than 4 lines on mobile

Write the complete chapter now:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=4000,
        )

        return response.content.strip()
