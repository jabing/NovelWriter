"""Tier-based character template system.

This module provides tier-specific templates for character creation,
defining required and optional fields based on character importance.

Tiers:
- Tier 0 (核心主角): Complete persona with full cognitive graph (500 tokens)
- Tier 1 (重要配角): Detailed persona with full cognitive graph (300 tokens)
- Tier 2 (普通配角): Simplified with partial cognitive graph (100 tokens)
- Tier 3 (社会公众): Minimal with no cognitive graph (0 tokens)

Usage:
    from src.novel_agent.novel.tier_template import TierTemplate

    template = TierTemplate()

    # Get template for a tier
    t0 = template.get_template(0)

    # Generate character from template
    char = template.generate_character_template(
        tier=0,
        name="林晚",
        base_data={"bio": "将军之子", "personality": "沉稳果敢"}
    )

    # Validate character data
    errors = template.validate_character(char, tier=0)
"""

from __future__ import annotations

from typing import Any


# === Tier Template Definitions ===
# Each tier defines required fields, optional fields, and metadata
TIER_TEMPLATES: dict[int, dict[str, Any]] = {
    0: {
        "name": "核心主角",
        "description": "核心主角 - 完整人设，包含认知图谱",
        "required_fields": [
            {"field": "name", "label": "姓名", "type": "str"},
            {"field": "bio", "label": "人物简介", "type": "str"},
            {"field": "personality", "label": "性格特征", "type": "str"},
            {"field": "mbti", "label": "MBTI人格类型", "type": "str"},
            {"field": "background", "label": "背景故事", "type": "str"},
            {"field": "motivations", "label": "人物动机", "type": "str"},
        ],
        "optional_fields": [
            {"field": "relationships", "label": "人物关系", "type": "dict[str, str]"},
            {"field": "appearance", "label": "外貌描写", "type": "str"},
            {"field": "skills", "label": "技能特长", "type": "list[str]"},
            {"field": "weaknesses", "label": "弱点缺陷", "type": "list[str]"},
            {"field": "speech_pattern", "label": "说话风格", "type": "str"},
            {"field": "mannerisms", "label": "行为习惯", "type": "list[str]"},
            {"field": "goals", "label": "短期目标", "type": "list[str]"},
            {"field": "secrets", "label": "秘密", "type": "list[str]"},
        ],
        "token_budget": 500,
        "has_cognitive_graph": True,
        "cognitive_graph_type": "full",
    },
    1: {
        "name": "重要配角",
        "description": "重要配角 - 详细人设，包含认知图谱",
        "required_fields": [
            {"field": "name", "label": "姓名", "type": "str"},
            {"field": "bio", "label": "人物简介", "type": "str"},
            {"field": "personality", "label": "性格特征", "type": "str"},
            {"field": "profession", "label": "职业身份", "type": "str"},
        ],
        "optional_fields": [
            {"field": "background", "label": "背景故事", "type": "str"},
            {"field": "relationships", "label": "人物关系", "type": "dict[str, str]"},
            {"field": "appearance", "label": "外貌描写", "type": "str"},
            {"field": "skills", "label": "技能特长", "type": "list[str]"},
            {"field": "motivations", "label": "人物动机", "type": "str"},
        ],
        "token_budget": 300,
        "has_cognitive_graph": True,
        "cognitive_graph_type": "full",
    },
    2: {
        "name": "普通配角",
        "description": "普通配角 - 简化人设，简化认知图谱",
        "required_fields": [
            {"field": "name", "label": "姓名", "type": "str"},
            {"field": "bio", "label": "人物简介", "type": "str"},
            {"field": "profession", "label": "职业身份", "type": "str"},
            {"field": "key_traits", "label": "关键特征", "type": "list[str]"},
        ],
        "optional_fields": [
            {"field": "appearance", "label": "外貌描写", "type": "str"},
            {"field": "relationships", "label": "人物关系", "type": "dict[str, str]"},
        ],
        "token_budget": 100,
        "has_cognitive_graph": True,
        "cognitive_graph_type": "simplified",
    },
    3: {
        "name": "社会公众",
        "description": "社会公众 - 最简人设，无认知图谱",
        "required_fields": [
            {"field": "name", "label": "姓名", "type": "str"},
            {"field": "role", "label": "角色定位", "type": "str"},
            {"field": "description", "label": "基本描述", "type": "str"},
        ],
        "optional_fields": [],
        "token_budget": 0,
        "has_cognitive_graph": False,
        "cognitive_graph_type": None,
    },
}

