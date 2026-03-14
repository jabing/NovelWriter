# src/llm/optimized_model_router.py
"""Optimized Model Router - Maximum quality with cost efficiency.

Strategy:
- Tier 1: System/Interaction → GLM-5 (FREE)
- Tier 2: Architecture/Logic → GLM-5 (FREE)
- Tier 3: Elite Content → Kimi/Claude (Premium)
- Tier 4: Standard Content → Cost-effective models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Types of tasks with different quality requirements."""
    # System/Interaction (FREE - GLM-5)
    CLI_INTERACTION = "cli_interaction"      # 命令解析
    PARAM_VALIDATION = "param_validation"    # 参数验证
    HELP_SYSTEM = "help_system"              # 帮助文档
    ERROR_HANDLING = "error_handling"        # 错误处理

    # Architecture/Logic (FREE - GLM-5)
    STORY_ARCHITECTURE = "story_architecture"    # 故事架构
    WORLDBUILDING = "worldbuilding"              # 世界观
    SYSTEM_DESIGN = "system_design"              # 系统流设计
    LOGIC_CHECK = "logic_check"                  # 逻辑验证
    PLOT_PLANNING = "plot_planning"              # 情节规划

    # Elite Content (PREMIUM - Kimi/Claude)
    GOLDEN_CHAPTER = "golden_chapter"        # 黄金章节
    EMOTIONAL_PEAK = "emotional_peak"        # 情感高潮
    CLIMAX = "climax"                        # 故事高潮
    FINALE = "finale"                        # 大结局
    CHARACTER_CORE = "character_core"        # 核心角色

    # Standard Content (BALANCED)
    DAILY_CHAPTER = "daily_chapter"          # 日常章节
    TRANSITION = "transition"                # 过渡章节
    DIALOGUE = "dialogue"                    # 对话生成
    DESCRIPTION = "description"              # 场景描写

    # Economy Content (CHEAP)
    FILLER = "filler"                        # 填充内容
    SUMMARY = "summary"                      # 总结/回顾
    TEMPLATE = "template"                    # 模板生成
    BRAINSTORM = "brainstorm"                # 头脑风暴


@dataclass
class ModelAssignment:
    """Model assignment for a specific task."""
    task_type: TaskType
    primary_model: str
    fallback_model: str
    quality_tier: str
    max_tokens: int
    temperature: float
    reasoning: str


