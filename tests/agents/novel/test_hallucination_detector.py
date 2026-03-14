# tests/novel/test_hallucination_detector.py
"""Comprehensive tests for HallucinationDetector.

Tests cover:
- Initialization and configuration
- Rule-based detection patterns
- Vector similarity detection
- Hallucination classification
- Confidence scoring
- Integration with VectorStore
- Chapter 5 hallucinated reference case
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.novel.hallucination_detector import (
    ConfidenceLevel,
    Hallucination,
    HallucinationDetector,
    HallucinationReport,
    HallucinationType,
)


class TestHallucinationDetectorInit:
    """Test HallucinationDetector initialization."""

    def test_basic_initialization(self):
        """Test basic initialization without vector store."""
        detector = HallucinationDetector()

        assert detector.vector_store is None
        assert detector.threshold == 0.8
        assert detector.use_hhem is False
        assert detector.min_text_length == 20
        assert len(detector._compiled_quote_patterns) > 0
        assert len(detector._compiled_fact_patterns) > 0
        assert len(detector._compiled_creative_patterns) > 0

    def test_initialization_with_vector_store(self):
        """Test initialization with vector store."""
        mock_store = MagicMock()
        detector = HallucinationDetector(vector_store=mock_store)

        assert detector.vector_store == mock_store

    def test_custom_threshold(self):
        """Test custom threshold."""
        detector = HallucinationDetector(threshold=0.9)

        assert detector.threshold == 0.9

    def test_hhem_enabled(self):
        """Test HHEM enabled."""
        detector = HallucinationDetector(use_hhem=True)

        assert detector.use_hhem is True


class TestConfidenceLevel:
    """Test confidence level determination."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_high_confidence(self, detector):
        """Test high confidence level."""
        level = detector._get_confidence_level(0.95)
        assert level == ConfidenceLevel.HIGH

    def test_medium_confidence(self, detector):
        """Test medium confidence level."""
        level = detector._get_confidence_level(0.8)
        assert level == ConfidenceLevel.MEDIUM

    def test_low_confidence(self, detector):
        """Test low confidence level."""
        level = detector._get_confidence_level(0.5)
        assert level == ConfidenceLevel.LOW

    def test_boundary_high(self, detector):
        """Test high confidence boundary."""
        level = detector._get_confidence_level(0.9)
        assert level == ConfidenceLevel.HIGH

    def test_boundary_medium(self, detector):
        """Test medium confidence boundary."""
        level = detector._get_confidence_level(0.7)
        assert level == ConfidenceLevel.MEDIUM


class TestSentenceExtraction:
    """Test sentence extraction."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector(min_text_length=5)
    def test_extract_chinese_sentences(self, detector):
        """Test extracting Chinese sentences."""
        text = "这是第一句。这是第二句。这是第三句。"
        sentences = detector._extract_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "这是第一句"

    def test_extract_english_sentences(self, detector):
        """Test extracting English sentences."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = detector._extract_sentences(text)

        assert len(sentences) == 3

    def test_extract_mixed_sentences(self, detector):
        """Test extracting mixed language sentences."""
        text = "Alice said hello. 然后她离开了。 She was sad!"
        sentences = detector._extract_sentences(text)

        assert len(sentences) == 3

    def test_filter_short_sentences(self, detector):
        """Test filtering of short sentences."""
        text = "短。这是一句比较长的句子。"
        sentences = detector._extract_sentences(text)

        assert len(sentences) == 1
        assert "比较长的句子" in sentences[0]


