# src/agents/reader_persona.py
"""Reader Persona - Target audience analysis and validation."""

from dataclasses import dataclass
from typing import Any

from src.agents.base import AgentResult, BaseAgent


@dataclass
class ReaderPersona:
    """Target reader profile for web fiction."""
    name: str
    age_range: tuple[int, int]
    gender_preference: str  # "male", "female", "any"

    # Reading habits
    preferred_reading_time: list[str]  # "commute", "bedtime", "weekend", "breaks"
    average_session_minutes: int
    chapters_per_session: int

    # Content preferences
    favorite_genres: list[str]
    favorite_tropes: list[str]
    hated_tropes: list[str]
    content_triggers: list[str]  # Things they want to avoid

    # Engagement style
    engagement_level: str  # "lurker", "commenter", "voter", "superfan"
    platform_preference: list[str]  # "wattpad", "royalroad", "qidian", etc.

    # Pain points and desires
    reading_pain_points: list[str]
    story_desires: list[str]
    character_preferences: list[str]

    # Demographics
    region: str
    language: str
    device_preference: str  # "mobile", "tablet", "desktop"


@dataclass
class ContentValidationResult:
    """Result of validating content against reader persona."""
    overall_match_score: float  # 0-100
    chapter_appropriateness: dict[int, float]  # Chapter -> score
    strengths: list[str]
    concerns: list[str]
    recommendations: list[str]
    risk_factors: list[str]


