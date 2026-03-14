"""Unit tests for summary compression functionality.

This module tests the SummaryCompressor class and its integration with
HierarchicalStoryState for managing token budgets.
"""

from pathlib import Path

import pytest

from src.novel_agent.novel.compression import (
    COMPRESSION_THRESHOLDS,
    SummaryCompressor,
)
from src.novel_agent.novel.hierarchical_state import HierarchicalStoryState
from src.novel_agent.novel.summaries import ArcSummary, ChapterSummary


class TestSummaryCompressorInit:
    """Test SummaryCompressor initialization."""

    def test_default_initialization(self) -> None:
        """Test default compressor initialization."""
        compressor = SummaryCompressor()
        assert compressor.llm is None
        assert compressor.enable_llm is True
        assert compressor.hybrid_threshold == 1.5

    def test_initialization_without_llm(self) -> None:
        """Test compressor with LLM disabled."""
        compressor = SummaryCompressor(enable_llm=False)
        assert compressor.enable_llm is False

    def test_initialization_with_custom_threshold(self) -> None:
        """Test compressor with custom hybrid threshold."""
        compressor = SummaryCompressor(hybrid_threshold=2.0)
        assert compressor.hybrid_threshold == 2.0


class TestTokenEstimation:
    """Test token estimation functionality."""

    def test_estimate_empty_text(self) -> None:
        """Test token estimation for empty text."""
        compressor = SummaryCompressor()
        assert compressor._estimate_tokens("") == 0

    def test_estimate_chinese_text(self) -> None:
        """Test token estimation for Chinese text."""
        compressor = SummaryCompressor()
        # Chinese characters ~1 token each
        text = "这是一个测试。"
        tokens = compressor._estimate_tokens(text)
        assert tokens > 0
        assert tokens >= len(text) * 0.5  # At least half

    def test_estimate_english_text(self) -> None:
        """Test token estimation for English text."""
        compressor = SummaryCompressor()
        # English ~0.25 tokens per character
        text = "This is a test."
        tokens = compressor._estimate_tokens(text)
        assert tokens > 0

    def test_estimate_mixed_text(self) -> None:
        """Test token estimation for mixed Chinese/English text."""
        compressor = SummaryCompressor()
        text = "这是一个test。Mixed content here。"
        tokens = compressor._estimate_tokens(text)
        assert tokens > 0


class TestKeyPointExtraction:
    """Test key point extraction functionality."""

    def test_extract_from_empty_text(self) -> None:
        """Test extraction from empty text."""
        compressor = SummaryCompressor()
        points = compressor._extract_key_points("")
        assert points == []

    def test_extract_single_sentence(self) -> None:
        """Test extraction from single sentence."""
        compressor = SummaryCompressor()
        text = "This is a single sentence."
        points = compressor._extract_key_points(text)
        assert len(points) == 1
        assert points[0] == text

    def test_extract_multiple_sentences(self) -> None:
        """Test extraction from multiple sentences."""
        compressor = SummaryCompressor()
        text = "First sentence. Second sentence. Third sentence."
        points = compressor._extract_key_points(text, num_points=2)
        assert len(points) <= 2
        assert "First sentence" in points[0]

    def test_extract_with_keywords(self) -> None:
        """Test extraction prioritizes sentences with keywords."""
        compressor = SummaryCompressor()
        text = "This is normal. This is key important information. This is also normal."
        points = compressor._extract_key_points(text, num_points=2)
        # Should include sentence with "important"
        assert any("important" in p for p in points)


class TestSmartTruncation:
    """Test smart truncation functionality."""

    def test_truncate_empty_text(self) -> None:
        """Test truncation of empty text."""
        compressor = SummaryCompressor()
        result = compressor._smart_truncate("", max_tokens=100)
        assert result == ""

    def test_no_truncation_needed(self) -> None:
        """Test text that doesn't need truncation."""
        compressor = SummaryCompressor()
        text = "Short text."
        result = compressor._smart_truncate(text, max_tokens=100)
        assert result == text

    def test_truncation_at_sentence_boundary(self) -> None:
        """Test truncation preserves sentence boundaries."""
        compressor = SummaryCompressor()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = compressor._smart_truncate(text, max_tokens=15)  # Increased to ensure at least one sentence fits
        assert result.endswith("...")
        # Should not cut in middle of sentence (should have at least one complete sentence with period)
        assert "." in result[:-3]

    def test_truncation_long_first_sentence(self) -> None:
        """Test truncation when first sentence is too long."""
        compressor = SummaryCompressor()
        text = "This is a very long first sentence that goes on and on and contains many words. Second sentence."
        result = compressor._smart_truncate(text, max_tokens=3)
        assert result.endswith("...")
        assert len(result) < len(text)


