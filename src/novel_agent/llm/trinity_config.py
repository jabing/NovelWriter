# src/llm/trinity_config.py
"""Multi-Provider Model Configuration for NovelWriter.

Supported Providers:
- Zhipu AI Coding Plan: GLM-5, GLM-4.7 (free via Coding Plan)
- Bailian Coding Plan (Alibaba): Qwen3.5 Plus, Qwen3 Max, Qwen3 Coder, GLM, Kimi
- Infini AI: DeepSeek, MiniMax, GLM, Kimi
- Volcengine Ark: Doubao Seed 2.0 series, DeepSeek, MiniMax, GLM, Kimi
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelProvider:
    """Model provider configuration."""
    name: str
    provider_type: str
    api_key: str
    base_url: str | None = None
    models: dict[str, str] | None = None


# Provider configurations
USER_PROVIDERS = {
    "zhipuai-coding-plan": ModelProvider(
        name="Zhipu AI Coding Plan",
        provider_type="zhipu",
        api_key="7a0c4a13c22d48cda9d648aa82527485.UCIs1spSr9rgh7QR",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        models={
            "glm-5": "GLM-5",
            "glm-4.7": "GLM 4.7",
        }
    ),
    "bailian-coding-plan": ModelProvider(
        name="Alibaba Cloud Bailian (Anthropic Format)",
        provider_type="bailian",
        api_key="sk-sp-fa4102caa5da4638af04b7618682f6dc",
        base_url="https://coding.dashscope.aliyuncs.com/apps/anthropic/v1",
        models={
            "qwen3.5-plus": "Qwen3.5 Plus",
            "qwen3-max-2026-01-23": "Qwen3 Max 2026-01-23",
            "qwen3-coder-next": "Qwen3 Coder Next",
            "qwen3-coder-plus": "Qwen3 Coder Plus",
            "glm-5": "GLM-5",
            "glm-4.7": "GLM 4.7",
            "kimi-k2.5": "Kimi K2.5",
        }
    ),
    "infini": ModelProvider(
        name="Infini AI (OpenAI Compatible)",
        provider_type="infini",
        api_key="sk-cp-5bfck6tiavjuqv2b",
        base_url="https://cloud.infini-ai.com/maas/coding/v1",
        models={
            "deepseek-v3.2": "DeepSeek V3.2",
            "deepseek-v3.2-thinking": "DeepSeek V3.2 Thinking",
            "minimax-m2.1": "MiniMax M2.1",
            "minimax-m2.5": "MiniMax M2.5",
            "glm-4.7": "GLM 4.7",
            "glm-5": "GLM-5",
            "kimi-k2.5": "Kimi K2.5",
        }
    ),
    "volcengine": ModelProvider(
        name="Volcengine Ark Coding",
        provider_type="volcengine",
        api_key="02c770c5-a6a3-48c8-aaa4-0369d451e18a",
        base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
        models={
            "doubao-seed-2.0-code": "Doubao Seed 2.0 Code",
            "doubao-seed-2.0-pro": "Doubao Seed 2.0 Pro",
            "doubao-seed-2.0-lite": "Doubao Seed 2.0 Lite",
            "doubao-seed-code": "Doubao Seed Code",
            "minimax-m2.5": "MiniMax M2.5",
            "kimi-k2.5": "Kimi K2.5",
            "glm-4.7": "GLM 4.7",
            "deepseek-v3.2": "DeepSeek V3.2",
        }
    ),
}


# Model capabilities and routing rules
TRINITY_MODELS = {
    # === ELITE MODELS (Best for critical content) ===
    "kimi-k2.5": {
        "name": "Kimi K2.5",
        "provider": "infini",
        "alternatives": ["bailian-coding-plan", "volcengine"],
        "strengths": ["emotion", "creativity", "golden_chapters", "chinese_culture", "reasoning"],
        "cost_per_1k_tokens": 0.015,
        "context_window": 256000,
        "max_output": 32768,
        "temperature_recommended": 1.0,
        "use_for": ["golden_1", "golden_2", "golden_3", "climax", "emotional_peaks", "finale"],
        "quality_tier": "elite",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },
    "qwen3-max-2026-01-23": {
        "name": "Qwen3 Max 2026-01-23",
        "provider": "bailian-coding-plan",
        "strengths": ["reasoning", "creativity", "chinese", "multimodal"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 262144,
        "max_output": 32768,
        "temperature_recommended": 0.7,
        "use_for": ["golden_chapters", "climax", "complex_plot"],
        "quality_tier": "elite",
    },
    "doubao-seed-2.0-pro": {
        "name": "Doubao Seed 2.0 Pro",
        "provider": "volcengine",
        "strengths": ["reasoning", "coding", "chinese"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 128000,
        "temperature_recommended": 0.7,
        "use_for": ["golden_chapters", "plot_planning", "logic_checking"],
        "quality_tier": "elite",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },

    # === REASONING MODELS (Deep thinking) ===
    "deepseek-v3.2-thinking": {
        "name": "DeepSeek V3.2 Thinking",
        "provider": "infini",
        "strengths": ["reasoning", "logic", "plot_consistency", "problem_solving"],
        "cost_per_1k_tokens": 0.004,
        "context_window": 128000,
        "max_output": 8192,
        "temperature_recommended": 0.7,
        "use_for": ["plot_planning", "mystery", "logic_checking", "revision"],
        "quality_tier": "reasoning",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },
    "qwen3.5-plus": {
        "name": "Qwen3.5 Plus",
        "provider": "bailian-coding-plan",
        "strengths": ["reasoning", "multimodal", "long_context"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 1000000,
        "max_output": 65536,
        "temperature_recommended": 0.7,
        "use_for": ["plot_planning", "complex_analysis", "long_narrative"],
        "quality_tier": "reasoning",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },
    "doubao-seed-2.0-code": {
        "name": "Doubao Seed 2.0 Code",
        "provider": "volcengine",
        "strengths": ["coding", "reasoning", "system_design"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 128000,
        "temperature_recommended": 0.7,
        "use_for": ["system_novels", "coding_tasks", "plot_logic"],
        "quality_tier": "reasoning",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },

    # === STANDARD MODELS (Daily content) ===
    "deepseek-v3.2": {
        "name": "DeepSeek V3.2",
        "provider": "infini",
        "alternatives": ["volcengine"],
        "strengths": ["cost_efficiency", "consistency", "volume", "chinese"],
        "cost_per_1k_tokens": 0.002,
        "context_window": 128000,
        "max_output": 8192,
        "temperature_recommended": 0.8,
        "use_for": ["daily_chapters", "transition", "bulk_generation"],
        "quality_tier": "standard",
    },
    "qwen3-coder-next": {
        "name": "Qwen3 Coder Next",
        "provider": "bailian-coding-plan",
        "strengths": ["coding", "system_design", "chinese"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 262144,
        "max_output": 65536,
        "temperature_recommended": 0.7,
        "use_for": ["system_novels", "technical_content"],
        "quality_tier": "standard",
    },
    "qwen3-coder-plus": {
        "name": "Qwen3 Coder Plus",
        "provider": "bailian-coding-plan",
        "strengths": ["coding", "volume", "chinese"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 1000000,
        "max_output": 65536,
        "temperature_recommended": 0.8,
        "use_for": ["daily_chapters", "system_novels"],
        "quality_tier": "standard",
    },
    "doubao-seed-code": {
        "name": "Doubao Seed Code",
        "provider": "volcengine",
        "strengths": ["coding", "chinese", "cost_efficiency"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 128000,
        "temperature_recommended": 0.7,
        "use_for": ["system_novels", "coding_content"],
        "quality_tier": "standard",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },

    # === BUDGET MODELS (High volume) ===
    "minimax-m2.1": {
        "name": "MiniMax M2.1",
        "provider": "infini",
        "strengths": ["speed", "cost_efficiency", "multimodal"],
        "cost_per_1k_tokens": 0.001,
        "context_window": 256000,
        "max_output": 8192,
        "temperature_recommended": 0.7,
        "use_for": ["filler", "rough_drafts", "volume_content"],
        "quality_tier": "budget",
    },
    "minimax-m2.5": {
        "name": "MiniMax M2.5",
        "provider": "infini",
        "alternatives": ["volcengine"],
        "strengths": ["ultra_long_context", "cost_efficiency"],
        "cost_per_1k_tokens": 0.0015,
        "context_window": 256000,
        "max_output": 8192,
        "temperature_recommended": 0.7,
        "use_for": ["filler", "volume_content", "long_chapters"],
        "quality_tier": "budget",
    },
    "doubao-seed-2.0-lite": {
        "name": "Doubao Seed 2.0 Lite",
        "provider": "volcengine",
        "strengths": ["speed", "cost_efficiency"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 128000,
        "temperature_recommended": 0.8,
        "use_for": ["filler", "rough_drafts"],
        "quality_tier": "budget",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },

    # === UTILITY MODELS (Free via Coding Plan) ===
    "glm-5": {
        "name": "GLM-5",
        "provider": "zhipuai-coding-plan",
        "alternatives": ["infini", "bailian-coding-plan"],
        "strengths": ["coding", "architecture", "worldbuilding", "system_design"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 200000,
        "max_output": 32768,
        "temperature_recommended": 0.6,
        "use_for": ["outline", "worldbuilding", "system_flow", "coding_tasks"],
        "quality_tier": "utility",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },
    "glm-4.7": {
        "name": "GLM 4.7",
        "provider": "zhipuai-coding-plan",
        "alternatives": ["infini", "bailian-coding-plan", "volcengine"],
        "strengths": ["balanced", "multimodal"],
        "cost_per_1k_tokens": 0.0,
        "context_window": 128000,
        "max_output": 8192,
        "temperature_recommended": 0.7,
        "use_for": ["standard_content", "transition", "worldbuilding"],
        "quality_tier": "utility",
        "budget_tokens": 8192,
        "supports_thinking": True,
    },
}


# Chapter type to model mapping
CHAPTER_ROUTING = {
    1: {"model": "kimi-k2.5", "reason": "Golden Chapter 1 - Reader retention critical"},
    2: {"model": "kimi-k2.5", "reason": "Golden Chapter 2 - Continue building investment"},
    3: {"model": "kimi-k2.5", "reason": "Golden Chapter 3 - Commit reader to journey"},
    "volume_start": {"model": "kimi-k2.5", "reason": "Volume start - New arc hook"},
    "climax": {"model": "kimi-k2.5", "reason": "Story climax - Peak quality required"},
    "finale": {"model": "kimi-k2.5", "reason": "Story finale - Satisfying conclusion"},
    "emotional_peak": {"model": "kimi-k2.5", "reason": "Emotional peak - High nuance needed"},
    "standard": {"model": "deepseek-v3.2", "reason": "Standard chapter - Cost effective"},
    "outline": {"model": "glm-5", "reason": "Outline/Architecture - GLM-5 (no extra cost)"},
    "system_design": {"model": "qwen3-coder-next", "reason": "System novel - Coder optimized"},
}


# Genre-specific optimizations
GENRE_CONFIG = {
    "romance": {
        "elite_model": "kimi-k2.5",
        "standard_model": "deepseek-v3.2",
        "emotional_chapters": "kimi-k2.5",
        "logic_chapters": "deepseek-v3.2",
        "outline": "glm-5",
    },
    "fantasy": {
        "elite_model": "kimi-k2.5",
        "standard_model": "deepseek-v3.2",
        "worldbuilding": "glm-5",
        "magic_system": "glm-5",
        "outline": "glm-5",
    },
    "scifi": {
        "elite_model": "qwen3.5-plus",
        "standard_model": "deepseek-v3.2",
        "technical": "deepseek-v3.2-thinking",
        "worldbuilding": "glm-5",
        "outline": "glm-5",
    },
    "system": {
        "elite_model": "qwen3-coder-next",
        "standard_model": "qwen3-coder-plus",
        "coding": "doubao-seed-2.0-code",
        "outline": "glm-5",
    },
    "mystery": {
        "elite_model": "deepseek-v3.2-thinking",
        "standard_model": "deepseek-v3.2",
        "plot_check": "deepseek-v3.2-thinking",
        "outline": "glm-5",
    },
    "history": {
        "elite_model": "kimi-k2.5",
        "standard_model": "deepseek-v3.2",
        "outline": "glm-5",
    },
    "military": {
        "elite_model": "doubao-seed-2.0-pro",
        "standard_model": "deepseek-v3.2",
        "outline": "glm-5",
    },
}


def get_provider_config(provider_name: str) -> ModelProvider | None:
    """Get provider configuration."""
    return USER_PROVIDERS.get(provider_name)


def get_model_config(model_name: str) -> dict[str, Any] | None:
    """Get model configuration."""
    return TRINITY_MODELS.get(model_name)


def get_all_models_by_tier(tier: str) -> list[str]:
    """Get all models for a specific quality tier."""
    return [
        model_id for model_id, config in TRINITY_MODELS.items()
        if config.get("quality_tier") == tier
    ]


def get_models_with_thinking() -> list[str]:
    """Get all models that support thinking mode."""
    return [
        model_id for model_id, config in TRINITY_MODELS.items()
        if config.get("supports_thinking")
    ]


def estimate_cost(chapter_count: int, genre: str = "fantasy") -> dict[str, Any]:
    """Estimate cost for a novel using user's configuration.

    Assumes:
    - 3 golden chapters (Kimi)
    - 10% elite chapters (Kimi)
    - 10% reasoning chapters (DeepSeek V3.2 Thinking for mystery/scifi)
    - 77% standard chapters (DeepSeek V3.2)
    - Outline/Architecture (GLM-5, free)
    """
    golden = 3
    elite = max(1, int(chapter_count * 0.1))
    reasoning = max(1, int(chapter_count * 0.1)) if genre in ["scifi", "mystery", "system"] else 0
    standard = chapter_count - golden - elite - reasoning

    tokens_per_chapter = 3000

    kimi_cost = (golden + elite) * tokens_per_chapter * 0.015 / 1000
    thinking_cost = reasoning * tokens_per_chapter * 0.004 / 1000
    v3_cost = standard * tokens_per_chapter * 0.002 / 1000

    total = kimi_cost + thinking_cost + v3_cost

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
                "model": "deepseek-v3.2-thinking",
                "cost": round(thinking_cost, 2),
            },
            "standard": {
                "chapters": standard,
                "model": "deepseek-v3.2",
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
    estimate = estimate_cost(100, "fantasy")
    print(f"100 章奇幻小说预估成本：¥{estimate['total_variable_cost']}")
    print(f"平均每章成本：¥{estimate['cost_per_chapter_avg']}")
    print(f"相比全用 Kimi 节省：¥{estimate['savings_vs_all_kimi']}")
    print()
    print(f"Elite models: {get_all_models_by_tier('elite')}")
    print(f"Thinking models: {get_models_with_thinking()}")
