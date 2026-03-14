"""Tests for chapter summarization system."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.llm.base import LLMResponse
from src.novel_agent.novel.chapter_summarizer import (
    ArcSummarizer,
    ChapterSummarizer,
)
from src.novel_agent.novel.summaries import ChapterSummary


class TestChapterSummarizer:
    """Test ChapterSummarizer class."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM instance."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def summarizer(self, mock_llm: MagicMock) -> ChapterSummarizer:
        """Create a ChapterSummarizer instance."""
        return ChapterSummarizer(mock_llm)

    @pytest.mark.asyncio
    async def test_summarize_basic(
        self, summarizer: ChapterSummarizer, mock_llm: MagicMock
    ) -> None:
        """Test basic chapter summarization."""
        # Mock LLM response
        mock_llm.generate_with_system.return_value = LLMResponse(
            content="""{
                "summary": "英雄开始他的冒险旅程，离开了家乡。",
                "key_events": ["离开家乡", "遇到导师", "接受任务"],
                "character_changes": {"英雄": "变得更加坚定"},
                "location": "小村庄",
                "plot_threads_advanced": ["主线任务"],
                "plot_threads_resolved": [],
                "sentiment": "hopeful"
            }""",
            tokens_used=100,
            model="test",
        )

        summary = await summarizer.summarize(
            chapter_number=1,
            title="开始",
            content="这是章节内容...",
        )

        assert summary.chapter_number == 1
        assert summary.title == "开始"
        assert "英雄" in summary.summary
        assert len(summary.key_events) == 3
        assert summary.sentiment == "hopeful"

    @pytest.mark.asyncio
    async def test_summarize_calculates_word_count(
        self, summarizer: ChapterSummarizer, mock_llm: MagicMock
    ) -> None:
        """Test that word count is calculated when not provided."""
        mock_llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "测试摘要", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )

        content = "one two three four five"
        summary = await summarizer.summarize(
            chapter_number=1,
            title="Test",
            content=content,
        )

        assert summary.word_count == 5

    @pytest.mark.asyncio
    async def test_summarize_uses_provided_word_count(
        self, summarizer: ChapterSummarizer, mock_llm: MagicMock
    ) -> None:
        """Test that provided word count is used."""
        mock_llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "测试", "key_events": [], "sentiment": "neutral"}',
            tokens_used=50,
            model="test",
        )

        summary = await summarizer.summarize(
            chapter_number=1,
            title="Test",
            content="short content",
            word_count=1000,
        )

        assert summary.word_count == 1000

    @pytest.mark.asyncio
    async def test_summarize_handles_llm_failure(
        self, summarizer: ChapterSummarizer, mock_llm: MagicMock
    ) -> None:
        """Test graceful handling of LLM failures."""
        mock_llm.generate_with_system.side_effect = Exception("LLM error")

        summary = await summarizer.summarize(
            chapter_number=1,
            title="Test",
            content="这是一些测试内容。" * 50,
        )

        # Should return fallback summary
        assert summary.chapter_number == 1
        assert summary.title == "Test"
        assert len(summary.summary) > 0
        assert summary.sentiment == "neutral"


class TestContentTruncation:
    """Test content truncation logic."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM instance."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def summarizer(self, mock_llm: MagicMock) -> ChapterSummarizer:
        """Create a ChapterSummarizer instance."""
        return ChapterSummarizer(mock_llm)

    def test_short_content_not_truncated(self, summarizer: ChapterSummarizer) -> None:
        """Test that short content is not truncated."""
        content = "短内容"
        result = summarizer._truncate_content(content, max_chars=1000)
        assert result == content

    def test_long_content_is_truncated(self, summarizer: ChapterSummarizer) -> None:
        """Test that long content is truncated."""
        content = "x" * 10000
        result = summarizer._truncate_content(content, max_chars=1000)
        assert len(result) < 1100  # Some overhead for ellipsis
        assert "省略" in result

    def test_truncation_keeps_beginning_and_end(self, summarizer: ChapterSummarizer) -> None:
        """Test that truncation preserves start and end."""
        content = "START" + "x" * 10000 + "END"
        result = summarizer._truncate_content(content, max_chars=1000)
        assert "START" in result
        assert "END" in result


class TestSummaryTruncation:
    """Test summary truncation logic."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def summarizer(self, mock_llm: MagicMock) -> ChapterSummarizer:
        return ChapterSummarizer(mock_llm, max_summary_length=100)

    def test_short_summary_not_truncated(self, summarizer: ChapterSummarizer) -> None:
        """Test that short summary is not truncated."""
        summary = "这是一个简短的摘要。"
        result = summarizer._truncate_summary(summary)
        assert result == summary

    def test_long_summary_is_truncated(self, summarizer: ChapterSummarizer) -> None:
        """Test that long summary is truncated."""
        summary = "x" * 200
        result = summarizer._truncate_summary(summary)
        assert len(result) <= 100
        assert result.endswith("...")


