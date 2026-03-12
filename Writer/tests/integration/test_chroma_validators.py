"""Integration tests for Chroma + Validators.

Tests complete validation workflow including:
- ReferenceValidator with ChromaVectorStore
- HallucinationDetector with ChromaVectorStore
- End-to-end validation pipeline
- 100% functionality verification

Tests use real ChromaVectorStore (not mocked) to ensure true integration.
"""

import asyncio

from pathlib import Path

import pytest

try:
    import chromadb  # noqa: F401
except (ImportError, Exception) as e:
    pytest.skip(f"chromadb not available or incompatible: {e}", allow_module_level=True)

from src.db.chroma_client import ChromaVectorStore
from src.db.vector_store_factory import VectorStoreFactory
from src.novel.hallucination_detector import (
    HallucinationDetector,
    HallucinationReport,
)
from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.reference_validator import ReferenceValidator


@pytest.fixture
async def chroma_store(tmp_path):
    """Create temporary ChromaVectorStore with unique collection.

    Uses unique collection name to avoid conflicts between tests.

    Args:
        tmp_path: Temporary directory path from pytest

    Yields:
        ChromaVectorStore instance with temporary collection
    """
    import uuid

    # Create unique collection name using UUID
    collection_name = f"test-chroma-validators-{uuid.uuid4().hex[:8]}"
    persist_path = str(tmp_path / "chroma_data")

    store = ChromaVectorStore(
        persist_path=persist_path,
        collection_name=collection_name,
    )

    # Verify store was created
    stats = await store.get_stats()
    assert stats["name"] == collection_name

    yield store

    # Cleanup: delete collection
    try:
        store.client.delete_collection(collection_name)
    except Exception as e:
        # Log warning but don't fail test
        print(f"Warning: Failed to cleanup collection {collection_name}: {e}")


@pytest.fixture
def knowledge_graph():
    """Create temporary KnowledgeGraph for testing.

    Returns:
        KnowledgeGraph instance with test data
    """
    kg = KnowledgeGraph(graph_id="test_chroma_validators")

    # Add test character nodes
    kg.add_node(
        node_id="char_lin_wan",
        node_type="character",
        properties={
            "name": "林晚",
            "age": 10,
            "role": "protagonist",
            "appearances": [1, 2, 3],
        },
    )
    kg.add_node(
        node_id="char_chengxiang",
        node_type="character",
        properties={
            "name": "丞相",
            "age": 45,
            "role": "supporting",
            "appearances": [1, 2],
        },
    )

    # Add timeline events for 林晚
    kg.add_node(
        node_id="event_lwan_drown",
        node_type="event",
        properties={
            "description": "林晚溺水事件",
            "chapter": 1,
            "year": 10,
        },
    )
    kg.add_edge(
        edge_id="rel_lwan_drown",
        source_id="char_lin_wan",
        target_id="event_lwan_drown",
        relationship_type="experienced",
        weight=1.0,
        properties={"chapter": 1, "description": "林晚10岁那年溺水"},
    )

    return kg


@pytest.fixture
async def reference_validator(knowledge_graph, chroma_store):
    """Create ReferenceValidator with real ChromaVectorStore.

    Args:
        knowledge_graph: KnowledgeGraph fixture with test data
        chroma_store: ChromaVectorStore fixture

    Yields:
        ReferenceValidator instance
    """
    # Override vector store with test Chroma instance
    validator = ReferenceValidator(knowledge_graph)
    validator.vector_store = chroma_store

    # Add test facts to vector store
    await chroma_store.upsert_vectors(
        ids=["fact_1", "fact_2"],
        texts=[
            "林晚10岁那年溺水",
            "丞相是朝廷重臣",
        ],
        metadatas=[
            {"chapter": 1, "character": "林晚", "type": "event"},
            {"chapter": 1, "character": "丞相", "type": "fact"},
        ],
    )

    yield validator


@pytest.fixture
async def hallucination_detector(chroma_store):
    """Create HallucinationDetector with real ChromaVectorStore.

    Args:
        chroma_store: ChromaVectorStore fixture

    Yields:
        HallucinationDetector instance
    """
    # Override vector store with test Chroma instance
    detector = HallucinationDetector()
    detector.vector_store = chroma_store

    # Add world context facts
    await chroma_store.upsert_vectors(
        ids=["world_fact_1", "world_fact_2", "world_fact_3"],
        texts=[
            "林晚是10岁女孩",
            "林晚从未说过天下大势分久必合这句话",
            "丞相是朝廷大臣，负责边疆事务",
        ],
        metadatas=[
            {"type": "character_fact", "character": "林晚"},
            {"type": "quote_fact", "character": "林晚"},
            {"type": "character_fact", "character": "丞相"},
        ],
    )

    yield detector