class OptimizedModelRouter:
    """Router optimized for quality and cost.

    Cost-Quality Matrix:

    Task Category          | Model          | Cost/1k  | Quality | Usage %
    ----------------------|----------------|----------|---------|--------
    System/Interaction     | GLM-5          | FREE     | ★★★★    | 20%
    Architecture/Logic     | GLM-5          | FREE     | ★★★★★   | 15%
    Elite Content          | Kimi/Claude    | $0.015   | ★★★★★   | 15%
    Standard Content       | DeepSeek/GPT   | $0.002   | ★★★☆    | 45%
    Economy Content        | Haiku/Mini     | $0.0005  | ★★☆☆    | 5%

    Total Cost Savings: ~40% vs all-Kimi approach
    """

    # Cost-optimized assignments
    ASSIGNMENTS = {
        # === TIER 1: System/Interaction (FREE) ===
        TaskType.CLI_INTERACTION: ModelAssignment(
            task_type=TaskType.CLI_INTERACTION,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=500,
            temperature=0.3,
            reasoning="命令解析需要逻辑准确，GLM-5编程能力强且免费"
        ),

        TaskType.PARAM_VALIDATION: ModelAssignment(
            task_type=TaskType.PARAM_VALIDATION,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=300,
            temperature=0.1,
            reasoning="参数验证是确定性逻辑，GLM-5最可靠且免费"
        ),

        TaskType.HELP_SYSTEM: ModelAssignment(
            task_type=TaskType.HELP_SYSTEM,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=1000,
            temperature=0.5,
            reasoning="帮助文档需要结构化输出，GLM-5擅长"
        ),

        TaskType.ERROR_HANDLING: ModelAssignment(
            task_type=TaskType.ERROR_HANDLING,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=500,
            temperature=0.3,
            reasoning="错误处理需要准确分析，GLM-5逻辑强"
        ),

        # === TIER 2: Architecture/Logic (FREE) ===
        TaskType.STORY_ARCHITECTURE: ModelAssignment(
            task_type=TaskType.STORY_ARCHITECTURE,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=4000,
            temperature=0.6,
            reasoning="故事架构是系统设计，GLM-5架构能力最强且免费"
        ),

        TaskType.WORLDBUILDING: ModelAssignment(
            task_type=TaskType.WORLDBUILDING,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=4000,
            temperature=0.7,
            reasoning="世界观构建需要逻辑一致性，GLM-5最合适"
        ),

        TaskType.SYSTEM_DESIGN: ModelAssignment(
            task_type=TaskType.SYSTEM_DESIGN,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=4000,
            temperature=0.6,
            reasoning="系统流设计是编程任务，GLM-5 Coding Plan优势"
        ),

        TaskType.LOGIC_CHECK: ModelAssignment(
            task_type=TaskType.LOGIC_CHECK,
            primary_model="glm-5",
            fallback_model="deepseek-r1",
            quality_tier="free",
            max_tokens=2000,
            temperature=0.3,
            reasoning="逻辑检查需要严谨推理，GLM-5或R1"
        ),

        TaskType.PLOT_PLANNING: ModelAssignment(
            task_type=TaskType.PLOT_PLANNING,
            primary_model="glm-5",
            fallback_model="kimi-k2.5",
            quality_tier="free",
            max_tokens=4000,
            temperature=0.7,
            reasoning="情节规划是架构工作，GLM-5免费且高效"
        ),

        # === TIER 3: Elite Content (PREMIUM - 必须最高质量) ===
        TaskType.GOLDEN_CHAPTER: ModelAssignment(
            task_type=TaskType.GOLDEN_CHAPTER,
            primary_model="kimi-k2.5",  # 中文
            fallback_model="claude-3.5-sonnet",  # 英文
            quality_tier="premium",
            max_tokens=4000,
            temperature=0.7,
            reasoning="黄金章节决定读者留存，必须用Kimi/Claude最高质量"
        ),

        TaskType.EMOTIONAL_PEAK: ModelAssignment(
            task_type=TaskType.EMOTIONAL_PEAK,
            primary_model="kimi-k2.5",
            fallback_model="claude-3.5-sonnet",
            quality_tier="premium",
            max_tokens=4000,
            temperature=0.75,
            reasoning="情感高潮需要细腻描写，不能用便宜模型"
        ),

        TaskType.CLIMAX: ModelAssignment(
            task_type=TaskType.CLIMAX,
            primary_model="kimi-k2.5",
            fallback_model="claude-opus-4",
            quality_tier="premium",
            max_tokens=4000,
            temperature=0.7,
            reasoning="故事高潮是核心，质量第一不考虑成本"
        ),

        TaskType.FINALE: ModelAssignment(
            task_type=TaskType.FINALE,
            primary_model="kimi-k2.5",
            fallback_model="claude-opus-4",
            quality_tier="premium",
            max_tokens=4000,
            temperature=0.7,
            reasoning="大结局决定口碑，必须用最好模型"
        ),

        TaskType.CHARACTER_CORE: ModelAssignment(
            task_type=TaskType.CHARACTER_CORE,
            primary_model="kimi-k2.5",
            fallback_model="claude-3.5-sonnet",
            quality_tier="premium",
            max_tokens=3000,
            temperature=0.75,
            reasoning="核心角色是故事灵魂，质量优先"
        ),

        # === TIER 4: Standard Content (BALANCED) ===
        TaskType.DAILY_CHAPTER: ModelAssignment(
            task_type=TaskType.DAILY_CHAPTER,
            primary_model="deepseek-v3",  # 如果可用
            fallback_model="gpt-4o-mini",
            quality_tier="standard",
            max_tokens=4000,
            temperature=0.8,
            reasoning="日常章节量大，用成本效益好的模型"
        ),

        TaskType.TRANSITION: ModelAssignment(
            task_type=TaskType.TRANSITION,
            primary_model="gpt-4o-mini",
            fallback_model="claude-3.5-haiku",
            quality_tier="standard",
            max_tokens=3000,
            temperature=0.8,
            reasoning="过渡章节质量要求中等，可以降级"
        ),

        TaskType.DIALOGUE: ModelAssignment(
            task_type=TaskType.DIALOGUE,
            primary_model="kimi-k2.5",
            fallback_model="gpt-4o-mini",
            quality_tier="standard",
            max_tokens=2000,
            temperature=0.85,
            reasoning="对话生成相对简单，可适度降级"
        ),

        TaskType.DESCRIPTION: ModelAssignment(
            task_type=TaskType.DESCRIPTION,
            primary_model="gpt-4o-mini",
            fallback_model="kimi-k2.5",
            quality_tier="standard",
            max_tokens=1500,
            temperature=0.8,
            reasoning="场景描写可以用较便宜的模型"
        ),

        # === TIER 5: Economy Content (CHEAP) ===
        TaskType.FILLER: ModelAssignment(
            task_type=TaskType.FILLER,
            primary_model="claude-3.5-haiku",
            fallback_model="gpt-4o-mini",
            quality_tier="economy",
            max_tokens=2000,
            temperature=0.9,
            reasoning="填充内容成本优先，用最便宜的模型"
        ),

        TaskType.SUMMARY: ModelAssignment(
            task_type=TaskType.SUMMARY,
            primary_model="glm-5",
            fallback_model="claude-3.5-haiku",
            quality_tier="economy",
            max_tokens=1000,
            temperature=0.5,
            reasoning="总结可以用GLM-5免费或Haiku便宜模型"
        ),

        TaskType.TEMPLATE: ModelAssignment(
            task_type=TaskType.TEMPLATE,
            primary_model="glm-5",
            fallback_model="glm-5",
            quality_tier="free",
            max_tokens=1500,
            temperature=0.4,
            reasoning="模板生成是结构化任务，GLM-5免费搞定"
        ),

        TaskType.BRAINSTORM: ModelAssignment(
            task_type=TaskType.BRAINSTORM,
            primary_model="claude-3.5-haiku",
            fallback_model="gpt-4o-mini",
            quality_tier="economy",
            max_tokens=2000,
            temperature=0.95,
            reasoning="头脑风暴需要创意但不用精细，用经济模型"
        ),
    }

    def __init__(self, language: str = "zh"):
        """Initialize router.

        Args:
            language: "zh" for Chinese, "en" for English
        """
        self.language = language
        self.usage_stats = {}

    def route(self, task_type: TaskType | str, **context) -> ModelAssignment:
        """Get optimal model assignment for task.

        Args:
            task_type: Type of task
            **context: Additional context (chapter_number, content_type, etc.)

        Returns:
            ModelAssignment with optimal model selection
        """
        # Convert string to enum if needed
        if isinstance(task_type, str):
            task_type = TaskType(task_type)

        assignment = self.ASSIGNMENTS.get(task_type)
        if not assignment:
            # Default to standard tier
            return self.ASSIGNMENTS[TaskType.DAILY_CHAPTER]

        # Adjust for language
        if self.language == "en" and assignment.primary_model == "kimi-k2.5":
            # Use Claude for English content instead of Kimi
            assignment = ModelAssignment(
                task_type=assignment.task_type,
                primary_model=assignment.fallback_model,  # Usually Claude
                fallback_model="gpt-4o-mini",
                quality_tier=assignment.quality_tier,
                max_tokens=assignment.max_tokens,
                temperature=assignment.temperature,
                reasoning=assignment.reasoning + " (English: using Claude instead of Kimi)",
            )

        return assignment

    def get_cost_estimate(
        self,
        total_chapters: int = 100,
        golden_ratio: float = 0.15,
        language: str = "zh"
    ) -> dict[str, Any]:
        """Estimate cost with optimized routing.

        Args:
            total_chapters: Total chapters
            golden_ratio: Percentage of golden/elite chapters
            language: Target language

        Returns:
            Cost breakdown
        """
        avg_tokens = 3000

        # Chapter distribution
        golden_count = int(total_chapters * golden_ratio)
        standard_count = int(total_chapters * 0.70)
        economy_count = total_chapters - golden_count - standard_count

        # Architecture work (FREE)
        architecture_tokens = 10000  # 10k tokens for outline/worldbuilding

        costs = {
            "architecture": {
                "tokens": architecture_tokens,
                "model": "GLM-5",
                "cost": 0.0,  # FREE
                "note": "Coding Plan - Unlimited",
            },
            "golden_chapters": {
                "count": golden_count,
                "tokens": golden_count * avg_tokens,
                "model": "Kimi K2.5" if language == "zh" else "Claude 3.5",
                "cost": golden_count * (avg_tokens / 1000) * 0.015,
            },
            "standard_chapters": {
                "count": standard_count,
                "tokens": standard_count * avg_tokens,
                "model": "GPT-4o Mini / DeepSeek",
                "cost": standard_count * (avg_tokens / 1000) * 0.002,
            },
            "economy_chapters": {
                "count": economy_count,
                "tokens": economy_count * avg_tokens,
                "model": "Claude Haiku / GLM-5",
                "cost": economy_count * (avg_tokens / 1000) * 0.0005,
            },
        }

        total_cost = sum(c["cost"] for c in costs.values())

        # Compare to all-premium approach
        all_premium_cost = total_chapters * (avg_tokens / 1000) * 0.015
        savings = all_premium_cost - total_cost

        return {
            "language": language,
            "total_chapters": total_chapters,
            "breakdown": costs,
            "total_cost_usd": round(total_cost, 2),
            "total_cost_rmb": round(total_cost * 7.2, 2),
            "all_premium_cost": round(all_premium_cost, 2),
            "savings_usd": round(savings, 2),
            "savings_percent": round(savings / all_premium_cost * 100, 1),
            "cost_per_chapter": round(total_cost / total_chapters, 3),
        }


