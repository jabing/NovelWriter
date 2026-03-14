"""Unit tests for CharacterPromotion.

Tests cover:
- Promotion eligibility checks
- Demotion eligibility checks
- Tier transitions (promotion and demotion)
- Transition history tracking
- Template switching
"""

import pytest

from src.novel_agent.novel.character_promotion import (
    DEMOTION_RULES,
    PROMOTION_RULES,
    CharacterPromotion,
    DemotionCheckResult,
    PromotionCheckResult,
    TierTransition,
    TransitionType,
)


class TestCharacterPromotionBasics:
    """Basic tests for CharacterPromotion class."""

    def test_init(self) -> None:
        """Test initialization."""
        cp = CharacterPromotion()
        assert cp is not None

    def test_get_promotion_rules(self) -> None:
        """Test getting promotion rules."""
        cp = CharacterPromotion()
        rules = cp.get_promotion_rules()

        assert len(rules) == 3
        assert (3, 2) in rules
        assert (2, 1) in rules
        assert (1, 0) in rules

    def test_get_demotion_rules(self) -> None:
        """Test getting demotion rules."""
        cp = CharacterPromotion()
        rules = cp.get_demotion_rules()

        assert len(rules) == 3
        assert (0, 1) in rules
        assert (1, 2) in rules
        assert (2, 3) in rules

    def test_get_transition_rules(self) -> None:
        """Test getting all transition rules."""
        cp = CharacterPromotion()
        rules = cp.get_transition_rules()

        assert "promotion" in rules
        assert "demotion" in rules
        assert len(rules["promotion"]) == 3
        assert len(rules["demotion"]) == 3


class TestCheckPromotion:
    """Tests for promotion eligibility checking."""

    def test_check_promotion_tier_3_to_2_meets_requirements(self) -> None:
        """Test promotion from tier 3 to 2 with all requirements met."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 3}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=5,
            dialogue_count=3,
        )

        assert result.can_promote is True
        assert result.current_tier == 3
        assert result.target_tier == 2
        assert len(result.missing_requirements) == 0

    def test_check_promotion_tier_3_to_2_insufficient_appearances(self) -> None:
        """Test promotion from tier 3 to 2 with insufficient appearances."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 3}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=2,
            dialogue_count=3,
        )

        assert result.can_promote is False
        assert result.current_tier == 3
        assert result.target_tier is None
        assert len(result.missing_requirements) > 0

    def test_check_promotion_tier_3_to_2_insufficient_dialogues(self) -> None:
        """Test promotion from tier 3 to 2 with insufficient dialogues."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 3}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=5,
            dialogue_count=1,
        )

        assert result.can_promote is False
        assert len(result.missing_requirements) > 0

    def test_check_promotion_tier_2_to_1_meets_requirements(self) -> None:
        """Test promotion from tier 2 to 1 with all requirements met."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 2}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=6,
            plot_involvement=True,
        )

        assert result.can_promote is True
        assert result.current_tier == 2
        assert result.target_tier == 1

    def test_check_promotion_tier_2_to_1_missing_plot_involvement(self) -> None:
        """Test promotion from tier 2 to 1 without plot involvement."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 2}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=6,
            plot_involvement=False,
        )

        assert result.can_promote is False
        assert any("剧情" in req for req in result.missing_requirements)

    def test_check_promotion_tier_1_to_0_meets_requirements(self) -> None:
        """Test promotion from tier 1 to 0 with all requirements met."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 1}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=12,
            plot_central=True,
        )

        assert result.can_promote is True
        assert result.current_tier == 1
        assert result.target_tier == 0

    def test_check_promotion_tier_1_to_0_missing_plot_central(self) -> None:
        """Test promotion from tier 1 to 0 without being plot central."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 1}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=15,
            plot_central=False,
        )

        assert result.can_promote is False

    def test_check_promotion_tier_0_cannot_promote(self) -> None:
        """Test that tier 0 characters cannot be promoted."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 0}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=100,
        )

        assert result.can_promote is False
        assert "highest tier" in result.reason.lower() or "无法" in result.reason

    def test_check_promotion_default_tier(self) -> None:
        """Test promotion check with missing tier (defaults to 3)."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test"}

        result = cp.check_promotion(
            character_data=character_data,
            chapter_appearances=5,
            dialogue_count=3,
        )

        assert result.current_tier == 3


class TestCheckDemotion:
    """Tests for demotion eligibility checking."""

    def test_check_demotion_tier_0_to_1_meets_threshold(self) -> None:
        """Test demotion from tier 0 to 1 with sufficient absence."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 0}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=6,
        )

        assert result.should_demote is True
        assert result.current_tier == 0
        assert result.target_tier == 1

    def test_check_demotion_tier_0_to_1_insufficient_absence(self) -> None:
        """Test demotion from tier 0 to 1 with insufficient absence."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 0}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=3,
        )

        assert result.should_demote is False
        assert result.target_tier is None

    def test_check_demotion_tier_1_to_2_meets_threshold(self) -> None:
        """Test demotion from tier 1 to 2 with sufficient absence."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 1}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=4,
        )

        assert result.should_demote is True
        assert result.target_tier == 2

    def test_check_demotion_tier_2_to_3_meets_threshold(self) -> None:
        """Test demotion from tier 2 to 3 with sufficient absence."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 2}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=3,
        )

        assert result.should_demote is True
        assert result.target_tier == 3

    def test_check_demotion_tier_3_cannot_demote(self) -> None:
        """Test that tier 3 characters cannot be demoted."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test", "tier": 3}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=100,
        )

        assert result.should_demote is False
        assert "lowest tier" in result.reason.lower() or "无法" in result.reason

    def test_check_demotion_default_tier(self) -> None:
        """Test demotion check with missing tier (defaults to 3)."""
        cp = CharacterPromotion()
        character_data = {"id": "char1", "name": "Test"}

        result = cp.check_demotion(
            character_data=character_data,
            chapter_absence=10,
        )

        assert result.current_tier == 3
        assert result.should_demote is False