class TestCreativeFictionDetection:
    """Test creative fiction detection."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_detect_chinese_simile(self, detector):
        """Test detecting Chinese similes."""
        assert detector._is_creative_fiction("他仿佛看到了希望")
        assert detector._is_creative_fiction("她好像一只蝴蝶")
        assert detector._is_creative_fiction("这似乎是个好主意")

    def test_detect_chinese_uncertainty(self, detector):
        """Test detecting Chinese uncertainty markers."""
        assert detector._is_creative_fiction("也许明天会下雨")
        assert detector._is_creative_fiction("可能他会来")
        assert detector._is_creative_fiction("大概是这个意思")

    def test_detect_chinese_imagination(self, detector):
        """Test detecting Chinese imagination markers."""
        assert detector._is_creative_fiction("她在幻想中看到了未来")
        assert detector._is_creative_fiction("他在梦境中与父亲相见")
        assert detector._is_creative_fiction("这只是想象")

    def test_detect_chinese_legend(self, detector):
        """Test detecting Chinese legend markers."""
        assert detector._is_creative_fiction("据说这片森林有精灵")
        assert detector._is_creative_fiction("传说中有一条巨龙")
        assert detector._is_creative_fiction("相传古代有一位英雄")

    def test_detect_english_creative(self, detector):
        """Test detecting English creative markers."""
        assert detector._is_creative_fiction("According to folklore, this is true")
        assert detector._is_creative_fiction("The legend says he was immortal")
        assert detector._is_creative_fiction("Rumor has it that...")

    def test_not_creative(self, detector):
        """Test non-creative text."""
        assert not detector._is_creative_fiction("她十岁那年溺水了")
        assert not detector._is_creative_fiction("He was born in 1990")


class TestQuotationExtraction:
    """Test quotation extraction."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_extract_chinese_quotation(self, detector):
        """Test extracting Chinese quotations."""
        text = '林晚说过："天下大势，分久必合"'
        quotes = detector._extract_quotations(text)

        assert len(quotes) == 1
        assert quotes[0]["speaker"] == "林晚"
        assert quotes[0]["quote"] == "天下大势，分久必合"

    def test_extract_english_quotation(self, detector):
        """Test extracting English quotations."""
        text = 'Alice said: "The world is round"'
        quotes = detector._extract_quotations(text)

        assert len(quotes) == 1
        assert quotes[0]["speaker"] == "Alice"
        assert quotes[0]["quote"] == "The world is round"

    def test_extract_multiple_quotations(self, detector):
        """Test extracting multiple quotations."""
        text = '林晚说过："第一句"。王明说过："第二句"'
        quotes = detector._extract_quotations(text)

        assert len(quotes) == 2

    def test_no_quotations(self, detector):
        """Test text with no quotations."""
        text = "这是一段普通文本，没有引号。"
        quotes = detector._extract_quotations(text)

        assert len(quotes) == 0


class TestFactualClaimExtraction:
    """Test factual claim extraction."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_extract_chinese_age_claim(self, detector):
        """Test extracting Chinese age claims."""
        text = "她十岁那年溺水了"
        claims = detector._extract_factual_claims(text)

        assert len(claims) >= 1
        assert claims[0]["value"] == "十"

    def test_extract_chinese_birth_place(self, detector):
        """Test extracting Chinese birth place."""
        text = "她出生于北京"
        claims = detector._extract_factual_claims(text)

        assert len(claims) >= 1

    def test_extract_english_age_claim(self, detector):
        """Test extracting English age claims."""
        text = "She drowned at the age of ten"
        claims = detector._extract_factual_claims(text)

        assert len(claims) >= 1

    def test_extract_year_claim(self, detector):
        """Test extracting year claims."""
        text = "This happened in 1990"
        claims = detector._extract_factual_claims(text)

        assert len(claims) >= 1


class TestRuleBasedDetection:
    """Test rule-based hallucination detection."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_detect_unknown_speaker_quotation(self, detector):
        """Test detecting quotation from unknown speaker."""
        text = '林晚说过："天下大势，分久必合"'
        context = "王明是一个普通学生。"  # 林晚不在上下文中

        results = detector._detect_via_rules(text, context)

        assert len(results) > 0
        assert any(h.hallucination_type == HallucinationType.FACTUAL_HALLUCINATION for h in results)

    def test_detect_known_speaker_quotation(self, detector):
        """Test detecting quotation from known speaker (unverified)."""
        text = '林晚说过："天下大势，分久必合"'
        context = "林晚是故事的主角，一个普通的女孩。"  # 林晚在上下文中

        results = detector._detect_via_rules(text, context)

        # Should detect as unverifiable since quote is not verified
        assert len(results) > 0
        assert any(h.hallucination_type == HallucinationType.UNVERIFIABLE for h in results)

    def test_creative_quotation_not_flagged_as_error(self, detector):
        """Test that creative quotations are not flagged as errors."""
        text = '据说林晚说过："天下大势，分久必合"'
        context = "林晚是故事的主角。"

        results = detector._detect_via_rules(text, context)

        # Should be classified as creative fiction, not factual hallucination
        creative_results = [
            h for h in results if h.hallucination_type == HallucinationType.CREATIVE_FICTION
        ]
        assert len(creative_results) > 0


