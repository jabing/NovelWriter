# src/llm/final_model_config.py
"""Final Model Configuration - Clear separation of domestic and international APIs.

Architecture:
- Domestic Models (国内): Official APIs
  * DeepSeek: Official API (https://api.deepseek.com)
  * Kimi: Official Moonshot API (https://api.moonshot.cn)
  * GLM-5: Zhipu Coding Plan (https://open.bigmodel.cn)

- International Models (国外): Laozhang.ai Proxy
  * GPT-4o/5: via laozhang.ai
  * Claude 3.5/3.7/4: via laozhang.ai
  * Gemini: via laozhang.ai
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelEndpoint:
    """Complete endpoint configuration for a model."""
    name: str
    model_id: str  # API model identifier
    provider: str  # "deepseek", "moonshot", "zhipu", "laozhang"
    api_key: str
    base_url: str
    type: str  # "domestic" or "international"
    strengths: list[str]
    cost_per_1k_tokens: float  # in USD
    quality_tier: str  # "elite", "standard", "economy"


# ============================================
# DOMESTIC MODELS (国内模型 - Infini AI Proxy)
# ============================================
# Infini AI 提供 Kimi/DeepSeek 的代理访问
# BaseURL: https://cloud.infini-ai.com/maas/coding/v1
# API Key: sk-cp-5bfck6tiavjuqv2b

DOMESTIC_MODELS = {
    "kimi-k2.5": ModelEndpoint(
        name="Kimi K2.5",
        model_id="kimi-k2.5",
        provider="infini",
        api_key="sk-cp-5bfck6tiavjuqv2b",  # Infini AI Key
        base_url="https://cloud.infini-ai.com/maas/coding/v1",
        type="domestic",
        strengths=["emotion", "chinese_culture", "creativity", "long_context"],
        cost_per_1k_tokens=0.015,
        quality_tier="elite",
    ),

    "deepseek-v3": ModelEndpoint(
        name="Kimi K2.5 (via Infini)",
        model_id="kimi-k2.5",
        provider="infini",
        api_key="sk-cp-5bfck6tiavjuqv2b",
        base_url="https://cloud.infini-ai.com/maas/coding/v1",
        type="domestic",
        strengths=["chinese", "cost_efficiency", "consistency", "long_context"],
        cost_per_1k_tokens=0.015,
        quality_tier="standard",
    ),

    "deepseek-r1": ModelEndpoint(
        name="Kimi K2.5 (via Infini) - 推理",
        model_id="kimi-k2.5",
        provider="infini",
        api_key="sk-cp-5bfck6tiavjuqv2b",
        base_url="https://cloud.infini-ai.com/maas/coding/v1",
        type="domestic",
        strengths=["reasoning", "logic", "chinese", "long_context"],
        cost_per_1k_tokens=0.015,
        quality_tier="elite",
    ),

    "glm-5": ModelEndpoint(
        name="GLM-5",
        model_id="glm-5",
        provider="zhipu",
        api_key="7a0c4a13c22d48cda9d648aa82527485.UCIs1spSr9rgh7QR",  # Your key
        base_url="https://open.bigmodel.cn/api/paas/v4",
        type="domestic",
        strengths=["coding", "architecture", "worldbuilding", "system_design"],
        cost_per_1k_tokens=0.0,  # FIXED by Coding Plan!
        quality_tier="elite",
    ),
}


# ============================================
# INTERNATIONAL MODELS (国外模型 - Laozhang.ai)
# ============================================
# API Key: sk-dxRvT5PyeobdbCbu8b65863f727e4101A3C0646aB6C33dF5
# Status: ✅ 已测试，所有模型可用
# Last Tested: 2025-02-21
# Note: 旧Key (sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6) 已弃用

INTERNATIONAL_MODELS = {
    # GPT Series
    "gpt-4o": ModelEndpoint(
        name="GPT-4o",
        model_id="gpt-4o",
        provider="laozhang",
        api_key="sk-dxRvT5PyeobdbCbu8b65863f727e4101A3C0646aB6C33dF5",  # Updated - 全部模型可用
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["versatility", "instruction_following", "creativity"],
        cost_per_1k_tokens=0.005,
        quality_tier="elite",
    ),

    "gpt-4o-mini": ModelEndpoint(
        name="GPT-4o Mini",
        model_id="gpt-4o-mini",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["cost_efficiency", "speed", "good_quality"],
        cost_per_1k_tokens=0.0006,
        quality_tier="standard",
    ),

    "gpt-5-chat": ModelEndpoint(
        name="GPT-5 Chat",
        model_id="gpt-5-chat-latest",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["latest", "advanced_reasoning", "best_quality"],
        cost_per_1k_tokens=0.01,
        quality_tier="elite",
    ),

    # Claude Series (Best for emotional content)
    "claude-3.5-sonnet": ModelEndpoint(
        name="Claude 3.5 Sonnet",
        model_id="claude-3-5-sonnet-20241022",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["emotional_nuance", "literary_quality", "safety"],
        cost_per_1k_tokens=0.006,
        quality_tier="elite",
    ),

    "claude-3.7-sonnet": ModelEndpoint(
        name="Claude 3.7 Sonnet",
        model_id="claude-3-7-sonnet-latest",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["improved_reasoning", "coding", "writing"],
        cost_per_1k_tokens=0.008,
        quality_tier="elite",
    ),

    "claude-opus-4": ModelEndpoint(
        name="Claude Opus 4",
        model_id="claude-opus-4-20250514",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["highest_quality", "complex_tasks", "masterpiece"],
        cost_per_1k_tokens=0.03,
        quality_tier="elite",
    ),

    "claude-3.5-haiku": ModelEndpoint(
        name="Claude 3.5 Haiku",
        model_id="claude-3-5-haiku-latest",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["speed", "efficiency", "decent_quality"],
        cost_per_1k_tokens=0.0005,
        quality_tier="economy",
    ),

    # Gemini Series
    "gemini-2.5-pro": ModelEndpoint(
        name="Gemini 2.5 Pro",
        model_id="gemini-2.5-pro",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["1M_context", "multimodal", "long_novels"],
        cost_per_1k_tokens=0.005,
        quality_tier="elite",
    ),

    "gemini-2.5-flash": ModelEndpoint(
        name="Gemini 2.5 Flash",
        model_id="gemini-2.5-flash",
        provider="laozhang",
        api_key="sk-gMRHVngzmf8u8o8J2dA5Eb0424C141BaBa1fCc30923281F6",
        base_url="https://api.laozhang.ai/v1",
        type="international",
        strengths=["speed", "long_context", "cost_efficient"],
        cost_per_1k_tokens=0.0007,
        quality_tier="standard",
    ),
}


# ============================================
# ROUTING STRATEGIES
# ============================================

CHINESE_NOVEL_STRATEGY = {
    "name": "Chinese Web Novel (国内网文)",
    "description": "Use domestic models for Chinese content",
    "routing": {
        "golden_chapters": "kimi-k2.5",      # Kimi for emotional nuance
        "daily_chapters": "deepseek-v3",     # DeepSeek for cost efficiency
        "outline": "glm-5",                   # GLM for architecture (FREE)
        "system_coding": "glm-5",             # GLM for system design (FREE)
        "reasoning": "deepseek-r1",          # R1 for complex logic
    },
}

ENGLISH_NOVEL_STRATEGY = {
    "name": "English Web Novel (国外网文)",
    "description": "Use international models for English content",
    "routing": {
        "golden_chapters": "claude-3.5-sonnet",  # Claude for emotional depth
        "daily_chapters": "gpt-4o-mini",          # GPT-4o Mini for cost
        "outline": "gpt-4o",                       # GPT-4o for planning
        "masterpiece": "claude-opus-4",           # Opus for premium quality
        "volume": "gemini-2.5-flash",             # Gemini for long context
    },
}

HYBRID_STRATEGY = {
    "name": "Hybrid (中文为主 + 英文章节)",
    "description": "Use domestic for Chinese, international for English chapters",
    "routing": {
        "chinese_golden": "kimi-k2.5",
        "chinese_daily": "deepseek-v3",
        "english_golden": "claude-3.5-sonnet",
        "english_daily": "gpt-4o-mini",
        "outline": "glm-5",  # GLM can handle both
    },
}


def get_model_for_task(
    language: str,  # "zh" or "en"
    task_type: str,  # "golden", "daily", "outline", "reasoning"
    quality_requirement: str = "standard",  # "economy", "standard", "premium"
) -> ModelEndpoint:
    """Get appropriate model for task.

    Args:
        language: "zh" for Chinese, "en" for English
        task_type: Type of creative task
        quality_requirement: Quality tier needed

    Returns:
        ModelEndpoint configuration
    """

    if language == "zh":
        # Chinese content - use domestic models
        if task_type == "golden" or quality_requirement == "premium":
            return DOMESTIC_MODELS["kimi-k2.5"]
        elif task_type == "outline" or task_type == "system":
            return DOMESTIC_MODELS["glm-5"]  # FREE
        elif task_type == "reasoning":
            return DOMESTIC_MODELS["deepseek-r1"]
        else:
            return DOMESTIC_MODELS["deepseek-v3"]

    else:
        # English content - use international models
        if task_type == "golden" or quality_requirement == "premium":
            return INTERNATIONAL_MODELS["claude-3.5-sonnet"]
        elif task_type == "masterpiece":
            return INTERNATIONAL_MODELS["claude-opus-4"]
        elif task_type == "outline":
            return INTERNATIONAL_MODELS["gpt-4o"]
        elif task_type == "volume" or task_type == "long":
            return INTERNATIONAL_MODELS["gemini-2.5-flash"]
        else:
            return INTERNATIONAL_MODELS["gpt-4o-mini"]


def estimate_cost_detailed(
    total_chapters: int,
    language: str,
    golden_ratio: float = 0.15,  # 15% golden chapters
) -> dict[str, Any]:
    """Estimate detailed cost breakdown.

    Args:
        total_chapters: Total chapters
        language: "zh" or "en"
        golden_ratio: Percentage of elite chapters

    Returns:
        Cost breakdown dict
    """
    avg_tokens = 3000
    golden_count = int(total_chapters * golden_ratio)
    standard_count = total_chapters - golden_count

    if language == "zh":
        # Chinese pricing
        golden_model = DOMESTIC_MODELS["kimi-k2.5"]
        standard_model = DOMESTIC_MODELS["deepseek-v3"]
        outline_model = DOMESTIC_MODELS["glm-5"]

        golden_cost = golden_count * (avg_tokens / 1000) * golden_model.cost_per_1k_tokens
        standard_cost = standard_count * (avg_tokens / 1000) * standard_model.cost_per_1k_tokens
        outline_cost = 0.0  # GLM is FREE

    else:
        # English pricing
        golden_model = INTERNATIONAL_MODELS["claude-3.5-sonnet"]
        standard_model = INTERNATIONAL_MODELS["gpt-4o-mini"]
        outline_model = INTERNATIONAL_MODELS["gpt-4o"]

        golden_cost = golden_count * (avg_tokens / 1000) * golden_model.cost_per_1k_tokens
        standard_cost = standard_count * (avg_tokens / 1000) * standard_model.cost_per_1k_tokens
        outline_cost = 2 * (avg_tokens / 1000) * outline_model.cost_per_1k_tokens  # 2 outlines

    total_usd = golden_cost + standard_cost + outline_cost
    total_rmb = total_usd * 7.2

    return {
        "language": language,
        "total_chapters": total_chapters,
        "breakdown": {
            "golden_chapters": {
                "count": golden_count,
                "model": golden_model.name,
                "cost_usd": round(golden_cost, 2),
                "cost_rmb": round(golden_cost * 7.2, 2),
            },
            "standard_chapters": {
                "count": standard_count,
                "model": standard_model.name,
                "cost_usd": round(standard_cost, 2),
                "cost_rmb": round(standard_cost * 7.2, 2),
            },
            "outline": {
                "model": outline_model.name,
                "cost_usd": round(outline_cost, 2),
                "cost_rmb": round(outline_cost * 7.2, 2),
                "note": "FREE" if outline_model.cost_per_1k_tokens == 0 else "",
            },
        },
        "total_usd": round(total_usd, 2),
        "total_rmb": round(total_rmb, 2),
        "cost_per_chapter": round(total_rmb / total_chapters, 2),
    }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("模型配置方案 (Model Configuration)")
    print("=" * 60)

    print("\n【国内模型 - Domestic】")
    for key, model in DOMESTIC_MODELS.items():
        cost = "FREE" if model.cost_per_1k_tokens == 0 else f"${model.cost_per_1k_tokens}/1k"
        print(f"  {key}: {model.name} ({cost})")
        print(f"    URL: {model.base_url}")
        print(f"    Strengths: {', '.join(model.strengths)}")
        print()

    print("【国外模型 - International (via Laozhang.ai)】")
    for key, model in INTERNATIONAL_MODELS.items():
        if "haiku" in key or "opus" in key or "gemini" in key:
            continue  # Skip some for brevity
        print(f"  {key}: {model.name} (${model.cost_per_1k_tokens}/1k)")
    print("  ... (and more)")

    print("\n" + "=" * 60)
    print("成本预估 (Cost Estimation) - 100章小说")
    print("=" * 60)

    zh_estimate = estimate_cost_detailed(100, "zh")
    print("\n中文小说 (Chinese):")
    print(f"  总成本: ¥{zh_estimate['total_rmb']}")
    print(f"  平均每章: ¥{zh_estimate['cost_per_chapter']}")
    print("  GLM-5 架构: FREE (Coding Plan)")

    en_estimate = estimate_cost_detailed(100, "en")
    print("\n英文小说 (English):")
    print(f"  总成本: ¥{en_estimate['total_rmb']}")
    print(f"  平均每章: ¥{en_estimate['cost_per_chapter']}")
    print("  使用 Claude 3.5 Sonnet + GPT-4o Mini")

    print("\n" + "=" * 60)
