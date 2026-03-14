# Military Writer Agent (with language support)
"""Military Writer Agent."""

from typing import Any

from src.novel_agent.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS
from src.novel_agent.novel.continuity import StoryState


class MilitaryWriter(BaseWriter):
    """Military fiction writer with tactical expertise."""

    GENRE = "military"
    DOMAIN_KNOWLEDGE = """
Military knowledge for realistic combat and strategy:
- Military ranks and organizational structures
- Tactical formations and strategies
- Weapon systems (historical and modern)
- Combat psychology and unit cohesion
- Logistics and supply chain importance
- Naval, ground, and aerial warfare principles
- Command and control systems
- Rules of engagement and military law
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
        """Write a military fiction chapter using LLM.

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
        genre_prompt = GENRE_PROMPTS.get("military", "")
        language_instruction = get_language_instruction(language)

        system_prompt = f"""You are a bestselling military fiction web novel author.
{genre_prompt}
#PZ|
#XX|{self.DOMAIN_KNOWLEDGE}
{language_instruction}
#NB|
XP|WEB FICTION REQUIREMENTS (CRITICAL):
#BT|1. OPENING HOOK (First 300 words):
#NM|   - MUST start with action, combat, or military tension
#WV|   - NO lengthy tactical briefings first
#TH|   - Drop reader into the chaos immediately
#QH|
#KV|2. CHAPTER STRUCTURE:
#QQ|   - Scene changes every 800-1000 words
#QZ|   - Each scene advances tactical situation or develops soldiers
#QH|   - Build tension through military challenges
#XZ|
#NZ|3. CLOSING HOOK (Last 200 words):
#HT|   MUST end with ONE of:
#XN|   - New tactical threat or order
#YS|   - Character in combat danger
#RW|   - Moral dilemma about warfare
#VX|   - Unexpected enemy action
#JB|   - Cliffhanger in middle of operation
#SV|
WS|4. MOBILE READABILITY:
#QW|   - NO paragraph longer than 4 lines on mobile (60 words max)
#MM|   - Mix short punchy sentences with longer ones
#TH|   - Dialogue should be 30-50% of content
#VB|
KM|5. MILITARY ENGAGEMENT:
#MP|   - Show warfare through soldier's eyes
#QW|   - Balance action with human moments
#QZ|   - Use accurate terminology without overwhelming
#YR|
KB|{'CRITICAL - GOLDEN CHAPTER ' + str(chapter_number) + ': This is one of the first 3 chapters. It MUST be exceptional. Start with strongest hook possible, end with irresistible cliffhanger. Reader retention depends on this chapter!' if chapter_number <= 3 else ''}
WR|
PY|Write engaging prose that keeps readers binge-reading."""

        char_info = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('role', '')}, {c.get('military_rank', c.get('occupation', 'Unknown'))}"
            for c in characters[:5]
        ])

        world_info = ""
        if world_context.get("rules"):
            rules = world_context["rules"]
            world_info += f"Conflict: {rules.get('name', 'Unknown conflict')}\n"
            world_info += f"Tech Level: {rules.get('technology_level', 'Unknown')}\n"
        if world_context.get("society"):
            society = world_context["society"]
            if society.get("government"):
                world_info += f"Factions: {society['government'].get('key_figures', [])}\n"
        if world_context.get("locations"):
            loc = world_context["locations"][0] if world_context["locations"] else {}
            world_info += f"Theater: {loc.get('name', 'Unknown')} - {loc.get('description', '')[:100]}\n"

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

        user_prompt = f"""Write Chapter {chapter_number} of a military fiction web novel.
{''}
{'CRITICAL: This is Chapter ' + str(chapter_number) + ' of the GOLDEN 3 CHAPTERS. This MUST be exceptional to retain readers!' if chapter_number <= 3 else ''}

CHAPTER OUTLINE:
{enhanced_outline}

CHARACTERS IN THIS CHAPTER:
{char_info}

MILITARY CONTEXT:
{world_info}

{f"STYLE GUIDE: {style_guide}" if style_guide else ""}

YB|STRICT REQUIREMENTS:
WX|1. Word count: 2000-3000 words
2. Opening hook (first 300 words): Start with action, combat, or military tension
HN|3. Closing hook (last 200 words): Must create cliffhanger or unresolved tension
KH|4. Paragraphs: Maximum 60 words each (mobile-friendly)
ZX|5. Dialogue: At least 30% of content
VZ|6. Scenes: Change scene every 800-1000 words if chapter is long
BP|7. Show warfare through soldier's perspective
YB|
NT|WRITING CHECKLIST:
ST|☑ First sentence grabs attention immediately
RZ|☑ First 300 words establish military conflict or tension
TP|☑ Combat/tactics shown through character experience
YT|☑ Human moments balance action scenes
MJ|☑ Last 200 words end with hook that demands next chapter
RB|☑ No paragraph longer than 4 lines on mobile
QX|
MS|Write the complete chapter now:"""


        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=4000,
        )

        return response.content.strip()