class TestCompressArcSummary:
    """Test arc summary compression."""

    def test_no_compression_needed(self) -> None:
        """Test arc summary that doesn't need compression."""
        compressor = SummaryCompressor()
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary="Short summary.",
        )
        result = compressor.compress_arc_summary(summary, max_tokens=400)
        assert result.summary == summary.summary

    def test_compression_reduces_size(self) -> None:
        """Test that compression actually reduces summary size."""
        compressor = SummaryCompressor()
        # Create a long summary
        long_text = "This is a sentence. " * 50  # Very long summary
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary=long_text,
            major_events=["Event " + str(i) for i in range(20)],
            character_arcs={f"Character {i}": f"Arc {i}" for i in range(10)},
        )
        result = compressor.compress_arc_summary(summary, max_tokens=50)

        # Should be compressed
        assert len(result.summary) < len(summary.summary)
        # Should limit events
        assert len(result.major_events) <= 5
        # Should limit character arcs
        assert len(result.character_arcs) <= 3

    def test_compression_preserves_essential_fields(self) -> None:
        """Test that compression preserves essential arc fields."""
        compressor = SummaryCompressor()
        summary = ArcSummary(
            arc_number=2,
            start_chapter=11,
            end_chapter=20,
            title="Important Arc",
            summary="A" * 1000,
        )
        result = compressor.compress_arc_summary(summary, max_tokens=50)

        assert result.arc_number == summary.arc_number
        assert result.start_chapter == summary.start_chapter
        assert result.end_chapter == summary.end_chapter
        assert result.title == summary.title

    def test_original_unchanged(self) -> None:
        """Test that original summary is not modified."""
        compressor = SummaryCompressor()
        original_summary = "Original summary text. " * 50
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary=original_summary,
        )
        result = compressor.compress_arc_summary(summary, max_tokens=50)

        assert summary.summary == original_summary
        assert result.summary != original_summary


class TestCompressChapterSummary:
    """Test chapter summary compression."""

    def test_no_compression_needed(self) -> None:
        """Test chapter summary that doesn't need compression."""
        compressor = SummaryCompressor()
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary="Short summary.",
        )
        result = compressor.compress_chapter_summary(summary, max_tokens=250)
        assert result.summary == summary.summary

    def test_compression_reduces_size(self) -> None:
        """Test that compression actually reduces chapter summary size."""
        compressor = SummaryCompressor()
        long_text = "This is a sentence. " * 50
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary=long_text,
            key_events=["Event " + str(i) for i in range(10)],
            character_changes={f"Char {i}": f"Change {i}" for i in range(5)},
        )
        result = compressor.compress_chapter_summary(summary, max_tokens=50)

        assert len(result.summary) < len(summary.summary)
        assert len(result.key_events) <= 3
        assert len(result.character_changes) <= 2

    def test_compression_preserves_essential_fields(self) -> None:
        """Test that compression preserves essential chapter fields."""
        compressor = SummaryCompressor()
        summary = ChapterSummary(
            chapter_number=5,
            title="Important Chapter",
            summary="A" * 1000,
            word_count=5000,
            sentiment="dark",
        )
        result = compressor.compress_chapter_summary(summary, max_tokens=50)

        assert result.chapter_number == summary.chapter_number
        assert result.title == summary.title
        assert result.word_count == summary.word_count
        assert result.sentiment == summary.sentiment


class TestCompressText:
    """Test general text compression."""

    def test_compress_empty_text(self) -> None:
        """Test compression of empty text."""
        compressor = SummaryCompressor()
        result = compressor.compress_text("", max_tokens=100)
        assert result.success is True
        assert result.data["text"] == ""

    def test_no_compression_needed_text(self) -> None:
        """Test text that doesn't need compression."""
        compressor = SummaryCompressor()
        text = "Short text."
        result = compressor.compress_text(text, max_tokens=100)
        assert result.success is True
        assert result.method == "none"
        assert result.data["text"] == text

    def test_smart_truncate_compression(self) -> None:
        """Test smart truncate compression method."""
        compressor = SummaryCompressor()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = compressor.compress_text(text, max_tokens=5)
        assert result.success is True
        assert result.method == "smart_truncate"
        assert result.data["text"].endswith("...")

    def test_hard_truncate_compression(self) -> None:
        """Test hard truncate compression method."""
        compressor = SummaryCompressor()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = compressor.compress_text(text, max_tokens=5, preserve_sentences=False)
        assert result.success is True
        assert result.method == "hard_truncate"


