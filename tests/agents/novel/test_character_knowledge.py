"""Tests for CharacterKnowledge class."""

import pytest

from src.novel_agent.novel.character_knowledge import (
    CharacterKnowledge,
    CognitiveConflict,
    KnowledgeEntry,
    KnowledgeSource,
)
from src.novel_agent.novel.cognitive_graph import CognitiveGraph


class TestKnowledgeSource:
    """Test KnowledgeSource enum."""

    def test_source_values(self) -> None:
        """Test that source enum has expected values."""
        assert KnowledgeSource.DIRECT.value == "direct"
        assert KnowledgeSource.HEARSAY.value == "hearsay"
        assert KnowledgeSource.INFERENCE.value == "inference"
        assert KnowledgeSource.DISCOVERY.value == "discovery"


class TestKnowledgeEntry:
    """Test KnowledgeEntry dataclass."""

    def test_entry_creation(self) -> None:
        """Test creating a knowledge entry."""
        entry = KnowledgeEntry(
            fact_id="fact1",
            learned_chapter=3,
            source=KnowledgeSource.HEARSAY,
            confidence=0.8,
            context="从仆人那里听说",
        )

        assert entry.fact_id == "fact1"
        assert entry.learned_chapter == 3
        assert entry.source == KnowledgeSource.HEARSAY
        assert entry.confidence == 0.8
        assert entry.context == "从仆人那里听说"

    def test_entry_to_dict(self) -> None:
        """Test converting entry to dictionary."""
        entry = KnowledgeEntry(
            fact_id="fact1",
            learned_chapter=3,
            source=KnowledgeSource.DIRECT,
            confidence=1.0,
        )

        result = entry.to_dict()

        assert result["fact_id"] == "fact1"
        assert result["learned_chapter"] == 3
        assert result["source"] == "direct"
        assert result["confidence"] == 1.0
        assert result["context"] == ""


class TestCognitiveConflict:
    """Test CognitiveConflict dataclass."""

    def test_conflict_creation(self) -> None:
        """Test creating a cognitive conflict."""
        conflict = CognitiveConflict(
            fact_id="fact1",
            fact_content="丞相私通敌国",
            conflict_type="unknown_knowledge",
            description="Character doesn't know this fact",
            chapter=5,
            action_description="林晚质问丞相私通敌国的事",
        )

        assert conflict.fact_id == "fact1"
        assert conflict.conflict_type == "unknown_knowledge"

    def test_conflict_to_dict(self) -> None:
        """Test converting conflict to dictionary."""
        conflict = CognitiveConflict(
            fact_id="fact1",
            fact_content="test content",
            conflict_type="insufficient_confidence",
            description="test description",
            chapter=3,
            action_description="test action",
        )

        result = conflict.to_dict()

        assert result["fact_id"] == "fact1"
        assert result["conflict_type"] == "insufficient_confidence"
        assert result["chapter"] == 3


class TestCharacterKnowledgeInit:
    """Test CharacterKnowledge initialization."""

    def test_init_with_graph(self) -> None:
        """Test initialization with provided graph."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)

        ck = CharacterKnowledge("char1", graph)

        assert ck.character_id == "char1"
        assert ck.graph is graph
        assert ck.fact_count == 0

    def test_init_without_graph(self) -> None:
        """Test initialization without provided graph."""
        ck = CharacterKnowledge("char2")

        assert ck.character_id == "char2"
        assert ck.graph is not None
        assert isinstance(ck.graph, CognitiveGraph)

    def test_init_sets_tier_from_graph(self) -> None:
        """Test that tier is set from graph if character exists."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)

        ck = CharacterKnowledge("char1", graph)

        scope = ck.get_knowledge_scope()
        assert scope["tier"] == 0


