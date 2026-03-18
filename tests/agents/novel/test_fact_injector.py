"""Tests for continuity enhancement features in fact injection system.

Tests cover:
- ProtectedFactCategory enum (5 categories)
- Dynamic max_facts calculation
- Scoring weights validation
- Protected slot reservation logic
"""

from pathlib import Path

import pytest

from src.novel_agent.novel.fact_database import ProtectedFactCategory
from src.novel_agent.novel.fact_injector import (
    RelevanceScorer,
    RelevantFactInjector,
    calculate_max_facts,
)

PROTECTED_SLOTS = RelevantFactInjector.PROTECTED_SLOTS


class TestProtectedFactCategory:
    """Test ProtectedFactCategory enum."""

    def test_immutable_category_exists(self) -> None:
        """Test IMMUTABLE category exists."""
        assert hasattr(ProtectedFactCategory, "IMMUTABLE")
        assert ProtectedFactCategory.IMMUTABLE.value == "immutable"

    def test_secret_category_exists(self) -> None:
        """Test SECRET category exists."""
        assert hasattr(ProtectedFactCategory, "SECRET")
        assert ProtectedFactCategory.SECRET.value == "secret"

    def test_promise_category_exists(self) -> None:
        """Test PROMISE category exists."""
        assert hasattr(ProtectedFactCategory, "PROMISE")
        assert ProtectedFactCategory.PROMISE.value == "promise"

    def test_world_rule_category_exists(self) -> None:
        """Test WORLD_RULE category exists."""
        assert hasattr(ProtectedFactCategory, "WORLD_RULE")
        assert ProtectedFactCategory.WORLD_RULE.value == "world_rule"

    def test_foreshadow_category_exists(self) -> None:
        """Test FORESHADOW category exists."""
        assert hasattr(ProtectedFactCategory, "FORESHADOW")
        assert ProtectedFactCategory.FORESHADOW.value == "foreshadow"

    def test_all_categories_exist(self) -> None:
        """Test all 5 categories exist."""
        categories = list(ProtectedFactCategory)
        assert len(categories) == 5
        category_names = {c.value for c in categories}
        expected = {"immutable", "secret", "promise", "world_rule", "foreshadow"}
        assert category_names == expected

    def test_category_iteration(self) -> None:
        """Test category iteration order."""
        categories = list(ProtectedFactCategory)
        category_values = [c.value for c in categories]
        assert "immutable" in category_values
        assert "secret" in category_values
        assert "promise" in category_values
        assert "world_rule" in category_values
        assert "foreshadow" in category_values


class TestCalculateMaxFacts:
    """Test calculate_max_facts function."""

    def test_minIMUM_limit(self) -> None:
        """Test that minimum is 30 facts."""
        # 10 chapters * 1.5 = 15, but minimum is 30
        assert calculate_max_facts(10) == 30
        # 5 chapters * 1.5 = 7.5, but minimum is 30
        assert calculate_max_facts(5) == 30
        # 1 chapter * 1.5 = 1.5, but minimum is 30
        assert calculate_max_facts(1) == 30

    def test_maximum_limit(self) -> None:
        """Test that maximum is 50 facts."""
        # 100 chapters * 1.5 = 150, but maximum is 50
        assert calculate_max_facts(100) == 50
        # 200 chapters * 1.5 = 300, but maximum is 50
        assert calculate_max_facts(200) == 50
        # 500 chapters * 1.5 = 750, but maximum is 50
        assert calculate_max_facts(500) == 50

    def test_normal_range_calculation(self) -> None:
        """Test normal range calculation (30-50 facts)."""
        # 20 chapters * 1.5 = 30
        assert calculate_max_facts(20) == 30
        # 30 chapters * 1.5 = 45
        assert calculate_max_facts(30) == 45
        # 33 chapters * 1.5 = 49.5 -> 49
        assert calculate_max_facts(33) == 49
        # 34 chapters * 1.5 = 51, but capped at 50
        assert calculate_max_facts(34) == 50

    def test_exact_values_from_spec(self) -> None:
        """Test exact values from specification."""
        # 30 chapters -> 45 facts
        assert calculate_max_facts(30) == 45
        # 10 chapters -> 30 facts (minimum)
        assert calculate_max_facts(10) == 30
        # 100 chapters -> 50 facts (maximum)
        assert calculate_max_facts(100) == 50


