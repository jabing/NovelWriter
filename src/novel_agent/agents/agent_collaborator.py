# src/agents/agent_collaborator.py
"""Multi-Agent Collaboration System.

Enables multiple specialized writers to collaborate on content that spans genres.
Example: A romance novel with historical elements can have RomanceWriter and
HistoryWriter work together on appropriate sections.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.novel_agent.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class CollaborationMode(str, Enum):
    """How agents collaborate."""
    SEQUENTIAL = "sequential"      # Agent A → Agent B (handoff)
    PARALLEL = "parallel"          # Agent A + Agent B → Merge
    LEAD_SUPPORT = "lead_support"  # Lead agent with specialist support
    DYNAMIC = "dynamic"            # AI decides based on content


@dataclass
class AgentRole:
    """Role assignment for an agent in collaboration."""
    agent_type: str
    expertise: list[str]
    sections: list[str] = field(default_factory=list)
    is_lead: bool = False


@dataclass
class CollaborationPlan:
    """Plan for multi-agent collaboration."""
    mode: CollaborationMode
    lead_agent: str
    supporting_agents: list[AgentRole]
    section_assignments: dict[str, str]  # section -> agent_type
    handoff_points: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CollaborativeResult:
    """Result from collaborative writing."""
    content: str
    contributions: dict[str, str]  # agent_type -> their contribution
    integration_notes: str
    quality_scores: dict[str, float]


class AgentCollaborator:
    """Orchestrates collaboration between multiple specialized writers.

    Use Cases:
    1. Romance + History: Historical romance with accurate period details
    2. Sci-Fi + Fantasy: Science fantasy with both tech and magic
    3. Romance + Thriller: Romantic thriller with suspense elements
    4. Any + Military: Military accuracy in any genre

    Example:
        collaborator = AgentCollaborator(llm=llm)
        result = await collaborator.collaborate(
            content_type="chapter",
            outline="Chapter about a ball in 19th century Vienna...",
            genres=["romance", "history"],
            mode=CollaborationMode.LEAD_SUPPORT,
        )
    """

    # Genre expertise mapping
    GENRE_EXPERTISE = {
        "romance": ["emotions", "relationships", "dialogue", "chemistry", "tension"],
        "history": ["period accuracy", "historical events", "culture", "language", "customs"],
        "fantasy": ["magic systems", "worldbuilding", "mythology", "creatures"],
        "scifi": ["technology", "science", "future society", "space"],
        "military": ["tactics", "weapons", "strategy", "military culture"],
        "thriller": ["suspense", "pacing", "mystery", "tension"],
    }

    # Content elements that benefit from specific genres
    CONTENT_INDICATORS = {
        "romance": ["kiss", "love", "attraction", "date", "relationship", "heart", "passion"],
        "history": ["century", "era", "historical", "period", "war", "king", "queen", "empire"],
        "fantasy": ["magic", "spell", "dragon", "sword", "castle", "wizard", "curse"],
        "scifi": ["space", "ship", "alien", "technology", "future", "planet", "robot"],
        "military": ["battle", "soldier", "army", "tactics", "weapon", "mission", "command"],
        "thriller": ["danger", "threat", "mystery", "secret", "chase", "escape", "suspicion"],
    }

    def __init__(
        self,
        llm: BaseLLM,
        default_mode: CollaborationMode = CollaborationMode.LEAD_SUPPORT,
    ) -> None:
        """Initialize collaborator.

        Args:
            llm: LLM instance
            default_mode: Default collaboration mode
        """
        self.llm = llm
        self.default_mode = default_mode
        self._writers: dict[str, Any] = {}

    def _get_writer(self, genre: str) -> Any:
        """Get or create writer for genre."""
        if genre not in self._writers:
            from src.novel_agent.agents.writers.writer_factory import WriterFactory
            try:
                self._writers[genre] = WriterFactory.create_writer(genre, llm=self.llm)
            except Exception:
                # Fallback to generic writer
                from src.novel_agent.agents.writers.base_writer import BaseWriter
                self._writers[genre] = BaseWriter(llm=self.llm)
        return self._writers[genre]

    async def analyze_content_needs(
        self,
        outline: str,
        genres: list[str],
    ) -> CollaborationPlan:
        """Analyze content to determine collaboration plan.

        Args:
            outline: Chapter/section outline
            genres: List of genres involved

        Returns:
            CollaborationPlan with agent assignments
        """
        system_prompt = """You are a content analysis expert. Analyze the outline