class ReaderPersonaAnalyzer(BaseAgent):
    """Agent that analyzes target reader personas and validates content.

    Helps ensure content matches target audience expectations and preferences.
    """

    # Predefined personas for common web fiction demographics
    PERSONA_TEMPLATES = {
        "young_adult_female": ReaderPersona(
            name="Young Adult Female (16-24)",
            age_range=(16, 24),
            gender_preference="female",
            preferred_reading_time=["bedtime", "commute", "breaks"],
            average_session_minutes=20,
            chapters_per_session=2,
            favorite_genres=["romance", "fantasy", "drama", "young adult"],
            favorite_tropes=[
                "enemies to lovers",
                "slow burn",
                "forced proximity",
                "grumpy/sunshine",
                "fake relationship",
            ],
            hated_tropes=[
                "love triangle",
                "miscommunication",
                "insta-love",
            ],
            content_triggers=["sexual violence", "graphic gore", "animal cruelty"],
            engagement_level="voter",
            platform_preference=["wattpad", "webnovel"],
            reading_pain_points=[
                "chapters that don't end with hooks",
                "too much exposition",
                "boring protagonists",
                "slow pacing",
            ],
            story_desires=[
                "strong emotional connection",
                "character growth",
                "satisfying romance",
                "page-turning plot",
            ],
            character_preferences=[
                "relatable protagonist",
                "complex love interest",
                "supportive friends",
                "clear antagonist",
            ],
            region="global",
            language="en",
            device_preference="mobile",
        ),

        "millennial_urban_professional": ReaderPersona(
            name="Millennial Urban Professional (25-35)",
            age_range=(25, 35),
            gender_preference="any",
            preferred_reading_time=["commute", "lunch break", "bedtime"],
            average_session_minutes=15,
            chapters_per_session=1,
            favorite_genres=["thriller", "mystery", "scifi", "literary fiction"],
            favorite_tropes=[
                "unreliable narrator",
                "twist ending",
                "found family",
                "redemption arc",
            ],
            hated_tropes=[
                "deus ex machina",
                "predictable plots",
                "paper-thin villains",
            ],
            content_triggers=["child harm"],
            engagement_level="commenter",
            platform_preference=["royalroad", "amazon"],
            reading_pain_points=[
                "spelling errors",
                "inconsistent characterization",
                "plot holes",
                "wasted potential",
            ],
            story_desires=[
                "intellectual stimulation",
                "unexpected twists",
                "satisfying endings",
                "high production value",
            ],
            character_preferences=[
                "morally gray characters",
                "competent protagonists",
                "authentic dialogue",
                "growth and change",
            ],
            region="north_america",
            language="en",
            device_preference="mobile",
        ),

        "litpg_gamer": ReaderPersona(
            name="LitRPG/Gamer Enthusiast (18-30)",
            age_range=(18, 30),
            gender_preference="male",
            preferred_reading_time=["evening", "weekend"],
            average_session_minutes=45,
            chapters_per_session=3,
            favorite_genres=["litrpg", "isekai", "progression fantasy", "scifi"],
            favorite_tropes=[
                "leveling system",
                "underdog protagonist",
                "skill progression",
                "dungeon diving",
                "guild building",
            ],
            hated_tropes=[
                "plot armor",
                "stupid decisions for drama",
                "ignored game mechanics",
                "harem without development",
            ],
            content_triggers=["ntr", "rape"],
            engagement_level="superfan",
            platform_preference=["royalroad", "webnovel"],
            reading_pain_points=[
                "inconsistent power levels",
                "boring grinding chapters",
                "too much status screen",
                "stupid MC decisions",
            ],
            story_desires=[
                "satisfying progression",
                "cool abilities",
                "epic battles",
                "logical worldbuilding",
            ],
            character_preferences=[
                "competent protagonist",
                "loyal companions",
                "memorable villains",
                "progression clarity",
            ],
            region="global",
            language="en",
            device_preference="desktop",
        ),

        "chinese_web_novel_reader": ReaderPersona(
            name="Chinese Web Novel Regular (20-40)",
            age_range=(20, 40),
            gender_preference="any",
            preferred_reading_time=["commute", "breaks", "evening"],
            average_session_minutes=30,
            chapters_per_session=5,
            favorite_genres=["xianxia", "wuxia", "urban fantasy", "historical"],
            favorite_tropes=[
                "cultivation",
                "face-slapping",
                "hidden identity",
                "revenge",
                "loyal followers",
            ],
            hated_tropes=[
                "endless repetitive arcs",
                "forgotten characters",
                "abandoned plot threads",
                "deus ex machina breakthroughs",
            ],
            content_triggers=[],
            engagement_level="commenter",
            platform_preference=["qidian", "jinjiang", "webnovel"],
            reading_pain_points=[
                "slow release schedule",
                "filler chapters",
                "inconsistent power scaling",
                "too many side characters",
            ],
            story_desires=[
                "satisfying face-slapping",
                "steady power progression",
                "loyal relationships",
                "epic scale",
            ],
            character_preferences=[
                "hardworking protagonist",
                "loyal friends/allies",
                "arrogant young masters (to defeat)",
                "wise mentors",
            ],
            region="china",
            language="zh",
            device_preference="mobile",
        ),
    }

    def __init__(self, name: str = "Reader Persona Analyzer", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Analyze or create reader persona.

        Args:
            input_data: Can contain:
                - action: "get_template", "validate_content", "create_custom"
                - persona_key: str (for get_template)
                - content: str or list[str] (for validate_content)
                - custom_params: dict (for create_custom)

        Returns:
            AgentResult with persona or validation results
        """
        try:
            action = input_data.get("action", "get_template")

            if action == "get_template":
                persona_key = input_data.get("persona_key", "young_adult_female")
                persona = self._get_persona_template(persona_key)
                return AgentResult(
                    success=True,
                    data={"persona": self._serialize_persona(persona)}
                )

            elif action == "validate_content":
                content = input_data.get("content", "")
                persona_key = input_data.get("persona_key", "young_adult_female")
                persona = self._get_persona_template(persona_key)

                validation = await self._validate_content(content, persona)
                return AgentResult(
                    success=True,
                    data={"validation": self._serialize_validation(validation)}
                )

            elif action == "create_custom":
                params = input_data.get("custom_params", {})
                persona = self._create_custom_persona(params)
                return AgentResult(
                    success=True,
                    data={"persona": self._serialize_persona(persona)}
                )

            else:
                return AgentResult(
                    success=False,
                    data={},
                    errors=[f"Unknown action: {action}"]
                )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Persona analysis failed: {str(e)}"]
            )

    def _get_persona_template(self, key: str) -> ReaderPersona:
        """Get predefined persona template."""
        if key not in self.PERSONA_TEMPLATES:
            key = "young_adult_female"  # Default
        return self.PERSONA_TEMPLATES[key]

    def _create_custom_persona(self, params: dict[str, Any]) -> ReaderPersona:
        """Create custom persona from parameters."""
        return ReaderPersona(
            name=params.get("name", "Custom Persona"),
            age_range=params.get("age_range", (18, 35)),
            gender_preference=params.get("gender_preference", "any"),
            preferred_reading_time=params.get("preferred_reading_time", ["evening"]),
            average_session_minutes=params.get("average_session_minutes", 20),
            chapters_per_session=params.get("chapters_per_session", 2),
            favorite_genres=params.get("favorite_genres", []),
            favorite_tropes=params.get("favorite_tropes", []),
            hated_tropes=params.get("hated_tropes", []),
            content_triggers=params.get("content_triggers", []),
            engagement_level=params.get("engagement_level", "lurker"),
            platform_preference=params.get("platform_preference", []),
            reading_pain_points=params.get("reading_pain_points", []),
            story_desires=params.get("story_desires", []),
            character_preferences=params.get("character_preferences", []),
            region=params.get("region", "global"),
            language=params.get("language", "en"),
            device_preference=params.get("device_preference", "mobile"),
        )

    async def _validate_content(
        self, content: str, persona: ReaderPersona
    ) -> ContentValidationResult:
        """Validate content against reader persona."""

        strengths = []
        concerns = []
        recommendations = []
        risk_factors = []

        # Check mobile readability
        paragraphs = content.split('\n\n')
        long_paras = sum(1 for p in paragraphs if len(p.split()) > 60)
        if long_para_ratio := long_paras / max(len(paragraphs), 1) > 0.3:
            if persona.device_preference == "mobile":
                concerns.append(f"{long_para_ratio:.0%} paragraphs too long for mobile reading")
                recommendations.append("Break paragraphs into 4-line chunks for mobile")
        else:
            strengths.append("Good mobile readability")

        # Check dialogue ratio
        dialogue_words = sum(len(line.split()) for line in content.split('"') if content.split('"').index(line) % 2 == 1)
        total_words = len(content.split())
        dialogue_ratio = dialogue_words / max(total_words, 1)

        if dialogue_ratio < 0.25:
            concerns.append(f"Low dialogue ratio ({dialogue_ratio:.0%}) - may feel slow")
            recommendations.append("Add more dialogue to increase engagement")
        elif dialogue_ratio > 0.50:
            if "dialogue-heavy" not in persona.story_desires:
                concerns.append("Very high dialogue ratio - may lack description")
        else:
            strengths.append("Good dialogue balance")

        # Check hooks
        first_300 = ' '.join(content.split()[:300])
        if any(word in first_300.lower() for word in ['suddenly', 'impossible', 'never', 'shock', 'scream']):
            strengths.append("Strong opening hook")
        else:
            concerns.append("Opening may lack strong hook")
            recommendations.append("Start with action, dialogue, or intrigue")

        last_200 = ' '.join(content.split()[-200:])
        hook_words = ['?', '!', '...', 'what', 'who', 'how', 'wait', 'truth', 'secret']
        if any(word in last_200.lower() for word in hook_words):
            strengths.append("Closing hook present")
        else:
            concerns.append("Chapter ending lacks hook")
            recommendations.append("End with cliffhanger or unresolved question")

        # Check for pain points
        if "slow pacing" in persona.reading_pain_points:
            # Check for exposition-heavy sections
            exposition_indicators = ['was a', 'had been', 'used to', 'meant that']
            exposition_count = sum(content.lower().count(indicator) for indicator in exposition_indicators)
            if exposition_count > 10:
                concerns.append("May have too much exposition/backstory")
                recommendations.append("Show backstory through action, not narration")

        # Calculate overall score
        score = 70  # Base score
        score += len(strengths) * 5
        score -= len(concerns) * 5
        score = max(0, min(100, score))

        # Identify risk factors
        if len(concerns) > len(strengths):
            risk_factors.append("More concerns than strengths - revision recommended")
        if score < 60:
            risk_factors.append("Low match score - may not resonate with target audience")

        return ContentValidationResult(
            overall_match_score=score,
            chapter_appropriateness={1: score},  # Could expand for multiple chapters
            strengths=strengths,
            concerns=concerns,
            recommendations=recommendations,
            risk_factors=risk_factors,
        )

    def _serialize_persona(self, persona: ReaderPersona) -> dict[str, Any]:
        """Convert persona to dict."""
        return {
            "name": persona.name,
            "age_range": persona.age_range,
            "gender_preference": persona.gender_preference,
            "preferred_reading_time": persona.preferred_reading_time,
            "average_session_minutes": persona.average_session_minutes,
            "chapters_per_session": persona.chapters_per_session,
            "favorite_genres": persona.favorite_genres,
            "favorite_tropes": persona.favorite_tropes,
            "hated_tropes": persona.hated_tropes,
            "content_triggers": persona.content_triggers,
            "engagement_level": persona.engagement_level,
            "platform_preference": persona.platform_preference,
            "reading_pain_points": persona.reading_pain_points,
            "story_desires": persona.story_desires,
            "character_preferences": persona.character_preferences,
            "region": persona.region,
            "language": persona.language,
            "device_preference": persona.device_preference,
        }

    def _serialize_validation(self, validation: ContentValidationResult) -> dict[str, Any]:
        """Convert validation to dict."""
        return {
            "overall_match_score": validation.overall_match_score,
            "chapter_appropriateness": validation.chapter_appropriateness,
            "strengths": validation.strengths,
            "concerns": validation.concerns,
            "recommendations": validation.recommendations,
            "risk_factors": validation.risk_factors,
        }

    def get_recommendations_for_persona(self, persona_key: str) -> list[str]:
        """Get writing recommendations for a specific persona."""
        persona = self._get_persona_template(persona_key)

        recommendations = []

        # Device-based recommendations
        if persona.device_preference == "mobile":
            recommendations.append("Keep paragraphs under 60 words (4 mobile lines)")
            recommendations.append("Use short, punchy sentences")

        # Time-based recommendations
        if "commute" in persona.preferred_reading_time:
            recommendations.append("Chapter hooks must be immediate - readers start/stop frequently")
        if "bedtime" in persona.preferred_reading_time:
            recommendations.append("Emotional beats should be satisfying but not too intense")

        # Engagement-based recommendations
        if persona.engagement_level in ["commenter", "superfan"]:
            recommendations.append("Leave room for reader interpretation and discussion")
            recommendations.append("Character decisions should spark debate")

        # Pain point avoidance
        for pain_point in persona.reading_pain_points[:3]:
            if "slow" in pain_point.lower():
                recommendations.append("Maintain brisk pacing - avoid lengthy exposition")
            if "boring" in pain_point.lower():
                recommendations.append("Ensure protagonist has clear agency and drive")

        return recommendations