# Usage example
if __name__ == "__main__":
    router = OptimizedModelRouter(language="zh")

    print("=" * 70)
    print("优化模型路由 - 质量保证 + 成本控制")
    print("=" * 70)

    # Show some examples
    examples = [
        TaskType.CLI_INTERACTION,
        TaskType.STORY_ARCHITECTURE,
        TaskType.GOLDEN_CHAPTER,
        TaskType.DAILY_CHAPTER,
        TaskType.FILLER,
    ]

    print("\n【任务路由示例】")
    for task in examples:
        assignment = router.route(task)
        print(f"\n{task.value}:")
        print(f"  模型: {assignment.primary_model}")
        print(f"  层级: {assignment.quality_tier}")
        print(f"  原因: {assignment.reasoning}")

    # Cost estimate
    print("\n" + "=" * 70)
    print("【100章中文小说成本预估】")
    estimate = router.get_cost_estimate(100)

    print(f"\n总成本: ${estimate['total_cost_usd']} (¥{estimate['total_cost_rmb']})")
    print(f"平均每章: ${estimate['cost_per_chapter']}")
    print(f"\n相比全用Kimi节省: ${estimate['savings_usd']} ({estimate['savings_percent']}%)")

    print("\n成本 breakdown:")
    for key, value in estimate['breakdown'].items():
        cost = value['cost']
        if cost == 0:
            print(f"  {key}: FREE")
        else:
            print(f"  {key}: ${cost:.2f}")

    print("\n" + "=" * 70)