class TestVectorSimilarityDetection:
    """Test vector similarity-based detection."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        store = MagicMock()
        store.query_similar = AsyncMock()
        return store

    @pytest.mark.asyncio
    async def test_high_similarity_detection(self, mock_vector_store):
        """Test detection with high similarity."""
        mock_vector_store.query_similar.return_value = [
            MagicMock(score=0.95, id="fact_1", metadata={})
        ]
        detector = HallucinationDetector(vector_store=mock_vector_store)

        similarity, reason = await detector._detect_via_vector_similarity(
            "林晚是一个女孩", "林晚是一个十岁的女孩"
        )

        assert similarity >= 0.85
        assert "High similarity" in reason

    @pytest.mark.asyncio
    async def test_low_similarity_detection(self, mock_vector_store):
        """Test detection with low similarity."""
        mock_vector_store.query_similar.return_value = [
            MagicMock(score=0.3, id="fact_1", metadata={})
        ]
        detector = HallucinationDetector(vector_store=mock_vector_store)

        similarity, reason = await detector._detect_via_vector_similarity(
            "林晚说过天下大势", "林晚是一个十岁的女孩"
        )

        assert similarity < 0.5
        assert "Low similarity" in reason or "potential hallucination" in reason

    @pytest.mark.asyncio
    async def test_no_vector_store(self):
        """Test detection without vector store."""
        detector = HallucinationDetector()

        similarity, reason = await detector._detect_via_vector_similarity(
            "Some text", "Some context"
        )

        assert similarity == 0.5
        assert "not available" in reason


class TestHallucinationClassification:
    """Test hallucination classification."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    def test_classify_creative_fiction(self, detector):
        """Test classifying creative fiction."""
        text = "据说有一个古老的传说..."
        context = "一些世界背景信息"

        result = detector.classify_hallucination(text, context)
        assert result == HallucinationType.CREATIVE_FICTION

    def test_classify_factual_hallucination(self, detector):
        """Test classifying factual hallucination."""
        text = '未知角色说过："这是一句引言"'
        context = "只有张三和李四两个人"  # 未知角色不在上下文中

        result = detector.classify_hallucination(text, context)
        assert result == HallucinationType.FACTUAL_HALLUCINATION

    def test_classify_unverifiable(self, detector):
        """Test classifying unverifiable content."""
        text = "这是一段普通的描述性文字"
        context = "一些背景信息"

        result = detector.classify_hallucination(text, context)
        # Should be unverifiable since there's no quotation or factual claim
        assert result in [
            HallucinationType.UNVERIFIABLE,
            HallucinationType.POTENTIAL_ERROR,
        ]


