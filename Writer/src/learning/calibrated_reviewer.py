# src/learning/calibrated_reviewer.py
"""Calibrated Reviewer - Role-specific review standards."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default role-specific review standards
ROLE_STANDARDS: dict[str, dict[str, Any]] = {
    "protagonist": {
        "essential": ["成长弧线清晰", "读者可共情", "性格复杂立体", "动机合理明确"],
        "avoid": ["玛丽苏/杰克苏", "完美无缺", "被动无主见"],
        "scoring_focus": [
            ("情感真实度", 0.25),
            ("成长潜力", 0.25),
            ("复杂度", 0.25),
            ("读者代入感", 0.25),
        ],
        "description": "主角 - 故事的核心人物",
    },
    "antagonist": {
        "essential": ["动机合理", "非脸谱化", "有深度和复杂性", "构成真实威胁"],
        "avoid": ["纯粹的恶", "无脑反派", "动机不明"],
        "scoring_focus": [
            ("动机合理性", 0.30),
            ("复杂性", 0.30),
            ("威胁感", 0.20),
            ("记忆点", 0.20),
        ],
        "description": "反派 - 与主角对立的角色",
    },
    "love_interest": {
        "essential": ["有吸引力", "独立人格", "与主角有化学感", "有明显缺陷"],
        "avoid": ["完美恋人", "工具人", "缺乏主动性"],
        "scoring_focus": [
            ("吸引力", 0.25),
            ("独立人格", 0.25),
            ("化学感", 0.25),
            ("真实性", 0.25),
        ],
        "description": "恋爱对象 - 与主角有感情线的角色",
    },
    "supporting": {
        "essential": ["功能明确", "有记忆点", "不抢主角戏", "独特个性"],
        "avoid": ["可有可无", "千篇一律", "过度抢戏"],
        "scoring_focus": [
            ("功能性", 0.30),
            ("记忆点", 0.30),
            ("独特性", 0.20),
            ("篇幅控制", 0.20),
        ],
        "description": "配角 - 支持故事发展的角色",
    },
    "mentor": {
        "essential": ["智慧可信", "引导有方", "有人性弱点", "不喧宾夺主"],
        "avoid": ["全知全能", "说教机器", "抢主角风头"],
        "scoring_focus": [
            ("智慧感", 0.30),
            ("引导效果", 0.30),
            ("人情味", 0.20),
            ("退场时机", 0.20),
        ],
        "description": "导师 - 指导主角成长的角色",
    },
}

# Content type standards
CONTENT_STANDARDS: dict[str, dict[str, Any]] = {
    "character": {
        "required_fields": ["name", "role", "personality", "background"],
        "quality_dimensions": ["深度", "一致性", "独特性", "可塑性"],
    },
    "outline": {
        "required_fields": ["title", "acts", "climax", "resolution"],
        "quality_dimensions": ["结构", "节奏", "张力", "完整性"],
    },
    "chapter": {
        "required_fields": ["scenes", "dialogue", "narrative"],
        "quality_dimensions": ["流畅度", "画面感", "情感", "推进"],
    },
}


class CalibratedReviewer:
    """Generate calibrated review prompts based on content and role type.

    Usage:
        reviewer = CalibratedReviewer()

        # Get calibrated review prompt for a protagonist
        prompt = reviewer.get_review_prompt("character", role="protagonist")

        # Get role-specific standards
        standards = reviewer.get_role_standards("antagonist")
    """

    DEFAULT_STORAGE_PATH = "data/learning/reviewer_calibration.json"

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self._custom_standards: dict[str, dict[str, Any]] = {}
        self._load()
        logger.info("CalibratedReviewer initialized")

    def get_review_prompt(
        self,
        content_type: str,
        role: str | None = None,
        genre: str | None = None
    ) -> str:
        """Generate calibrated review prompt.

        Args:
            content_type: Type of content ("character", "outline", "chapter")
            role: Role type for characters ("protagonist", "antagonist", etc.)
            genre: Genre hint for context

        Returns:
            Complete review system prompt
        """
        if content_type == "character" and role:
            return self._build_character_prompt(role, genre)
        elif content_type == "outline":
            return self._build_outline_prompt(genre)
        elif content_type == "chapter":
            return self._build_chapter_prompt(genre)
        else:
            return self._build_generic_prompt(content_type)

    def get_role_standards(self, role: str) -> dict[str, Any]:
        """Get standards for a specific role.

        Returns custom standards if available, otherwise defaults.
        """
        if role in self._custom_standards:
            return self._custom_standards[role]
        return ROLE_STANDARDS.get(role, ROLE_STANDARDS["supporting"])

    def get_scoring_rubric(self, content_type: str, role: str | None) -> str:
        """Generate scoring rubric description."""
        if content_type == "character" and role:
            standards = self.get_role_standards(role)
            scoring = standards.get("scoring_focus", [])
            lines = ["评分维度:"]
            for dimension, weight in scoring:
                lines.append(f"  - {dimension}: {int(weight * 100)}%")
            return "\n".join(lines)
        return "使用通用评分标准"

    def update_standards(
        self,
        role: str,
        additions: list[str] | None = None,
        removals: list[str] | None = None
    ) -> None:
        """Update role standards (for learning).

        Args:
            role: Role to update
            additions: Features to add to "essential"
            removals: Features to remove from "essential"
        """
        standards = self.get_role_standards(role)

        if additions:
            for item in additions:
                if item not in standards.get("essential", []):
                    standards.setdefault("essential", []).append(item)

        if removals:
            standards["essential"] = [
                e for e in standards.get("essential", [])
                if e not in removals
            ]

        self._custom_standards[role] = standards
        self._save()
        logger.info(f"Updated standards for role: {role}")

    def _build_character_prompt(self, role: str, genre: str | None) -> str:
        """Build character review prompt."""
        standards = self.get_role_standards(role)
        role_name = standards.get("description", f"{role} 角色")

        essential = standards.get("essential", [])
        avoid = standards.get("avoid", [])
        scoring = standards.get("scoring_focus", [])

        # Build criteria section
        criteria_lines = ["评分维度 (权重):"]
        for dimension, weight in scoring:
            criteria_lines.append(f"- {dimension} ({int(weight * 100)}%): 评估{dimension}程度")

        # Build essential section
        essential_lines = ["必须具备的品质:"]
        for e in essential:
            essential_lines.append(f"✓ {e}")

        # Build avoid section
        avoid_lines = ["应该避免的问题:"]
        for a in avoid:
            avoid_lines.append(f"✗ {a}")

        prompt = f"""You are a character development expert evaluating a {role_name}.