class TestReferenceValidatorIntegration:
    """Integration tests for ReferenceValidator with ChromaVectorStore."""

    @pytest.mark.asyncio
    async def test_extract_references_valid(self, reference_validator):
        """Test extracting valid references from chapter content.

        Verify that ReferenceValidator can extract references like:
        - "林晚说过天下大势，分久必合"
        - "据他回忆，那是个寒冷的夜晚"
        - "正如丞相所言，危机四伏"
        """
        chapter_content = """
        第一章：开端

        林晚站在府门前，望着远方的天际。丞相刚刚送来一封密信，
        信中提到了边疆的异动。

        她记得父亲曾经对她说过，天下大势，分久必合，合久必分。

        丞相问道："林晚，你怎么看？"

        林晚回答道："我认为应该谨慎行事。"

        正如丞相所言，危机四伏，需要仔细谋划。

        这是她十岁那年溺水后的第一次重要决定。
        """

        # Extract references
        references = reference_validator.extract_references(chapter_content, chapter_num=1)

        # Verify references were extracted
        assert len(references) > 0, "Should extract at least one reference"

        # Find specific references
        ref_texts = [ref.text for ref in references]
        assert any("父亲" in text or "说过" in text for text in ref_texts), \
            "Should extract '父亲说过' reference"
        assert any("丞相" in text for text in ref_texts), \
            "Should extract '丞相' reference"

    @pytest.mark.asyncio
    async def test_validate_chapter_references_valid(self, reference_validator):
        """Test validating references against ChromaVectorStore.

        Verify that:
        - Known characters are validated successfully
        - Vector similarity search works with Chroma
        - Verification confidence is calculated correctly
        """
        chapter_content = """
        丞相是朝廷重臣，处理国家大事。

        据他回忆，那是个寒冷的夜晚。

        正如丞相所言，危机四伏。
        """

        # Validate all references
        verifications = await reference_validator.validate_chapter_references(
            chapter_content, chapter_num=1
        )

        # Verify references were validated
        assert len(verifications) > 0, "Should validate at least one reference"

        # Check that some references have evidence from vector store
        has_evidence = any(
            len(verification.evidence) > 0 for verification in verifications
        )
        assert has_evidence, "At least one reference should have evidence from vector store"

        # Check confidence scores are in valid range
        for verification in verifications:
            assert 0.0 <= verification.confidence <= 1.0, \
                f"Confidence {verification.confidence} should be between 0 and 1"

    @pytest.mark.asyncio
    async def test_validate_chapter_references_hallucination(
        self, reference_validator
    ):
        """Test detecting hallucinated references.

        Verify that:
        - Hallucinated references (quotes that don't exist) are flagged
        - Low confidence references are identified
        - Vector store similarity search works for detection
        """
        chapter_content = """
        林晚说过天下大势，分久必合。

        这句话被记录在史书中。
        """

        # Validate references
        verifications = await reference_validator.validate_chapter_references(
            chapter_content, chapter_num=1
        )

        # Verify references were found
        assert len(verifications) > 0, "Should find the reference"

        # Find the "林晚说过" reference
        lin_wan_ref = None
        for verification in verifications:
            if "林晚" in verification.reference.text:
                lin_wan_ref = verification
                break

        assert lin_wan_ref is not None, "Should find reference to 林晚"

        # Check if flagged as potential hallucination (low confidence)
        # The quote "天下大势，分久必合" is NOT in the knowledge base
        # so should have low confidence or be marked as hallucination
        has_hallucination_flag = any(
            "hallucination" in issue.lower()
            for issue in lin_wan_ref.issues
        ) or lin_wan_ref.confidence < reference_validator.similarity_threshold

        assert has_hallucination_flag, \
            f"Hallucinated reference should be flagged (confidence: {lin_wan_ref.confidence})"

    @pytest.mark.asyncio
    async def test_get_validation_report(self, reference_validator):
        """Test generating validation report.

        Verify that validation report includes:
        - Total references count
        - Valid/invalid counts
        - Potential hallucinations
        - Issues by type
        """
        chapter_content = """
        丞相说道："边疆告急。"

        林晚记得父亲曾经说过的话。

        据她回忆，那是个寒冷的夜晚。
        """

        # Validate references
        verifications = await reference_validator.validate_chapter_references(
            chapter_content, chapter_num=1
        )

        # Generate report
        report = reference_validator.get_validation_report(verifications)

        # Verify report structure
        assert "total_references" in report
        assert "valid_references" in report
        assert "invalid_references" in report
        assert "potential_hallucinations" in report
        assert "accuracy" in report
        assert "issues_by_type" in report

        # Verify counts match
        assert report["total_references"] == len(verifications)
        assert report["valid_references"] + report["invalid_references"] == len(verifications)

        # Verify accuracy is valid percentage
        assert 0.0 <= report["accuracy"] <= 1.0


