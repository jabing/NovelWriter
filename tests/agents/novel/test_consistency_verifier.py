"""Tests for ConsistencyVerifier double-layer verification system."""

import pytest

from src.novel.cognitive_graph import CognitiveGraph
from src.novel.consistency_verifier import (
    ChapterVerificationResult,
    ConsistencyVerifier,
    DoubleLayerResult,
    LayerVerificationResult,
    VerificationReport,
)
from src.novel.global_fact_layer import Conflict, ConflictSeverity, ConflictType


class TestConsistencyVerifierInit:
    """Test ConsistencyVerifier initialization."""

    def test_init_with_graph(self) -> None:
        """Test initialization with a CognitiveGraph."""
        graph = CognitiveGraph()
        verifier = ConsistencyVerifier(graph)
        
        assert verifier.graph is graph
        assert verifier.global_layer is not None
        assert verifier.character_ids == []

    def test_init_with_characters(self) -> None:
        """Test initialization initializes character knowledge for existing characters."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        
        verifier = ConsistencyVerifier(graph)
        
        assert len(verifier.character_ids) == 2
        assert "char1" in verifier.character_ids
        assert "char2" in verifier.character_ids

    def test_add_character(self) -> None:
        """Test adding a character after initialization."""
        graph = CognitiveGraph()
        verifier = ConsistencyVerifier(graph)
        
        ck = verifier.add_character("new_char")
        
        assert "new_char" in verifier.character_ids
        assert ck is not None


class TestVerifyFact:
    """Test verify_fact method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        return graph

    def test_verify_fact_no_conflicts(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying a fact with no conflicts."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.verify_fact("fact1")
        
        assert isinstance(result, DoubleLayerResult)
        assert result.fact_id == "fact1"
        assert result.global_layer.passed is True
        assert result.overall_passed is True

    def test_verify_fact_with_content_conflict(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying a fact with content conflict."""
        # Add conflicting fact
        setup_graph.add_fact_node(
            "fact2",
            "event",
            "林晚没有去京城",
            "char1",
            chapter=2,
        )
        
        verifier = ConsistencyVerifier(setup_graph)
        result = verifier.verify_fact("fact1")
        
        assert result.global_layer.passed is False
        assert result.global_layer.issue_count > 0


class TestVerifyChapter:
    """Test verify_chapter method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        return graph

    def test_verify_chapter_empty(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying an empty chapter."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.verify_chapter("", 1)
        
        assert isinstance(result, ChapterVerificationResult)
        assert result.chapter_number == 1
        assert result.passed is True

    def test_verify_chapter_with_facts(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying a chapter with facts."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.verify_chapter("林晚在京城遇到了丞相。", 1)
        
        assert result.chapter_number == 1
        assert result.facts_checked >= 0


class TestVerifyCharacterKnowledge:
    """Test verify_character_knowledge method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            "secret",
            "丞相私通敌国",
            "char2",
            chapter=3,
        )
        return graph

    def test_verify_unknown_character(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying an unknown character returns passed."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.verify_character_knowledge("unknown_char")
        
        assert result.passed is True
        assert result.issue_count == 0

    def test_verify_character_no_knowledge(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying a character with no knowledge."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.verify_character_knowledge("char1")
        
        assert result.passed is True

    def test_verify_character_with_knowledge(self, setup_graph: CognitiveGraph) -> None:
        """Test verifying a character with learned knowledge."""
        verifier = ConsistencyVerifier(setup_graph)
        _ = verifier.learn_fact_for_character("char1", "fact1", chapter=5)
        
        result = verifier.verify_character_knowledge("char1", chapter=5)
        
        assert result.passed is True

    def test_verify_character_knowledge_timing(self, setup_graph: CognitiveGraph) -> None:
        """Test detecting knowledge timing issue."""
        verifier = ConsistencyVerifier(setup_graph)
        _ = verifier.learn_fact_for_character("char1", "fact1", chapter=5)
        
        # Check at chapter 3 - character shouldn't know this yet
        result = verifier.verify_character_knowledge("char1", chapter=3)
        
        # Should have timing issue
        assert result.issue_count > 0


class TestGetVerificationReport:
    """Test get_verification_report method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        return graph

    def test_empty_report(self, setup_graph: CognitiveGraph) -> None:
        """Test report with no data."""
        verifier = ConsistencyVerifier(setup_graph)
        
        report = verifier.get_verification_report()
        
        assert isinstance(report, VerificationReport)
        assert report.total_facts == 0
        assert report.total_characters == 2
        assert report.passed is True
        assert report.total_issues == 0

    def test_report_with_facts(self, setup_graph: CognitiveGraph) -> None:
        """Test report with facts."""
        setup_graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        
        verifier = ConsistencyVerifier(setup_graph)
        report = verifier.get_verification_report()
        
        assert report.total_facts == 1
        assert report.total_characters == 2
        assert report.passed is True

    def test_report_with_conflicts(self, setup_graph: CognitiveGraph) -> None:
        """Test report with conflicts."""
        setup_graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        setup_graph.add_fact_node(
            "fact2",
            "event",
            "林晚没有去京城",
            "char2",
            chapter=2,
        )
        
        verifier = ConsistencyVerifier(setup_graph)
        report = verifier.get_verification_report()
        
        assert report.total_facts == 2
        # Should have content conflicts
        assert len(report.global_conflicts) > 0

    def test_report_properties(self, setup_graph: CognitiveGraph) -> None:
        """Test report properties."""
        verifier = ConsistencyVerifier(setup_graph)
        report = verifier.get_verification_report()
        
        assert report.critical_count == 0
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_report_to_dict(self, setup_graph: CognitiveGraph) -> None:
        """Test report serialization."""
        verifier = ConsistencyVerifier(setup_graph)
        report = verifier.get_verification_report()
        
        data = report.to_dict()
        
        assert "total_facts" in data
        assert "total_characters" in data
        assert "passed" in data
        assert "summary" in data


class TestCheckDoubleLayer:
    """Test check_double_layer method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        return graph

    def test_check_double_layer(self, setup_graph: CognitiveGraph) -> None:
        """Test double-layer check is same as verify_fact."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.check_double_layer("fact1")
        expected = verifier.verify_fact("fact1")
        
        assert result.fact_id == expected.fact_id
        assert result.overall_passed == expected.overall_passed


class TestLearnFactForCharacter:
    """Test learn_fact_for_character method."""

    @pytest.fixture
    def setup_graph(self) -> CognitiveGraph:
        """Create a graph with test data."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_fact_node(
            "fact1",
            "secret",
            "丞相私通敌国",
            "char2",
            chapter=3,
        )
        return graph

    def test_learn_fact(self, setup_graph: CognitiveGraph) -> None:
        """Test learning a fact for a character."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.learn_fact_for_character(
            "char1", "fact1", chapter=5, source="hearsay"
        )
        
        assert result is True
        ck = verifier.get_character_knowledge("char1")
        assert ck is not None
        assert ck.knows_fact("fact1")

    def test_learn_fact_unknown_character(self, setup_graph: CognitiveGraph) -> None:
        """Test learning a fact for an unknown character adds them."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.learn_fact_for_character(
            "new_char", "fact1", chapter=5
        )
        
        assert result is True
        assert "new_char" in verifier.character_ids

    def test_learn_fact_unknown_fact(self, setup_graph: CognitiveGraph) -> None:
        """Test learning an unknown fact returns False."""
        verifier = ConsistencyVerifier(setup_graph)
        
        result = verifier.learn_fact_for_character(
            "char1", "unknown_fact", chapter=5
        )
        
        assert result is False


class TestLayerVerificationResult:
    """Test LayerVerificationResult dataclass."""

    def test_passed_result(self) -> None:
        """Test a passing result."""
        result = LayerVerificationResult(
            layer_name="global",
            passed=True,
        )
        
        assert result.passed is True
        assert result.issue_count == 0
        assert result.issues == []

    def test_failed_result(self) -> None:
        """Test a failing result."""
        result = LayerVerificationResult(
            layer_name="character",
            passed=False,
            issues=[{"type": "test", "description": "Test issue"}],
            issue_count=1,
        )
        
        assert result.passed is False
        assert result.issue_count == 1

    def test_to_dict(self) -> None:
        """Test serialization."""
        result = LayerVerificationResult(
            layer_name="global",
            passed=True,
            issues=[],
            issue_count=0,
        )
        
        data = result.to_dict()
        
        assert data["layer_name"] == "global"
        assert data["passed"] is True


class TestDoubleLayerResult:
    """Test DoubleLayerResult dataclass."""

    def test_overall_passed(self) -> None:
        """Test overall_passed is True when both layers pass."""
        global_result = LayerVerificationResult("global", True)
        character_result = LayerVerificationResult("character", True)
        
        result = DoubleLayerResult(
            fact_id="fact1",
            global_layer=global_result,
            character_layer=character_result,
            overall_passed=True,
        )
        
        assert result.overall_passed is True

    def test_overall_failed(self) -> None:
        """Test overall_passed is False when one layer fails."""
        global_result = LayerVerificationResult("global", False, issue_count=1)
        character_result = LayerVerificationResult("character", True)
        
        result = DoubleLayerResult(
            fact_id="fact1",
            global_layer=global_result,
            character_layer=character_result,
            overall_passed=False,
        )
        
        assert result.overall_passed is False

    def test_to_dict(self) -> None:
        """Test serialization."""
        global_result = LayerVerificationResult("global", True)
        character_result = LayerVerificationResult("character", True)
        
        result = DoubleLayerResult(
            fact_id="fact1",
            global_layer=global_result,
            character_layer=character_result,
            overall_passed=True,
        )
        
        data = result.to_dict()
        
        assert data["fact_id"] == "fact1"
        assert "global_layer" in data
        assert "character_layer" in data


class TestChapterVerificationResult:
    """Test ChapterVerificationResult dataclass."""

    def test_passed_result(self) -> None:
        """Test a passing chapter result."""
        result = ChapterVerificationResult(
            chapter_number=1,
            passed=True,
        )
        
        assert result.chapter_number == 1
        assert result.passed is True
        assert result.global_conflicts == []
        assert result.cognitive_conflicts == []

    def test_failed_result(self) -> None:
        """Test a failing chapter result."""
        conflict = Conflict(
            conflict_type=ConflictType.CONTENT_CONFLICT,
            severity=ConflictSeverity.WARNING,
            fact_id_1="fact1",
            fact_id_2="fact2",
            description="Test conflict",
            chapter=1,
        )
        
        result = ChapterVerificationResult(
            chapter_number=1,
            passed=False,
            global_conflicts=[conflict],
            facts_checked=5,
        )
        
        assert result.passed is False
        assert len(result.global_conflicts) == 1
        assert result.facts_checked == 5

    def test_to_dict(self) -> None:
        """Test serialization."""
        result = ChapterVerificationResult(
            chapter_number=5,
            passed=True,
            facts_checked=10,
            characters_checked=3,
        )
        
        data = result.to_dict()
        
        assert data["chapter_number"] == 5
        assert data["passed"] is True
        assert data["facts_checked"] == 10


class TestVerificationReport:
    """Test VerificationReport dataclass."""

    def test_empty_report(self) -> None:
        """Test an empty report."""
        report = VerificationReport(
            total_facts=0,
            total_characters=0,
        )
        
        assert report.total_facts == 0
        assert report.total_characters == 0
        assert report.passed is True
        assert report.total_issues == 0

    def test_issue_counts(self) -> None:
        """Test issue counting."""
        conflicts = [
            Conflict(ConflictType.CONTENT_CONFLICT, ConflictSeverity.CRITICAL, "f1"),
            Conflict(ConflictType.CONTENT_CONFLICT, ConflictSeverity.ERROR, "f2"),
            Conflict(ConflictType.CONTENT_CONFLICT, ConflictSeverity.ERROR, "f3"),
            Conflict(ConflictType.CONTENT_CONFLICT, ConflictSeverity.WARNING, "f4"),
        ]
        
        report = VerificationReport(
            total_facts=4,
            total_characters=2,
            global_conflicts=conflicts,
        )
        
        assert report.critical_count == 1
        assert report.error_count == 2
        assert report.warning_count == 1
        assert report.total_issues == 4

    def test_to_dict(self) -> None:
        """Test serialization."""
        report = VerificationReport(
            total_facts=10,
            total_characters=5,
            passed=True,
            summary="All good",
        )
        
        data = report.to_dict()
        
        assert data["total_facts"] == 10
        assert data["total_characters"] == 5
        assert data["passed"] is True
        assert data["summary"] == "All good"


class TestIntegration:
    """Integration tests for ConsistencyVerifier."""

    def test_full_workflow(self) -> None:
        """Test a full verification workflow."""
        # Setup
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        graph.add_character_node("char2", "丞相", tier=1)
        graph.add_location_node("loc1", "京城")
        
        # Add facts
        graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
            properties={"location": "京城", "timestamp": 1000},
        )
        graph.add_fact_node(
            "fact2",
            "secret",
            "丞相私通敌国",
            "char2",
            chapter=3,
        )
        
        # Create verifier
        verifier = ConsistencyVerifier(graph)
        
        # Character learns secret
        _ = verifier.learn_fact_for_character("char1", "fact2", chapter=5, source="discovery")
        
        # Verify chapter
        chapter_result = verifier.verify_chapter("林晚在京城发现了丞相的秘密。", 5)
        assert chapter_result.chapter_number == 5
        
        # Verify fact
        fact_result = verifier.verify_fact("fact1")
        assert fact_result is not None
        
        # Verify character knowledge
        char_result = verifier.verify_character_knowledge("char1", chapter=5)
        assert char_result is not None
        
        # Get full report
        report = verifier.get_verification_report()
        assert report.total_facts == 2
        assert report.total_characters == 2

    def test_conflict_detection(self) -> None:
        """Test conflict detection across layers."""
        graph = CognitiveGraph()
        graph.add_character_node("char1", "林晚", tier=0)
        
        # Add conflicting facts
        graph.add_fact_node(
            "fact1",
            "event",
            "林晚去了京城",
            "char1",
            chapter=1,
        )
        graph.add_fact_node(
            "fact2",
            "event",
            "林晚没有去京城",
            "char1",
            chapter=2,
        )
        
        verifier = ConsistencyVerifier(graph)
        report = verifier.get_verification_report()
        
        # Should detect content conflict
        assert len(report.global_conflicts) > 0
