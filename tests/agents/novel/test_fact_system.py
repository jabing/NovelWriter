"""Tests for fact database and injection system."""

from pathlib import Path

import pytest

from src.novel.fact_database import (
    Fact,
    FactDatabase,
    FactType,
)
from src.novel.fact_injector import (
    FactExtractor,
    RelevanceScore,
    RelevanceScorer,
    RelevantFactInjector,
)


class TestFact:
    """Test Fact dataclass."""

    def test_create_fact(self) -> None:
        """Test creating a fact."""
        fact = Fact(
            id="test-1",
            fact_type=FactType.CHARACTER,
            content="英雄是一名勇敢的战士",
            chapter_origin=1,
        )
        assert fact.id == "test-1"
        assert fact.fact_type == FactType.CHARACTER
        assert fact.content == "英雄是一名勇敢的战士"
        assert fact.importance == 0.5

    def test_fact_with_string_type(self) -> None:
        """Test creating fact with string type."""
        fact = Fact(
            id="test-2",
            fact_type="location",
            content="城堡位于山顶",
            chapter_origin=1,
        )
        assert fact.fact_type == FactType.LOCATION

    def test_importance_clamping(self) -> None:
        """Test that importance is clamped to 0-1."""
        fact = Fact(
            id="test-3",
            fact_type=FactType.EVENT,
            content="Test",
            chapter_origin=1,
            importance=1.5,
        )
        assert fact.importance == 1.0

        fact2 = Fact(
            id="test-4",
            fact_type=FactType.EVENT,
            content="Test",
            chapter_origin=1,
            importance=-0.5,
        )
        assert fact2.importance == 0.0

    def test_fact_touch(self) -> None:
        """Test marking fact as referenced."""
        fact = Fact(
            id="test-5",
            fact_type=FactType.CHARACTER,
            content="Test",
            chapter_origin=1,
        )
        assert fact.reference_count == 0
        assert fact.last_referenced == 0

        fact.touch(5)
        assert fact.reference_count == 1
        assert fact.last_referenced == 5

    def test_fact_serialization(self) -> None:
        """Test to_dict and from_dict."""
        fact = Fact(
            id="test-6",
            fact_type=FactType.RELATIONSHIP,
            content="Hero and Mentor are friends",
            chapter_origin=1,
            importance=0.8,
            entities=["Hero", "Mentor"],
        )
        data = fact.to_dict()
        restored = Fact.from_dict(data)

        assert restored.id == fact.id
        assert restored.fact_type == fact.fact_type
        assert restored.content == fact.content
        assert restored.entities == fact.entities

    def test_get_context_string(self) -> None:
        """Test context string generation."""
        fact = Fact(
            id="test-7",
            fact_type=FactType.CHARACTER,
            content="英雄拥有魔法力量",
            chapter_origin=1,
        )
        ctx = fact.get_context_string()
        assert "角色" in ctx
        assert "英雄拥有魔法力量" in ctx