class TestScoringWeights:
    """Test RelevanceScorer weights."""

    def test_weights_sum_to_one(self) -> None:
        """Test that weights sum to 1.0."""
        scorer = RelevanceScorer()
        total = sum(scorer.WEIGHTS.values())
        assert abs(total - 1.0) < 0.0001, f"Weights sum to {total}, not 1.0"

    def test_correct_recency_weight(self) -> None:
        """Test recency weight is 0.15."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["recency"] == 0.15

    def test_correct_importance_weight(self) -> None:
        """Test importance weight is 0.20."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["importance"] == 0.20

    def test_correct_narrative_significance_weight(self) -> None:
        """Test narrative_significance weight is 0.25."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["narrative_significance"] == 0.25

    def test_correct_frequency_weight(self) -> None:
        """Test frequency weight is 0.10."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["frequency"] == 0.10

    def test_correct_relationship_weight(self) -> None:
        """Test relationship weight is 0.15."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["relationship"] == 0.15

    def test_correct_debt_urgency_weight(self) -> None:
        """Test debt_urgency weight is 0.15."""
        scorer = RelevanceScorer()
        assert scorer.WEIGHTS["debt_urgency"] == 0.15

    def test_all_weight_keys_present(self) -> None:
        """Test all expected weight keys are present."""
        scorer = RelevanceScorer()
        expected_keys = {
            "recency",
            "importance",
            "narrative_significance",
            "frequency",
            "relationship",
            "debt_urgency",
        }
        actual_keys = set(scorer.WEIGHTS.keys())
        assert actual_keys == expected_keys

    def test_custom_weights_sum_to_one(self) -> None:
        """Test custom weights also sum to 1.0."""
        scorer = RelevanceScorer(
            recency_weight=0.10,
            importance_weight=0.25,
            narrative_significance_weight=0.20,
            frequency_weight=0.15,
            relationship_weight=0.20,
            debt_urgency_weight=0.10,
        )
        total = sum(scorer.WEIGHTS.values())
        assert abs(total - 1.0) < 0.0001, f"Custom weights sum to {total}, not 1.0"


class TestProtectedSlotReservation:
    """Test PROTECTED_SLOTS reservation logic."""

    def test_all_categories_have_protected_slots(self) -> None:
        """Test all categories have protected slots defined."""
        categories = list(ProtectedFactCategory)
        for category in categories:
            assert category in PROTECTED_SLOTS, f"Missing protected slots for {category}"

    def test_immutable_protected_slots(self) -> None:
        """Test IMMUTABLE has 3 protected slots."""
        assert PROTECTED_SLOTS[ProtectedFactCategory.IMMUTABLE] == 3

    def test_secret_protected_slots(self) -> None:
        """Test SECRET has 3 protected slots."""
        assert PROTECTED_SLOTS[ProtectedFactCategory.SECRET] == 3

    def test_promise_protected_slots(self) -> None:
        """Test PROMISE has 3 protected slots."""
        assert PROTECTED_SLOTS[ProtectedFactCategory.PROMISE] == 3

    def test_world_rule_protected_slots(self) -> None:
        """Test WORLD_RULE has 2 protected slots."""
        assert PROTECTED_SLOTS[ProtectedFactCategory.WORLD_RULE] == 2

    def test_foreshadow_protected_slots(self) -> None:
        """Test FORESHADOW has 3 protected slots."""
        assert PROTECTED_SLOTS[ProtectedFactCategory.FORESHADOW] == 3

    def test_total_protected_slots(self) -> None:
        """Test total protected slots equals 14."""
        total = sum(PROTECTED_SLOTS.values())
        assert total == 14, f"Total protected slots is {total}, expected 14"

    def test_protected_slots_do_not_exceed_maximum(self) -> None:
        """Test protected slots don't exceed 50% of max facts (50)."""
        max_facts = 50
        half_max = max_facts * 0.5
        total_protected = sum(PROTECTED_SLOTS.values())
        assert total_protected <= half_max, (
            f"Protected slots ({total_protected}) exceed 50% of max ({half_max})"
        )

    def test_protected_slots_dict_keys_match_categories(self) -> None:
        """Test PROTECTED_SLOTS keys match ProtectedFactCategory enum."""
        categories = set(c.value for c in ProtectedFactCategory)
        slot_keys = set(PROTECTED_SLOTS.keys())
        # PROTECTED_SLOTS uses enum keys directly
        assert slot_keys == set(ProtectedFactCategory)


class TestRelevanceScorerIntegration:
    """Integration tests for relevance scoring with weights."""

    @pytest.fixture
    def scorer(self) -> RelevanceScorer:
        """Create a RelevanceScorer instance."""
        return RelevanceScorer()

    def test_weighted_score_calculation(self, scorer: RelevanceScorer) -> None:
        """Test total score is correctly calculated from weighted components."""
        from src.novel_agent.novel.fact_database import Fact, FactType

        fact = Fact(
            id="test-score",
            fact_type=FactType.CHARACTER,
            content="Test character",
            chapter_origin=1,
            importance=0.6,
            reference_count=5,
            entities=["Hero"],
        )

        score = scorer.score_fact(
            fact=fact,
            current_chapter=10,
            active_entities=["Hero"],
            narrative_significance=0.7,
            debt_urgency=0.4,
        )

        # Verify total_score is weighted sum
        expected = (
            score.recency_score * 0.15
            + score.importance_score * 0.20
            + score.narrative_significance_score * 0.25
            + score.frequency_score * 0.10
            + score.relationship_score * 0.15
            + score.debt_urgency_score * 0.15
        )
        assert abs(score.total_score - expected) < 0.0001, (
            f"Score mismatch: {score.total_score} vs {expected}"
        )

    def test_relevance_scorer_weight_access(self, scorer: RelevanceScorer) -> None:
        """Test that RelevanceScorer.WEIGHTS is accessible."""
        assert "recency" in scorer.WEIGHTS
        assert "importance" in scorer.WEIGHTS
        assert "narrative_significance" in scorer.WEIGHTS
        assert "frequency" in scorer.WEIGHTS
        assert "relationship" in scorer.WEIGHTS
        assert "debt_urgency" in scorer.WEIGHTS


class TestRelevantFactInjectorWithProtectedSlots:
    """Integration tests for RelevantFactInjector with protected slots."""

    @pytest.fixture
    def temp_storage(self, tmp_path) -> Path:
        """Create temporary storage directory."""
        from pathlib import Path

        return tmp_path / "novels"

    def test_injector_has_protected_slots(self, temp_storage) -> None:
        """Test injector has PROTECTED_SLOTS defined."""
        injector = RelevantFactInjector(temp_storage, "test_novel")
        assert hasattr(injector, "PROTECTED_SLOTS")
        assert len(injector.PROTECTED_SLOTS) == 5

    def test_injector_protected_slots_match_constants(self, temp_storage) -> None:
        """Test injector PROTECTED_SLOTS matches module constant."""
        injector = RelevantFactInjector(temp_storage, "test_novel")
        assert injector.PROTECTED_SLOTS == PROTECTED_SLOTS