class TestShouldCompress:
    """Test compression detection."""

    def test_should_compress_arc_true(self) -> None:
        """Test detecting arc summary that needs compression."""
        compressor = SummaryCompressor()
        long_text = "A" * 1000  # Long text
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary=long_text,
        )
        assert compressor.should_compress_arc(summary, max_tokens=10) is True

    def test_should_compress_arc_false(self) -> None:
        """Test detecting arc summary that doesn't need compression."""
        compressor = SummaryCompressor()
        summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary="Short.",
        )
        assert compressor.should_compress_arc(summary, max_tokens=400) is False

    def test_should_compress_chapter_true(self) -> None:
        """Test detecting chapter summary that needs compression."""
        compressor = SummaryCompressor()
        long_text = "A" * 1000
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary=long_text,
        )
        assert compressor.should_compress_chapter(summary, max_tokens=10) is True

    def test_should_compress_chapter_false(self) -> None:
        """Test detecting chapter summary that doesn't need compression."""
        compressor = SummaryCompressor()
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary="Short.",
        )
        assert compressor.should_compress_chapter(summary, max_tokens=250) is False


class TestCompressionThresholds:
    """Test compression threshold constants."""

    def test_arc_summary_threshold(self) -> None:
        """Test arc summary threshold value."""
        assert COMPRESSION_THRESHOLDS["arc_summary"] == 400

    def test_chapter_summary_threshold(self) -> None:
        """Test chapter summary threshold value."""
        assert COMPRESSION_THRESHOLDS["chapter_summary"] == 250

    def test_global_state_threshold(self) -> None:
        """Test global state threshold value."""
        assert COMPRESSION_THRESHOLDS["global_state"] == 500


class TestHierarchicalStateCompression:
    """Test compression integration with HierarchicalStoryState."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    def test_state_with_compression_enabled(self, temp_storage: Path) -> None:
        """Test that compression is enabled by default."""
        state = HierarchicalStoryState(temp_storage, "test_novel")
        assert state._enable_compression is True
        assert state._compressor is not None

    def test_state_with_compression_disabled(self, temp_storage: Path) -> None:
        """Test that compression can be disabled."""
        state = HierarchicalStoryState(temp_storage, "test_novel", enable_compression=False)
        assert state._enable_compression is False

    def test_save_arc_summary_with_compression(self, temp_storage: Path) -> None:
        """Test that arc summaries are compressed when saved."""
        state = HierarchicalStoryState(temp_storage, "test_novel")

        # Create a long arc summary
        long_summary = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test Arc",
            summary="This is a very long summary. " * 100,
            major_events=["Event " + str(i) for i in range(20)],
        )

        # Save it
        state.save_arc_summary(long_summary)

        # Load it back
        loaded = state.get_arc_summary(1)
        assert loaded is not None
        # Should be compressed (shorter than original)
        assert len(loaded.summary) < len(long_summary.summary)

    def test_save_chapter_summary_with_compression(self, temp_storage: Path) -> None:
        """Test that chapter summaries are compressed when saved."""
        state = HierarchicalStoryState(temp_storage, "test_novel")

        # Create a long chapter summary
        long_summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary="This is a very long summary. " * 50,
            key_events=["Event " + str(i) for i in range(10)],
        )

        # Save it
        state.save_chapter_summary(long_summary)

        # Load it back
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        # Should be compressed
        assert len(loaded.summary) < len(long_summary.summary)

    def test_save_without_compression(self, temp_storage: Path) -> None:
        """Test that summaries are not compressed when disabled."""
        state = HierarchicalStoryState(temp_storage, "test_novel", enable_compression=False)

        original_text = "This is the summary text."
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary=original_text,
        )

        state.save_chapter_summary(summary)
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.summary == original_text

    def test_short_summary_not_compressed(self, temp_storage: Path) -> None:
        """Test that short summaries are not unnecessarily compressed."""
        state = HierarchicalStoryState(temp_storage, "test_novel")

        short_text = "Short summary."
        summary = ChapterSummary(
            chapter_number=1,
            title="Test Chapter",
            summary=short_text,
        )

        state.save_chapter_summary(summary)
        loaded = state.get_chapter_summary(1)
        assert loaded is not None
        assert loaded.summary == short_text
