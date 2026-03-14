# src/agents/project_planner.py
"""Project Planner Agent - Interactive project planning assistant.

Similar to a "plan" role in software development, this agent helps authors:
1. Define project goals and constraints
2. Identify target audience
3. Select publishing platforms
4. Determine language and style
5. Set content boundaries (mature content, themes, etc.)
6. Create a comprehensive project specification

Usage:
    planner = ProjectPlanner(llm=llm)
    plan = await planner.plan_interactive()
    # or
    plan = await planner.plan_from_description("I want to write a YA romance...")
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.novel_agent.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class AudienceAge(str, Enum):
    """Target audience age group."""
    CHILDREN = "children"          # 8-12
    YOUNG_ADULT = "young_adult"    # 13-18
    NEW_ADULT = "new_adult"        # 18-25
    ADULT = "adult"                # 18+
    MATURE = "mature"              # 18+ with explicit content


class ContentRating(str, Enum):
    """Content rating level."""
    GENERAL = "general"            # Suitable for all ages
    TEEN = "teen"                  # Some mature themes
    MATURE = "mature"              # Explicit content allowed
    EXPLICIT = "explicit"          # Adult only


class PublishingGoal(str, Enum):
    """Primary publishing goal."""
    WATTPAD = "wattpad"            # Build audience on Wattpad
    ROYAL_ROAD = "royal_road"      # Web serial audience
    SELF_PUBLISH = "self_publish"  # Kindle, etc.
    TRADITIONAL = "traditional"    # Seek traditional publisher
    SERIAL = "serial"              # Multiple platforms serial
    PERSONAL = "personal"          # Personal project/learning


@dataclass
class ContentBoundaries:
    """Defines what content is allowed/forbidden."""
    allow_explicit_content: bool = False
    allow_violence: str = "none"  # none, mild, moderate, graphic
    allow_sexual_content: str = "none"  # none, implied, mild, explicit
    allow_dark_themes: bool = True
    dark_theme_treatment: str = "metaphorical"  # metaphorical, psychological, direct
    sensitive_topics: list[str] = field(default_factory=list)
    forbidden_topics: list[str] = field(default_factory=list)
    content_notes: str = ""


@dataclass
class TargetAudience:
    """Target audience definition."""
    age_group: AudienceAge = AudienceAge.YOUNG_ADULT
    primary_gender: str = "all"  # all, female, male
    regions: list[str] = field(default_factory=lambda: ["US", "UK"])
    reading_level: str = "casual"  # casual, intermediate, advanced
    interests: list[str] = field(default_factory=list)
    tropes_preferred: list[str] = field(default_factory=list)
    tropes_avoid: list[str] = field(default_factory=list)


@dataclass
class StylePreferences:
    """Writing style preferences."""
    pov: str = "first"  # first, third_limited, third_omniscient
    tense: str = "past"  # past, present
    tone: str = "balanced"  # dark, balanced, light
    pacing: str = "moderate"  # slow, moderate, fast
    dialogue_ratio: str = "balanced"  # dialogue_heavy, balanced, narrative_heavy
    description_level: str = "moderate"  # minimal, moderate, detailed
    chapter_length_target: int = 2500  # words per chapter
    language_style: str = "contemporary"  # contemporary, formal, poetic


@dataclass
class PublishingPlan:
    """Publishing strategy."""
    primary_platform: str = "wattpad"
    secondary_platforms: list[str] = field(default_factory=list)
    update_schedule: str = "weekly"  # daily, weekly, biweekly
    serialization: bool = True
    language_versions: list[str] = field(default_factory=lambda: ["en"])
    marketing_tags: list[str] = field(default_factory=list)
    completion_target: str = "1_year"  # 3_months, 6_months, 1_year, ongoing


@dataclass
class ProjectPlan:
    """Complete project plan."""
    # Basic Info
    title: str = ""
    genre: str = ""
    subgenres: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    premise: str = ""
    logline: str = ""

    # Scope
    target_words: int = 300000
    target_chapters: int = 100
    estimated_completion: str = "1_year"

    # Details
    audience: TargetAudience = field(default_factory=TargetAudience)
    boundaries: ContentBoundaries = field(default_factory=ContentBoundaries)
    style: StylePreferences = field(default_factory=StylePreferences)
    publishing: PublishingPlan = field(default_factory=PublishingPlan)

    # Project Goals
    primary_goal: str = "engagement"  # engagement, completion, revenue, learning
    success_metrics: list[str] = field(default_factory=list)

    # Metadata
    inspiration: str = ""
    comparable_works: list[str] = field(default_factory=list)
    unique_selling_points: list[str] = field(default_factory=list)

    # Planning State
    planning_complete: bool = False
    confirmed: bool = False
    notes: str = ""


class ProjectPlanner:
    """Interactive project planning assistant.

    Guides authors through a structured planning process to ensure
    all key decisions are made before writing begins.

    Example:
        planner = ProjectPlanner(llm=llm)

        # Start interactive planning
        response = await planner.start_planning()
        print(response.question)  # First question

        # Answer questions
        response = await planner.answer("I want to write a YA romance...")

        # Continue until complete
        while not response.is_complete:
            response = await planner.answer(user_input)

        # Get final plan
        plan = planner.get_plan()
    """

    # Planning stages
    STAGES = [
        "concept",        # What do you want to write?
        "audience",       # Who is this for?
        "scope",          # How long/complex?
        "content",        # What's allowed?
        "style",          # How should it read?
        "publishing",     # Where will it go?
        "review",         # Confirm everything
    ]

    def __init__(
        self,
        llm: BaseLLM,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize planner.

        Args:
            llm: LLM for generating questions and processing answers
            on_progress: Callback for progress updates (stage, message)
        """
        self.llm = llm
        self.on_progress = on_progress
        self.plan = ProjectPlan()
        self.current_stage = 0
        self.conversation_history: list[dict[str, str]] = []
        self.stage_data: dict[str, Any] = {}

    async def start_planning(self) -> dict[str, Any]:
        """Start the planning process.

        Returns:
            Dict with question, stage, and guidance
        """
        self.current_stage = 0
        self.plan = ProjectPlan()
        self.conversation_history = []

        return await self._ask_stage_question("concept")

    async def answer(self, user_input: str) -> dict[str, Any]:
        """Process user's answer and advance planning.

        Args:
            user_input: User's response to current question

        Returns:
            Dict with next question or completion status
        """
        self.conversation_history.append({"role": "user", "content": user_input})

        # Process the answer with LLM
        stage_name = self.STAGES[self.current_stage]
        processed = await self._process_answer(stage_name, user_input)

        # Update plan with extracted info
        self._update_plan(stage_name, processed)

        # Check if stage is complete
        if processed.get("stage_complete", False):
            self.current_stage += 1

            if self.current_stage >= len(self.STAGES):
                return await self._finalize_plan()

            return await self._ask_stage_question(self.STAGES[self.current_stage])

        # Ask follow-up question in same stage
        return await self._ask_followup(stage_name, processed)

    async def quick_plan(self, description: str, title: str | None = None) -> ProjectPlan:
        """Create a plan from a description without interaction.

        Useful for when the user provides a comprehensive description
        upfront and doesn't want step-by-step planning.

        Args:
            description: Natural language project description
            title: Optional title override (if provided, ignores LLM-generated title)

        Returns:
            ProjectPlan extracted from description
        """
        system_prompt = """You are a book planning expert. Extract all relevant
information from the user's description to create a complete project plan.
Output valid JSON only."""

        user_prompt = f"""Extract a complete project plan from this description:

"{description}"

Generate a JSON project plan:
{{
    "title": "Suggested title",
    "genre": "primary genre",
    "subgenres": ["subgenre1", "subgenre2"],
    "premise": "One sentence premise",
    "target_words": 300000,
    "target_chapters": 100,
    "audience": {{
        "age_group": "young_adult",
        "primary_gender": "all",
        "regions": ["US", "UK"],
        "interests": ["romance", "drama"],
        "tropes_preferred": ["enemies to lovers"],
        "tropes_avoid": ["love triangles"]
    }},
    "boundaries": {{
        "allow_explicit_content": false,
        "allow_violence": "mild",
        "allow_sexual_content": "implied",
        "allow_dark_themes": true,
        "dark_theme_treatment": "metaphorical",
        "sensitive_topics": ["abuse", "trauma"],
        "forbidden_topics": [],
        "content_notes": "Handle dark themes through metaphor"
    }},
    "style": {{
        "pov": "first",
        "tense": "past",
        "tone": "balanced",
        "pacing": "moderate",
        "chapter_length_target": 2500
    }},
    "publishing": {{
        "primary_platform": "wattpad",
        "secondary_platforms": ["royal_road"],
        "update_schedule": "weekly",
        "language_versions": ["en"],
        "marketing_tags": ["dark-romance", "secrets", "elite-society"]
    }},
    "primary_goal": "engagement",
    "themes": ["theme1", "theme2"],
    "inspiration": "What inspired this",
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
            data = json.loads(content)

            # Build ProjectPlan from data
            self.plan = self._dict_to_plan(data)
            self.plan.planning_complete = True

            # Override title if user provided one
            if title:
                self.plan.title = title

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse plan: {e}")
            # Create minimal plan
            self.plan.title = "New Project"
            self.plan.genre = "general"
            self.plan.premise = description[:200]

        return self.plan

    async def _ask_stage_question(self, stage: str) -> dict[str, Any]:
        """Generate question for current stage."""
        stage_prompts = {
            "concept": """Let's plan your book project! I'll guide you through the key decisions.

