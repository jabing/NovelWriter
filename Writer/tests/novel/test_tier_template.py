"""Unit tests for TierTemplate.

Tests cover:
- Template retrieval for each tier
- Field listing (required, optional, all)
- Character template generation
- Validation of character data
- Tier suggestion
"""

import pytest

from src.novel.tier_template import (
    FIELD_DESCRIPTIONS,
    TIER_TEMPLATES,
    TierTemplate,
)


class TestTierTemplateBasics:
    """Basic tests for TierTemplate class."""

    def test_init(self) -> None:
        """Test initialization."""
        template = TierTemplate()
        assert template is not None

    def test_get_template_tier_0(self) -> None:
        """Test getting template for tier 0."""
        template = TierTemplate()
        t0 = template.get_template(0)

        assert t0["name"] == "核心主角"
        assert t0["token_budget"] == 500
        assert t0["has_cognitive_graph"] is True
        assert t0["cognitive_graph_type"] == "full"

    def test_get_template_tier_1(self) -> None:
        """Test getting template for tier 1."""
        template = TierTemplate()
        t1 = template.get_template(1)

        assert t1["name"] == "重要配角"
        assert t1["token_budget"] == 300
        assert t1["has_cognitive_graph"] is True

    def test_get_template_tier_2(self) -> None:
        """Test getting template for tier 2."""
        template = TierTemplate()
        t2 = template.get_template(2)

        assert t2["name"] == "普通配角"
        assert t2["token_budget"] == 100
        assert t2["has_cognitive_graph"] is True
        assert t2["cognitive_graph_type"] == "simplified"

    def test_get_template_tier_3(self) -> None:
        """Test getting template for tier 3."""
        template = TierTemplate()
        t3 = template.get_template(3)

        assert t3["name"] == "社会公众"
        assert t3["token_budget"] == 0
        assert t3["has_cognitive_graph"] is False
        assert t3["cognitive_graph_type"] is None

    def test_get_template_invalid_tier(self) -> None:
        """Test getting template for invalid tier raises error."""
        template = TierTemplate()

        with pytest.raises(ValueError) as exc_info:
            template.get_template(4)
        assert "Invalid tier" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            template.get_template(-1)
        assert "Invalid tier" in str(exc_info.value)

    def test_get_all_templates(self) -> None:
        """Test getting all templates."""
        template = TierTemplate()
        all_templates = template.get_all_templates()

        assert len(all_templates) == 4
        assert 0 in all_templates
        assert 1 in all_templates
        assert 2 in all_templates
        assert 3 in all_templates


class TestFieldListing:
    """Tests for field listing methods."""

    def test_get_required_fields_tier_0(self) -> None:
        """Test required fields for tier 0."""
        template = TierTemplate()
        required = template.get_required_fields(0)

        assert "name" in required
        assert "bio" in required
        assert "personality" in required
        assert "mbti" in required
        assert "background" in required
        assert "motivations" in required
        assert len(required) == 6

    def test_get_required_fields_tier_1(self) -> None:
        """Test required fields for tier 1."""
        template = TierTemplate()
        required = template.get_required_fields(1)

        assert "name" in required
        assert "bio" in required
        assert "personality" in required
        assert "profession" in required
        assert len(required) == 4

    def test_get_required_fields_tier_2(self) -> None:
        """Test required fields for tier 2."""
        template = TierTemplate()
        required = template.get_required_fields(2)

        assert "name" in required
        assert "bio" in required
        assert "profession" in required
        assert "key_traits" in required
        assert len(required) == 4

    def test_get_required_fields_tier_3(self) -> None:
        """Test required fields for tier 3."""
        template = TierTemplate()
        required = template.get_required_fields(3)

        assert "name" in required
        assert "role" in required
        assert "description" in required
        assert len(required) == 3

    def test_get_optional_fields_tier_0(self) -> None:
        """Test optional fields for tier 0."""
        template = TierTemplate()
        optional = template.get_optional_fields(0)

        assert "relationships" in optional
        assert "appearance" in optional
        assert "skills" in optional
        assert "weaknesses" in optional
        assert len(optional) > 0

    def test_get_optional_fields_tier_3_empty(self) -> None:
        """Test optional fields for tier 3 is empty."""
        template = TierTemplate()
        optional = template.get_optional_fields(3)

        assert optional == []

    def test_get_all_fields(self) -> None:
        """Test getting all fields."""
        template = TierTemplate()
        all_fields = template.get_all_fields(0)
        required = template.get_required_fields(0)
        optional = template.get_optional_fields(0)

        for field in required:
            assert field in all_fields
        for field in optional:
            assert field in all_fields

    def test_get_field_info(self) -> None:
        """Test getting field info."""
        template = TierTemplate()
        info = template.get_field_info("name")

        assert info["field"] == "name"
        assert info["label"] == "姓名"
        assert info["type"] == "str"
        assert "description" in info

    def test_get_field_info_not_found(self) -> None:
        """Test getting info for non-existent field."""
        template = TierTemplate()
        info = template.get_field_info("nonexistent_field")

        assert info == {}