to determine which sections need which genre expertise.
Output valid JSON only."""

        genre_info = "\n".join([
            f"- {g}: {', '.join(self.GENRE_EXPERTISE.get(g, []))}"
            for g in genres
        ])

        user_prompt = f"""Analyze this outline and determine how {len(genres)} writers should collaborate.

GENRES AND EXPERTISE:
{genre_info}

OUTLINE:
{outline[:2000]}

Generate a JSON collaboration plan:
{{
    "mode": "lead_support",
    "lead_genre": "romance",
    "support_needed": {{
        "history": ["period details", "historical accuracy"],
        "military": ["battle scene accuracy"]
    }},
    "sections": [
        {{
            "section": "opening",
            "primary_genre": "romance",
            "support_genres": [],
            "description": "Emotional scene between lovers"
        }},
        {{
            "section": "ballroom",
            "primary_genre": "history",
            "support_genres": ["romance"],
            "description": "Historical ball with romantic tension"
        }}
    ],
    "handoff_points": [
        {{"location": "after paragraph 3", "from": "romance", "to": "history", "reason": "historical context needed"}}
    ]
}}"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            plan_data = json.loads(content)

            return CollaborationPlan(
                mode=CollaborationMode(plan_data.get("mode", "lead_support")),
                lead_agent=plan_data.get("lead_genre", genres[0]),
                supporting_agents=[
                    AgentRole(
                        agent_type=genre,
                        expertise=expertise,
                    )
                    for genre, expertise in plan_data.get("support_needed", {}).items()
                ],
                section_assignments={
                    s["section"]: s["primary_genre"]
                    for s in plan_data.get("sections", [])
                },
                handoff_points=plan_data.get("handoff_points", []),
            )
        except (json.JSONDecodeError, ValueError):
            # Default plan
            return CollaborationPlan(
                mode=CollaborationMode.LEAD_SUPPORT,
                lead_agent=genres[0],
                supporting_agents=[
                    AgentRole(agent_type=g, expertise=self.GENRE_EXPERTISE.get(g, []))
                    for g in genres[1:]
                ],
                section_assignments={},
                handoff_points=[],
            )

    async def collaborate(
        self,
        content_type: str,
        outline: str,
        genres: list[str],
        mode: CollaborationMode | None = None,
        characters: list[dict[str, Any]] | None = None,
        world_context: dict[str, Any] | None = None,
        chapter_number: int = 1,
    ) -> CollaborativeResult:
        """Execute collaborative writing with multiple agents.

        Args:
            content_type: "chapter", "scene", "outline"
            outline: Content outline
            genres: List of genres to involve
            mode: Collaboration mode (auto-selected if None)
            characters: Character profiles
            world_context: World building context
            chapter_number: Chapter number if applicable

        Returns:
            CollaborativeResult with integrated content
        """
        logger.info(f"Starting {len(genres)}-agent collaboration: {genres}")

        # Step 1: Analyze content and create plan
        plan = await self.analyze_content_needs(outline, genres)
        if mode:
            plan.mode = mode


        # Step 2: Execute based on collaboration mode
        if plan.mode == CollaborationMode.LEAD_SUPPORT:
            result = await self._execute_lead_support(
                plan, outline, characters or [], world_context or {}, chapter_number
            )
        elif plan.mode == CollaborationMode.SEQUENTIAL:
            result = await self._execute_sequential(
                plan, outline, characters or [], world_context or {}, chapter_number
            )
        elif plan.mode == CollaborationMode.PARALLEL:
            result = await self._execute_parallel(
                plan, outline, characters or [], world_context or {}, chapter_number
            )
        else:  # DYNAMIC
            result = await self._execute_dynamic(
                plan, outline, characters or [], world_context or {}, chapter_number
            )

        return result

    async def _execute_lead_support(
        self,
        plan: CollaborationPlan,
        outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        chapter_number: int,
    ) -> CollaborativeResult:
        """Lead agent writes, support agents enhance specific sections.

        Flow:
        1. Lead agent writes full content
        2. Support agents enhance their areas of expertise
        3. Lead agent integrates enhancements
        """
        contributions: dict[str, str] = {}

        # Step 1: Lead agent writes initial draft
        lead_writer = self._get_writer(plan.lead_agent)

        # Create context with support expectations
        support_context = "\n".join([
            f"- {role.agent_type}: Focus on {', '.join(role.expertise)}"
            for role in plan.supporting_agents
        ])

        enhanced_outline = f"""{outline}

[Multi-Genre Collaboration]
Primary Genre: {plan.lead_agent}
Supporting Genres:
{support_context}

Note: Other specialists will enhance specific sections after initial draft."""

        lead_content = await lead_writer.write_chapter(
            chapter_number=chapter_number,
            chapter_outline=enhanced_outline,
            characters=characters,
            world_context=world_context,
        )
        contributions[plan.lead_agent] = lead_content

        # Step 2: Each support agent enhances their sections
        enhanced_sections: list[dict[str, Any]] = []

        for role in plan.supporting_agents:
            self._get_writer(role.agent_type)

            enhancement = await self._get_enhancement(
                lead_content=lead_content,
                support_genre=role.agent_type,
                expertise=role.expertise,
                characters=characters,
            )

            if enhancement.get("sections"):
                enhanced_sections.extend(enhancement["sections"])
                contributions[role.agent_type] = enhancement.get("enhanced_content", "")

        # Step 3: Integrate enhancements
        final_content = await self._integrate_enhancements(
            original=lead_content,
            enhancements=enhanced_sections,
            lead_genre=plan.lead_agent,
        )

        return CollaborativeResult(
            content=final_content,
            contributions=contributions,
            integration_notes=f"Lead: {plan.lead_agent}, Support: {', '.join(r.agent_type for r in plan.supporting_agents)}",
            quality_scores={plan.lead_agent: 8.0},  # Placeholder
        )

    async def _execute_sequential(
        self,
        plan: CollaborationPlan,
        outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        chapter_number: int,
    ) -> CollaborativeResult:
        """Agents write sequentially, handing off at specified points.

        Flow:
        1. Agent A writes section 1
        2. Handoff to Agent B
        3. Agent B writes section 2 based on section 1
        4. Continue until complete
        """
        contributions: dict[str, str] = {}
        all_content: list[str] = []

        # Parse outline into sections
        sections = self._split_outline(outline, plan.section_assignments)

        current_context = ""

        for i, (section_name, section_outline) in enumerate(sections.items()):
            # Determine which agent writes this section
            agent_type = plan.section_assignments.get(section_name, plan.lead_agent)
            writer = self._get_writer(agent_type)

            # Include previous context
            context_aware_outline = f"""{section_outline}

[Previous Context]
{current_context[-1000:] if current_context else "Beginning of chapter"}

Write this section, maintaining continuity with previous content."""

            section_content = await writer.write_chapter(
                chapter_number=chapter_number,
                chapter_outline=context_aware_outline,
                characters=characters,
                world_context=world_context,
            )

            contributions[f"{agent_type}_{i}"] = section_content
            all_content.append(section_content)
            current_context = "\n".join(all_content)

        # Integrate all sections
        final_content = await self._smooth_transitions(all_content, plan.handoff_points)

        return CollaborativeResult(
            content=final_content,
            contributions=contributions,
            integration_notes=f"Sequential: {' → '.join(plan.section_assignments.values())}",
            quality_scores={},
        )

    async def _execute_parallel(
        self,
        plan: CollaborationPlan,
        outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        chapter_number: int,
    ) -> CollaborativeResult:
        """Agents write different aspects in parallel, then merge.

        Flow:
        1. Agent A writes emotional/romance layer
        2. Agent B writes historical/technical layer (parallel)
        3. Merge layers into cohesive content
        """
        import asyncio

        tasks: dict[str, Any] = {}

        # Create genre-specific outlines
        for genre in [plan.lead_agent] + [r.agent_type for r in plan.supporting_agents]:
            writer = self._get_writer(genre)
            expertise = self.GENRE_EXPERTISE.get(genre, [])

            genre_outline = f"""{outline}

[Focus: {genre.upper()}]
You are responsible for: {', '.join(expertise)}
Write the {genre} elements of this chapter. Other agents will handle other aspects."""

            tasks[genre] = asyncio.create_task(
                writer.write_chapter(
                    chapter_number=chapter_number,
                    chapter_outline=genre_outline,
                    characters=characters,
                    world_context=world_context,
                )
            )

        # Wait for all agents
        contributions = {}
        for genre, task in tasks.items():
            contributions[genre] = await task

        # Merge contributions
        final_content = await self._merge_parallel_contributions(
            contributions, plan.lead_agent
        )

        return CollaborativeResult(
            content=final_content,
            contributions=contributions,
            integration_notes=f"Parallel merge of: {', '.join(contributions.keys())}",
            quality_scores={},
        )

    async def _execute_dynamic(
        self,
        plan: CollaborationPlan,
        outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        chapter_number: int,
    ) -> CollaborativeResult:
        """AI dynamically decides which agent handles each part.

        This is the most flexible mode - an orchestrator AI decides
        in real-time which specialist should write each paragraph.
        """
        # Start with lead agent
        self._get_writer(plan.lead_agent)

        # Create dynamic collaboration context
        available_agents = [plan.lead_agent] + [r.agent_type for r in plan.supporting_agents]

        system_prompt = f"""You are a writing orchestrator managing multiple specialist writers.
Available specialists: {', '.join(available_agents)}

For each section, decide:
1. Which specialist should write it
2. What they should focus on
3. How to hand off to the next specialist

Write collaboratively to create the best content."""

        user_prompt = f"""Write Chapter {chapter_number} using dynamic collaboration.

OUTLINE:
{outline}

CHARACTERS:
{self._format_characters(characters)}

Write this chapter, switching between specialists as needed.
Mark handoffs clearly: [HANDOFF: romance → history]

Begin writing:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=4000,
        )

        content = response.content

        # Extract contributions from markers
        contributions = self._extract_dynamic_contributions(content, available_agents)

        # Remove markers from final content
        import re
        clean_content = re.sub(r'\[HANDOFF:.*?\]', '', content)

        return CollaborativeResult(
            content=clean_content.strip(),
            contributions=contributions,
            integration_notes="Dynamic collaboration with AI orchestration",
            quality_scores={},
        )

    async def _get_enhancement(
        self,
        lead_content: str,
        support_genre: str,
        expertise: list[str],
        characters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get enhancements from support agent."""
        system_prompt = f"""You are a {support_genre} specialist.
Your job is to enhance the {support_genre} elements in the content.
Focus on: {', '.join(expertise)}

Output valid JSON only."""

        user_prompt = f"""Analyze this chapter and enhance the {support_genre} elements.

CONTENT:
{lead_content[:3000]}

Generate JSON:
{{
    "analysis": "What {support_genre} elements need enhancement",
    "sections": [
        {{
            "location": "paragraph 2",
            "original": "...",
            "enhanced": "...",
            "reason": "Added period-appropriate details"
        }}
    ],
    "enhanced_content": "Full enhanced version or specific sections",
    "notes": "What was improved"
}}"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"sections": [], "enhanced_content": "", "notes": ""}

    async def _integrate_enhancements(
        self,
        original: str,
        enhancements: list[dict[str, Any]],
        lead_genre: str,
    ) -> str:
        """Integrate enhancements into original content."""
        if not enhancements:
            return original

        system_prompt = f"""You are a {lead_genre} writer integrating specialist enhancements.