**Stage 1: Concept**

First, tell me about your book idea:
- What's the core concept or premise?
- What genre(s) are you thinking?
- Any initial title ideas?

Example: A YA romance about a girl who discovers her elite school hides dark secrets""",

            "audience": """**Stage 2: Target Audience**

Great concept! Now let's define your readers:

- What age group? (children 8-12, young adult 13-18, new adult 18-25, adult 18+)
- Primary region/market? (US, UK, international)
- What tropes do they love? What should we avoid?
- Any specific reader interests to target?

Your current concept: {concept}""",

            "scope": """**Stage 3: Scope & Scale**

Let's set realistic goals:

- Target word count? (Typical: 80K-120K for YA, 300K+ for web serial)
- Number of chapters planned?
- How much time can you commit? (affects update schedule)
- Is this a standalone or series?

Current audience: {audience}""",

            "content": """**Stage 4: Content Boundaries**

Important for both writing and publishing:

- Any mature content? (violence, romance intensity)
- How should dark themes be handled? (direct, metaphorical, psychological)
- Any topics to avoid completely?
- Content warnings needed?

Your genre: {genre}""",

            "style": """**Stage 5: Writing Style**

How should your story read?

- Point of view? (first person, third limited, omniscient)
- Past or present tense?
- Tone? (dark, balanced, light/hopeful)
- Pacing preference? (slow burn, moderate, fast-paced)
- Chapter length preference? (1.5K, 2.5K, 4K words)""",

            "publishing": """**Stage 6: Publishing Strategy**