FIELD_DESCRIPTIONS: dict[str, str] = {
    "name": "角色姓名，唯一标识",
    "bio": "人物简介，概括性描述",
    "personality": "性格特征，如【沉稳果敢】【温和善良】",
    "mbti": "MBTI人格类型，如INTJ、ENFP",
    "background": "背景故事，包括出身、经历",
    "motivations": "人物动机，驱动行为的内在原因",
    "relationships": "人物关系，如{林晚: 挚友}",
    "appearance": "外貌描写，视觉特征",
    "skills": "技能特长，如【剑术】【医术】",
    "weaknesses": "弱点缺陷，人物的不完美之处",
    "speech_pattern": "说话风格，如【言语简洁，用词精准】",
    "mannerisms": "行为习惯，如【习惯摸下巴】【走路时喜欢观察四周】",
    "goals": "短期目标，人物追求的事物",
    "secrets": "秘密，人物隐藏的事情",
    "profession": "职业身份，如【将军】【商人】",
    "key_traits": "关键特征，如【忠诚】【勇敢】",
    "role": "角色定位，如【路人】【士兵】",
    "description": "基本描述，简短说明",
}


class TierTemplate:
    """Tier-based character template system.

    Provides tier-specific templates for character creation with
    validation and generation capabilities.

    Attributes:
        templates: Dictionary of tier templates (0-3)
    """

    def __init__(self) -> None:
        """Initialize the tier template system."""
        self._templates = TIER_TEMPLATES

    def get_template(self, tier: int) -> dict[str, Any]:
        """Get the template for a specific tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            Template dictionary with required_fields, optional_fields,
            token_budget, has_cognitive_graph, and description.

        Raises:
            ValueError: If tier is not in range 0-3.
        """
        if tier not in self._templates:
            raise ValueError(
                f"Invalid tier: {tier}. Must be 0 (核心主角), 1 (重要配角), "
                f"2 (普通配角), or 3 (社会公众)."
            )
        return self._templates[tier].copy()

    def get_all_templates(self) -> dict[int, dict[str, Any]]:
        """Get all tier templates.

        Returns:
            Dictionary mapping tier to template.
        """
        return {tier: template.copy() for tier, template in self._templates.items()}

    def get_required_fields(self, tier: int) -> list[str]:
        """Get required field names for a tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            List of required field names.

        Raises:
            ValueError: If tier is not in range 0-3.
        """
        template = self.get_template(tier)
        return [f["field"] for f in template["required_fields"]]

    def get_optional_fields(self, tier: int) -> list[str]:
        """Get optional field names for a tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            List of optional field names.

        Raises:
            ValueError: If tier is not in range 0-3.
        """
        template = self.get_template(tier)
        return [f["field"] for f in template["optional_fields"]]

    def get_all_fields(self, tier: int) -> list[str]:
        """Get all field names (required + optional) for a tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            List of all field names.

        Raises:
            ValueError: If tier is not in range 0-3.
        """
        return self.get_required_fields(tier) + self.get_optional_fields(tier)

    def get_field_info(self, field_name: str) -> dict[str, str]:
        """Get information about a specific field.

        Args:
            field_name: Name of the field.

        Returns:
            Dictionary with field name, label, type, and description.
            Returns empty dict if field not found.
        """
        # Search all templates for the field
        for template in self._templates.values():
            for field in template["required_fields"] + template["optional_fields"]:
                if field["field"] == field_name:
                    return {
                        "field": field["field"],
                        "label": field["label"],
                        "type": field["type"],
                        "description": FIELD_DESCRIPTIONS.get(field_name, ""),
                    }
        return {}

    def get_token_budget(self, tier: int) -> int:
        """Get token budget for a tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            Token budget for the tier.
        """
        template = self.get_template(tier)
        return template["token_budget"]

    def has_cognitive_graph(self, tier: int) -> bool | str:
        """Check if tier supports cognitive graph.

        Args:
            tier: Character tier (0-3)

        Returns:
            True for full cognitive graph, "simplified" for partial,
            False for none.
        """
        template = self.get_template(tier)
        return template["has_cognitive_graph"]

    def generate_character_template(
        self,
        tier: int,
        name: str,
        base_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a character template with default structure for a tier.

        Creates a character data structure with all fields initialized
        to appropriate default values based on tier.

        Args:
            tier: Character tier (0-3)
            name: Character name
            base_data: Optional base data to populate fields

        Returns:
            Character data dictionary with tier-appropriate structure.

        Raises:
            ValueError: If tier is not in range 0-3.
        """
        template = self.get_template(tier)
        base_data = base_data or {}

        # Initialize character data
        character: dict[str, Any] = {
            "name": name,
            "tier": tier,
        }

        # Add tier metadata
        character["_tier_info"] = {
            "tier": tier,
            "name": template["name"],
            "description": template["description"],
            "token_budget": template["token_budget"],
            "has_cognitive_graph": template["has_cognitive_graph"],
            "cognitive_graph_type": template["cognitive_graph_type"],
        }

        def _get_default(field_type: str) -> Any:
            if field_type == "str":
                return ""
            elif field_type == "list[str]":
                return []
            elif field_type == "dict[str, str]":
                return {}
            return None

        for field in template["required_fields"]:
            field_name = field["field"]
            field_type = field["type"]
            if field_name == "name":
                continue
            if field_name in base_data:
                character[field_name] = base_data[field_name]
            else:
                character[field_name] = _get_default(field_type)

        for field in template["optional_fields"]:
            field_name = field["field"]
            field_type = field["type"]
            if field_name in base_data:
                character[field_name] = base_data[field_name]
            else:
                character[field_name] = _get_default(field_type)

        return character

    def validate_character(
        self,
        character_data: dict[str, Any],
        tier: int,
    ) -> list[str]:
        """Validate character data against tier template.

        Checks that all required fields are present and non-empty.

        Args:
            character_data: Character data to validate.
            tier: Expected character tier.

        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors: list[str] = []

        template = self.get_template(tier)
        required_fields = [f["field"] for f in template["required_fields"]]

        for field_name in required_fields:
            # Check field exists
            if field_name not in character_data:
                errors.append(f"缺少必填字段: {field_name} ({FIELD_DESCRIPTIONS.get(field_name, '')})")
                continue

            # Check field is not empty
            value = character_data[field_name]
            if value is None:
                errors.append(f"字段不能为空: {field_name}")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"字段不能为空字符串: {field_name}")
            elif isinstance(value, list | dict) and len(value) == 0:
                errors.append(f"字段不能为空容器: {field_name}")

        return errors

    def validate_and_get_errors(
        self,
        character_data: dict[str, Any],
        tier: int,
    ) -> dict[str, Any]:
        """Validate character and return structured result.

        Args:
            character_data: Character data to validate.
            tier: Expected character tier.

        Returns:
            Dictionary with:
            - valid: bool
            - errors: list of error messages
            - missing_fields: list of missing required field names
            - empty_fields: list of empty required field names
        """
        template = self.get_template(tier)
        required_fields = [f["field"] for f in template["required_fields"]]

        missing_fields: list[str] = []
        empty_fields: list[str] = []
        errors: list[str] = []

        for field_name in required_fields:
            if field_name not in character_data:
                missing_fields.append(field_name)
                errors.append(f"缺少必填字段: {field_name}")
                continue

            value = character_data[field_name]
            if value is None:
                empty_fields.append(field_name)
                errors.append(f"字段不能为空: {field_name}")
            elif isinstance(value, str) and not value.strip():
                empty_fields.append(field_name)
                errors.append(f"字段不能为空字符串: {field_name}")
            elif isinstance(value, list | dict) and len(value) == 0:
                empty_fields.append(field_name)
                errors.append(f"字段不能为空容器: {field_name}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "missing_fields": missing_fields,
            "empty_fields": empty_fields,
        }

    def get_tier_description(self, tier: int) -> str:
        """Get human-readable description for a tier.

        Args:
            tier: Character tier (0-3)

        Returns:
            Description string.
        """
        template = self.get_template(tier)
        return f"Tier {tier}: {template['name']} - {template['description']}"

    def suggest_tier(self, character_data: dict[str, Any]) -> int:
        """Suggest an appropriate tier based on character data completeness.

        Analyzes which fields are populated and suggests the most
        appropriate tier.

        Args:
            character_data: Character data to analyze.

        Returns:
            Suggested tier (0-3).
        """
        # Count populated fields for each tier
        scores: dict[int, int] = {}

        for tier in range(4):
            template = self.get_template(tier)
            required = [f["field"] for f in template["required_fields"]]
            optional = [f["field"] for f in template["optional_fields"]]

            # Score based on required fields present
            required_present = sum(1 for f in required if f in character_data and character_data[f])
            # Score based on optional fields present
            optional_present = sum(1 for f in optional if f in character_data and character_data[f])

            # Weight: required fields more important
            scores[tier] = required_present * 2 + optional_present

        # Return tier with highest score
        return max(scores, key=lambda t: scores[t])


__all__ = [
    "TierTemplate",
    "TIER_TEMPLATES",
    "FIELD_DESCRIPTIONS",
]
