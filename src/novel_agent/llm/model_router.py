# src/llm/model_router.py
"""Intelligent Model Router - Selects optimal LLM based on content type and quality requirements."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.llm.deepseek import DeepSeekLLM


class ContentTier(Enum):
    """Content quality tiers."""
    ELITE = "elite"           # Top 5% content - highest quality
    STANDARD = "standard"     # Main content - good quality
    MASS_PROD = "mass_prod"   # Bulk content - acceptable quality


class ChapterType(Enum):
    """Types of web novel chapters."""
    GOLDEN_1 = "golden_1"           # Chapter 1 (most critical)
    GOLDEN_2 = "golden_2"           # Chapter 2
    GOLDEN_3 = "golden_3"           # Chapter 3
    VOLUME_START = "volume_start"   # First chapter of volume/act
    CLIMAX = "climax"               # Story climax
    EMOTIONAL_PEAK = "emotional_peak"  # Emotional high point
    TRANSITION = "transition"       # Bridge chapters
    FILLER = "filler"               # Filler content
    FINALE = "finale"               # Final chapter


class NovelGenre(Enum):
    """Web novel genres with different requirements."""
    ROMANCE = "romance"             # High emotional requirement
    FANTASY = "fantasy"             # High worldbuilding requirement
    SCIFI = "scifi"                 # High logic/consistency requirement
    HISTORY = "history"             # High accuracy requirement
    MILITARY = "military"           # High action/detail requirement
    URBAN = "urban"                 # Medium overall
    SYSTEM = "system"               # High logic/programming requirement


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


class ModelRouter:
    """Intelligent router for selecting LLM based on content requirements.

    Routes content to appropriate model based on:
    - Chapter type (golden chapters get best model)
    - Genre requirements (romance needs emotion, scifi needs logic)
    - Quality requirements (climax vs filler)
    - Cost constraints
    """

    # Model configurations
    MODELS = {
        "kimi_k2.5": {
            "name": "Kimi K2.5",
            "provider": "moonshot",
            "strengths": ["emotion", "creativity", "multimodal", "long_context"],
            "cost_per_1k_tokens": 0.015,  # ¥0.015
            "context_window": 256000,
            "temperature_range": (0.3, 0.9),
            "best_for": ["romance", "emotional_peaks", "golden_chapters"],
        },
        "glm5": {
            "name": "GLM-5",
            "provider": "zhipu",
            "strengths": ["logic", "coding", "agent", "reasoning"],
            "cost_per_1k_tokens": 0.012,
            "context_window": 200000,
            "temperature_range": (0.2, 0.8),
            "best_for": ["scifi", "system", "architecture", "plotting"],
        },
        "deepseek_v3": {
            "name": "DeepSeek V3",
            "provider": "deepseek",
            "strengths": ["chinese", "cost_efficiency", "long_context"],
            "cost_per_1k_tokens": 0.002,
            "context_window": 1000000,  # 1M
            "temperature_range": (0.3, 0.9),
            "best_for": ["daily_chapters", "bulk_generation", "standard_content"],
        },
        "minimax_m2.5": {
            "name": "MiniMax M2.5",
            "provider": "minimax",
            "strengths": ["speed", "ultra_long_context", "cost_efficiency"],
            "cost_per_1k_tokens": 0.0015,
            "context_window": 1000000,  # 1M
            "temperature_range": (0.3, 0.8),
            "best_for": ["filler", "rough_drafts", "volume_content"],
        },
    }

    # Chapter type priority mapping
    CHAPTER_PRIORITY = {
        ChapterType.GOLDEN_1: {"tier": ContentTier.ELITE, "weight": 10},
        ChapterType.GOLDEN_2: {"tier": ContentTier.ELITE, "weight": 9},
        ChapterType.GOLDEN_3: {"tier": ContentTier.ELITE, "weight": 9},
        ChapterType.VOLUME_START: {"tier": ContentTier.ELITE, "weight": 8},
        ChapterType.CLIMAX: {"tier": ContentTier.ELITE, "weight": 10},
        ChapterType.EMOTIONAL_PEAK: {"tier": ContentTier.ELITE, "weight": 9},
        ChapterType.FINALE: {"tier": ContentTier.ELITE, "weight": 10},
        ChapterType.TRANSITION: {"tier": ContentTier.STANDARD, "weight": 5},
        ChapterType.FILLER: {"tier": ContentTier.MASS_PROD, "weight": 2},
    }

    # Genre model preferences
    GENRE_PREFERENCES = {
        NovelGenre.ROMANCE: {
            "elite": "kimi_k2.5",
            "standard": "deepseek_v3",
            "mass_prod": "deepseek_v3",
            "reason": "Romance requires high emotional nuance",
        },
        NovelGenre.FANTASY: {
            "elite": "glm5",  # Worldbuilding logic
            "standard": "deepseek_v3",
            "mass_prod": "minimax_m2.5",
            "reason": "Fantasy needs strong worldbuilding logic",
        },
        NovelGenre.SCIFI: {
            "elite": "glm5",  # Logic + consistency
            "standard": "glm5",
            "mass_prod": "deepseek_v3",
            "reason": "Sci-fi requires scientific consistency",
        },
        NovelGenre.HISTORY: {
            "elite": "kimi_k2.5",  # Detail accuracy
            "standard": "deepseek_v3",
            "mass_prod": "minimax_m2.5",
            "reason": "Historical accuracy + cultural nuance",
        },
        NovelGenre.MILITARY: {
            "elite": "glm5",  # Tactical accuracy
            "standard": "deepseek_v3",
            "mass_prod": "minimax_m2.5",
            "reason": "Military needs tactical logic",
        },
        NovelGenre.SYSTEM: {
            "elite": "glm5",  # Programming ability
            "standard": "glm5",
            "mass_prod": "deepseek_v3",
            "reason": "System novels require coding logic",
        },
        NovelGenre.URBAN: {
            "elite": "kimi_k2.5",
            "standard": "deepseek_v3",
            "mass_prod": "minimax_m2.5",
            "reason": "Urban fiction needs relatability",
        },
    }

    def __init__(self, budget_mode: str = "balanced"):
        """Initialize router.

        Args:
            budget_mode: "quality", "balanced", or "economy"
        """
        self.budget_mode = budget_mode
        self.usage_stats = {
            model: {"tokens": 0, "cost": 0.0, "calls": 0}
            for model in self.MODELS.keys()
        }

    def route(
        self,
        chapter_number: int,
        total_chapters: int,
        genre: str,
        chapter_type: ChapterType | None = None,
        content_description: str = "",
        quality_requirement: str = "standard",
    ) -> RoutingDecision:
        """Route content to appropriate model.

        Args:
            chapter_number: Current chapter number
            total_chapters: Total chapters in novel
            genre: Novel genre
            chapter_type: Specific chapter type (optional)
            content_description: Brief description of content
            quality_requirement: "high", "standard", or "low"

        Returns:
            RoutingDecision with model selection
        """
        # Detect chapter type if not provided
        if chapter_type is None:
            chapter_type = self._detect_chapter_type(
                chapter_number, total_chapters, content_description
            )

        # Get tier based on chapter type
        tier_info = self.CHAPTER_PRIORITY.get(
            chapter_type, {"tier": ContentTier.STANDARD, "weight": 5}
        )
        tier = tier_info["tier"]

        # Adjust tier based on budget mode
        tier = self._adjust_tier_for_budget(tier)

        # Get genre preference
        genre_enum = NovelGenre(genre.lower()) if genre.lower() in [
            g.value for g in NovelGenre
        ] else NovelGenre.URBAN

        preference = self.GENRE_PREFERENCES.get(genre_enum, self.GENRE_PREFERENCES[NovelGenre.URBAN])

        # Select models based on tier and genre
        if tier == ContentTier.ELITE:
            primary = preference["elite"]
            fallback = "kimi_k2.5" if primary != "kimi_k2.5" else "glm5"
            temperature = 0.7
            reasoning = f"ELITE tier: {preference['reason']}. Using best model for maximum quality."

        elif tier == ContentTier.STANDARD:
            primary = preference["standard"]
            fallback = "deepseek_v3" if primary != "deepseek_v3" else "glm5"
            temperature = 0.8
            reasoning = "STANDARD tier: Good quality with cost efficiency."

        else:  # MASS_PROD
            primary = preference["mass_prod"]
            fallback = "deepseek_v3"
            temperature = 0.8
            reasoning = "MASS_PROD tier: Cost-optimized for volume generation."

        # Special case: Architecture/outline always uses GLM-5
        if "outline" in content_description.lower() or "architecture" in content_description.lower():
            primary = "glm5"
            reasoning = "Architecture work requires strong logic and planning capabilities."

        # Special case: Emotional content always uses Kimi
        if any(word in content_description.lower() for word in ["romance", "love", "emotional", "kiss", "confession"]):
            if tier == ContentTier.ELITE:
                primary = "kimi_k2.5"
                reasoning = "Emotional content requires highest emotional intelligence."

        # Calculate estimated cost
        estimated_tokens = 3000  # Average chapter
        cost_per_1k = self.MODELS[primary]["cost_per_1k_tokens"]
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k

        return RoutingDecision(
            primary_model=primary,
            fallback_model=fallback,
            tier=tier,
            temperature=temperature,
            max_tokens=4000,
            reasoning=reasoning,
            estimated_cost=estimated_cost,
        )

    def _detect_chapter_type(
        self, chapter_number: int, total_chapters: int, description: str
    ) -> ChapterType:
        """Automatically detect chapter type."""
        # Golden chapters
        if chapter_number == 1:
            return ChapterType.GOLDEN_1
        elif chapter_number == 2:
            return ChapterType.GOLDEN_2
        elif chapter_number == 3:
            return ChapterType.GOLDEN_3

        # Volume starts (every 50 chapters approx)
        if chapter_number % 50 == 1 and chapter_number > 3:
            return ChapterType.VOLUME_START

        # Climax (85-95% through)
        if total_chapters > 0:
            progress = chapter_number / total_chapters
            if 0.85 <= progress <= 0.95:
                return ChapterType.CLIMAX
            if progress > 0.95:
                return ChapterType.FINALE

        # Check description for emotional content
        if any(word in description.lower() for word in ["climax", "peak", "emotional", "revelation"]):
            return ChapterType.EMOTIONAL_PEAK

        if any(word in description.lower() for word in ["filler", "side story", "extra"]):
            return ChapterType.FILLER

        if any(word in description.lower() for word in ["transition", "bridge", "setup"]):
            return ChapterType.TRANSITION

        return ChapterType.TRANSITION

    def _adjust_tier_for_budget(self, tier: ContentTier) -> ContentTier:
        """Adjust tier based on budget mode."""
        if self.budget_mode == "quality":
            # Always use best possible
            return ContentTier.ELITE if tier in [ContentTier.ELITE, ContentTier.STANDARD] else tier
        elif self.budget_mode == "economy":
            # Downgrade where possible
            if tier == ContentTier.STANDARD:
                return ContentTier.MASS_PROD
            elif tier == ContentTier.ELITE:
                return ContentTier.STANDARD
        # balanced: keep as is
        return tier

    def get_model_instance(self, model_key: str, api_keys: dict[str, str]) -> BaseLLM:
        """Get LLM instance for selected model.

        Args:
            model_key: Key from MODELS dict
            api_keys: Dict of API keys for different providers

        Returns:
            BaseLLM instance
        """
        model_config = self.MODELS.get(model_key)
        if not model_config:
            raise ValueError(f"Unknown model: {model_key}")

        provider = model_config["provider"]
        api_key = api_keys.get(provider)

        if not api_key:
            raise ValueError(f"No API key for provider: {provider}")

        # Create appropriate LLM instance
        if provider == "deepseek":
            return DeepSeekLLM(api_key=api_key)
        elif provider == "moonshot":
            # Would need to implement KimiLLM
            from src.novel_agent.llm.kimi import KimiLLM
            return KimiLLM(api_key=api_key)
        elif provider == "zhipu":
            from src.novel_agent.llm.glm import GLMLLM
            return GLMLLM(api_key=api_key)
        elif provider == "minimax":
            from src.novel_agent.llm.minimax import MiniMaxLLM
            return MiniMaxLLM(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def get_usage_report(self) -> dict[str, Any]:
        """Get usage statistics report."""
        total_cost = sum(stats["cost"] for stats in self.usage_stats.values())
        total_tokens = sum(stats["tokens"] for stats in self.usage_stats.values())

        return {
            "total_cost": round(total_cost, 2),
            "total_tokens": total_tokens,
            "model_breakdown": {
                model: {
                    "cost": round(stats["cost"], 2),
                    "tokens": stats["tokens"],
                    "calls": stats["calls"],
                    "percentage": round(stats["cost"] / total_cost * 100, 1) if total_cost > 0 else 0,
                }
                for model, stats in self.usage_stats.items()
            },
            "budget_mode": self.budget_mode,
        }

    def recommend_strategy(self, genre: str, total_chapters: int, budget: float) -> dict[str, Any]:
        """Recommend model strategy based on constraints."""
        genre_enum = NovelGenre(genre.lower()) if genre.lower() in [
            g.value for g in NovelGenre
        ] else NovelGenre.URBAN

        # Calculate costs for different strategies
        strategies = {
            "premium": {
                "description": "Maximum quality - Kimi K2.5 for everything",
                "model_mix": {"kimi_k2.5": 100},
                "avg_cost_per_chapter": 0.045,  # 3000 tokens * 0.015
                "total_cost": total_chapters * 0.045,
            },
            "hybrid_elite": {
                "description": "Elite hybrid - Kimi+GLM5 for golden, DeepSeek for rest",
                "model_mix": {"kimi_k2.5": 10, "glm5": 10, "deepseek_v3": 80},
                "avg_cost_per_chapter": 0.015,
                "total_cost": total_chapters * 0.015,
            },
            "balanced": {
                "description": "Balanced - DeepSeek main, Kimi for golden only",
                "model_mix": {"kimi_k2.5": 5, "deepseek_v3": 95},
                "avg_cost_per_chapter": 0.003,
                "total_cost": total_chapters * 0.003,
            },
            "economy": {
                "description": "Economy - MiniMax bulk, DeepSeek standard",
                "model_mix": {"deepseek_v3": 70, "minimax_m2.5": 30},
                "avg_cost_per_chapter": 0.002,
                "total_cost": total_chapters * 0.002,
            },
        }

        # Filter strategies by budget
        affordable = {
            name: strat for name, strat in strategies.items()
            if strat["total_cost"] <= budget
        }

        # Recommend best quality within budget
        if affordable:
            best = min(affordable.values(), key=lambda x: x["total_cost"])
            recommended = next(k for k, v in strategies.items() if v == best)
        else:
            recommended = "economy"

        return {
            "genre": genre_enum.value,
            "total_chapters": total_chapters,
            "budget": budget,
            "recommended_strategy": recommended,
            "strategy_details": strategies[recommended],
            "all_strategies": strategies,
            "affordable_strategies": list(affordable.keys()),
        }