Where will readers find your work?

- Primary platform? (Wattpad, Royal Road, Kindle Vella, etc.)
- Multiple platforms or focus on one?
- Language versions needed? (English only, bilingual, translations)
- Update schedule? (daily, weekly, bi-weekly)
- Marketing approach? (tags, communities, cross-promotion)""",

            "review": """**Stage 7: Final Review**

Let's confirm your project plan:

{plan_summary}

Does this look correct? Any changes needed?

Type "confirm" to finalize, or tell me what to adjust.""",
        }

        question = stage_prompts.get(stage, "What would you like to discuss?")

        # Fill in context
        if "{concept}" in question:
            question = question.format(concept=self.plan.premise or "Not yet defined")
        if "{audience}" in question:
            question = question.format(audience=self.plan.audience.age_group.value if self.plan.audience else "Not set")
        if "{genre}" in question:
            question = question.format(genre=self.plan.genre or "Not set")
        if "{plan_summary}" in question:
            question = question.format(plan_summary=self._format_plan_summary())

        if self.on_progress:
            self.on_progress(stage, question)

        return {
            "question": question,
            "stage": stage,
            "stage_number": self.current_stage + 1,
            "total_stages": len(self.STAGES),
            "is_complete": False,
        }

    async def _process_answer(self, stage: str, answer: str) -> dict[str, Any]:
        """Process user's answer for a stage."""
        system_prompt = f"""You are a book planning assistant. Extract structured information
from the user's response for the "{stage}" planning stage.
Output valid JSON only."""

        context = self._get_plan_context()

        user_prompt = f"""Current project context:
{context}

User's response for {stage} stage:
"{answer}"

Extract relevant information and determine:
1. What information was provided
2. Is this stage complete or need follow-up?
3. Any clarifications needed?

Generate JSON:
{{
    "extracted": {{
        // Information extracted from answer for this stage
    }},
    "stage_complete": true/false,
    "followup_needed": true/false,
    "followup_question": "If follow-up needed, what to ask",
    "clarifications": ["Any unclear points"]
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
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "extracted": {},
                "stage_complete": True,
                "followup_needed": False,
            }

    def _update_plan(self, stage: str, processed: dict[str, Any]) -> None:
        """Update plan with extracted information."""
        extracted = processed.get("extracted", {})

        if stage == "concept":
            if "title" in extracted:
                self.plan.title = extracted["title"]
            if "genre" in extracted:
                self.plan.genre = extracted["genre"]
            if "subgenres" in extracted:
                self.plan.subgenres = extracted["subgenres"]
            if "premise" in extracted:
                self.plan.premise = extracted["premise"]
            if "logline" in extracted:
                self.plan.logline = extracted["logline"]

        elif stage == "audience":
            if "age_group" in extracted:
                self.plan.audience.age_group = AudienceAge(extracted["age_group"])
            if "primary_gender" in extracted:
                self.plan.audience.primary_gender = extracted["primary_gender"]
            if "regions" in extracted:
                self.plan.audience.regions = extracted["regions"]
            if "interests" in extracted:
                self.plan.audience.interests = extracted["interests"]
            if "tropes_preferred" in extracted:
                self.plan.audience.tropes_preferred = extracted["tropes_preferred"]
            if "tropes_avoid" in extracted:
                self.plan.audience.tropes_avoid = extracted["tropes_avoid"]

        elif stage == "scope":
            if "target_words" in extracted:
                self.plan.target_words = extracted["target_words"]
            if "target_chapters" in extracted:
                self.plan.target_chapters = extracted["target_chapters"]
            if "estimated_completion" in extracted:
                self.plan.estimated_completion = extracted["estimated_completion"]

        elif stage == "content":
            if "allow_explicit_content" in extracted:
                self.plan.boundaries.allow_explicit_content = extracted["allow_explicit_content"]
            if "allow_violence" in extracted:
                self.plan.boundaries.allow_violence = extracted["allow_violence"]
            if "allow_sexual_content" in extracted:
                self.plan.boundaries.allow_sexual_content = extracted["allow_sexual_content"]
            if "dark_theme_treatment" in extracted:
                self.plan.boundaries.dark_theme_treatment = extracted["dark_theme_treatment"]
            if "sensitive_topics" in extracted:
                self.plan.boundaries.sensitive_topics = extracted["sensitive_topics"]
            if "forbidden_topics" in extracted:
                self.plan.boundaries.forbidden_topics = extracted["forbidden_topics"]

        elif stage == "style":
            if "pov" in extracted:
                self.plan.style.pov = extracted["pov"]
            if "tense" in extracted:
                self.plan.style.tense = extracted["tense"]
            if "tone" in extracted:
                self.plan.style.tone = extracted["tone"]
            if "pacing" in extracted:
                self.plan.style.pacing = extracted["pacing"]
            if "chapter_length_target" in extracted:
                self.plan.style.chapter_length_target = extracted["chapter_length_target"]

        elif stage == "publishing":
            if "primary_platform" in extracted:
                self.plan.publishing.primary_platform = extracted["primary_platform"]
            if "secondary_platforms" in extracted:
                self.plan.publishing.secondary_platforms = extracted["secondary_platforms"]
            if "update_schedule" in extracted:
                self.plan.publishing.update_schedule = extracted["update_schedule"]
            if "language_versions" in extracted:
                self.plan.publishing.language_versions = extracted["language_versions"]
            if "marketing_tags" in extracted:
                self.plan.publishing.marketing_tags = extracted["marketing_tags"]

        elif stage == "review":
            if extracted.get("confirmed"):
                self.plan.confirmed = True

    async def _ask_followup(self, stage: str, processed: dict[str, Any]) -> dict[str, Any]:
        """Ask follow-up question if needed."""
        if processed.get("followup_needed") and processed.get("followup_question"):
            return {
                "question": processed["followup_question"],
                "stage": stage,
                "stage_number": self.current_stage + 1,
                "total_stages": len(self.STAGES),
                "is_complete": False,
            }

        # No follow-up needed, move to next stage
        self.current_stage += 1
        if self.current_stage >= len(self.STAGES):
            return await self._finalize_plan()

        return await self._ask_stage_question(self.STAGES[self.current_stage])

    async def _finalize_plan(self) -> dict[str, Any]:
        """Finalize and return the complete plan."""
        self.plan.planning_complete = True

        return {
            "question": f"""✅ **Planning Complete!**