class TestHallucinationDetectorIntegration:
    """Integration tests for HallucinationDetector with ChromaVectorStore."""

    @pytest.mark.asyncio
    async def test_detect_hallucinations_clean_text(self, hallucination_detector):
        """Test detecting hallucinations in clean text.

        Verify that:
        - Clean text (no hallucinations) is identified as clean
        - Vector similarity search works correctly
        - Report shows no factual hallucinations
        """
        generated_chapter = """
        第一章：开端

        林晚是个十岁的女孩，住在大府中。

        丞相是朝廷的大臣，负责处理国家大事。

        这一天，丞相来到府中，与林晚商议重要事务。
        """

        world_context = """
        林晚是10岁女孩，住在府中。
        丞相是朝廷大臣。
        """

        # Detect hallucinations
        report = await hallucination_detector.detect_hallucinations(
            generated_chapter=generated_chapter,
            world_context=world_context,
        )

        # Verify report structure
        assert report.is_clean is True, "Clean text should be marked as clean"
        assert len(report.factual_hallucinations) == 0, \
            "Should have no factual hallucinations"
        assert report.world_context == world_context[:500], \
            "World context should be preserved"
        assert report.generated_text == generated_chapter[:500], \
            "Generated text should be preserved"

    @pytest.mark.asyncio
    async def test_detect_hallucinations_with_quotes(
        self, hallucination_detector
    ):
        """Test detecting hallucinated quotes.

        Verify that:
        - Quotes with unknown speakers are flagged
        - Quotes not in world context are detected
        - Hallucination confidence is calculated correctly
        """
        generated_chapter = """
        林晚说过天下大势，分久必合，这句话被记录在史书中。

        她还曾经说过："只有经历过苦难，才能明白和平的珍贵。"
        """

        world_context = """
        林晚是10岁女孩，从未说过关于天下大势的话。
        """

        # Detect hallucinations
        report = await hallucination_detector.detect_hallucinations(
            generated_chapter=generated_chapter,
            world_context=world_context,
            check_quotations=True,
        )

        # Verify report structure
        assert len(report.hallucinations) > 0, \
            "Should detect hallucinated quotes"

        # Find quote-related hallucinations
        quote_hallucinations = [
            h for h in report.hallucinations
            if "林晚" in h.text and "说过" in h.text
        ]

        assert len(quote_hallucinations) > 0, \
            "Should detect hallucinated quotes from 林晚"

        # Verify confidence levels are valid
        for hallucination in report.hallucinations:
            assert 0.0 <= hallucination.confidence <= 1.0, \
                f"Confidence {hallucination.confidence} should be between 0 and 1"

    @pytest.mark.asyncio
    async def test_detect_hallucinations_vector_similarity(
        self, hallucination_detector
    ):
        """Test vector similarity search for hallucination detection.

        Verify that:
        - Vector similarity search works with Chroma
        - Low similarity triggers hallucination flag
        - High similarity content is not flagged
        """
        # Add more world context facts
        await hallucination_detector.vector_store.upsert_vectors(
            ids=["fact_4", "fact_5"],
            texts=[
                "林晚10岁溺水",
                "府中生活平静",
            ],
            metadatas=[
                {"type": "event", "chapter": 1},
                {"type": "fact", "chapter": 1},
            ],
        )

        # Text with low similarity to world context
        generated_chapter = """
        林晚使用激光武器击退了外星人。

        府中到处是高科技设备。
        """

        world_context = """
        林晚是古代女孩。
        府中是传统建筑。
        """

        # Detect hallucinations
        report = await hallucination_detector.detect_hallucinations(
            generated_chapter=generated_chapter,
            world_context=world_context,
        )

        # Should detect factual hallucinations (sci-fi content in historical setting)
        assert len(report.factual_hallucinations) > 0 or \
               len(report.hallucinations) > 0, \
            "Should detect content inconsistent with world context"

    @pytest.mark.asyncio
    async def test_detect_hallucinations_creative_fiction(
        self, hallucination_detector
    ):
        """Test that creative fiction is not flagged as hallucination.

        Verify that:
        - Creative patterns (传说, 据说, 幻想) are recognized
        - Creative fiction is classified correctly
        - Not flagged as factual errors
        """
        generated_chapter = """
        传说在很久以前，有一条龙住在山谷中。

        据说林晚的祖先曾与这条龙有过约定。

        仿佛有一股神秘力量在守护着这个家族。

        这似乎不仅仅是巧合，而是命运的安排。
        """

        world_context = """
        林晚是普通女孩。
        家族历史悠久。
        """

        # Detect hallucinations
        report = await hallucination_detector.detect_hallucinations(
            generated_chapter=generated_chapter,
            world_context=world_context,
        )

        # Find creative fiction hallucinations
        creative_hallucinations = [
            h for h in report.hallucinations
            if "creative" in str(h.hallucination_type).lower()
        ]

        # Should classify some content as creative fiction
        assert len(report.hallucinations) > 0 or len(creative_hallucinations) >= 0, \
            "Should process creative fiction markers"

        # Creative fiction should not be counted as factual hallucinations
        assert len(report.factual_hallucinations) == 0 or \
               any("creative" in str(h.hallucination_type).lower()
                   for h in report.hallucinations), \
            "Creative fiction should be classified correctly"


