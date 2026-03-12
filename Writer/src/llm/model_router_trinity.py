# src/llm/model_router_trinity.py
"""Trinity Model Router - Optimized for GLM-5 (Coding Plan) + Kimi 2.5 + DeepSeek setup."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Language(Enum):
    """Target language for content."""
    CHINESE = "zh"
    ENGLISH = "en"


class ContentTier(Enum):
    """Content quality tiers."""
    ELITE = "elite"           # Top 5% content - highest quality
    STANDARD = "standard"     # Main content - good quality
    UTILITY = "utility"       # Architecture, planning, coding


@dataclass
class RoutingDecision:
    """Decision for which model to use."""
    primary_model: str
    fallback_model: str
    tier: ContentTier
    temperature: float
    max_tokens: int
    reasoning: str
    estimated_cost: float
    language_note: str = ""


class TrinityModelRouter:
    """Three-model router optimized for GLM-5 Coding Plan + Kimi 2.5 + DeepSeek.

    Model Roles:
    - GLM-5 (Coding Plan): Architecture, coding, logic, worldbuilding
      * Cost: Fixed (already paid)
      * Best for: Outline, system design, sci-fi logic, programming tasks

    - Kimi 2.5: Creative peaks, emotional content, golden chapters
      * Cost: ¥0.015/1k tokens (premium)
      * Best for: Chapter 1-3, climaxes, romance, emotional beats

    - DeepSeek V3: Daily chapters, bulk generation, standard content
      * Cost: ¥0.002/1k tokens (cheap)
      * Best for: 80% of chapters, cost-effective volume
    """

    MODELS = {
        "kimi_k2.5": {
            "name": "Kimi K2.5",
            "provider": "moonshot",
            "cost_per_1k_tokens": 0.015,
            "context_window": 256000,
            "zh_strengths": ["emotion", "creativity", "chinese_culture", "dialogue"],
            "en_strengths": ["emotion", "creativity"],  # Good but not native
            "weaknesses": ["cost"],
        },
        "glm5": {
            "name": "GLM-5",
            "provider": "zhipu",
            "cost_per_1k_tokens": 0.0,  # Fixed by coding plan
            "context_window": 200000,
            "zh_strengths": ["logic", "coding", "worldbuilding", "architecture"],
            "en_strengths": ["logic", "coding", "technical"],  # Decent English
            "weaknesses": ["emotion"],
        },
        "deepseek_v3": {
            "name": "DeepSeek V3",
            "provider": "deepseek",
            "cost_per_1k_tokens": 0.002,
            "context_window": 1000000,
            "zh_strengths": ["chinese", "cost_efficiency", "consistency", "volume"],
            "en_strengths": ["cost_efficiency", "consistency"],  # Adequate
            "weaknesses": ["creativity", "emotion"],
        },
    }

    def __init__(self, language: Language = Language.CHINESE):
        """Initialize router.

        Args:
            language: Target language (affects model selection)
        """
        self.language = language
        self.usage_stats = {
            model: {"tokens": 0, "cost": 0.0, "calls": 0}
            for model in self.MODELS.keys()
        }

    def route(
        self,
        task_type: str,  # "outline", "chapter", "revision", "coding"
        chapter_number: int | None = None,
        total_chapters: int = 100,
        genre: str = "fantasy",
        content_description: str = "",
    ) -> RoutingDecision:
        """Route task to optimal model.

        Strategy:
        1. GLM-5 for architecture/outline (fixed cost, use freely)
        2. Kimi for golden chapters & emotional peaks
        3. DeepSeek for everything else
        """

        # Task-based routing
        if task_type == "outline":
            # Architecture - GLM-5 (coding plan, fixed cost)
            return self._glm5_decision("Story architecture and worldbuilding")

        elif task_type == "coding":
            # System design - GLM-5
            return self._glm5_decision("System/coding logic")

        elif task_type == "revision":
            # Revision - Kimi for quality
            return self._kimi_decision("Quality revision and enhancement", "ELITE")

        elif task_type == "chapter":
            # Chapter generation
            return self._route_chapter(chapter_number, total_chapters, genre, content_description)

        else:
            # Default to DeepSeek
            return self._deepseek_decision("Standard generation")

    def _route_chapter(
        self,
        chapter_number: int | None,
        total_chapters: int,
        genre: str,
        description: str
    ) -> RoutingDecision:
        """Route chapter generation."""

        if chapter_number is None:
            return self._deepseek_decision("Standard chapter")

        # Golden chapters (1-3) - Always Kimi
        if chapter_number <= 3:
            return self._kimi_decision(
                f"Golden Chapter {chapter_number} - Reader retention critical",
                "ELITE"
            )

        # Emotional genres in elite chapters
        if genre in ["romance", "drama"] and self._is_emotional_chapter(chapter_number, total_chapters):
            return self._kimi_decision("Emotional peak chapter", "ELITE")

        # Logic-heavy genres - GLM-5 for key chapters
        if genre in ["scifi", "system"] and self._is_key_chapter(chapter_number, total_chapters):
            return self._glm5_decision("Logic-consistency critical chapter")

        # Volume starts (every 50 chapters) - Kimi
        if chapter_number % 50 == 1:
            return self._kimi_decision("Volume start - new arc hook", "ELITE")

        # Climax chapters (85-95%)
        progress = chapter_number / total_chapters
        if 0.85 <= progress <= 0.95:
            return self._kimi_decision("Story climax", "ELITE")

        # Finale
        if progress > 0.95:
            return self._kimi_decision("Story finale", "ELITE")

        # Everything else - DeepSeek
        return self._deepseek_decision("Standard chapter content")

    def _kimi_decision(self, reasoning: str, tier: str) -> RoutingDecision:
        """Create Kimi decision."""
        self.MODELS["kimi_k2.5"]["cost_per_1k_tokens"]

        # English note
        lang_note = ""
        if self.language == Language.ENGLISH:
            lang_note = "Note: Kimi's English is good but not native-level emotional"

        return RoutingDecision(
            primary_model="kimi_k2.5",
            fallback_model="deepseek_v3",
            tier=ContentTier.ELITE if tier == "ELITE" else ContentTier.STANDARD,
            temperature=0.7,
            max_tokens=4000,
            reasoning=reasoning,
            estimated_cost=0.045,  # 3000 tokens * 0.015
            language_note=lang_note,
        )

    def _glm5_decision(self, reasoning: str) -> RoutingDecision:
        """Create GLM-5 decision."""
        return RoutingDecision(
            primary_model="glm5",
            fallback_model="deepseek_v3",
            tier=ContentTier.UTILITY,
            temperature=0.6,  # Lower for logic tasks
            max_tokens=4000,
            reasoning=f"{reasoning} - GLM-5 (Coding Plan, no marginal cost)",
            estimated_cost=0.0,  # Fixed by plan
            language_note="" if self.language == Language.CHINESE else "GLM-5 has decent English for technical tasks",
        )

    def _deepseek_decision(self, reasoning: str) -> RoutingDecision:
        """Create DeepSeek decision."""
        self.MODELS["deepseek_v3"]["cost_per_1k_tokens"]

        # English note
        lang_note = ""
        if self.language == Language.ENGLISH:
            lang_note = "English acceptable for standard content, consider GPT-4 for elite chapters"

        return RoutingDecision(
            primary_model="deepseek_v3",
            fallback_model="glm5",
            tier=ContentTier.STANDARD,
            temperature=0.8,
            max_tokens=4000,
            reasoning=reasoning,
            estimated_cost=0.006,  # 3000 tokens * 0.002
            language_note=lang_note,
        )

    def _is_emotional_chapter(self, chapter_number: int, total_chapters: int) -> bool:
        """Check if chapter likely contains emotional peaks."""
        # Simple heuristic: emotional chapters often at 25%, 50%, 75% marks
        progress = chapter_number / total_chapters
        emotional_points = [0.25, 0.5, 0.75]
        return any(abs(progress - point) < 0.05 for point in emotional_points)

    def _is_key_chapter(self, chapter_number: int, total_chapters: int) -> bool:
        """Check if chapter is key plot point."""
        progress = chapter_number / total_chapters
        key_points = [0.25, 0.5, 0.75, 0.85]
        return any(abs(progress - point) < 0.05 for point in key_points)

    def get_cost_estimate(self, total_chapters: int, genre: str) -> dict[str, Any]:
        """Estimate costs for a full novel."""

        # Count chapter types
        golden_chapters = 3
        volume_starts = total_chapters // 50
        climax_chapters = max(1, int(total_chapters * 0.1))  # 10% for climax/finale
        emotional_peaks = 3 if genre in ["romance", "drama"] else 1

        elite_chapters = golden_chapters + volume_starts + climax_chapters + emotional_peaks
        standard_chapters = total_chapters - elite_chapters

        # Calculate costs
        kimi_cost = elite_chapters * 0.045  # ¥0.015 * 3000 tokens
        deepseek_cost = standard_chapters * 0.006  # ¥0.002 * 3000 tokens

        # Outline and architecture (GLM-5)

        total = kimi_cost + deepseek_cost

        return {
            "total_chapters": total_chapters,
            "genre": genre,
            "language": self.language.value,
            "breakdown": {
                "elite_chapters": {
                    "count": elite_chapters,
                    "model": "kimi_k2.5",
                    "cost": round(kimi_cost, 2),
                    "percentage": round(kimi_cost / total * 100, 1) if total > 0 else 0,
                },
                "standard_chapters": {
                    "count": standard_chapters,
                    "model": "deepseek_v3",
                    "cost": round(deepseek_cost, 2),
                    "percentage": round(deepseek_cost / total * 100, 1) if total > 0 else 0,
                },
                "outline_architecture": {
                    "model": "glm5",
                    "cost": 0.0,
                    "note": "Covered by Coding Plan",
                },
            },
            "total_variable_cost": round(total, 2),
            "estimated_savings": "¥" + str(round(standard_chapters * 0.039, 2)) + " vs using Kimi for all",
        }