class TestCharacterGeneration:
    """Tests for character template generation."""

    def test_generate_character_tier_0(self) -> None:
        """Test generating character template for tier 0."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=0,
            name="林晚",
            base_data={"bio": "将军之子", "personality": "沉稳果敢"},
        )

        assert char["name"] == "林晚"
        assert char["tier"] == 0
        assert char["bio"] == "将军之子"
        assert char["personality"] == "沉稳果敢"
        assert char["_tier_info"]["token_budget"] == 500

    def test_generate_character_tier_1(self) -> None:
        """Test generating character template for tier 1."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=1,
            name="陈风",
            base_data={"bio": "商人", "profession": "商人"},
        )

        assert char["name"] == "陈风"
        assert char["tier"] == 1
        assert char["bio"] == "商人"
        assert char["profession"] == "商人"
        assert char["_tier_info"]["token_budget"] == 300

    def test_generate_character_tier_2(self) -> None:
        """Test generating character template for tier 2."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=2,
            name="小二",
            base_data={"bio": "客栈伙计", "profession": "伙计"},
        )

        assert char["name"] == "小二"
        assert char["tier"] == 2
        assert char["bio"] == "客栈伙计"
        assert char["_tier_info"]["token_budget"] == 100

    def test_generate_character_tier_3(self) -> None:
        """Test generating character template for tier 3."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=3,
            name="路人甲",
            base_data={"role": "路人", "description": "路人"},
        )

        assert char["name"] == "路人甲"
        assert char["tier"] == 3
        assert char["_tier_info"]["token_budget"] == 0
        assert char["_tier_info"]["has_cognitive_graph"] is False

    def test_generate_character_with_empty_base_data(self) -> None:
        """Test generating character with empty base data."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=0,
            name="测试角色",
            base_data=None,
        )

        assert char["name"] == "测试角色"
        assert char["bio"] == ""
        assert char["personality"] == ""
        assert char["mbti"] == ""
        assert char["background"] == ""
        assert char["motivations"] == ""

    def test_generate_character_initializes_list_fields(self) -> None:
        """Test that list fields are initialized as empty lists."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=0,
            name="测试",
            base_data=None,
        )

        assert char["skills"] == []
        assert char["weaknesses"] == []
        assert char["mannerisms"] == []
        assert char["goals"] == []
        assert char["secrets"] == []

    def test_generate_character_initializes_dict_fields(self) -> None:
        """Test that dict fields are initialized as empty dicts."""
        template = TierTemplate()
        char = template.generate_character_template(
            tier=0,
            name="测试",
            base_data=None,
        )

        assert char["relationships"] == {}


