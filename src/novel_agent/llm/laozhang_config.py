# src/llm/laozhang_config.py
"""Laozhang.ai API Configuration - Third-party API for international models.

Supports major international LLMs through a unified OpenAI-compatible API.
Best for English web novel creation when premium quality is required.

API Base: https://api.laozhang.ai/v1
Docs: Supports all OpenAI-compatible endpoints
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class LaozhangModel:
    """Model configuration for Laozhang API."""
    id: str  # API model ID
    name: str  # Display name
    provider: str  # Original provider (openai, anthropic, google)
    strengths: list[str]
    cost_per_1k_tokens: float  # Estimated cost in USD
    context_window: int
    quality_tier: str  # "elite", "standard", "economy"
    best_for: list[str]


# Supported models (based on common third-party API offerings)
# Update this list based on actual /v1/models response
LAOZHANG_MODELS = {
    # OpenAI Models
    "gpt-4o": LaozhangModel(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        strengths=["creativity", "instruction_following", "versatility"],
        cost_per_1k_tokens=0.005,  # Input + Output avg
        context_window=128000,
        quality_tier="elite",
        best_for=["golden_chapters", "creative_writing", "dialogue"],
    ),
    "gpt-4o-mini": LaozhangModel(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        strengths=["cost_efficiency", "speed", "good_quality"],
        cost_per_1k_tokens=0.0006,
        context_window=128000,
        quality_tier="standard",
        best_for=["daily_chapters", "bulk_generation"],
    ),
    "gpt-5.2-chat-latest": LaozhangModel(
        id="gpt-5.2-chat-latest",
        name="GPT-5.2 (Latest)",
        provider="openai",
        strengths=["latest_features", "improved_reasoning", "creativity"],
        cost_per_1k_tokens=0.01,  # Premium pricing
        context_window=128000,
        quality_tier="elite",
        best_for=["premium_content", "complex_plots"],
    ),

    # Anthropic Models
    "claude-3-5-sonnet": LaozhangModel(
        id="claude-3-5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        strengths=["emotional_nuance", "literary_quality", "safety"],
        cost_per_1k_tokens=0.006,
        context_window=200000,
        quality_tier="elite",
        best_for=["romance", "literary_fiction", "emotional_peaks"],
    ),
    "claude-3-opus": LaozhangModel(
        id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        strengths=["highest_quality", "complex_reasoning", "creativity"],
        cost_per_1k_tokens=0.03,  # Most expensive
        context_window=200000,
        quality_tier="elite",
        best_for=["masterpiece", "award_worthy", "premium_publishing"],
    ),
    "claude-3-haiku": LaozhangModel(
        id="claude-3-haiku",
        name="Claude 3 Haiku",
        provider="anthropic",
        strengths=["speed", "cost_efficiency", "decent_quality"],
        cost_per_1k_tokens=0.0005,
        context_window=200000,
        quality_tier="economy",
        best_for=["rough_drafts", "brainstorming", "volume"],
    ),

    # Google Models
    "gemini-1-5-pro": LaozhangModel(
        id="gemini-1-5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        strengths=["long_context", "multimodal", "reasoning"],
        cost_per_1k_tokens=0.005,
        context_window=1000000,  # 1M tokens
        quality_tier="elite",
        best_for=["long_novels", "complex_worldbuilding"],
    ),
    "gemini-1-5-flash": LaozhangModel(
        id="gemini-1-5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        strengths=["speed", "long_context", "cost_efficient"],
        cost_per_1k_tokens=0.0007,
        context_window=1000000,
        quality_tier="standard",
        best_for=["daily_chapters", "long_form"],
    ),
}


# English novel creation recommendations
ENGLISH_NOVEL_STRATEGY = {
    "premium": {
        "description": "Best quality - Claude 3.5 Sonnet for everything",
        "models": {
            "golden_chapters": "claude-3-5-sonnet",
            "daily_chapters": "claude-3-5-sonnet",
            "outline": "claude-3-opus",  # Use Opus for critical planning
        },
        "cost_per_chapter": 0.018,  # ~3000 tokens
    },
    "balanced": {
        "description": "Balanced quality - Mix of Claude and GPT-4o",
        "models": {
            "golden_chapters": "claude-3-5-sonnet",  # Best for emotional content
            "daily_chapters": "gpt-4o",  # Fast and versatile
            "rough_drafts": "gpt-4o-mini",  # Cheap for initial drafts
            "outline": "claude-3-opus",
        },
        "cost_per_chapter": 0.008,
    },
    "economy": {
        "description": "Cost-effective - GPT-4o Mini + selective Claude",
        "models": {
            "golden_chapters": "claude-3-5-sonnet",  # Still use best for gold
            "daily_chapters": "gpt-4o-mini",
            "volume": "claude-3-haiku",
            "outline": "gpt-4o",
        },
        "cost_per_chapter": 0.002,
    },
}


def get_model_for_chapter(
    chapter_number: int,
    total_chapters: int,
    genre: str,
    strategy: str = "balanced"
) -> tuple[str, str]:
    """Get recommended model for a specific chapter.

    Returns:
        tuple: (model_id, reasoning)
    """
    strat = ENGLISH_NOVEL_STRATEGY.get(strategy, ENGLISH_NOVEL_STRATEGY["balanced"])
    models = strat["models"]

    # Determine chapter importance
    is_golden = chapter_number <= 3
    is_volume_start = chapter_number > 3 and chapter_number % 50 == 1
    progress = chapter_number / total_chapters if total_chapters > 0 else 0
    is_climax = 0.85 <= progress <= 0.95
    is_finale = progress > 0.95

    # Route to appropriate model
    if is_golden or is_climax or is_finale:
        model_key = models.get("golden_chapters", "claude-3-5-sonnet")
        reason = f"Chapter {chapter_number}: {'Golden' if is_golden else 'Climax' if is_climax else 'Finale'} - Premium quality"

    elif is_volume_start:
        model_key = models.get("golden_chapters", "claude-3-5-sonnet")
        reason = f"Chapter {chapter_number}: Volume start - Hook chapter"

    elif genre.lower() in ["romance", "literary"] and chapter_number % 10 == 0:
        # Emotional peaks in romance
        model_key = models.get("golden_chapters", "claude-3-5-sonnet")
        reason = f"Chapter {chapter_number}: Emotional peak in {genre}"

    elif chapter_number == 0 or "outline" in str(chapter_number).lower():
        # Outline/Planning
        model_key = models.get("outline", "claude-3-opus")
        reason = "Outline/Architecture - Critical planning phase"

    else:
        # Standard chapters
        model_key = models.get("daily_chapters", "gpt-4o")
        reason = f"Chapter {chapter_number}: Standard content"

    return model_key, reason


def estimate_english_cost(
    total_chapters: int,
    genre: str = "fantasy",
    strategy: str = "balanced",
    avg_tokens_per_chapter: int = 3000
) -> dict[str, Any]:
    """Estimate cost for English novel using Laozhang API.

    Args:
        total_chapters: Total number of chapters
        genre: Novel genre (affects model selection)
        strategy: "premium", "balanced", or "economy"
        avg_tokens_per_chapter: Average tokens per chapter

    Returns:
        Cost breakdown dict
    """
    strat = ENGLISH_NOVEL_STRATEGY.get(strategy, ENGLISH_NOVEL_STRATEGY["balanced"])

    # Count chapter types
    golden_count = 3 + max(1, int(total_chapters * 0.1))  # Golden + volume starts + climax

    if genre.lower() in ["romance", "literary"]:
        emotional_peaks = total_chapters // 10  # More emotional chapters
    else:
        emotional_peaks = total_chapters // 20

    elite_chapters = golden_count + emotional_peaks
    standard_chapters = total_chapters - elite_chapters

    # Get models
    models = strat["models"]
    elite_model_key = models.get("golden_chapters", "claude-3-5-sonnet")
    standard_model_key = models.get("daily_chapters", "gpt-4o")

    elite_model = LAOZHANG_MODELS.get(elite_model_key)
    standard_model = LAOZHANG_MODELS.get(standard_model_key)

    # Calculate costs in USD
    elite_cost = elite_chapters * (avg_tokens_per_chapter / 1000) * elite_model.cost_per_1k_tokens
    standard_cost = standard_chapters * (avg_tokens_per_chapter / 1000) * standard_model.cost_per_1k_tokens
    total_usd = elite_cost + standard_cost

    # Convert to RMB (approximate)
    total_rmb = total_usd * 7.2

    return {
        "strategy": strategy,
        "total_chapters": total_chapters,
        "genre": genre,
        "breakdown": {
            "elite_chapters": {
                "count": elite_chapters,
                "model": elite_model.name,
                "cost_usd": round(elite_cost, 2),
            },
            "standard_chapters": {
                "count": standard_chapters,
                "model": standard_model.name,
                "cost_usd": round(standard_cost, 2),
            },
        },
        "total_cost_usd": round(total_usd, 2),
        "total_cost_rmb": round(total_rmb, 2),
        "cost_per_chapter_usd": round(total_usd / total_chapters, 3),
        "comparison": {
            "vs_all_claude": f"Save {((total_chapters * 0.018 - total_usd) / (total_chapters * 0.018) * 100):.0f}%",
            "vs_all_gpt4": f"Save {((total_chapters * 0.015 - total_usd) / (total_chapters * 0.015) * 100):.0f}%",
        }
    }


# API Configuration
LAOZHANG_API_CONFIG = {
    "base_url": "https://api.laozhang.ai/v1",
    "api_key": "sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
    "supports_streaming": True,
    "supports_functions": True,
    "timeout": 120,
}


def create_client():
    """Create OpenAI-compatible client for Laozhang API."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("Install openai: pip install openai")

    return AsyncOpenAI(
        api_key=LAOZHANG_API_CONFIG["api_key"],
        base_url=LAOZHANG_API_CONFIG["base_url"],
        timeout=LAOZHANG_API_CONFIG["timeout"],
    )


# Example usage
if __name__ == "__main__":
    # Estimate costs
    for strategy in ["premium", "balanced", "economy"]:
        estimate = estimate_english_cost(100, "romance", strategy)
        print(f"\n{strategy.upper()} Strategy:")
        print(f"  Total: ${estimate['total_cost_usd']} (¥{estimate['total_cost_rmb']})")
        print(f"  Per chapter: ${estimate['cost_per_chapter_usd']}")
        print(f"  {estimate['comparison']['vs_all_claude']} vs all-Claude")