class TestPromote:
    """Tests for promotion execution."""

    def test_promote_tier_3_to_2(self) -> None:
        """Test executing promotion from tier 3 to 2."""
        cp = CharacterPromotion()

        result = cp.promote("char1", from_tier=3, to_tier=2)

        assert result["success"] is True
        assert result["character_id"] == "char1"
        assert result["from_tier"] == 3
        assert result["to_tier"] == 2

    def test_promote_tier_2_to_1(self) -> None:
        """Test executing promotion from tier 2 to 1."""
        cp = CharacterPromotion()

        result = cp.promote("char1", from_tier=2, to_tier=1)

        assert result["success"] is True
        assert result["to_tier"] == 1

    def test_promote_tier_1_to_0(self) -> None:
        """Test executing promotion from tier 1 to 0."""
        cp = CharacterPromotion()

        result = cp.promote("char1", from_tier=1, to_tier=0)

        assert result["success"] is True
        assert result["to_tier"] == 0

    def test_promote_with_reason(self) -> None:
        """Test promotion with custom reason."""
        cp = CharacterPromotion()

        result = cp.promote("char1", from_tier=2, to_tier=1, reason="剧情需要")

        assert result["success"] is True
        assert "剧情需要" in result["transition"]["reason"]

    def test_promote_invalid_direction(self) -> None:
        """Test promotion with wrong direction raises error."""
        cp = CharacterPromotion()

        with pytest.raises(ValueError) as exc_info:
            cp.promote("char1", from_tier=2, to_tier=3)
        assert "to_tier < from_tier" in str(exc_info.value)

    def test_promote_skip_tier(self) -> None:
        """Test promotion with skipped tier raises error."""
        cp = CharacterPromotion()

        with pytest.raises(ValueError) as exc_info:
            cp.promote("char1", from_tier=3, to_tier=1)
        assert "Cannot skip tiers" in str(exc_info.value)

    def test_promote_invalid_tier_range(self) -> None:
        """Test promotion with invalid tier raises error."""
        cp = CharacterPromotion()

        with pytest.raises(ValueError):
            cp.promote("char1", from_tier=-1, to_tier=0)

        with pytest.raises(ValueError):
            cp.promote("char1", from_tier=0, to_tier=4)

    def test_promote_records_history(self) -> None:
        """Test that promotion is recorded in history."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)

        history = cp.get_transition_history("char1")
        assert len(history) == 1
        assert history[0].transition_type == TransitionType.PROMOTION


class TestDemote:
    """Tests for demotion execution."""

    def test_demote_tier_0_to_1(self) -> None:
        """Test executing demotion from tier 0 to 1."""
        cp = CharacterPromotion()

        result = cp.demote("char1", from_tier=0, to_tier=1)

        assert result["success"] is True
        assert result["character_id"] == "char1"
        assert result["from_tier"] == 0
        assert result["to_tier"] == 1

    def test_demote_tier_1_to_2(self) -> None:
        """Test executing demotion from tier 1 to 2."""
        cp = CharacterPromotion()

        result = cp.demote("char1", from_tier=1, to_tier=2)

        assert result["success"] is True
        assert result["to_tier"] == 2

    def test_demote_tier_2_to_3(self) -> None:
        """Test executing demotion from tier 2 to 3."""
        cp = CharacterPromotion()

        result = cp.demote("char1", from_tier=2, to_tier=3)

        assert result["success"] is True
        assert result["to_tier"] == 3

    def test_demote_with_reason(self) -> None:
        """Test demotion with custom reason."""
        cp = CharacterPromotion()

        result = cp.demote("char1", from_tier=1, to_tier=2, reason="长期缺席")

        assert result["success"] is True
        assert "长期缺席" in result["transition"]["reason"]

    def test_demote_invalid_direction(self) -> None:
        """Test demotion with wrong direction raises error."""
        cp = CharacterPromotion()

        with pytest.raises(ValueError) as exc_info:
            cp.demote("char1", from_tier=2, to_tier=1)
        assert "to_tier > from_tier" in str(exc_info.value)

    def test_demote_skip_tier(self) -> None:
        """Test demotion with skipped tier raises error."""
        cp = CharacterPromotion()

        with pytest.raises(ValueError) as exc_info:
            cp.demote("char1", from_tier=0, to_tier=2)
        assert "Cannot skip tiers" in str(exc_info.value)

    def test_demote_records_history(self) -> None:
        """Test that demotion is recorded in history."""
        cp = CharacterPromotion()
        cp.demote("char1", from_tier=1, to_tier=2)

        history = cp.get_transition_history("char1")
        assert len(history) == 1
        assert history[0].transition_type == TransitionType.DEMOTION


class TestTemplateSwitch:
    """Tests for template switching."""

    def test_apply_template_switch_tier_0(self) -> None:
        """Test applying template for tier 0."""
        cp = CharacterPromotion()

        result = cp.apply_template_switch("char1", 0)

        assert result["success"] is True
        assert result["new_tier"] == 0
        assert result["token_budget"] == 500
        assert result["has_cognitive_graph"] is True

    def test_apply_template_switch_tier_1(self) -> None:
        """Test applying template for tier 1."""
        cp = CharacterPromotion()

        result = cp.apply_template_switch("char1", 1)

        assert result["success"] is True
        assert result["token_budget"] == 300

    def test_apply_template_switch_tier_2(self) -> None:
        """Test applying template for tier 2."""
        cp = CharacterPromotion()

        result = cp.apply_template_switch("char1", 2)

        assert result["success"] is True
        assert result["token_budget"] == 100

    def test_apply_template_switch_tier_3(self) -> None:
        """Test applying template for tier 3."""
        cp = CharacterPromotion()

        result = cp.apply_template_switch("char1", 3)

        assert result["success"] is True
        assert result["token_budget"] == 0
        assert result["has_cognitive_graph"] is False

    def test_apply_template_switch_invalid_tier(self) -> None:
        """Test applying template for invalid tier."""
        cp = CharacterPromotion()

        result = cp.apply_template_switch("char1", 5)

        assert result["success"] is False
        assert "error" in result


class TestTransitionHistory:
    """Tests for transition history tracking."""

    def test_get_transition_history_empty(self) -> None:
        """Test getting history when empty."""
        cp = CharacterPromotion()

        history = cp.get_transition_history()
        assert history == []

    def test_get_transition_history_by_character(self) -> None:
        """Test getting history for specific character."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.promote("char2", from_tier=2, to_tier=1)

        history_char1 = cp.get_transition_history("char1")
        history_char2 = cp.get_transition_history("char2")

        assert len(history_char1) == 1
        assert len(history_char2) == 1
        assert history_char1[0].character_id == "char1"

    def test_get_transition_history_limit(self) -> None:
        """Test history limit parameter."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.promote("char1", from_tier=2, to_tier=1)
        cp.promote("char1", from_tier=1, to_tier=0)

        history = cp.get_transition_history(limit=2)
        assert len(history) == 2

    def test_get_character_tier_history(self) -> None:
        """Test getting complete tier history for a character."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.demote("char1", from_tier=2, to_tier=3)

        history = cp.get_character_tier_history("char1")

        assert len(history) == 2

    def test_clear_history(self) -> None:
        """Test clearing history."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.demote("char2", from_tier=1, to_tier=2)

        count = cp.clear_history()

        assert count == 2
        assert len(cp.get_transition_history()) == 0


class TestStatistics:
    """Tests for transition statistics."""

    def test_get_statistics_empty(self) -> None:
        """Test statistics when no transitions."""
        cp = CharacterPromotion()

        stats = cp.get_statistics()

        assert stats["total_transitions"] == 0
        assert stats["promotions"] == 0
        assert stats["demotions"] == 0

    def test_get_statistics_with_transitions(self) -> None:
        """Test statistics with transitions."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.promote("char2", from_tier=2, to_tier=1)
        cp.demote("char3", from_tier=0, to_tier=1)

        stats = cp.get_statistics()

        assert stats["total_transitions"] == 3
        assert stats["promotions"] == 2
        assert stats["demotions"] == 1
        assert stats["unique_characters"] == 3

    def test_get_statistics_multiple_transitions_same_character(self) -> None:
        """Test statistics for character with multiple transitions."""
        cp = CharacterPromotion()
        cp.promote("char1", from_tier=3, to_tier=2)
        cp.demote("char1", from_tier=2, to_tier=3)

        stats = cp.get_statistics()

        assert stats["unique_characters"] == 1
        assert stats["characters_with_multiple_transitions"] == 1