class TestValidation:
    """Tests for character validation."""

    def test_validate_valid_character_tier_0(self) -> None:
        """Test validating a valid tier 0 character."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": "将军之子",
            "personality": "沉稳果敢",
            "mbti": "INTJ",
            "background": "出生于将门世家",
            "motivations": "守护家族荣耀",
        }

        errors = template.validate_character(char, tier=0)
        assert errors == []

    def test_validate_valid_character_tier_1(self) -> None:
        """Test validating a valid tier 1 character."""
        template = TierTemplate()
        char = {
            "name": "陈风",
            "bio": "商人",
            "personality": "精明能干",
            "profession": "商人",
        }

        errors = template.validate_character(char, tier=1)
        assert errors == []

    def test_validate_valid_character_tier_2(self) -> None:
        """Test validating a valid tier 2 character."""
        template = TierTemplate()
        char = {
            "name": "小二",
            "bio": "客栈伙计",
            "profession": "伙计",
            "key_traits": ["勤快", "机灵"],
        }

        errors = template.validate_character(char, tier=2)
        assert errors == []

    def test_validate_valid_character_tier_3(self) -> None:
        """Test validating a valid tier 3 character."""
        template = TierTemplate()
        char = {
            "name": "路人甲",
            "role": "路人",
            "description": "路人",
        }

        errors = template.validate_character(char, tier=3)
        assert errors == []

    def test_validate_missing_required_field(self) -> None:
        """Test validation catches missing required field."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": "将军之子",
        }

        errors = template.validate_character(char, tier=0)
        assert len(errors) > 0
        assert any("personality" in e for e in errors)

    def test_validate_empty_string_field(self) -> None:
        """Test validation catches empty string field."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": "",
            "personality": "沉稳果敢",
            "mbti": "INTJ",
            "background": "出生于将门世家",
            "motivations": "守护家族荣耀",
        }

        errors = template.validate_character(char, tier=0)
        assert any("bio" in e for e in errors)

    def test_validate_empty_list_field(self) -> None:
        """Test validation catches empty list field."""
        template = TierTemplate()
        char = {
            "name": "小二",
            "bio": "客栈伙计",
            "profession": "伙计",
            "key_traits": [],
        }

        errors = template.validate_character(char, tier=2)
        assert any("key_traits" in e for e in errors)

    def test_validate_none_field(self) -> None:
        """Test validation catches None field."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": None,
            "personality": "沉稳果敢",
            "mbti": "INTJ",
            "background": "出生于将门世家",
            "motivations": "守护家族荣耀",
        }

        errors = template.validate_character(char, tier=0)
        assert any("bio" in e for e in errors)

    def test_validate_and_get_errors(self) -> None:
        """Test structured validation result."""
        template = TierTemplate()
        char = {
            "name": "林晚",
        }

        result = template.validate_and_get_errors(char, tier=0)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert len(result["missing_fields"]) > 0
        assert "bio" in result["missing_fields"]

    def test_validate_and_get_errors_valid(self) -> None:
        """Test structured validation result for valid character."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": "将军之子",
            "personality": "沉稳果敢",
            "mbti": "INTJ",
            "background": "出生于将门世家",
            "motivations": "守护家族荣耀",
        }

        result = template.validate_and_get_errors(char, tier=0)

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["missing_fields"] == []
        assert result["empty_fields"] == []


class TestTierMetadata:
    """Tests for tier metadata methods."""

    def test_get_token_budget(self) -> None:
        """Test getting token budget."""
        template = TierTemplate()

        assert template.get_token_budget(0) == 500
        assert template.get_token_budget(1) == 300
        assert template.get_token_budget(2) == 100
        assert template.get_token_budget(3) == 0

    def test_has_cognitive_graph(self) -> None:
        """Test checking cognitive graph support."""
        template = TierTemplate()

        assert template.has_cognitive_graph(0) is True
        assert template.has_cognitive_graph(1) is True
        assert template.has_cognitive_graph(2) is True
        assert template.has_cognitive_graph(3) is False

    def test_get_tier_description(self) -> None:
        """Test getting tier description."""
        template = TierTemplate()

        desc0 = template.get_tier_description(0)
        assert "Tier 0" in desc0
        assert "核心主角" in desc0

        desc3 = template.get_tier_description(3)
        assert "Tier 3" in desc3
        assert "社会公众" in desc3


class TestTierSuggestion:
    """Tests for tier suggestion."""

    def test_suggest_tier_0_full_data(self) -> None:
        """Test suggesting tier 0 for complete data."""
        template = TierTemplate()
        char = {
            "name": "林晚",
            "bio": "将军之子",
            "personality": "沉稳果敢",
            "mbti": "INTJ",
            "background": "出生于将门世家",
            "motivations": "守护家族荣耀",
            "skills": ["剑术", "兵法"],
        }

        suggested = template.suggest_tier(char)
        assert suggested == 0

    def test_suggest_tier_1_medium_data(self) -> None:
        """Test suggesting tier 1 for medium data."""
        template = TierTemplate()
        char = {
            "name": "陈风",
            "bio": "商人",
            "personality": "精明能干",
            "profession": "商人",
            "background": "出身商贾之家",
        }

        suggested = template.suggest_tier(char)
        assert suggested == 1

    def test_suggest_tier_2_simple_data(self) -> None:
        """Test suggesting tier 2 for simple data."""
        template = TierTemplate()
        char = {
            "name": "小二",
            "bio": "客栈伙计",
            "profession": "伙计",
            "key_traits": ["勤快", "机灵"],
        }

        suggested = template.suggest_tier(char)
        assert suggested == 2

    def test_suggest_tier_3_minimal_data(self) -> None:
        """Test suggesting tier 3 for minimal data."""
        template = TierTemplate()
        char = {
            "name": "路人甲",
            "role": "路人",
            "description": "路人",
        }

        suggested = template.suggest_tier(char)
        assert suggested == 3

    def test_suggest_tier_name_only(self) -> None:
        """Test suggesting tier with only name."""
        template = TierTemplate()
        char = {"name": "路人乙"}

        suggested = template.suggest_tier(char)
        assert suggested in [0, 1, 2, 3]


class TestConstants:
    """Tests for module constants."""

    def test_tier_templates_structure(self) -> None:
        """Test TIER_TEMPLATES has correct structure."""
        assert len(TIER_TEMPLATES) == 4

        for tier in range(4):
            assert tier in TIER_TEMPLATES
            template = TIER_TEMPLATES[tier]
            assert "name" in template
            assert "description" in template
            assert "required_fields" in template
            assert "optional_fields" in template
            assert "token_budget" in template
            assert "has_cognitive_graph" in template

    def test_field_descriptions_exists(self) -> None:
        """Test FIELD_DESCRIPTIONS has entries."""
        assert "name" in FIELD_DESCRIPTIONS
        assert "bio" in FIELD_DESCRIPTIONS
        assert "personality" in FIELD_DESCRIPTIONS
        assert "mbti" in FIELD_DESCRIPTIONS
