# src/agents/writers/history.py
"""History Writer Agent."""

from typing import Any

from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS
from src.novel_agent.novel.continuity import StoryState


class HistoryWriter(BaseWriter):
    """Historical fiction writer with period expertise."""

    GENRE = "history"
    DOMAIN_KNOWLEDGE = """
Historical knowledge for accurate period writing:
- Major historical events and their timelines
- Daily life details across different eras
- Social hierarchies and customs
- Period-appropriate language and expressions
- Historical weapons, clothing, architecture
- Political systems and governance
- Economic systems and trade

When writing historical content:
1. Research the specific time period thoroughly
2. Avoid anachronisms (verify technology, language, customs)
3. Balance accuracy with narrative engagement
4. Consider different perspectives of the era
5. Use period-appropriate dialogue without being impenetrable
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
        """Write a historical fiction chapter using LLM.

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
        genre_prompt = GENRE_PROMPTS.get("history", "")
        language_instruction = get_language_instruction(language)

        system_prompt = f"""You are a bestselling historical fiction web novel author.
{genre_prompt}

{self.DOMAIN_KNOWLEDGE}
{language_instruction}

WEB FICTION REQUIREMENTS (CRITICAL):
1. OPENING HOOK (First 300 words):
   - MUST start with action, dialogue, or period-appropriate intrigue
   - NO dry historical exposition first
   - Drop reader into the drama immediately

2. CHAPTER STRUCTURE:
   - Scene changes every 800-1000 words
   - Each scene advances plot or reveals historical character
   - Build tension through historical conflicts

3. CLOSING HOOK (Last 200 words):
   MUST end with ONE of:
   - Historical revelation that changes everything
   - Character in peril from historical circumstances
   - New historical challenge or quest
   - Unresolved mystery from the past
   - Unexpected historical twist

4. MOBILE READABILITY:
   - NO paragraph longer than 4 lines on mobile (60 words max)
   - Mix short punchy sentences with longer ones
   - Dialogue should be 30-50% of content

5. HISTORICAL ENGAGEMENT:
   - Show history through character experience, not lectures
   - Use period details to immerse, not overwhelm
   - Balance accuracy with compelling narrative

{'CRITICAL - GOLDEN CHAPTER ' + str(chapter_number) + ': This is one of the first 3 chapters. It MUST be exceptional. Start with strongest hook possible, end with irresistible cliffhanger. Reader retention depends on this chapter!' if chapter_number <= 3 else ''}

Write engaging prose that keeps readers binge-reading."""

        char_info = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('role', '')}, {c.get('occupation', 'Unknown')}"
            for c in characters[:5]
        ])

        world_info = ""
        if world_context.get("rules"):
            rules = world_context["rules"]
            world_info += f"Time Period: {rules.get('time_period', 'Unknown')}\n"
        if world_context.get("history"):
            history = world_context["history"]
            world_info += f"Historical Context: {history.get('recent_history', '')[:200]}\n"
        if world_context.get("locations"):
            loc = world_context["locations"][0] if world_context["locations"] else {}
            world_info += f"Location: {loc.get('name', 'Unknown')} - {loc.get('description', '')[:150]}\n"

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

        user_prompt = f"""Write Chapter {chapter_number} of a historical fiction web novel.

{'CRITICAL: This is Chapter ' + str(chapter_number) + ' of the GOLDEN 3 CHAPTERS. This MUST be exceptional to retain readers!' if chapter_number <= 3 else ''}

CHAPTER OUTLINE:
{enhanced_outline}

CHARACTERS IN THIS CHAPTER:
{char_info}

HISTORICAL CONTEXT:
{world_info}

{f"STYLE GUIDE: {style_guide}" if style_guide else ""}

STRICT REQUIREMENTS:
1. Word count: 2000-3000 words
2. Opening hook (first 300 words): Start with action, dialogue, or period intrigue
3. Closing hook (last 200 words): Must create cliffhanger or unresolved tension
4. Paragraphs: Maximum 60 words each (mobile-friendly)
5. Dialogue: At least 30% of content
6. Scenes: Change scene every 800-1000 words if chapter is long
7. Show history through character experience, not lectures

WRITING CHECKLIST:
☑ First sentence grabs attention immediately
☑ First 300 words establish historical conflict or intrigue
☑ Period details woven naturally into narrative
☑ Character actions true to era but relatable
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
