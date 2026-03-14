# src/agents/writers/scifi.py
"""Sci-Fi Writer Agent."""

from typing import Any

from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS
from src.novel_agent.novel.continuity import StoryState


class SciFiWriter(BaseWriter):
    """Science fiction writer with physics and astronomy knowledge."""

    GENRE = "scifi"
    DOMAIN_KNOWLEDGE = """
Physics knowledge for sci-fi writing:
- Faster-than-light travel limitations and theoretical workarounds
- Time dilation effects at relativistic speeds
- Black hole physics (event horizon, Hawking radiation)
- Dyson spheres and megastructures
- Genetic engineering and its ethical implications
- Quantum mechanics and its narrative possibilities
- Exoplanet science and habitability

When writing sci-fi:
1. Ensure scientific plausibility or clearly establish fictional rules
2. Use correct terminology
3. Consider implications of technology on society
4. Balance hard science with emotional storytelling
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
        """Write a sci-fi chapter using LLM.

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
        genre_prompt = GENRE_PROMPTS.get("scifi", "")

        language_instruction = get_language_instruction(language)
        system_prompt = f"""You are a bestselling science fiction web novel author.
{genre_prompt}

{self.DOMAIN_KNOWLEDGE}
{language_instruction}

WEB FICTION REQUIREMENTS (CRITICAL):
1. OPENING HOOK (First 300 words):
   - MUST start with action, dialogue, or intriguing tech/mystery
   - NO lengthy exposition dumps
   - Drop reader into middle of situation immediately

2. CHAPTER STRUCTURE:
   - Scene changes every 800-1000 words
   - Each scene advances plot or reveals character
   - Build tension progressively

3. CLOSING HOOK (Last 200 words):
   MUST end with ONE of:
   - Discovery that changes everything
   - New threat or danger revealed
   - Character in peril or dilemma
   - Unanswered question about tech/mystery
   - Unexpected twist or revelation

4. MOBILE READABILITY:
   - NO paragraph longer than 4 lines on mobile (60 words max)
   - Mix short punchy sentences with longer ones
   - Dialogue should be 30-50% of content

5. SCI-FI ENGAGEMENT:
   - Show technology through use, not explanation
   - Create sense of wonder and discovery
   - Ground fantastic elements in relatable human experience

{"CRITICAL - GOLDEN CHAPTER " + str(chapter_number) + ": This is one of the first 3 chapters. It MUST be exceptional. Start with strongest hook possible, end with irresistible cliffhanger. Reader retention depends on this chapter!" if chapter_number <= 3 else ""}

Write engaging prose that keeps readers binge-reading."""

        # Format character info
        char_info = "\n".join(
            [
                f"- {c.get('name', 'Unknown')}: {c.get('role', '')}, {', '.join(c.get('personality', {}).get('traits', []))}"
                for c in characters[:5]  # Limit to main characters
            ]
        )

        # Format world context
        world_info = ""
        if world_context.get("rules"):
            rules = world_context["rules"]
            world_info += f"World: {rules.get('name', 'Unknown')}\n"
            world_info += f"Tech Level: {rules.get('technology_level', 'Unknown')}\n"
        if world_context.get("locations"):
            loc = world_context["locations"][0] if world_context["locations"] else {}
            world_info += f"Primary Location: {loc.get('name', 'Unknown')} - {loc.get('description', '')[:200]}\n"

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

        # Format optional sections
        style_section = f"STYLE GUIDE: {style_guide}" if style_guide else ""

        learning_section = ""
        if learning_hints:
            hint_lines = "\n".join(f"- {hint}" for hint in learning_hints)
            learning_section = f"LEARNED SUCCESSFUL PATTERNS (Apply these insights):\n{hint_lines}"

        user_prompt = f"""Write Chapter {chapter_number} of a science fiction web novel.

{"CRITICAL: This is Chapter " + str(chapter_number) + " of the GOLDEN 3 CHAPTERS. This MUST be exceptional to retain readers!" if chapter_number <= 3 else ""}

CHAPTER OUTLINE:
{enhanced_outline}

CHARACTERS IN THIS CHAPTER:
{char_info}

WORLD CONTEXT:
{world_info}

{style_section}

{learning_section}

STRICT REQUIREMENTS:
1. Word count: 2000-3000 words
2. Opening hook (first 300 words): Start with action, dialogue, or intriguing mystery
3. Closing hook (last 200 words): Must create cliffhanger or unresolved tension
4. Paragraphs: Maximum 60 words each (mobile-friendly)
5. Dialogue: At least 30% of content
6. Scenes: Change scene every 800-1000 words if chapter is long
7. Show technology through use, not lengthy explanation

WRITING CHECKLIST:
☑ First sentence grabs attention immediately
☑ First 300 words establish conflict or intrigue
☑ Science/tech shown through action and use
☑ Character depth revealed through choices
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
