# Romance Writer Agent (updated for multilingual support)
"""Romance Writer Agent with language support."""

from typing import Any

from src.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.llm.prompts import GENRE_PROMPTS
from src.novel.continuity import StoryState


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
BY|
XX|{self.DOMAIN_KNOWLEDGE}
{language_instruction}
NB|
XP|WEB FICTION REQUIREMENTS (CRITICAL):
BT|1. OPENING HOOK (First 300 words):
PS|   - MUST start with action, dialogue, or emotional jolt
HH|   - NO lengthy descriptions or exposition
ZV|   - Reader should immediately wonder \"what happens next?\"
XN|
KV|2. CHAPTER STRUCTURE:
MJ|   - Scene changes every 800-1000 words (prevents dragging)
TZ|   - Each scene has mini-conflict or emotional development
QZ|   - Build to emotional peak
VW|
NZ|3. CLOSING HOOK (Last 200 words):
HT|   MUST end with ONE of:
TZ|   - A question left unanswered
VZ|   - A sudden interruption
PB|   - A revelation that changes everything
RK|   - A character in emotional peril
HW|   - An unexpected arrival/message
NV|   - Strong emotion at fever pitch
YY|
WS|4. MOBILE READABILITY:
QW|   - NO paragraph longer than 4 lines on mobile (60 words max)
MM|   - Mix short punchy sentences with longer ones
TH|   - Dialogue should be 30-50% of content
SZ|
QX|5. EMOTIONAL ENGAGEMENT:
HS|   - Show emotions through physical cues and actions
NR|   - Internal thoughts reveal character depth
YT|   - Create palpable chemistry between leads
KB|
MK|{'CRITICAL - GOLDEN CHAPTER ' + str(chapter_number) + ': This is one of the first 3 chapters. It MUST be exceptional. Start with strongest hook possible, end with irresistible cliffhanger. Reader retention depends on this chapter!' if is_golden else ''}
YR|
PY|Write engaging prose that keeps readers binge-reading."""


        char_info = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('role', '')}, {', '.join(c.get('personality', {}).get('traits', []))}"
            for c in characters[:5]
        ])

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

        user_prompt = f"""Write Chapter {chapter_number} of a romance web novel.
{''}
{'CRITICAL: This is Chapter ' + str(chapter_number) + ' of the GOLDEN 3 CHAPTERS. This MUST be exceptional to retain readers!' if is_golden else ''}

CHAPTER OUTLINE:
{enhanced_outline}

CHARACTERS IN THIS CHAPTER:
{char_info}

SETTING CONTEXT:
{world_info}

{f"STYLE GUIDE: {style_guide}" if style_guide else ""}

YB|STRICT REQUIREMENTS:
WX|1. Word count: 2000-3000 words
2. Opening hook (first 300 words): Start with dialogue, action, or strong emotion
3. Closing hook (last 200 words): Must create cliffhanger or unresolved tension
KH|4. Paragraphs: Maximum 60 words each (mobile-friendly)
ZX|5. Dialogue: At least 30% of content
VZ|6. Scenes: Change scene every 800-1000 words if chapter is long
JQ|7. Emotional beats: Include 2-3 emotional high points
QY|
NT|WRITING CHECKLIST:
ST|☑ First sentence grabs attention immediately
YH|☑ First 300 words establish conflict or magical intrigue
VW|☑ Chemistry shown through dialogue and small moments
XQ|☑ Internal thoughts reveal character depth
MJ|☑ Last 200 words end with hook that demands next chapter
RB|☑ No paragraph longer than 4 lines on mobile
HP|
MS|Write the complete chapter now:"""


        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=4000,
        )

        return response.content.strip()