class TestFullDetection:
    """Test full hallucination detection workflow."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    @pytest.fixture
    def detector_with_store(self):
        """Create a detector with mock vector store."""
        store = MagicMock()
        store.query_similar = AsyncMock(return_value=[MagicMock(score=0.5, id="1", metadata={})])
        return HallucinationDetector(vector_store=store)

    @pytest.mark.asyncio
    async def test_detect_chapter5_hallucination(self, detector):
        """Test detecting Chapter 5 hallucinated reference.

        This is the key test case from the plan:
        - Generated text: "林晚说过天下大势，分久必合"
        - World context: 林晚是10岁女孩，从未说过这句话
        """
        generated_chapter = '林晚说过："天下大势，分久必合"'
        world_context = "林晚是一个十岁的女孩，性格内向，从未学过历史，也没有说过关于天下大势的话。"

        report = await detector.detect_hallucinations(generated_chapter, world_context)

        assert isinstance(report, HallucinationReport)
        assert len(report.factual_hallucinations) > 0
        assert any("林晚" in h.text for h in report.factual_hallucinations)

    @pytest.mark.asyncio
    async def test_detect_clean_text(self, detector):
        """Test detecting no hallucinations in clean text."""
        generated_chapter = "林晚是一个十岁的女孩，性格内向。"
        world_context = "林晚是一个十岁的女孩，性格内向。"

        report = await detector.detect_hallucinations(generated_chapter, world_context)

        assert isinstance(report, HallucinationReport)
        assert report.is_clean is True

    @pytest.mark.asyncio
    async def test_detect_creative_not_flagged(self, detector):
        """Test that creative content is not flagged as error."""
        generated_chapter = "据说传说中有一条巨龙守护着这座山。"
        world_context = "这是一座普通的山。"

        report = await detector.detect_hallucinations(generated_chapter, world_context)

        # Creative content should not be flagged as factual hallucination
        factual_errors = [
            h
            for h in report.hallucinations
            if h.hallucination_type == HallucinationType.FACTUAL_HALLUCINATION
        ]
        assert len(factual_errors) == 0

    @pytest.mark.asyncio
    async def test_report_structure(self, detector_with_store):
        """Test report structure."""
        report = await detector_with_store.detect_hallucinations(
            "Some text with a quotation.", "World context."
        )

        assert isinstance(report.total_detections, int)
        assert isinstance(report.detection_time_ms, float)
        assert isinstance(report.hallucinations, list)
        assert isinstance(report.factual_hallucinations, list)
        assert isinstance(report.creative_additions, list)

    @pytest.mark.asyncio
    async def test_quick_check_clean(self, detector):
        """Test quick check with clean text."""
        is_clean = await detector.quick_check("普通文本", "一些上下文")

        assert is_clean is True

    @pytest.mark.asyncio
    async def test_quick_check_with_hallucination(self, detector):
        """Test quick check with hallucination."""
        is_clean = await detector.quick_check('未知角色说过："这是一句话"', "只有张三一个人")

        assert is_clean is False


class TestHallucinationReport:
    """Test HallucinationReport methods."""

    def test_get_high_confidence_issues(self):
        """Test getting high confidence issues."""
        high_confidence_issue = Hallucination(
            text="Test hallucination",
            hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
            confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            reason="Test reason",
        )
        low_confidence_issue = Hallucination(
            text="Low confidence issue",
            hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
            confidence=0.5,
            confidence_level=ConfidenceLevel.LOW,
            reason="Test reason",
        )
        creative_issue = Hallucination(
            text="Creative addition",
            hallucination_type=HallucinationType.CREATIVE_FICTION,
            confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            reason="Test reason",
        )

        report = HallucinationReport(
            is_clean=False,
            hallucinations=[high_confidence_issue, low_confidence_issue, creative_issue],
        )

        high_issues = report.get_high_confidence_issues()
        assert len(high_issues) == 1
        assert high_issues[0] == high_confidence_issue


class TestPerformance:
    """Test performance requirements."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    @pytest.mark.asyncio
    async def test_detection_under_5_seconds(self, detector):
        """Test that detection completes under 5 seconds for a chapter."""
        import time

        # Generate a typical chapter length text
        chapter = "林晚走在街上。" * 500  # ~2500 characters
        context = "林晚是一个十岁的女孩。" * 100  # Context

        start = time.time()
        report = await detector.detect_hallucinations(chapter, context)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Detection took {elapsed:.2f}s, should be <5s"
        assert isinstance(report, HallucinationReport)


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return HallucinationDetector()

    @pytest.mark.asyncio
    async def test_empty_text(self, detector):
        """Test with empty text."""
        report = await detector.detect_hallucinations("", "Some context")

        assert isinstance(report, HallucinationReport)
        assert report.is_clean is True

    @pytest.mark.asyncio
    async def test_empty_context(self, detector):
        """Test with empty context."""
        report = await detector.detect_hallucinations("Some text", "")

        assert isinstance(report, HallucinationReport)

    @pytest.mark.asyncio
    async def test_very_long_text(self, detector):
        """Test with very long text."""
        long_text = "这是一段很长的文本。" * 1000
        context = "背景信息"

        report = await detector.detect_hallucinations(long_text, context)

        assert isinstance(report, HallucinationReport)

    @pytest.mark.asyncio
    async def test_special_characters(self, detector):
        """Test with special characters."""
        text = '角色说过："特殊字符！@#$%^&*()"'
        context = "背景"

        report = await detector.detect_hallucinations(text, context)

        assert isinstance(report, HallucinationReport)

    @pytest.mark.asyncio
    async def test_unicode_text(self, detector):
        """Test with Unicode text."""
        text = "角色说过：🎉🎊这是表情符号"
        context = "背景"

        report = await detector.detect_hallucinations(text, context)

        assert isinstance(report, HallucinationReport)