class TestLLMResponseParsing:
    """Test LLM response parsing."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def summarizer(self, mock_llm: MagicMock) -> ChapterSummarizer:
        return ChapterSummarizer(mock_llm)

    def test_parse_clean_json(self, summarizer: ChapterSummarizer) -> None:
        """Test parsing clean JSON response."""
        response = '{"summary": "测试", "key_events": ["事件1"]}'
        result = summarizer._parse_llm_response(response)
        assert result["summary"] == "测试"
        assert result["key_events"] == ["事件1"]

    def test_parse_json_in_code_block(self, summarizer: ChapterSummarizer) -> None:
        """Test parsing JSON from code block."""
        response = """```json
{"summary": "测试", "key_events": ["事件1"]}
```"""
        result = summarizer._parse_llm_response(response)
        assert result["summary"] == "测试"

    def test_parse_json_with_extra_text(self, summarizer: ChapterSummarizer) -> None:
        """Test parsing JSON with surrounding text."""
        response = """这是分析结果：
{"summary": "测试", "key_events": ["事件1"]}
以上是摘要。"""
        result = summarizer._parse_llm_response(response)
        assert result["summary"] == "测试"

    def test_parse_invalid_json_returns_empty(self, summarizer: ChapterSummarizer) -> None:
        """Test that invalid JSON returns empty dict."""
        response = "这不是JSON"
        result = summarizer._parse_llm_response(response)
        assert result == {}


class TestFallbackSummary:
    """Test fallback summary generation."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def summarizer(self, mock_llm: MagicMock) -> ChapterSummarizer:
        return ChapterSummarizer(mock_llm)

    def test_fallback_uses_content_start(self, summarizer: ChapterSummarizer) -> None:
        """Test that fallback uses beginning of content."""
        content = "这是开头内容。" + "填充" * 100
        result = summarizer._fallback_summary(content)
        assert "这是开头内容" in result

    def test_fallback_ends_at_sentence(self, summarizer: ChapterSummarizer) -> None:
        """Test that fallback tries to end at sentence boundary."""
        content = "这是第一句话。这是第二句话。这是第三句话。" * 20
        result = summarizer._fallback_summary(content)
        # Should end with a sentence
        assert result.endswith("。") or result.endswith("...")


class TestArcSummarizer:
    """Test ArcSummarizer class."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def arc_summarizer(self, mock_llm: MagicMock) -> ArcSummarizer:
        return ArcSummarizer(mock_llm)

    @pytest.fixture
    def chapter_summaries(self) -> list[ChapterSummary]:
        """Create sample chapter summaries."""
        return [
            ChapterSummary(
                chapter_number=1,
                title="第一章",
                summary="英雄离开家乡开始冒险。",
                key_events=["离开家乡"],
            ),
            ChapterSummary(
                chapter_number=2,
                title="第二章",
                summary="英雄遇到了导师。",
                key_events=["遇到导师"],
            ),
        ]

    @pytest.mark.asyncio
    async def test_summarize_arc_basic(
        self,
        arc_summarizer: ArcSummarizer,
        mock_llm: MagicMock,
        chapter_summaries: list[ChapterSummary],
    ) -> None:
        """Test basic arc summarization."""
        mock_llm.generate_with_system.return_value = LLMResponse(
            content="""{
                "title": "启程篇",
                "summary": "英雄开始他的冒险旅程。",
                "major_events": ["离开家乡", "遇到导师"],
                "character_arcs": {"英雄": "从普通人成长为冒险者"},
                "world_changes": [],
                "plot_threads_status": {"主线": "active"},
                "themes": ["成长", "冒险"]
            }""",
            tokens_used=200,
            model="test",
        )

        result = await arc_summarizer.summarize_arc(
            arc_number=1,
            start_chapter=1,
            end_chapter=2,
            chapter_summaries=chapter_summaries,
        )

        assert result["title"] == "启程篇"
        assert len(result["major_events"]) == 2
        assert "成长" in result["themes"]

    @pytest.mark.asyncio
    async def test_summarize_arc_handles_failure(
        self,
        arc_summarizer: ArcSummarizer,
        mock_llm: MagicMock,
        chapter_summaries: list[ChapterSummary],
    ) -> None:
        """Test graceful handling of LLM failures."""
        mock_llm.generate_with_system.side_effect = Exception("LLM error")

        result = await arc_summarizer.summarize_arc(
            arc_number=1,
            start_chapter=1,
            end_chapter=2,
            chapter_summaries=chapter_summaries,
        )

        # Should return fallback data
        assert "第1卷" in result["title"]
        assert result["major_events"] == []


class TestArcSummarizerParsing:
    """Test ArcSummarizer response parsing."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def arc_summarizer(self, mock_llm: MagicMock) -> ArcSummarizer:
        return ArcSummarizer(mock_llm)

    def test_parse_clean_json(self, arc_summarizer: ArcSummarizer) -> None:
        """Test parsing clean JSON."""
        response = '{"title": "测试", "summary": "摘要"}'
        result = arc_summarizer._parse_llm_response(response)
        assert result["title"] == "测试"

    def test_parse_json_in_code_block(self, arc_summarizer: ArcSummarizer) -> None:
        """Test parsing JSON from code block."""
        response = """```json
{"title": "测试", "summary": "摘要"}
```"""
        result = arc_summarizer._parse_llm_response(response)
        assert result["title"] == "测试"

    def test_fallback_arc_data(self, arc_summarizer: ArcSummarizer) -> None:
        """Test fallback arc data generation."""
        result = arc_summarizer._fallback_arc_data(
            arc_number=2,
            start_chapter=11,
            end_chapter=20,
        )

        assert "第2卷" in result["title"]
        assert "11" in result["summary"]
        assert "20" in result["summary"]