{chr(10).join(criteria_lines)}

{chr(10).join(essential_lines)}

{chr(10).join(avoid_lines)}

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - 完美符合角色要求，有独特亮点
- 8.0-8.9: Good - 基本符合要求，有小的改进空间
- 7.0-7.9: Acceptable - 可接受但有明显不足
- 6.0-6.9: Below average - 存在较多问题
- Below 6: Poor - 不符合角色要求

Be CRITICAL. Most initial drafts score 6-7. Only award 9+ for truly memorable characters.

Output valid JSON only."""

        return prompt

    def _build_outline_prompt(self, genre: str | None) -> str:
        """Build outline review prompt."""
        return """You are a story structure expert evaluating a novel outline.

EVALUATION CRITERIA:
- 结构完整性 (25%): 是否有三幕结构，高潮和结局
- 节奏把控 (25%): 情节推进是否合理
- 张力设计 (25%): 是否有足够的冲突和悬念
- 主题深度 (25%): 主题是否清晰且有深度

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - 结构完美，节奏紧凑
- 8.0-8.9: Good - 结构完整，有小问题
- 7.0-7.9: Acceptable - 基本可用
- 6.0-6.9: Below average - 需要较多修改
- Below 6: Poor - 结构混乱

Be CRITICAL. Output valid JSON only."""

    def _build_chapter_prompt(self, genre: str | None) -> str:
        """Build chapter review prompt."""
        return """You are a fiction writing expert evaluating a chapter.

EVALUATION CRITERIA:
- 流畅度 (25%): 叙述是否流畅自然
- 画面感 (25%): 描写是否生动有画面感
- 情感 (25%): 情感表达是否真挚动人
- 剧情推
进 (25%): 是否有效推进故事

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - 读者沉浸感强
- 8.0-8.9: Good - 阅读体验好
- 7.0-7.9: Acceptable - 可读但平淡
- 6.0-6.9: Below average - 需要修改
- Below 6: Poor - 难以阅读

Be CRITICAL. Output valid JSON only."""

    def _build_generic_prompt(self, content_type: str) -> str:
        """Build generic review prompt."""
        return f"""You are a content quality expert evaluating {content_type}.

Evaluate for:
1. Quality and depth
2. Consistency
3. Completeness
4. Engagement

SCORING: Be CRITICAL. Most drafts score 6-7. Award 9+ only for exceptional work.

Output valid JSON only."""

    def _load(self) -> None:
        """Load custom standards from file."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
            self._custom_standards = data.get("custom_standards", {})
        except (json.JSONDecodeError, KeyError):
            self._custom_standards = {}

    def _save(self) -> None:
        """Save custom standards to file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "custom_standards": self._custom_standards,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
