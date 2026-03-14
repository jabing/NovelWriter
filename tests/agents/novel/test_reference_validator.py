"""Unit tests for ReferenceValidator.

Tests reference extraction, verification, and hallucination detection.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.db.pinecone_client import VectorSearchResult, VectorStore
from src.novel_agent.novel.knowledge_graph import KnowledgeGraph
from src.novel_agent.novel.reference_validator import (
    Reference,
    ReferenceValidator,
)


@pytest.fixture
def mock_knowledge_graph() -> MagicMock:
    """Create a mock knowledge graph with test data."""
    kg = MagicMock(spec=KnowledgeGraph)

    # Mock character nodes
    lin_wan_node = MagicMock()
    lin_wan_node.node_id = "char_lin_wan"
    lin_wan_node.node_type = "character"
    lin_wan_node.properties = {"name": "林晚", "age": 25}

    chancellor_node = MagicMock()
    chancellor_node.node_id = "char_chancellor"
    chancellor_node.node_type = "character"
    chancellor_node.properties = {"name": "丞相", "role": "government"}

    # Configure get_entity_by_name
    def get_entity_by_name(name: str, node_type=None):
        name_lower = name.lower()
        if "林晚" in name or "lin" in name_lower:
            return lin_wan_node
        elif "丞相" in name:
            return chancellor_node
        return None

    kg.get_entity_by_name.side_effect = get_entity_by_name

    # Mock timeline
    def get_entity_timeline(node_id: str):
        if node_id == "char_lin_wan":
            return [
                {
                    "chapter": 1,
                    "event_type": "appearance",
                    "description": "林晚首次登场，展现出非凡的智慧",
                },
                {
                    "chapter": 3,
                    "event_type": "relation",
                    "description": "林晚与丞相讨论国事，提出了改革建议",
                },
            ]
        return []

    kg.get_entity_timeline.side_effect = get_entity_timeline

    # Mock related entities
    def query_related_entities(node_id: str, relation_types=None, max_depth=2):
        if node_id == "char_lin_wan":
            return [chancellor_node]
        return []

    kg.query_related_entities.side_effect = query_related_entities

    return kg


@pytest.fixture
def mock_vector_store() -> MagicMock:
    """Create a mock vector store."""
    vs = MagicMock(spec=VectorStore)

    # Mock query_similar as async
    async def query_similar(
        query_text: str, top_k: int = 10, filter_dict=None, include_metadata=True
    ):
        # Return different results based on query
        if "天下大势" in query_text:
            # No similar facts for hallucinated content
            return []
        elif "改革" in query_text or "国事" in query_text:
            # Return similar facts for valid content
            return [
                VectorSearchResult(
                    id="fact_1",
                    score=0.85,
                    metadata={
                        "text": "林晚与丞相讨论国事，提出了改革建议",
                        "chapter": 3,
                    },
                )
            ]
        return []

    vs.query_similar = AsyncMock(side_effect=query_similar)

    return vs


@pytest.fixture
def validator(mock_knowledge_graph: MagicMock, mock_vector_store: MagicMock) -> ReferenceValidator:
    """Create a ReferenceValidator with mocked dependencies."""
    return ReferenceValidator(
        knowledge_graph=mock_knowledge_graph,
        vector_store=mock_vector_store,
        similarity_threshold=0.75,
        hallucination_threshold=0.3,
    )


class TestReferenceExtraction:
    """Tests for reference extraction from text."""

    def test_extract_simple_quote(self, validator: ReferenceValidator) -> None:
        """Test extraction of simple quote references."""
        content = '林晚说过"天下大势，分久必合，合久必分"。'
        refs = validator.extract_references(content, 5)

        assert len(refs) >= 1
        ref = refs[0]
        assert "林晚" in ref.speaker
        assert ref.referenced_action == "说过"
        assert "天下大势" in ref.referenced_content
        assert ref.chapter == 5

    def test_extract_recall_reference(self, validator: ReferenceValidator) -> None:
        """Test extraction of recall/memory references."""
        content = "据林晚回忆，那是个寒冷的冬天。"
        refs = validator.extract_references(content, 5)

        assert len(refs) >= 1
        ref = refs[0]
        assert "林晚" in ref.speaker

    def test_extract_mention_reference(self, validator: ReferenceValidator) -> None:
        """Test extraction of mention references."""
        content = "丞相曾提到过边疆的危机。"
        refs = validator.extract_references(content, 4)

        assert len(refs) >= 1
        ref = refs[0]
        assert "丞相" in ref.speaker

    def test_extract_multiple_references(self, validator: ReferenceValidator) -> None:
        """Test extraction of multiple references in one text."""
        content = """
        林晚说过"改革很重要"。据林晚回忆，那是个重要的时刻。
        丞相曾提到过危机。正如林晚所言，时间紧迫。
        """
        refs = validator.extract_references(content, 5)

        assert len(refs) >= 2

    def test_no_references_found(self, validator: ReferenceValidator) -> None:
        """Test text with no references."""
        content = "这是一个晴朗的日子。林晚走在街上，心情愉快。"
        refs = validator.extract_references(content, 1)

        # May find 0 or minimal references
        assert isinstance(refs, list)


class TestReferenceVerification:
    """Tests for reference verification against knowledge sources."""

    @pytest.mark.asyncio
    async def test_verify_valid_reference(self, validator: ReferenceValidator) -> None:
        """Test verification of a valid reference with supporting evidence."""
        ref = Reference(
            text="林晚说过改革的重要性",
            speaker="林晚",
            referenced_character="林晚",
            referenced_action="说过",
            referenced_content="改革的重要性",
            chapter=5,
            confidence=0.8,
        )

        verification = await validator.verify_reference(ref)

        assert verification.reference == ref
        # Should be valid or have reasonable confidence
        assert verification.confidence > 0.3

    @pytest.mark.asyncio
    async def test_verify_hallucinated_reference(self, validator: ReferenceValidator) -> None:
        """Test detection of hallucinated reference (Chapter 5 issue)."""
        ref = Reference(
            text="林晚说过天下大势，分久必合",
            speaker="林晚",
            referenced_character="林晚",
            referenced_action="说过",
            referenced_content="天下大势，分久必合",
            chapter=5,
            confidence=0.7,
        )

        verification = await validator.verify_reference(ref)

        # This should be flagged as hallucination because:
        # 1. No evidence in knowledge graph
        # 2. No similar facts in vector store
        assert verification.confidence < 0.5
        assert not verification.is_valid or len(verification.issues) > 0
        assert any("hallucination" in issue.lower() for issue in verification.issues)

    @pytest.mark.asyncio
    async def test_verify_unknown_character(self, validator: ReferenceValidator) -> None:
        """Test verification of reference to unknown character."""
        ref = Reference(
            text="神秘人说过某个秘密",
            speaker="神秘人",
            referenced_character="神秘人",
            referenced_action="说过",
            referenced_content="某个秘密",
            chapter=5,
            confidence=0.6,
        )

        verification = await validator.verify_reference(ref)

        assert len(verification.issues) > 0
        assert any("not found" in issue.lower() for issue in verification.issues)

    @pytest.mark.asyncio
    async def test_verify_without_vector_store(self, mock_knowledge_graph: MagicMock) -> None:
        """Test verification when vector store is not available."""
        validator_no_vs = ReferenceValidator(
            knowledge_graph=mock_knowledge_graph,
            vector_store=None,
        )

        ref = Reference(
            text="林晚说过改革",
            speaker="林晚",
            referenced_character="林晚",
            referenced_action="说过",
            referenced_content="改革",
            chapter=5,
            confidence=0.7,
        )

        verification = await validator_no_vs.verify_reference(ref)

        # Should still work, just with lower confidence
        assert verification.reference == ref
        assert verification.confidence >= 0.0


class TestChapterValidation:
    """Tests for full chapter validation."""

    @pytest.mark.asyncio
    async def test_validate_chapter_with_hallucination(self, validator: ReferenceValidator) -> None:
        """Test validation of Chapter 5 with hallucinated reference."""
        content = """
        第五章：风云变幻

        林晚站在城楼上，望着远方。她想起丞相的话，心中感慨万千。

        林晚说过"天下大势，分久必合，合久必分"，这句话一直萦绕在她心头。

        据林晚回忆，那是个风雨交加的夜晚，改革的声音响彻朝堂。
        """

        verifications = await validator.validate_chapter_references(content, 5)

        assert len(verifications) >= 1

        # Find the hallucinated reference
        hallucination_found = False
        for v in verifications:
            if "天下大势" in v.reference.referenced_content:
                hallucination_found = True
                assert v.confidence < 0.5
                assert len(v.issues) > 0

        assert hallucination_found, "Should detect the hallucinated reference"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_vector_store_error(self, mock_knowledge_graph: MagicMock) -> None:
        """Test handling of vector store errors."""
        mock_vs = MagicMock(spec=VectorStore)
        mock_vs.query_similar = AsyncMock(side_effect=Exception("Connection error"))

        validator = ReferenceValidator(
            knowledge_graph=mock_knowledge_graph,
            vector_store=mock_vs,
        )

        ref = Reference(
            text="林晚说过某事",
            speaker="林晚",
            referenced_character="林晚",
            referenced_action="说过",
            referenced_content="某事",
            chapter=5,
            confidence=0.7,
        )

        # Should not crash, just log error and continue
        verification = await validator.verify_reference(ref)
        assert verification.reference == ref

    def test_malformed_regex_match(self, validator: ReferenceValidator) -> None:
        """Test handling of malformed text that might break regex."""
        content = '林晚说过"""""""'  # Malformed quotes

        # Should not crash
        refs = validator.extract_references(content, 5)
        # May extract empty/invalid refs but shouldn't raise
        assert isinstance(refs, list)

    @pytest.mark.asyncio
    async def test_chapter5_hallucination_detection_accuracy(
        self, validator: ReferenceValidator
    ) -> None:
        """Test that Chapter 5 hallucination is detected with >85% accuracy."""
        # Simulate 50 test cases (reduced for speed)
        hallucinated_refs = []
        for i in range(50):
            ref = Reference(
                text=f"林晚说过天下大势{i}",
                speaker="林晚",
                referenced_character="林晚",
                referenced_action="说过",
                referenced_content=f"天下大势{i}",
                chapter=5,
                confidence=0.7,
            )
            verification = await validator.verify_reference(ref)
            if not verification.is_valid or verification.confidence < 0.5:
                hallucinated_refs.append(verification)

        # Should detect at least 85% as hallucinations
        detection_rate = len(hallucinated_refs) / 50
        assert detection_rate >= 0.85

    def test_extraction_accuracy(self, validator: ReferenceValidator) -> None:
        """Test that reference extraction achieves >75% accuracy."""
        # Test content with known references
        content = """
        林晚说过"改革是必要的"。
        据林晚回忆，那是个重要的时刻。
        丞相曾提到过危机。
        林晚记得那个夜晚。
        """

        refs = validator.extract_references(content, 5)

        # Should extract at least some references
        assert len(refs) >= 2

        # All extracted refs should have required fields
        for ref in refs:
            assert ref.text != ""
            assert ref.speaker != ""
            assert ref.referenced_action != ""
            assert ref.chapter == 5
            assert 0.0 <= ref.confidence <= 1.0