class TestTierTransition:
    """Tests for TierTransition dataclass."""

    def test_transition_creation(self) -> None:
        """Test creating a transition."""
        transition = TierTransition(
            character_id="char1",
            from_tier=3,
            to_tier=2,
            transition_type=TransitionType.PROMOTION,
        )

        assert transition.character_id == "char1"
        assert transition.from_tier == 3
        assert transition.to_tier == 2

    def test_transition_type_auto_detection_promotion(self) -> None:
        """Test that promotion type is auto-detected."""
        transition = TierTransition(
            character_id="char1",
            from_tier=2,
            to_tier=1,
            transition_type=TransitionType.INVALID,
        )

        assert transition.transition_type == TransitionType.PROMOTION

    def test_transition_type_auto_detection_demotion(self) -> None:
        """Test that demotion type is auto-detected."""
        transition = TierTransition(
            character_id="char1",
            from_tier=1,
            to_tier=2,
            transition_type=TransitionType.INVALID,
        )

        assert transition.transition_type == TransitionType.DEMOTION

    def test_transition_to_dict(self) -> None:
        """Test converting transition to dictionary."""
        transition = TierTransition(
            character_id="char1",
            from_tier=3,
            to_tier=2,
            transition_type=TransitionType.PROMOTION,
            reason="Test promotion",
        )

        data = transition.to_dict()

        assert data["character_id"] == "char1"
        assert data["from_tier"] == 3
        assert data["to_tier"] == 2
        assert data["transition_type"] == "promotion"
        assert data["reason"] == "Test promotion"

    def test_transition_from_dict(self) -> None:
        """Test creating transition from dictionary."""
        data = {
            "character_id": "char1",
            "from_tier": 2,
            "to_tier": 1,
            "transition_type": "promotion",
            "reason": "Test",
            "metadata": {"key": "value"},
        }

        transition = TierTransition.from_dict(data)

        assert transition.character_id == "char1"
        assert transition.from_tier == 2
        assert transition.to_tier == 1


