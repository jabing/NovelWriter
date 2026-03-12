# src/llm/trinity_config.py
"""Trinity Model Configuration - Adapts to user's actual setup.

User Configuration:
- GLM-5: Zhipu AI Coding Plan (fixed cost)
- DeepSeek: Via Infini AI OpenAI-compatible API
- Kimi 2.5: Via Infini AI OpenAI-compatible API
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelProvider:
    """Model provider configuration."""
    name: str
    provider_type: str  # "zhipu", "infini"
    api_key: str
    base_url: str | None = None
    models: dict[str, str] | None = None


# User's actual configuration
USER_PROVIDERS = {
    "zhipuai-coding-plan": ModelProvider(
        name="Zhipu AI Coding Plan",
        provider_type="zhipu",
        api_key="7a0c4a13c22d48cda9d648aa82527485.UCIs1spSr9rgh7QR",
        base_url="https://open.bigmodel.cn/api/paas/v4",  # Zhipu official
        models={
            "glm-5": "GLM-5",
            "glm-4-plus": "GLM-4 Plus",
            "glm-4": "GLM-4",
        }
    ),
    "infini-openai": ModelProvider(
        name="Infini AI (OpenAI Compatible)",
        provider_type="infini",
        api_key="sk-cp-5bfck6tiavjuqv2b",
        base_url="https://cloud.infini-ai.com/maas/coding/v1",
        models={
            "deepseek-v3": "DeepSeek V3",
            "deepseek-r1": "DeepSeek R1",
            "kimi-k2.5": "Kimi K2.5",
            "kimi-k2-thinking": "Kimi K2 Thinking",
        }
    ),
}


# Model capabilities and routing rules
TRINITY_MODELS = {
    "kimi-k2.5": {
        "name": "Kimi K2.5",
        "provider": "infini-openai",
        "strengths": ["emotion", "creativity", "golden_chapters", "chinese_culture"],
        "cost_per_1k_tokens": 0.015,  # Infini AI pricing
        "context_window": 256000,
        "temperature_recommended": 0.7,
        "use_for": ["golden_1", "golden_2", "golden_3", "climax", "emotional_peaks", "finale"],
        "quality_tier": "elite",
    },
    "deepseek-v3": {
        "name": "DeepSeek V3",
        "provider": "infini-openai",
        "strengths": ["cost_efficiency", "consistency", "volume", "chinese"],
        "cost_per_1k_tokens": 0.002,  # Infini AI pricing
        "context_window": 1000000,  # 1M
        "temperature_recommended": 0.8,
        "use_for": ["daily_chapters", "transition", "bulk_generation"],
        "quality_tier": "standard",
    },
    "deepseek-r1": {
        "name": "DeepSeek R1 (Reasoning)",
        "provider": "infini-openai",
        "strengths": ["reasoning", "logic", "plot_consistency", "problem_solving"],
        "cost_per_1k_tokens": 0.004,  # Higher than V3
        "context_window": 64000,
        "temperature_recommended": 0.6,  # Lower for reasoning
        "use_for": ["plot_planning", "mystery", "logic_checking", "revision"],
        "quality_tier": "reasoning",
    },
    "glm-5": {
        "name": "GLM-5",
        "provider": "zhipuai-coding-plan",
        "strengths": ["coding", "architecture", "worldbuilding", "system_design"],
        "cost_per_1k_tokens": 0.0,  # FIXED by Coding Plan!
        "context_window": 200000,
        "temperature_recommended": 0.6,
        "use_for": ["outline", "worldbuilding", "system_flow", "coding_tasks"],
        "quality_tier": "utility",
        "note": "Already paid via Coding Plan - use freely!",
    },
    "kimi-k2-thinking": {
        "name": "Kimi K2 Thinking",
        "provider": "infini-openai",
        "strengths": ["deep_reasoning", "analysis", "planning"],
        "cost_per_1k_tokens": 0.015,  # Same as K2.5
        "context_window": 256000,
        "temperature_recommended": 0.6,
        "use_for": ["complex_analysis", "story_structure_review"],
        "quality_tier": "reasoning",
    },
}


# Chapter type to model mapping
CHAPTER_ROUTING = {
    # Golden chapters - always use best
    1: {"model": "kimi-k2.5", "reason": "Golden Chapter 1 - Reader retention critical"},
    2: {"model": "kimi-k2.5", "reason": "Golden Chapter 2 - Continue building investment"},
    3: {"model": "kimi-k2.5", "reason": "Golden Chapter 3 - Commit reader to journey"},

    # Special markers
    "volume_start": {"model": "kimi-k2.5", "reason": "Volume start - New arc hook"},
    "climax": {"model": "kimi-k2.5", "reason": "Story climax - Peak quality required"},
    "finale": {"model": "kimi-k2.5", "reason": "Story finale - Satisfying conclusion"},
    "emotional_peak": {"model": "kimi-k2.5", "reason": "Emotional peak - High nuance needed"},

    # Default
    "standard": {"model": "deepseek-v3", "reason": "Standard chapter - Cost effective"},
    "outline": {"model": "glm-5", "reason": "Outline/Architecture - GLM-5 (no extra cost)"},
}


# Genre-specific optimizations
GENRE_CONFIG = {
    "romance": {
        "elite_model": "kimi-k2.5",
        "standard_model": "deepseek-v3",
        "emotional_chapters": "kimi-k2.5",  # More Kimi for romance
        "logic_chapters": "deepseek-v3",
        "outline": "glm-5",
    },
    "fantasy": {
        "elite_model": "kimi-k2.5",
        "standard_model": "deepseek-v3",
        "worldbuilding": "glm-5",  # GLM for complex worldbuilding
        "magic_system": "glm-5",
        "outline": "glm-5",
    },
    "scifi": {
        "elite_model": "kimi-k2.5",  # Or "deepseek-r1" for hard sci-fi
        "standard_model": "deepseek-v3",
        "technical": "deepseek-r1",  # R1 for technical accuracy
        "worldbuilding": "glm-5",
        "outline": "glm-5",
    },
    "system": {
        "elite_model": "deepseek-r1",
        "standard_model": "deepseek-v3",
        "coding": "glm-5",  # GLM for system design
        "outline": "glm-5",
    },
    "mystery": {
        "elite_model": "deepseek-r1",  # R1 for plot logic
        "standard_model": "deepseek-v3",
        "plot_check": "deepseek-r1",
        "outline": "glm-5",
    },
}


def get_provider_config(provider_name: str) -> ModelProvider:
    """Get provider configuration."""
    return USER_PROVIDERS.get(provider_name)


def get_model_config(model_name: str) -> dict[str, Any]:
    """Get model configuration."""
    return TRINITY_MODELS.get(model_name)


def estimate_cost(chapter_count: int, genre: str = "fantasy") -> dict[str, Any]:
    """Estimate cost for a novel using user's configuration.

    Assumes:
    - 3 golden chapters (Kimi)
    - 10% elite chapters (Kimi)
    - 10% reasoning chapters (R1 for mystery/scifi)
    - 77% standard chapters (DeepSeek V3)
    - Outline/Architecture (GLM-5, free)
    """
    golden = 3
    elite = max(1, int(chapter_count * 0.1))
    reasoning = max(1, int(chapter_count * 0.1)) if genre in ["scifi", "mystery", "system"] else 0
    standard = chapter_count - golden - elite - reasoning

    # Calculate costs (3000 tokens per chapter average)
    tokens_per_chapter = 3000

    kimi_cost = (golden + elite) * tokens_per_chapter * 0.015 / 1000
    r1_cost = reasoning * tokens_per_chapter * 0.004 / 1000
    v3_cost = standard * tokens_per_chapter * 0.002 / 1000

    total = kimi_cost + r1_cost + v3_cost

    return {
        "total_chapters": chapter_count,
        "genre": genre,
        "breakdown": {
            "golden_elite": {
                "chapters": golden + elite,
                "model": "kimi-k2.5",
                "cost": round(kimi_cost, 2),
            },
            "reasoning": {
                "chapters": reasoning,
                "model": "deepseek-r1",
                "cost": round(r1_cost, 2),
            },
            "standard": {
                "chapters": standard,
                "model": "deepseek-v3",
                "cost": round(v3_cost, 2),
            },
            "outline_architecture": {
                "chapters": "N/A",
                "model": "glm-5",
                "cost": 0.0,
                "note": "Covered by Coding Plan",
            },
        },
        "total_variable_cost": round(total, 2),
        "cost_per_chapter_avg": round(total / chapter_count, 3),
        "savings_vs_all_kimi": round((chapter_count * tokens_per_chapter * 0.015 / 1000) - total, 2),
    }


# Example usage
if __name__ == "__main__":
    # Estimate 100 chapter fantasy novel
    estimate = estimate_cost(100, "fantasy")
    print(f"100章奇幻小说预估成本: ¥{estimate['total_variable_cost']}")
    print(f"平均每章成本: ¥{estimate['cost_per_chapter_avg']}")
    print(f"相比全用Kimi节省: ¥{estimate['savings_vs_all_kimi']}")
