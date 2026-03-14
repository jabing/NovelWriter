# src/agents/plot.py
"""Plot Agent - Story structure and chapter planning with emotional arcs."""

import json
import logging
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.agents.emotional_arc import EmotionalArcPlanner
from src.novel_agent.agents.writers.base_writer import get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS

logger = logging.getLogger(__name__)


class PlotAgent(BaseAgent):
    """Agent responsible for story structure and chapter planning with emotional arcs.

    Creates:
    - Main story arc
    - Chapter-by-chapter outlines
    - Foreshadowing plans
    - Pacing guidelines
    - Emotional arc planning (for web fiction optimization)
    """

    # Story structure templates
    STORY_STRUCTURES = {
        "three_act": {
            "act_1": {"chapters": "1-25%", "focus": "Setup, inciting incident"},
            "act_2a": {"chapters": "25-50%", "focus": "Rising action, midpoint"},
            "act_2b": {"chapters": "50-75%", "focus": "Complications, low point"},
            "act_3": {"chapters": "75-100%", "focus": "Climax, resolution"},
        },
        "heros_journey": {
            "departure": {"chapters": "1-20%", "focus": "Call to adventure, threshold"},
            "initiation": {"chapters": "20-70%", "focus": "Tests, allies, enemies, ordeal"},
            "return": {"chapters": "70-100%", "focus": "Reward, road back, resurrection"},
        },
        "save_the_cat": {
            "opening": {"chapters": "1-10%", "focus": "Opening image, theme stated"},
            "setup": {"chapters": "10-25%", "focus": "Setup, catalyst, debate"},
            "fun_and_games": {"chapters": "25-50%", "focus": "Break into two, B story"},
            "bad_guys": {"chapters": "50-75%", "focus": "Midpoint, all is lost"},
            "finale": {"chapters": "75-100%", "focus": "Dark night, finale, final image"},
        },
    }

    def __init__(self, name: str = "Plot Agent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute plot planning.

        Args:
            input_data: Must contain:
                - genre: str (scifi, fantasy, romance, history, military)
                - target_chapters: int
                - premise: str (optional story premise)
                - structure: str (optional: three_act, heros_journey, save_the_cat)
                - context: dict (optional: additional context like title, tone, themes)

        Returns:
            AgentResult with story outline in data['outline']
        """
        try:
            language = input_data.get("language")  # NEW: language for output
            genre = input_data.get("genre", "fantasy")
            target_chapters = input_data.get("target_chapters", 50)
            premise = input_data.get("premise", "")
            structure = input_data.get("structure", "three_act")
            context = input_data.get("context", {})

            # Debug logging
            logger.info("PlotAgent.execute called with:")
            logger.info(f"  genre: {genre}")
            logger.info(f"  target_chapters: {target_chapters}")
            logger.info(f"  premise: {premise[:100]}..." if premise else "  premise: (empty)")
            logger.info(f"  context: {context}")

            # Extract additional context (can come from context dict or be passed directly)
            title = context.get("title", "")
            tone = context.get("tone", "balanced")
            target_audience = context.get("target_audience", "young_adult")
            themes = context.get("themes", [])

            # Use context premise if not provided at top level
            if not premise and context.get("premise"):
                premise = context.get("premise", "")

            # Generate main arc with full context
            main_arc = await self.generate_main_arc(
                genre, premise, structure, title, tone, target_audience, themes, language
            )

            # Generate chapter outlines
            chapters = await self.generate_chapter_outlines(main_arc, target_chapters)

            # Generate foreshadowing plan
            foreshadowing = await self.generate_foreshadowing(main_arc, chapters)

            # Generate emotional arc plan (for web fiction optimization)
            emotional_arc_planner = EmotionalArcPlanner(llm=self.llm)
            key_moments = self._identify_key_moments(main_arc, target_chapters)

            emotional_result = await emotional_arc_planner.execute({
                "total_chapters": target_chapters,
                "genre": genre,
                "tone": tone,
                "key_moments": key_moments,
            })

            if emotional_result.success:
                # Safely handle data that might be a string
                if isinstance(emotional_result.data, dict):
                    emotional_result.data.get("emotional_journey")
                    emotional_arcs = emotional_result.data.get("chapter_arcs", {})
                else:
                    emotional_arcs = {}
                    logger.warning(f"emotional_result.data is not a dict: {type(emotional_result.data)}")
            else:
                emotional_arcs = {}
                logger.warning(f"Emotional arc planning failed: {emotional_result.errors}")

            outline = {
                "title": title or main_arc.get("title", "Novel Outline"),
                "genre": genre,
                "premise": premise,
                "structure": structure,
                "main_arc": main_arc,
                "chapters": chapters,
                "foreshadowing": foreshadowing,
                "emotional_arcs": emotional_arcs,
                "total_chapters": target_chapters,
                "tone": tone,
                "target_audience": target_audience,
            }

            # Store to memory if available
            if self.memory:
                await self.memory.store("/memory/plot/main_arc", main_arc)
                for i, chapter in enumerate(chapters):
                    await self.memory.store(
                        f"/memory/plot/chapter_{i+1:03d}",
                        chapter,
                    )

            return AgentResult(
                success=True,
                data={"outline": outline},
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Plot generation failed: {str(e)}"],
            )

    async def generate_main_arc(
        self,
        genre: str,
        premise: str,
        structure: str = "three_act",
        title: str = "",
        tone: str = "balanced",
        target_audience: str = "young_adult",
        themes: list[str] | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Generate main story arc using LLM.

        Args:
            genre: Story genre
            premise: Story premise
            structure: Story structure template
            title: Story title (if known)
            tone: Story tone (light/balanced/dark)
            target_audience: Target audience
            themes: Story themes

        Returns:
            Story arc structure
        """
        structure_template = self.STORY_STRUCTURES.get(structure, self.STORY_STRUCTURES["three_act"])

        genre_prompt = GENRE_PROMPTS.get(genre, "")

        system_prompt = f"""You are a master story architect specializing in {genre} fiction.
{genre_prompt}

Create compelling story arcs that follow proven narrative structures while feeling fresh and engaging.
Your output must be valid JSON."""

        # Build context description
        context_parts = []
        if title:
            context_parts.append(f"Title: {title}")
        if premise:
            context_parts.append(f"Premise: {premise}")
        if tone:
            context_parts.append(f"Tone: {tone}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")
        if themes:
            context_parts.append(f"Themes: {', '.join(themes)}")

        context_desc = "\n".join(context_parts) if context_parts else "No additional context provided"

        # Build title instruction
        title_instruction = ""
        if title:
            title_instruction = f"""
**CRITICAL: The story title MUST be exactly "{title}". Do NOT change or invent a new title.**
"""

        # Build language instruction
        language_instruction = get_language_instruction(language)

        user_prompt = f"""Create a main story arc for a {genre} novel.
{title_instruction}
{language_instruction}
Story Context:
{context_desc}

Structure: {structure}
Structure Template: {json.dumps(structure_template, indent=2)}

Generate a JSON response with this exact structure:
{{
    "title": "{title if title else 'Story Title'}",
    "logline": "One-sentence story description",
    "theme": "Core theme of the story",
    "main_conflict": "Description of the central conflict",
    "stakes": "What the protagonist stands to lose",
    "acts": [
        {{
            "name": "Act Name",
            "chapters": "Chapter range (e.g., 1-12)",
            "summary": "What happens in this act",
            "key_events": ["Event 1", "Event 2", "Event 3"],
            "emotional_arc": "How characters/readers feel"
        }}
    ],
    "climax": "Description of the climactic moment",
    "resolution": "How the story resolves"
}}

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
        )

        # Debug: log raw response
        logger.info(f"Main arc LLM response (first 1000 chars): {response.content[:1000]}")

        try:
            # Parse JSON response
            content = response.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            main_arc = json.loads(content)
            logger.info(f"Main arc parsed successfully. Title in response: {main_arc.get('title', 'N/A')}")
            # Validate with constitution
            validation_results = await self.validate_with_constitution("plot", main_arc)
            for rule_id, is_valid, error in validation_results:
                if not is_valid:
                    logger.warning(f"Constitution violation {rule_id} for plot: {error}")
            # Register story title in glossary
            if main_arc.get('title'):
                await self.register_with_glossary(
                    term=main_arc['title'],
                    term_type="concept",
                    definition=f"Story title: {main_arc.get('logline', 'No logline')}",
                    metadata={"genre": genre, "structure": structure}
                )
            return main_arc

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse main arc JSON: {e}")
            logger.error(f"Raw content: {response.content[:500]}")
            # Return basic structure if parsing fails
            return {
                "title": title or f"{genre.title()} Story",
                "logline": premise or f"A compelling {genre} adventure",
                "theme": "Growth through adversity",
                "main_conflict": "To be determined",
                "stakes": "Everything",
                "acts": [],
                "climax": "To be determined",
                "resolution": "To be determined",
                "_raw": response.content,
            }

    async def generate_chapter_outlines(
        self,
        main_arc: dict[str, Any],
        num_chapters: int,
    ) -> list[dict[str, Any]]:
        """Generate chapter-by-chapter outlines using LLM.

        Args:
            main_arc: Main story arc
            num_chapters: Number of chapters

        Returns:
            List of chapter outlines
        """
        system_prompt = """You are a chapter outline specialist.
Create detailed but flexible chapter outlines that advance the plot while allowing for organic storytelling.
Your output must be valid JSON."""

        arc_summary = json.dumps(main_arc, indent=2)[:2000]  # Truncate if too long

        user_prompt = f"""Generate detailed chapter outlines for a {num_chapters}-chapter novel.

Main Story Arc:
{arc_summary}

For each chapter, provide:
- A title
- A brief summary (2-3 sentences)
- Key events/plot points
- Characters involved
- Emotional beat

Generate a JSON array with this structure:
[
    {{
        "chapter": 1,
        "title": "Chapter Title",
        "summary": "Brief chapter summary",
        "key_events": ["Event 1", "Event 2"],
        "characters": ["Character 1", "Character 2"],
        "emotional_beat": "The emotional tone/purpose",
        "word_count_target": 2500
    }}
]

Generate outlines for all {num_chapters} chapters. Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=8000,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            chapters = json.loads(content)
            # Validate chapters with constitution
            if chapters:
                validation_results = await self.validate_with_constitution("plot", chapters[0])
                for rule_id, is_valid, error in validation_results:
                    if not is_valid:
                        logger.warning(f"Constitution violation {rule_id} for chapter outline: {error}")

            # Ensure we have the right number of chapters
            if isinstance(chapters, list):
                # Pad if needed
                while len(chapters) < num_chapters:
                    chapters.append({
                        "chapter": len(chapters) + 1,
                        "title": f"Chapter {len(chapters) + 1}",
                        "summary": "To be developed",
                        "key_events": [],
                        "characters": [],
                        "emotional_beat": "TBD",
                        "word_count_target": 2500,
                    })
                return chapters[:num_chapters]
            return []
        except json.JSONDecodeError:
            # Generate basic chapter structure
            return [
                {
                    "chapter": i + 1,
                    "title": f"Chapter {i + 1}",
                    "summary": "To be developed",
                    "key_events": [],
                    "characters": [],
                    "emotional_beat": "TBD",
                    "word_count_target": 2500,
                }
                for i in range(num_chapters)
            ]

    async def generate_foreshadowing(
        self,
        main_arc: dict[str, Any],
        chapters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate foreshadowing plan.

        Args:
            main_arc: Main story arc
            chapters: Chapter outlines

        Returns:
            List of foreshadowing elements
        """
        system_prompt = """You are a foreshadowing expert.
Create subtle setup and payoff patterns that make stories feel cohesive and rewarding.
Your output must be valid JSON."""

        user_prompt = f"""Create a foreshadowing plan for this novel.

Main climax: {main_arc.get('climax', 'Unknown')}
Key events in final act: {json.dumps(main_arc.get('acts', [])[-1] if main_arc.get('acts') else {}, indent=2)[:500]}

Generate 5-10 foreshadowing elements as a JSON array:
[
    {{
        "id": "foreshadow_001",
        "element": "What is foreshadowed",
        "planted_chapter": 3,
        "method": "How it's hinted (dialogue, symbol, etc.)",
        "payoff_chapter": 45,
        "payoff_description": "How it pays off"
    }}
]

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            foreshadowing_list = json.loads(content)
            # Validate foreshadowing with constitution
            foreshadowing_list = json.loads(content)
            if foreshadowing_list:
                validation_results = await self.validate_with_constitution("plot", foreshadowing_list[0])
                for rule_id, is_valid, error in validation_results:
                    if not is_valid:
                        logger.warning(f"Constitution violation {rule_id} for foreshadowing: {error}")
            return foreshadowing_list
        except json.JSONDecodeError:
            return []

    def _identify_key_moments(
        self, main_arc: dict[str, Any], total_chapters: int
    ) -> dict[str, list[int]]:
        """Identify key emotional moments from story arc.

        Args:
            main_arc: Main story arc
            total_chapters: Total number of chapters

        Returns:
            Dictionary mapping moment types to chapter numbers
        """
        key_moments = {
            "climax": [],
            "catharsis": [],
            "turning_points": [],
        }

        # Estimate climax position (usually 85-95%)
        climax_chapter = int(total_chapters * 0.90)
        key_moments["climax"].append(climax_chapter)

        # Add mid-point turning point (50%)
        midpoint = total_chapters // 2
        key_moments["turning_points"].append(midpoint)

        # Add first major turn (25%)
        first_turn = total_chapters // 4
        key_moments["turning_points"].append(first_turn)

        # Add catharsis points after major conflicts
        # These are typically after climax and at act breaks
        if total_chapters > 20:
            key_moments["catharsis"].append(int(total_chapters * 0.75))  # End of act 2
            key_moments["catharsis"].append(total_chapters)  # Final resolution

        return key_moments