class TestCharacterKnowledgeLearning:
    """Test learning and forgetting facts."""

    @pytest.fixture
    def setup(self) -> tuple[CognitiveGraph, CharacterKnowledge]:
        """Create graph and character knowledge for tests."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="丞相私通敌国",
            source_character="char2",
            chapter=3,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="林晚参加宴会",
            source_character="char1",
            chapter=1,
        )
        ck = CharacterKnowledge("char1", graph)
        return graph, ck

    def test_learn_fact_basic(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test learning a fact."""
        graph, ck = setup

        result = ck.learn_fact("fact1", chapter=5, source="hearsay", confidence=0.7)

        assert result is True
        assert ck.knows_fact("fact1")
        assert ck.fact_count == 1

    def test_learn_fact_nonexistent(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test learning a non-existent fact."""
        _, ck = setup

        result = ck.learn_fact("nonexistent_fact")

        assert result is False
        assert ck.fact_count == 0

    def test_learn_fact_updates_graph(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test that learning updates the graph."""
        graph, ck = setup

        ck.learn_fact("fact1", chapter=5, source="direct")

        knowledge = graph.get_character_knowledge("char1")
        assert len(knowledge) == 1
        assert knowledge[0][0]["id"] == "fact1"

    def test_learn_fact_default_values(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test learning with default values."""
        _, ck = setup

        ck.learn_fact("fact1", chapter=3)

        entry = ck.get_fact_learning_info("fact1")
        assert entry is not None
        assert entry.source == KnowledgeSource.DIRECT
        assert entry.confidence == 1.0

    def test_forget_fact(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test forgetting a fact."""
        _, ck = setup

        ck.learn_fact("fact1", chapter=5)
        assert ck.knows_fact("fact1")

        result = ck.forget_fact("fact1")

        assert result is True
        assert not ck.knows_fact("fact1")
        assert ck.fact_count == 0

    def test_forget_fact_not_known(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test forgetting a fact that wasn't known."""
        _, ck = setup

        result = ck.forget_fact("fact1")

        assert result is False

    def test_forget_fact_multiple_times(self, setup: tuple[CognitiveGraph, CharacterKnowledge]) -> None:
        """Test forgetting the same fact multiple times."""
        _, ck = setup

        ck.learn_fact("fact1", chapter=5)
        ck.forget_fact("fact1")
        result = ck.forget_fact("fact1")

        assert result is False


class TestCharacterKnowledgeQuery:
    """Test knowledge queries."""

    @pytest.fixture
    def setup(self) -> CharacterKnowledge:
        """Create character knowledge with some facts."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="丞相私通敌国",
            source_character="char2",
            chapter=2,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="林晚参加宴会",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact3",
            fact_type="secret",
            content="公主的隐藏身份",
            source_character="char3",
            chapter=4,
        )
        ck = CharacterKnowledge("char1", graph)
        ck.learn_fact("fact1", chapter=5, source="hearsay")
        ck.learn_fact("fact2", chapter=1, source="direct")
        ck.learn_fact("fact3", chapter=6, source="discovery")
        return ck

    def test_knows_fact_true(self, setup: CharacterKnowledge) -> None:
        """Test checking if fact is known."""
        assert setup.knows_fact("fact1") is True
        assert setup.knows_fact("fact2") is True

    def test_knows_fact_false(self, setup: CharacterKnowledge) -> None:
        """Test checking if unknown fact is known."""
        assert setup.knows_fact("nonexistent") is False

    def test_knows_fact_by_chapter(self, setup: CharacterKnowledge) -> None:
        """Test checking if fact is known by a specific chapter."""
        assert setup.knows_fact("fact1", chapter=5) is True
        assert setup.knows_fact("fact1", chapter=4) is False

    def test_get_knowledge(self, setup: CharacterKnowledge) -> None:
        """Test getting all knowledge."""
        knowledge = setup.get_knowledge()

        assert len(knowledge) == 3
        fact_ids = [k["id"] for k in knowledge]
        assert "fact1" in fact_ids
        assert "fact2" in fact_ids
        assert "fact3" in fact_ids

    def test_get_knowledge_by_chapter(self, setup: CharacterKnowledge) -> None:
        """Test getting knowledge as of a specific chapter."""
        knowledge = setup.get_knowledge(chapter=5)

        assert len(knowledge) == 2
        fact_ids = [k["id"] for k in knowledge]
        assert "fact1" in fact_ids
        assert "fact2" in fact_ids
        assert "fact3" not in fact_ids

    def test_get_knowledge_by_type(self, setup: CharacterKnowledge) -> None:
        """Test filtering knowledge by type."""
        secrets = setup.get_knowledge_by_type("secret")
        events = setup.get_knowledge_by_type("event")

        assert len(secrets) == 2
        assert len(events) == 1

    def test_get_fact_learning_info(self, setup: CharacterKnowledge) -> None:
        """Test getting learning info for a fact."""
        info = setup.get_fact_learning_info("fact1")

        assert info is not None
        assert info.fact_id == "fact1"
        assert info.learned_chapter == 5
        assert info.source == KnowledgeSource.HEARSAY

    def test_get_fact_learning_info_unknown(self, setup: CharacterKnowledge) -> None:
        """Test getting learning info for unknown fact."""
        info = setup.get_fact_learning_info("nonexistent")

        assert info is None

    def test_get_knowledge_summary(self, setup: CharacterKnowledge) -> None:
        """Test getting knowledge summary."""
        summary = setup.get_knowledge_summary()

        assert summary["total_facts"] == 3
        assert summary["by_type"]["secret"] == 2
        assert summary["by_type"]["event"] == 1
        assert summary["by_source"]["hearsay"] == 1
        assert summary["by_source"]["direct"] == 1
        assert summary["by_source"]["discovery"] == 1


class TestCognitiveConflictDetection:
    """Test cognitive conflict detection."""

    @pytest.fixture
    def setup(self) -> CharacterKnowledge:
        """Create character knowledge for conflict tests."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="丞相私通敌国",
            source_character="char2",
            chapter=3,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="secret",
            content="公主是刺客",
            source_character="char3",
            chapter=4,
        )
        ck = CharacterKnowledge("char1", graph)
        ck.learn_fact("fact1", chapter=5, source="hearsay", confidence=0.8)
        return ck

    def test_no_conflict_when_knowledge_exists(self, setup: CharacterKnowledge) -> None:
        """Test no conflict when character has knowledge."""
        conflicts = setup.check_cognitive_conflict(
            "林晚质问丞相私通敌国", chapter=5
        )

        assert len(conflicts) == 0

    def test_conflict_when_knowledge_not_yet_learned(
        self, setup: CharacterKnowledge
    ) -> None:
        """Test conflict when action is before learning."""
        conflicts = setup.check_cognitive_conflict(
            "林晚质问丞相私通敌国", chapter=4
        )

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "unknown_knowledge"
        assert conflicts[0].fact_id == "fact1"

    def test_conflict_when_knowledge_unknown(self, setup: CharacterKnowledge) -> None:
        """Test conflict when character doesn't know the fact at all."""
        conflicts = setup.check_cognitive_conflict(
            "林晚质问公主是刺客", chapter=5
        )

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "unknown_knowledge"
        assert conflicts[0].fact_id == "fact2"

    def test_no_conflict_for_unrelated_action(self, setup: CharacterKnowledge) -> None:
        """Test no conflict for action unrelated to known facts."""
        conflicts = setup.check_cognitive_conflict(
            "林晚在街上行走", chapter=3
        )

        assert len(conflicts) == 0

    def test_conflict_with_low_confidence_hearsay(
        self, setup: CharacterKnowledge
    ) -> None:
        """Test conflict when hearsay has low confidence."""
        setup.learn_fact("fact2", chapter=4, source="hearsay", confidence=0.3)

        conflicts = setup.check_cognitive_conflict(
            "林晚直接质问公主是刺客", chapter=5
        )

        assert any(c.conflict_type == "insufficient_confidence" for c in conflicts)


class TestUpdateFromChapter:
    """Test updating knowledge from chapter content."""

    @pytest.fixture
    def setup(self) -> CharacterKnowledge:
        """Create character knowledge for chapter update tests."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="event",
            content="林晚参加宴会",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="secret",
            content="丞相的秘密计划",
            source_character="char2",
            chapter=2,
        )
        graph.add_fact_node(
            "fact3",
            fact_type="event",
            content="边境发生战斗",
            source_character="char3",
            chapter=3,
        )
        return CharacterKnowledge("char1", graph)

    def test_update_with_witnessed_facts(self, setup: CharacterKnowledge) -> None:
        """Test updating with facts the character witnessed."""
        facts = [
            {
                "fact_id": "fact1",
                "how_learned": "witnessed",
            }
        ]

        count = setup.update_from_chapter(1, facts)

        assert count == 1
        assert setup.knows_fact("fact1")
        info = setup.get_fact_learning_info("fact1")
        assert info is not None
        assert info.source == KnowledgeSource.DIRECT

    def test_update_with_character_present(self, setup: CharacterKnowledge) -> None:
        """Test updating with facts where character was present."""
        facts = [
            {
                "fact_id": "fact1",
                "character_present": True,
            }
        ]

        count = setup.update_from_chapter(1, facts)

        assert count == 1
        info = setup.get_fact_learning_info("fact1")
        assert info is not None
        assert info.source == KnowledgeSource.DIRECT

    def test_update_with_told_by(self, setup: CharacterKnowledge) -> None:
        """Test updating with facts told to character."""
        facts = [
            {
                "fact_id": "fact2",
                "told_by": "char3",
            }
        ]

        count = setup.update_from_chapter(2, facts)

        assert count == 1
        info = setup.get_fact_learning_info("fact2")
        assert info is not None
        assert info.source == KnowledgeSource.HEARSAY
        assert info.confidence == 0.7

    def test_update_with_inference(self, setup: CharacterKnowledge) -> None:
        """Test updating with inferred facts."""
        facts = [
            {
                "fact_id": "fact2",
                "how_learned": "inferred",
            }
        ]

        count = setup.update_from_chapter(2, facts)

        assert count == 1
        info = setup.get_fact_learning_info("fact2")
        assert info is not None
        assert info.source == KnowledgeSource.INFERENCE
        assert info.confidence == 0.6

    def test_update_skips_already_known(self, setup: CharacterKnowledge) -> None:
        """Test that update skips facts already known."""
        setup.learn_fact("fact1", chapter=1)

        facts = [
            {
                "fact_id": "fact1",
                "how_learned": "witnessed",
            }
        ]

        count = setup.update_from_chapter(1, facts)

        assert count == 0


class TestKnowledgeScope:
    """Test knowledge scope functionality."""

    def test_get_knowledge_scope(self) -> None:
        """Test getting knowledge scope."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="location",
            content="京城",
            source_character="char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="relationship",
            content="与丞相相识",
            source_character="char1",
            chapter=2,
        )
        graph.add_fact_node(
            "fact3",
            fact_type="event",
            content="宴会",
            source_character="char1",
            chapter=3,
        )

        ck = CharacterKnowledge("char1", graph)
        ck.learn_fact("fact1", chapter=1)
        ck.learn_fact("fact2", chapter=2)
        ck.learn_fact("fact3", chapter=3)

        scope = ck.get_knowledge_scope()

        assert scope["tier"] == 0
        assert "京城" in scope["locations_known"]
        assert "与丞相相识" in scope["characters_known"]
        assert "宴会" in scope["events_witnessed"]


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict(self) -> None:
        """Test serializing to dictionary."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="秘密",
            source_character="char2",
            chapter=2,
        )

        ck = CharacterKnowledge("char1", graph)
        ck.learn_fact("fact1", chapter=3, source="hearsay", confidence=0.8)

        data = ck.to_dict()

        assert data["character_id"] == "char1"
        assert "fact1" in data["knowledge_entries"]
        assert data["knowledge_entries"]["fact1"]["learned_chapter"] == 3
        assert data["knowledge_entries"]["fact1"]["source"] == "hearsay"

    def test_from_dict(self) -> None:
        """Test deserializing from dictionary."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="秘密",
            source_character="char2",
            chapter=2,
        )

        data = {
            "character_id": "char1",
            "knowledge_entries": {
                "fact1": {
                    "fact_id": "fact1",
                    "learned_chapter": 3,
                    "source": "hearsay",
                    "confidence": 0.8,
                    "context": "",
                }
            },
            "scope": {"tier": 0},
        }

        ck = CharacterKnowledge.from_dict(data, graph)

        assert ck.character_id == "char1"
        assert ck.knows_fact("fact1")
        info = ck.get_fact_learning_info("fact1")
        assert info is not None
        assert info.learned_chapter == 3
        assert info.source == KnowledgeSource.HEARSAY

    def test_roundtrip(self) -> None:
        """Test serialization roundtrip."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            fact_type="secret",
            content="秘密",
            source_character="char2",
            chapter=2,
        )
        graph.add_fact_node(
            "fact2",
            fact_type="event",
            content="事件",
            source_character="char3",
            chapter=3,
        )

        original = CharacterKnowledge("char1", graph)
        original.learn_fact("fact1", chapter=3, source="hearsay", confidence=0.7)
        original.learn_fact("fact2", chapter=4, source="direct")

        data = original.to_dict()
        restored = CharacterKnowledge.from_dict(data, graph)

        assert restored.character_id == original.character_id
        assert restored.fact_count == original.fact_count
        assert restored.knows_fact("fact1")
        assert restored.knows_fact("fact2")


class TestActionFactReference:
    """Test action-fact reference detection."""

    @pytest.fixture
    def setup(self) -> CharacterKnowledge:
        """Create character knowledge for reference tests."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        return CharacterKnowledge("char1", graph)

    def test_exact_content_match(self, setup: CharacterKnowledge) -> None:
        """Test detection with exact content match."""
        result = setup._action_references_fact(
            "林晚质问丞相私通敌国的事",
            "丞相私通敌国",
        )
        assert result is True

    def test_partial_chinese_match(self, setup: CharacterKnowledge) -> None:
        """Test detection with partial Chinese content - requires multiple terms."""
        # "丞相" alone is only 1 term match, need more context
        result = setup._action_references_fact(
            "林晚质问丞相私通",
            "丞相私通敌国",
        )
        assert result is True

    def test_single_term_no_match(self, setup: CharacterKnowledge) -> None:
        """Test that single term match is not enough."""
        result = setup._action_references_fact(
            "林晚质问丞相",
            "丞相私通敌国",
        )
        assert result is False

    def test_no_match(self, setup: CharacterKnowledge) -> None:
        """Test detection with no match."""
        result = setup._action_references_fact(
            "林晚在街上行走",
            "丞相私通敌国",
        )
        assert result is False

    def test_english_match(self, setup: CharacterKnowledge) -> None:
        """Test detection with English content."""
        result = setup._action_references_fact(
            "John asked about the secret meeting",
            "secret meeting",
        )
        assert result is True