{self._format_plan_summary()}

Your project plan is ready. You can now:
- Start writing with `/write chapter 1`
- Generate outline with `/outline create`
- Create characters with `/character create`

Type "start" to begin writing, or ask any questions about the plan.""",
            "stage": "complete",
            "stage_number": len(self.STAGES),
            "total_stages": len(self.STAGES),
            "is_complete": True,
            "plan": self._plan_to_dict(),
        }

    def get_plan(self) -> ProjectPlan:
        """Get the current plan."""
        return self.plan

    def _plan_to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary."""
        return {
            "title": self.plan.title,
            "genre": self.plan.genre,
            "subgenres": self.plan.subgenres,
            "themes": self.plan.themes,
            "premise": self.plan.premise,
            "audience": {
                "age_group": self.plan.audience.age_group.value,
                "primary_gender": self.plan.audience.primary_gender,
                "regions": self.plan.audience.regions,
                "interests": self.plan.audience.interests,
                "tropes_preferred": self.plan.audience.tropes_preferred,
                "tropes_avoid": self.plan.audience.tropes_avoid,
            },
            "boundaries": {
                "allow_explicit_content": self.plan.boundaries.allow_explicit_content,
                "allow_violence": self.plan.boundaries.allow_violence,
                "allow_sexual_content": self.plan.boundaries.allow_sexual_content,
                "dark_theme_treatment": self.plan.boundaries.dark_theme_treatment,
                "sensitive_topics": self.plan.boundaries.sensitive_topics,
            },
            "style": {
                "pov": self.plan.style.pov,
                "tense": self.plan.style.tense,
                "tone": self.plan.style.tone,
                "pacing": self.plan.style.pacing,
                "chapter_length_target": self.plan.style.chapter_length_target,
            },
            "publishing": {
                "primary_platform": self.plan.publishing.primary_platform,
                "secondary_platforms": self.plan.publishing.secondary_platforms,
                "update_schedule": self.plan.publishing.update_schedule,
                "language_versions": self.plan.publishing.language_versions,
            },
        }

    def _dict_to_plan(self, data: dict[str, Any]) -> ProjectPlan:
        """Convert dictionary to ProjectPlan."""
        plan = ProjectPlan()

        plan.genre = data.get("genre", "")
        plan.subgenres = data.get("subgenres", [])
        plan.themes = data.get("themes", [])
        plan.premise = data.get("premise", "")
        plan.target_words = data.get("target_words", 300000)
        plan.target_chapters = data.get("target_chapters", 100)

        if "audience" in data:
            aud = data["audience"]
            plan.audience = TargetAudience(
                age_group=AudienceAge(aud.get("age_group", "young_adult")),
                primary_gender=aud.get("primary_gender", "all"),
                regions=aud.get("regions", ["US", "UK"]),
                interests=aud.get("interests", []),
                tropes_preferred=aud.get("tropes_preferred", []),
                tropes_avoid=aud.get("tropes_avoid", []),
            )

        if "boundaries" in data:
            bnd = data["boundaries"]
            plan.boundaries = ContentBoundaries(
                allow_explicit_content=bnd.get("allow_explicit_content", False),
                allow_violence=bnd.get("allow_violence", "none"),
                allow_sexual_content=bnd.get("allow_sexual_content", "none"),
                dark_theme_treatment=bnd.get("dark_theme_treatment", "metaphorical"),
                sensitive_topics=bnd.get("sensitive_topics", []),
                forbidden_topics=bnd.get("forbidden_topics", []),
            )

        if "style" in data:
            sty = data["style"]
            plan.style = StylePreferences(
                pov=sty.get("pov", "first"),
                tense=sty.get("tense", "past"),
                tone=sty.get("tone", "balanced"),
                pacing=sty.get("pacing", "moderate"),
                chapter_length_target=sty.get("chapter_length_target", 2500),
            )

        if "publishing" in data:
            pub = data["publishing"]
            plan.publishing = PublishingPlan(
                primary_platform=pub.get("primary_platform", "wattpad"),
                secondary_platforms=pub.get("secondary_platforms", []),
                update_schedule=pub.get("update_schedule", "weekly"),
                language_versions=pub.get("language_versions", ["en"]),
                marketing_tags=pub.get("marketing_tags", []),
            )

        plan.inspiration = data.get("inspiration", "")
        plan.comparable_works = data.get("comparable_works", [])
        plan.unique_selling_points = data.get("unique_selling_points", [])
        plan.notes = data.get("notes", "")

        return plan

    def _get_plan_context(self) -> str:
        """Get current plan as context string."""
        return f"""
Title: {self.plan.title or 'Not set'}
Genre: {self.plan.genre or 'Not set'}
Premise: {self.plan.premise or 'Not set'}
Target: {self.plan.target_words:,} words, {self.plan.target_chapters} chapters
Audience: {self.plan.audience.age_group.value if self.plan.audience else 'Not set'}
Platform: {self.plan.publishing.primary_platform if self.plan.publishing else 'Not set'}
"""

    def _format_plan_summary(self) -> str:
        """Format plan as readable summary."""
        return f"""📚 **{self.plan.title or 'Untitled Project'}**

**Concept:**
  • Genre: {self.plan.genre or 'Not set'}
  • Subgenres: {', '.join(self.plan.subgenres) or 'None'}
  • Premise: {self.plan.premise or 'Not defined'}

**Scope:**
  • Target: {self.plan.target_words:,} words / {self.plan.target_chapters} chapters
  • Chapter length: ~{self.plan.style.chapter_length_target:,} words

**Audience:**
  • Age group: {self.plan.audience.age_group.value}
  • Market: {', '.join(self.plan.audience.regions)}
  • Loved tropes: {', '.join(self.plan.audience.tropes_preferred[:3]) or 'Not specified'}
  • Avoided tropes: {', '.join(self.plan.audience.tropes_avoid[:3]) or 'None'}

**Content Guidelines:**
  • Explicit content: {'Yes' if self.plan.boundaries.allow_explicit_content else 'No'}
  • Violence: {self.plan.boundaries.allow_violence}
  • Sexual content: {self.plan.boundaries.allow_sexual_content}
  • Dark themes: {self.plan.boundaries.dark_theme_treatment}

**Style:**
  • POV: {self.plan.style.pov} person, {self.plan.style.tense} tense
  • Tone: {self.plan.style.tone}, Pacing: {self.plan.style.pacing}

**Publishing:**
  • Platform: {self.plan.publishing.primary_platform}
  • Languages: {', '.join(self.plan.publishing.language_versions)}
  • Schedule: {self.plan.publishing.update_schedule} updates"""