class TestPromotionCheckResult:
    """Tests for PromotionCheckResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a promotion check result."""
        result = PromotionCheckResult(
            can_promote=True,
            current_tier=3,
            target_tier=2,
            met_requirements=["出场次数: 5/3"],
            reason="满足晋升条件",
        )

        assert result.can_promote is True
        assert result.target_tier == 2


class TestDemotionCheckResult:
    """Tests for DemotionCheckResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a demotion check result."""
        result = DemotionCheckResult(
            should_demote=True,
            current_tier=0,
            target_tier=1,
            reason="连续缺席6章",
        )

        assert result.should_demote is True
        assert result.target_tier == 1


class TestConstants:
    """Tests for module constants."""

    def test_promotion_rules_structure(self) -> None:
        """Test PROMOTION_RULES has correct structure."""
        assert len(PROMOTION_RULES) == 3

        for key, rule in PROMOTION_RULES.items():
            assert len(key) == 2
            assert key[0] > key[1]  # Promotion: from > to
            assert "min_appearances" in rule
            assert "description" in rule

    def test_demotion_rules_structure(self) -> None:
        """Test DEMOTION_RULES has correct structure."""
        assert len(DEMOTION_RULES) == 3

        for key, rule in DEMOTION_RULES.items():
            assert len(key) == 2
            assert key[0] < key[1]  # Demotion: from < to
            assert "absent_chapters" in rule
            assert "description" in rule

    def test_promotion_rules_tier_sequence(self) -> None:
        """Test promotion rules cover correct tier transitions."""
        assert (3, 2) in PROMOTION_RULES
        assert (2, 1) in PROMOTION_RULES
        assert (1, 0) in PROMOTION_RULES

    def test_demotion_rules_tier_sequence(self) -> None:
        """Test demotion rules cover correct tier transitions."""
        assert (0, 1) in DEMOTION_RULES
        assert (1, 2) in DEMOTION_RULES
        assert (2, 3) in DEMOTION_RULES