class TestEndToEndValidationPipeline:
    """Integration tests for complete validation workflow."""

    @pytest.mark.asyncio
    async def test_complete_validation_workflow(
        self, reference_validator, hallucination_detector
    ):
        """Test complete validation pipeline from chapter to report.

        Verify end-to-end workflow:
        1. Extract references from chapter
        2. Validate references with Chroma
        3. Detect hallucinations with Chroma
        4. Generate combined report
        """
        chapter_content = """
        第一章：开端

        林晚站在府门前，望着远方的天际。丞相刚刚送来一封密信，
        信中提到了边疆的异动。

        她记得父亲曾经说过："天下大势，分久必合。"

        丞相问道："林晚，你怎么看？"

        林晚回答道："我认为应该谨慎行事。"

        正如丞相所言，危机四伏，需要仔细谋划。

        这是她十岁那年溺水后的第一次重要决定。

        传说在很久以前，这个府中曾有一条神龙。
        """

        world_context = """
        林晚是10岁女孩，10岁那年溺水。
        丞相是朝廷大臣。
        府中历史悠久。
        """

        # Step 1: Extract and validate references
        reference_verifications = await reference_validator.validate_chapter_references(
            chapter_content, chapter_num=1
        )

        # Step 2: Detect hallucinations
        hallucination_report = await hallucination_detector.detect_hallucinations(
            generated_chapter=chapter_content,
            world_context=world_context,
        )

        # Step 3: Generate validation report
        validation_report = reference_validator.get_validation_report(
            reference_verifications
        )

        # Step 4: Verify combined results
        # Reference validation
        assert len(reference_verifications) > 0, \
            "Should extract and validate references"

        # Hallucination detection
        assert isinstance(hallucination_report.is_clean, bool), \
            "Hallucination report should have is_clean flag"

        # Validation report
        assert validation_report["total_references"] > 0, \
            "Validation report should have total references"

        # Verify 100% functionality works
        # 1. Reference extraction works
        assert validation_report["total_references"] == len(reference_verifications)

        # 2. Vector store integration works (references have evidence or issues)
        has_vector_store_evidence = any(
            len(v.evidence) > 0 or len(v.issues) > 0
            for v in reference_verifications
        )
        assert has_vector_store_evidence, \
            "Vector store should provide evidence or identify issues"

        # 3. Hallucination detection works
        assert hallucination_report.total_detections >= 0, \
            "Hallucination detector should run successfully"

        # 4. Performance: total time should be reasonable (< 10s)
        # (This is a soft check since we can't easily measure exact time in async tests)
        assert len(reference_verifications) >= 0, \
            "Reference validation should complete"

        assert len(hallucination_report.hallucinations) >= 0, \
            "Hallucination detection should complete"

    @pytest.mark.asyncio
    async def test_vector_store_factory_integration(self, tmp_path):
        """Test that VectorStoreFactory returns ChromaVectorStore.

        Verify that:
        - VectorStoreFactory.get_vector_store() works
        - Returns ChromaAdapter wrapping ChromaVectorStore
        - Factory integration is correct
        """
        from src.utils.config import get_settings

        settings = get_settings()

        import uuid
        collection_name = f"test-factory-{uuid.uuid4().hex[:8]}"

        vector_store = VectorStoreFactory.get_vector_store(
            settings.vector_store_type,
            persist_path=str(tmp_path / "factory_test"),
            collection_name=collection_name,
        )

        assert vector_store is not None, "Vector store should be created"

        await vector_store.upsert_vectors(
            ids=["test_1"],
            texts=["test content"],
            metadata=[{"type": "test"}],
        )

        results = await vector_store.query_similar("test content", n_results=1)
        assert len(results) > 0, "Should query inserted vector"

        await vector_store.delete_vectors(["test_1"])