Maintain the voice and style while incorporating improvements.
Seamlessly blend the enhancements into the narrative."""

        enhancement_notes = "\n".join([
            f"- {e.get('location', 'unknown')}: {e.get('reason', '')}"
            for e in enhancements[:5]
        ])

        user_prompt = f"""Integrate these enhancements into the chapter.

ORIGINAL:
{original[:3000]}

ENHANCEMENTS:
{enhancement_notes}

Provide the integrated chapter, maintaining narrative flow:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_tokens=4000,
        )

        return response.content.strip()

    async def _smooth_transitions(
        self,
        sections: list[str],
        handoff_points: list[dict[str, Any]],
    ) -> str:
        """Smooth transitions between sections written by different agents."""
        if len(sections) <= 1:
            return sections[0] if sections else ""

        system_prompt = """You are an editor smoothing transitions between
sections written by different specialists. Ensure narrative continuity."""

        combined = "\n\n--- TRANSITION ---\n\n".join(sections)

        user_prompt = f"""Smooth the transitions in this multi-agent content:

{combined[:4000]}

Remove jarring transitions and ensure seamless flow:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=4000,
        )

        return response.content.strip()

    async def _merge_parallel_contributions(
        self,
        contributions: dict[str, str],
        lead_genre: str,
    ) -> str:
        """Merge parallel contributions into cohesive content."""
        system_prompt = f"""You are a {lead_genre} writer merging contributions
