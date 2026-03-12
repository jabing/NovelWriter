# src/agents/chapter_hook.py
"""Chapter Hook Agent - Generates compelling opening and closing hooks."""

import json
import random
from typing import Any

from src.agents.base import AgentResult, BaseAgent


class ChapterHookAgent(BaseAgent):
    """Agent responsible for creating hooks that grab and retain readers.

    Web novels live or die by their hooks:
    - Opening hook: Must grab attention in first 300 words
    - Closing hook: Must create desire to read next chapter
    """

    # Hook types for openings
    OPENING_HOOK_TYPES = [
        "in_medias_res",  # Start in middle of action
        "provocative_question",  # Start with intriguing question
        "emotional_jolt",  # Strong emotional moment
        "mysterious_statement",  # Something that raises questions
        "dialogue_confrontation",  # Start with tense dialogue
        "sensory_immersion",  # Vivid sensory details
        "paradox",  # Contradictory or paradoxical statement
        "character_contrast",  # Unexpected character trait revealed
    ]

    # Hook types for closings
    CLOSING_HOOK_TYPES = [
        "unanswered_question",  # Leave a question hanging
        "sudden_interruption",  # Action cut off mid-scene
        "revelation_setup",  # Just before revealing something big
        "peril_cliffhanger",  # Character in immediate danger
        "unexpected_arrival",  # Someone arrives unexpectedly
        "emotional_peak",  # Strong emotion at fever pitch
        "promise_broken",  # Something promised goes wrong
        "discovery",  # Finding something shocking
        "decision_moment",  # Character must choose, choice unknown
    ]

    # Mobile-friendly paragraph threshold
    MAX_PARAGRAPH_WORDS = 60  # ~4 lines on mobile

    def __init__(self, name: str = "Chapter Hook Agent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute hook generation.

        Args:
            input_data: Must contain:
                - chapter_number: int
                - chapter_type: str ("opening", "middle", "climax", "resolution")
                - chapter_content: str (existing content to enhance)
                - emotional_tone: str
                - characters_involved: list[str]
                - plot_context: dict

        Returns:
            AgentResult with enhanced content and hook analysis
        """
        try:
            chapter_number = input_data.get("chapter_number", 1)
            chapter_type = input_data.get("chapter_type", "middle")
            content = input_data.get("chapter_content", "")
            emotional_tone = input_data.get("emotional_tone", "neutral")
            input_data.get("characters_involved", [])
            plot_context = input_data.get("plot_context", {})

            # Generate or enhance opening hook
            opening_result = await self._craft_opening_hook(
                content, chapter_number, chapter_type, emotional_tone, plot_context
            )

            # Generate or enhance closing hook
            closing_result = await self._craft_closing_hook(
                content, chapter_number, chapter_type, emotional_tone, plot_context
            )

            # Optimize for mobile reading
            mobile_optimized = self._optimize_for_mobile(content)

            # Analyze hook strength
            hook_analysis = self._analyze_hook_strength(
                opening_result, closing_result, mobile_optimized
            )

            return AgentResult(
                success=True,
                data={
                    "original_content": content,
                    "enhanced_content": mobile_optimized,
                    "opening_hook": opening_result,
                    "closing_hook": closing_result,
                    "hook_analysis": hook_analysis,
                    "chapter_number": chapter_number,
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Hook generation failed: {str(e)}"]
            )

    async def _craft_opening_hook(
        self,
        content: str,
        chapter_number: int,
        chapter_type: str,
        emotional_tone: str,
        plot_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Craft a compelling opening hook."""

        # Select best hook type based on context
        hook_type = self._select_opening_hook_type(chapter_number, chapter_type, emotional_tone)

        system_prompt = f"""You are a master of web novel openings.
Your task is to create or enhance the opening hook of a chapter.

CRITICAL RULES:
1. First 300 words MUST grab the reader immediately
2. NO info-dumping or lengthy descriptions
3. Start with action, dialogue, or intrigue
4. Create immediate curiosity
5. Match the emotional tone: {emotional_tone}

HOOK TYPE TO USE: {hook_type}

GUIDELINES FOR {hook_type.upper()}:
{self._get_hook_guidelines(hook_type, "opening")}

Output valid JSON only."""

        # Get first 500 chars to understand context
        existing_opening = content[:500] if content else ""

        user_prompt = f"""Chapter {chapter_number} ({chapter_type})
Plot Context: {json.dumps(plot_context, indent=2)[:500]}

Current Opening:
{existing_opening}

Create or enhance the opening hook (first 300 words) using the {hook_type} technique.

Output JSON:
{{
    "hook_type": "{hook_type}",
    "opening_text": "The enhanced opening (200-300 words)",
    "hook_strength": 8,
    "why_it_works": "Explanation of why this hook grabs attention",
    "curiosity_elements": ["element 1", "element 2"]
}}"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=800
            )

            # Parse response
            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]

            result = json.loads(content_response)
            return result

        except Exception as e:
            # Fallback to generic hook
            return {
                "hook_type": hook_type,
                "opening_text": existing_opening[:300] if existing_opening else "The chapter begins...",
                "hook_strength": 5,
                "why_it_works": "Default opening",
                "curiosity_elements": [],
                "error": str(e)
            }

    async def _craft_closing_hook(
        self,
        content: str,
        chapter_number: int,
        chapter_type: str,
        emotional_tone: str,
        plot_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Craft a compelling closing hook that drives next chapter reads."""

        hook_type = self._select_closing_hook_type(chapter_type, emotional_tone)

        system_prompt = f"""You are a master of web novel cliffhangers.
Your task is to create or enhance the closing hook of a chapter.

CRITICAL RULES:
1. Last 200 words MUST create desire to read next chapter
2. MUST use one of these techniques: {', '.join(self.CLOSING_HOOK_TYPES)}
3. End at peak tension, never on resolution
4. Create an unanswered question or unexpected situation
5. Make reader feel "Just one more chapter..."

HOOK TYPE TO USE: {hook_type}

GUIDELINES FOR {hook_type.upper()}:
{self._get_hook_guidelines(hook_type, "closing")}

Output valid JSON only."""

        # Get last 500 chars
        existing_closing = content[-500:] if content else ""

        user_prompt = f"""Chapter {chapter_number} ({chapter_type})
Plot Context: {json.dumps(plot_context, indent=2)[:500]}

Current Ending:
{existing_closing}

Create or enhance the closing hook (last 200 words) using the {hook_type} technique.

MUST end with one of:
- An unanswered question
- Sudden interruption
- Just before a revelation
- Character in peril
- Unexpected arrival
- Strong emotion at peak

Output JSON:
{{
    "hook_type": "{hook_type}",
    "closing_text": "The enhanced closing (150-200 words)",
    "hook_strength": 9,
    "why_it_works": "Explanation of why readers will click next",
    "unanswered_questions": ["question 1", "question 2"],
    "emotional_peak": "Description of emotional climax"
}}"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
                max_tokens=600
            )

            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]

            result = json.loads(content_response)
            return result

        except Exception as e:
            return {
                "hook_type": hook_type,
                "closing_text": existing_closing[-200:] if existing_closing else "To be continued...",
                "hook_strength": 5,
                "why_it_works": "Default ending",
                "unanswered_questions": [],
                "emotional_peak": "none",
                "error": str(e)
            }

    def _optimize_for_mobile(self, content: str) -> str:
        """Optimize content for mobile reading."""
        paragraphs = content.split('\n\n')
        optimized = []

        for para in paragraphs:
            words = para.split()
            if len(words) > self.MAX_PARAGRAPH_WORDS:
                # Break long paragraphs
                current_chunk = []
                current_word_count = 0

                for word in words:
                    current_chunk.append(word)
                    current_word_count += 1

                    # Break at sentence end if paragraph too long
                    if current_word_count >= self.MAX_PARAGRAPH_WORDS and word.endswith(('.', '!', '?', '"')):
                        optimized.append(' '.join(current_chunk))
                        current_chunk = []
                        current_word_count = 0

                if current_chunk:
                    optimized.append(' '.join(current_chunk))
            else:
                optimized.append(para)

        return '\n\n'.join(optimized)

    def _analyze_hook_strength(
        self,
        opening: dict[str, Any],
        closing: dict[str, Any],
        content: str
    ) -> dict[str, Any]:
        """Analyze the strength of hooks in content."""

        # Check opening strength
        opening_strength = opening.get("hook_strength", 5)
        opening_text = opening.get("opening_text", "")

        # Analyze opening
        opening_issues = []
        if len(opening_text.split()) > 100 and not any(c in opening_text for c in ['"', '!', '?']):
            opening_issues.append("Opening may be too slow - add dialogue or action")

        if opening_text.lower().startswith(("it was", "the ", "a ", "in ", "on ")):
            opening_issues.append("Opening is generic - consider starting with dialogue or action")

        # Check closing strength
        closing_strength = closing.get("hook_strength", 5)
        closing_text = closing.get("closing_text", "")

        # Analyze closing
        closing_issues = []
        hook_indicators = ['?', '!', '...', 'what', 'who', 'how', 'why', 'wait', 'know', 'truth', 'secret']
        if not any(indicator in closing_text.lower()[-100:] for indicator in hook_indicators):
            closing_issues.append("Closing lacks hook - add question or unresolved tension")

        # Check mobile optimization
        paragraphs = content.split('\n\n')
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > self.MAX_PARAGRAPH_WORDS)

        return {
            "opening_score": opening_strength,
            "closing_score": closing_strength,
            "overall_hook_score": (opening_strength + closing_strength) / 2,
            "opening_issues": opening_issues,
            "closing_issues": closing_issues,
            "mobile_optimization": {
                "paragraphs_total": len(paragraphs),
                "paragraphs_too_long": long_paragraphs,
                "mobile_friendly": long_paragraphs < len(paragraphs) * 0.2
            },
            "recommendations": self._generate_recommendations(opening_issues, closing_issues)
        }

    def _select_opening_hook_type(
        self,
        chapter_number: int,
        chapter_type: str,
        emotional_tone: str
    ) -> str:
        """Select best hook type based on context."""
        if chapter_number == 1:
            return "in_medias_res"  # First chapter should start with action

        if emotional_tone in ["tense", "action", "suspense"]:
            return random.choice(["in_medias_res", "dialogue_confrontation"])

        if emotional_tone in ["mysterious", "intrigue"]:
            return random.choice(["mysterious_statement", "paradox"])

        if emotional_tone in ["emotional", "romantic"]:
            return random.choice(["emotional_jolt", "character_contrast"])

        return random.choice(self.OPENING_HOOK_TYPES)

    def _select_closing_hook_type(self, chapter_type: str, emotional_tone: str) -> str:
        """Select best closing hook type."""
        if chapter_type == "climax":
            return random.choice(["peril_cliffhanger", "revelation_setup"])

        if chapter_type == "resolution":
            return "unexpected_arrival"  # Hint at next arc

        if emotional_tone in ["tense", "action"]:
            return random.choice(["peril_cliffhanger", "sudden_interruption"])

        if emotional_tone in ["mysterious"]:
            return random.choice(["revelation_setup", "discovery"])

        return random.choice(self.CLOSING_HOOK_TYPES)

    def _get_hook_guidelines(self, hook_type: str, position: str) -> str:
        """Get specific guidelines for a hook type."""
        guidelines = {
            "in_medias_res": "Drop reader into middle of action. NO setup or backstory first.",
            "provocative_question": "Start with question that demands an answer. Make it personal.",
            "emotional_jolt": "Begin with peak emotion. Shock, fear, joy, or devastation.",
            "mysterious_statement": "Something impossible or contradictory. Make reader need to understand.",
            "dialogue_confrontation": "Start mid-conversation at moment of high stakes or conflict.",
            "sensory_immersion": "Vivid sensory details that create immediate atmosphere.",
            "paradox": "Something that shouldn't be possible but is.",
            "character_contrast": "Show unexpected trait or situation for character.",
            "unanswered_question": "End with question that must be answered in next chapter.",
            "sudden_interruption": "Action or dialogue cut off. Something interrupts at worst moment.",
            "revelation_setup": "Just before revealing something HUGE. Reader knows it's coming.",
            "peril_cliffhanger": "Character in immediate physical or emotional danger.",
            "unexpected_arrival": "Someone arrives who changes everything. Door opens, message arrives.",
            "emotional_peak": "Emotion at fever pitch. Love confessed, betrayal revealed.",
            "promise_broken": "Something sworn or promised goes wrong at worst moment.",
            "discovery": "Finding something that changes everything.",
            "decision_moment": "Character at crossroads. Choice unknown until next chapter.",
        }
        return guidelines.get(hook_type, "Create immediate engagement")

    def _generate_recommendations(
        self,
        opening_issues: list[str],
        closing_issues: list[str]
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if opening_issues:
            recommendations.append(f"Opening: {'; '.join(opening_issues)}")

        if closing_issues:
            recommendations.append(f"Closing: {'; '.join(closing_issues)}")

        if not opening_issues and not closing_issues:
            recommendations.append("Hooks are well-crafted - maintain this quality!")

        return recommendations