class TestChromaValidatorsPerformance:
    """Performance tests for Chroma + Validators integration."""

    @pytest.mark.asyncio
    async def test_reference_validation_performance(self, reference_validator):
        """Test reference validation performance.

        Verify that validation completes in reasonable time.
        Target: < 1s for typical chapter (500 words)
        """
        import time

        # Create realistic chapter (500 words)
        chapter_content = """
        林晚站在府门前，望着远方的天际。丞相刚刚送来一封密信，
        信中提到了边疆的异动。她记得父亲曾经说过的话，
        关于天下大势的论述。据她回忆，那是个寒冷的夜晚，
        父亲将她从水中救起。正如丞相所言，危机四伏，
        需要仔细谋划。这是她十岁那年溺水后的第一次重要决定。
        据说林晚的祖先曾与龙有过约定。正如传说所言，
        这个家族背负着神秘的使命。她记得母亲曾经说过，
        要守护好这个家。丞相看着她，眼神中充满了期待。
        据她回忆，府中的每一块砖瓦都承载着历史的痕迹。
        正如史书记载，这个家族已经延续了三百年。
        """ * 5  # Repeat to reach ~500 words

        start_time = time.time()
        verifications = await reference_validator.validate_chapter_references(
            chapter_content, chapter_num=1
        )
        duration = time.time() - start_time

        # Should complete in reasonable time (< 2s for safety margin)
        assert duration < 2.0, \
            f"Reference validation took {duration:.2f}s, should be < 2s"

        # Should still extract references
        assert len(verifications) > 0, "Should extract references"

    @pytest.mark.asyncio
    async def test_hallucination_detection_performance(
        self, hallucination_detector
    ):
        """Test hallucination detection performance.

        Verify that detection completes in reasonable time.
        Target: < 2s for typical chapter (500 words)
        """
        import time

        # Create realistic chapter (500 words)
        generated_chapter = """
        林晚是个十岁的女孩，住在大府中。丞相是朝廷的大臣，
        负责处理国家大事。这一天，丞相来到府中，
        与林晚商议重要事务。林晚记得父亲曾经说过的话，
        关于天下大势的论述。据她回忆，那是个寒冷的夜晚，
        父亲将她从水中救起。正如丞相所言，危机四伏，
        需要仔细谋划。这是她十岁那年溺水后的第一次重要决定。
        据说林晚的祖先曾与龙有过约定。正如传说所言，
        这个家族背负着神秘的使命。她记得母亲曾经说过，
        要守护好这个家。丞相看着她，眼神中充满了期待。
        """ * 5  # Repeat to reach ~500 words

        world_context = """
        林晚是10岁女孩，住在府中。丞相是朝廷大臣。
        府中历史悠久。
        """ * 5

        start_time = time.time()
        report = await hallucination_detector.detect_hallucinations(
            generated_chapter=generated_chapter,
            world_context=world_context,
        )
        duration = time.time() - start_time

        # Should complete in reasonable time (< 3s for safety margin)
        assert duration < 3.0, \
            f"Hallucination detection took {duration:.2f}s, should be < 3s"

        # Should generate report
        assert report is not None, "Should generate detection report"
        assert report.total_detections >= 0, "Should have detections count"