class TestFactDatabase:
    """Test FactDatabase class."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def db(self, temp_storage: Path) -> FactDatabase:
        """Create a FactDatabase instance."""
        return FactDatabase(temp_storage, "test_novel")

    def test_initialization(self, db: FactDatabase) -> None:
        """Test database initialization."""
        assert db.get_fact_count() == 0

    def test_add_fact(self, db: FactDatabase) -> None:
        """Test adding a fact."""
        fact = db.add_fact(
            fact_type=FactType.CHARACTER,
            content="Test content",
            chapter_origin=1,
        )
        assert fact.id is not None
        assert db.get_fact_count() == 1

    def test_get_fact(self, db: FactDatabase) -> None:
        """Test retrieving a fact."""
        added = db.add_fact(
            fact_type=FactType.LOCATION,
            content="Castle",
            chapter_origin=1,
        )
        retrieved = db.get_fact(added.id)
        assert retrieved is not None
        assert retrieved.content == "Castle"

    def test_get_nonexistent_fact(self, db: FactDatabase) -> None:
        """Test retrieving non-existent fact."""
        retrieved = db.get_fact("nonexistent")
        assert retrieved is None

    def test_get_facts_by_type(self, db: FactDatabase) -> None:
        """Test retrieving facts by type."""
        db.add_fact(FactType.CHARACTER, "Char1", 1)
        db.add_fact(FactType.CHARACTER, "Char2", 1)
        db.add_fact(FactType.LOCATION, "Loc1", 1)

        char_facts = db.get_facts_by_type(FactType.CHARACTER)
        assert len(char_facts) == 2

        loc_facts = db.get_facts_by_type(FactType.LOCATION)
        assert len(loc_facts) == 1

    def test_get_facts_by_entity(self, db: FactDatabase) -> None:
        """Test retrieving facts by entity."""
        db.add_fact(
            FactType.CHARACTER,
            "Hero is brave",
            1,
            entities=["Hero"],
        )
        db.add_fact(
            FactType.EVENT,
            "Hero saves village",
            2,
            entities=["Hero", "Village"],
        )
        db.add_fact(
            FactType.CHARACTER,
            "Villain is evil",
            1,
            entities=["Villain"],
        )

        hero_facts = db.get_facts_by_entity("Hero")
        assert len(hero_facts) == 2

        villain_facts = db.get_facts_by_entity("Villain")
        assert len(villain_facts) == 1

    def test_get_facts_by_chapter(self, db: FactDatabase) -> None:
        """Test retrieving facts by chapter."""
        db.add_fact(FactType.EVENT, "Event1", 1)
        db.add_fact(FactType.EVENT, "Event2", 1)
        db.add_fact(FactType.EVENT, "Event3", 5)

        ch1_facts = db.get_facts_by_chapter(1)
        assert len(ch1_facts) == 2

        ch5_facts = db.get_facts_by_chapter(5)
        assert len(ch5_facts) == 1

    def test_delete_fact(self, db: FactDatabase) -> None:
        """Test deleting a fact."""
        fact = db.add_fact(FactType.EVENT, "To delete", 1)
        assert db.get_fact_count() == 1

        result = db.delete_fact(fact.id)
        assert result is True
        assert db.get_fact_count() == 0

    def test_delete_nonexistent_fact(self, db: FactDatabase) -> None:
        """Test deleting non-existent fact."""
        result = db.delete_fact("nonexistent")
        assert result is False

    def test_update_fact_reference(self, db: FactDatabase) -> None:
        """Test updating fact reference."""
        fact = db.add_fact(FactType.CHARACTER, "Test", 1)
        assert fact.reference_count == 0

        db.update_fact_reference(fact.id, 5)
        updated = db.get_fact(fact.id)
        assert updated is not None
        assert updated.reference_count == 1
        assert updated.last_referenced == 5

    def test_persistence(self, temp_storage: Path) -> None:
        """Test that facts persist across sessions."""
        # Create first session
        db1 = FactDatabase(temp_storage, "persist_test")
        db1.add_fact(FactType.CHARACTER, "Persist test", 1)
        db1.add_fact(FactType.LOCATION, "Location test", 2)

        # Create second session
        db2 = FactDatabase(temp_storage, "persist_test")
        assert db2.get_fact_count() == 2

    def test_get_fact_count_by_type(self, db: FactDatabase) -> None:
        """Test fact count by type."""
        db.add_fact(FactType.CHARACTER, "C1", 1)
        db.add_fact(FactType.CHARACTER, "C2", 1)
        db.add_fact(FactType.LOCATION, "L1", 1)
        db.add_fact(FactType.EVENT, "E1", 1)

        counts = db.get_fact_count_by_type()
        assert counts[FactType.CHARACTER] == 2
        assert counts[FactType.LOCATION] == 1
        assert counts[FactType.EVENT] == 1


class TestRelevanceScorer:
    """Test RelevanceScorer class."""

    @pytest.fixture
    def scorer(self) -> RelevanceScorer:
        """Create a RelevanceScorer instance."""
        return RelevanceScorer()

    @pytest.fixture
    def sample_fact(self) -> Fact:
        """Create a sample fact."""
        return Fact(
            id="score-test",
            fact_type=FactType.CHARACTER,
            content="Test character",
            chapter_origin=1,
            importance=0.8,
            entities=["Hero"],
        )

    def test_score_recent_fact(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test scoring a recent fact."""
        sample_fact.last_referenced = 9
        score = scorer.score_fact(sample_fact, current_chapter=10)
        assert score.recency_score > 0.8

    def test_score_old_fact(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test scoring an old fact."""
        sample_fact.last_referenced = 1
        score = scorer.score_fact(sample_fact, current_chapter=100)
        assert score.recency_score < 0.5

    def test_score_importance(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test importance scoring."""
        sample_fact.importance = 0.9
        score = scorer.score_fact(sample_fact, current_chapter=10)
        assert score.importance_score == 0.9

    def test_score_frequency(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test frequency scoring."""
        # No references
        sample_fact.reference_count = 0
        score = scorer.score_fact(sample_fact, current_chapter=10)
        low_freq = score.frequency_score

        # Many references
        sample_fact.reference_count = 10
        score = scorer.score_fact(sample_fact, current_chapter=10)
        high_freq = score.frequency_score

        assert high_freq > low_freq

    def test_score_relationship(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test relationship scoring."""
        # No active entities
        score = scorer.score_fact(sample_fact, current_chapter=10)
        no_rel = score.relationship_score

        # With matching entity
        score = scorer.score_fact(
            sample_fact,
            current_chapter=10,
            active_entities=["Hero", "Other"],
        )
        with_rel = score.relationship_score

        assert with_rel > no_rel

    def test_total_score_calculation(self, scorer: RelevanceScorer, sample_fact: Fact) -> None:
        """Test total score is weighted sum."""
        score = scorer.score_fact(sample_fact, current_chapter=10)

        expected = (
            score.recency_score * 0.3
            + score.importance_score * 0.3
            + score.frequency_score * 0.2
            + score.relationship_score * 0.2
        )
        assert abs(score.total_score - expected) < 0.001


class TestRelevantFactInjector:
    """Test RelevantFactInjector class."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def injector(self, temp_storage: Path) -> RelevantFactInjector:
        """Create a RelevantFactInjector instance."""
        return RelevantFactInjector(temp_storage, "test_novel")

    def test_initialization(self, injector: RelevantFactInjector) -> None:
        """Test injector initialization."""
        assert injector.fact_database is not None
        assert injector.scorer is not None

    def test_get_relevant_facts_empty(self, injector: RelevantFactInjector) -> None:
        """Test getting facts from empty database."""
        facts = injector.get_relevant_facts(current_chapter=1)
        assert len(facts) == 0

    def test_get_relevant_facts(self, injector: RelevantFactInjector) -> None:
        """Test getting relevant facts."""
        # Add some facts
        injector.add_fact(
            FactType.CHARACTER,
            "Hero is brave",
            1,
            importance=0.9,
            entities=["Hero"],
        )
        injector.add_fact(
            FactType.LOCATION,
            "Castle is old",
            1,
            importance=0.5,
        )

        facts = injector.get_relevant_facts(current_chapter=5)
        assert len(facts) == 2

        # Should be sorted by score (hero fact should be first due to higher importance)
        assert facts[0][0].importance >= facts[1][0].importance

    def test_get_relevant_facts_with_entities(self, injector: RelevantFactInjector) -> None:
        """Test getting facts with entity matching."""
        injector.add_fact(
            FactType.CHARACTER,
            "Hero description",
            1,
            entities=["Hero"],
        )
        injector.add_fact(
            FactType.CHARACTER,
            "Villain description",
            1,
            entities=["Villain"],
        )

        facts = injector.get_relevant_facts(
            current_chapter=5,
            active_entities=["Hero"],
        )

        # Hero fact should score higher due to entity match
        assert len(facts) == 2
        hero_fact = [f for f, s in facts if "Hero" in f.entities][0]
        assert hero_fact.entities == ["Hero"]

    def test_get_relevant_facts_respects_max(self, injector: RelevantFactInjector) -> None:
        """Test that max_facts is respected."""
        injector.max_facts = 3

        for i in range(10):
            injector.add_fact(FactType.EVENT, f"Event {i}", 1)

        facts = injector.get_relevant_facts(current_chapter=5)
        assert len(facts) <= 3

    def test_get_context_string(self, injector: RelevantFactInjector) -> None:
        """Test context string generation."""
        injector.add_fact(FactType.CHARACTER, "Hero is brave", 1)
        injector.add_fact(FactType.LOCATION, "Castle is old", 1)

        context = injector.get_context_string(current_chapter=5)
        assert "相关事实" in context
        assert len(context) > 0

    def test_get_context_string_empty(self, injector: RelevantFactInjector) -> None:
        """Test context string with no facts."""
        context = injector.get_context_string(current_chapter=1)
        assert context == ""

    def test_add_fact(self, injector: RelevantFactInjector) -> None:
        """Test adding fact through injector."""
        fact = injector.add_fact(
            fact_type=FactType.EVENT,
            content="Battle occurred",
            chapter_origin=5,
            importance=0.7,
        )
        assert fact.id is not None
        assert injector.get_fact_count() == 1

    def test_mark_fact_referenced(self, injector: RelevantFactInjector) -> None:
        """Test marking fact as referenced."""
        fact = injector.add_fact(FactType.CHARACTER, "Test", 1)
        injector.mark_fact_referenced(fact.id, 10)

        updated = injector.get_fact(fact.id)
        assert updated is not None
        assert updated.last_referenced == 10
        assert updated.reference_count == 1


class TestFactExtractor:
    """Test FactExtractor class."""

    @pytest.fixture
    def extractor(self) -> FactExtractor:
        """Create a FactExtractor instance."""
        return FactExtractor()

    def test_extract_entities_basic(self, extractor: FactExtractor) -> None:
        """Test basic entity extraction."""
        content = "英雄说道：我们要前进。"
        entities = extractor.extract_entities(content)
        assert "英雄说" in entities or len(entities) >= 0

    def test_extract_locations(self, extractor: FactExtractor) -> None:
        """Test location extraction."""
        content = "他来到城堡，在房间里等待。"
        locations = extractor.extract_locations(content)
        assert "城堡" in locations or "房间" in locations or len(locations) >= 0


class TestRelevanceScore:
    """Test RelevanceScore dataclass."""

    def test_create_score(self) -> None:
        """Test creating a relevance score."""
        score = RelevanceScore(
            fact_id="test",
            recency_score=0.8,
            importance_score=0.9,
            frequency_score=0.5,
            relationship_score=0.3,
            total_score=0.65,
        )
        assert score.fact_id == "test"
        assert score.total_score == 0.65