from multiple specialists into a cohesive narrative."""

        contributions_text = "\n\n".join([
            f"=== {genre.upper()} CONTRIBUTION ===\n{content[:1500]}"
            for genre, content in contributions.items()
        ])

        user_prompt = f"""Merge these specialist contributions into one cohesive chapter:

{contributions_text}

Create a unified chapter that incorporates all elements naturally:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_tokens=4000,
        )

        return response.content.strip()

    def _split_outline(
        self,
        outline: str,
        assignments: dict[str, str],
    ) -> dict[str, str]:
        """Split outline into sections based on assignments."""
        if not assignments:
            return {"main": outline}

        # Simple split by paragraphs for now
        # TODO: More sophisticated section detection
        paragraphs = outline.split("\n\n")
        sections = {}

        for i, para in enumerate(paragraphs):
            section_name = f"section_{i+1}"
            sections[section_name] = para

        return sections

    def _format_characters(self, characters: list[dict[str, Any]]) -> str:
        """Format characters for prompt."""
        if not characters:
            return "No characters specified"

        return "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('role', '')}"
            for c in characters[:5]
        ])

    def _extract_dynamic_contributions(
        self,
        content: str,
        agents: list[str],
    ) -> dict[str, str]:
        """Extract contributions from dynamically generated content."""
        contributions = dict.fromkeys(agents, "")

        import re
        # Find handoff markers and split content
        pattern = r'\[HANDOFF:\s*(\w+)\s*→\s*(\w+)\]'
        parts = re.split(pattern, content)

        current_agent = agents[0] if agents else "unknown"

        for _i, part in enumerate(parts):
            if part in agents:
                current_agent = part
            elif part.strip():
                contributions[current_agent] += part.strip() + "\n"

        return contributions


# Convenience function for quick collaboration
async def collaborative_write(
    llm: BaseLLM,
    outline: str,
    genres: list[str],
    mode: str = "lead_support",
) -> str:
    """Quick collaborative writing helper.

    Args:
        llm: LLM instance
        outline: Content outline
        genres: List of genres to involve
        mode: Collaboration mode

    Returns:
        Collaboratively written content
    """
    collaborator = AgentCollaborator(llm=llm)

    mode_enum = CollaborationMode(mode)

    result = await collaborator.collaborate(
        content_type="chapter",
        outline=outline,
        genres=genres,
        mode=mode_enum,
    )

    return result.content
