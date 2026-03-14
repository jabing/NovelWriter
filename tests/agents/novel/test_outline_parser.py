"""Tests for the OutlineParser class."""

from __future__ import annotations

import pytest

from src.novel_agent.novel.outline_parser import (
    CHAPTER_PATTERNS,
    PLOT_KEYWORDS,
    TIME_PATTERNS,
    CharacterAppearance,
    ChapterInfo,
    OutlineParser,
    PlotThread,
    TimelineEvent,
)


class TestOutlineParserInit:
    """Tests for OutlineParser initialization."""

    def test_init(self) -> None:
        """Test basic initialization."""
        parser = OutlineParser()
        assert parser is not None
        assert parser._jieba_initialized is False


class TestSegmentText:
    """Tests for text segmentation."""

    def test_segment_empty_text(self) -> None:
        """Test segmenting empty text."""
        parser = OutlineParser()
        result = parser.segment_text("")
        assert result == []

    def test_segment_chinese_text_without_jieba(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback segmentation when jieba is not available."""
        parser = OutlineParser()
        
        monkeypatch.setattr("src.novel.outline_parser._jieba_available", False)
        
        text = "这是一段中文文本"
        result = parser.segment_text(text)
        
        assert len(result) > 0
        assert all(isinstance(s, str) for s in result)

    def test_segment_mixed_text(self) -> None:
        """Test segmenting mixed Chinese and English text."""
        parser = OutlineParser()
        
        text = "Hello 世界"
        result = parser.segment_text(text)
        
        assert len(result) > 0


class TestExtractChapterTitles:
    """Tests for chapter title extraction."""

    def test_extract_chinese_numeral_chapters(self) -> None:
        """Test extracting chapters with Chinese numerals."""
        parser = OutlineParser()
        
        text = """
第一章 命运的开端
这是第一章的内容。

第二章 风起云涌
这是第二章的内容。
"""
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[0]["title"] == "命运的开端"
        assert result[1]["number"] == 2
        assert result[1]["title"] == "风起云涌"

    def test_extract_arabic_numeral_chapters(self) -> None:
        """Test extracting chapters with Arabic numerals."""
        parser = OutlineParser()
        
        text = """
第1章 开始
内容

第2章 继续
内容
"""
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["number"] == 2

    def test_extract_english_chapters(self) -> None:
        """Test extracting English-style chapters."""
        parser = OutlineParser()
        
        text = """
Chapter 1 The Beginning
Content here.

Chapter 2 The Journey
More content.
"""
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["number"] == 2

    def test_extract_sections(self) -> None:
        """Test extracting section headers."""
        parser = OutlineParser()
        
        text = """
第一节 介绍
内容

第二节 发展
内容
"""
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 2
        assert result[0]["number"] == 1

    def test_extract_no_chapters(self) -> None:
        """Test text with no chapter markers."""
        parser = OutlineParser()
        
        text = "This is just plain text without any chapter markers."
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 0

    def test_chapter_positions(self) -> None:
        """Test that chapter positions are correct."""
        parser = OutlineParser()
        
        text = "前言\n第一章 标题\n内容\n第二章 另一标题"
        result = parser.extract_chapter_titles(text)
        
        assert len(result) == 2
        assert result[0]["position"] < result[1]["position"]


class TestChineseToInt:
    """Tests for Chinese numeral conversion."""

    def test_simple_numerals(self) -> None:
        """Test simple Chinese numerals."""
        parser = OutlineParser()
        
        assert parser._chinese_to_int("一") == 1
        assert parser._chinese_to_int("五") == 5
        assert parser._chinese_to_int("十") == 10

    def test_composite_numerals(self) -> None:
        """Test composite Chinese numerals."""
        parser = OutlineParser()
        
        assert parser._chinese_to_int("十一") == 11
        assert parser._chinese_to_int("二十") == 20
        assert parser._chinese_to_int("三十五") == 35

    def test_empty_string(self) -> None:
        """Test empty string."""
        parser = OutlineParser()
        assert parser._chinese_to_int("") == 0


class TestExtractPlotThreads:
    """Tests for plot thread extraction."""

    def test_extract_main_plot(self) -> None:
        """Test extracting main plot."""
        parser = OutlineParser()
        
        text = "主线：林晚发现丞相的秘密"
        result = parser.extract_plot_threads(text)
        
        assert len(result) == 1
        assert result[0]["type"] == "main"
        assert result[0]["keyword"] == "主线"
        assert result[0]["content"] == "林晚发现丞相的秘密"

    def test_extract_multiple_threads(self) -> None:
        """Test extracting multiple plot threads."""
        parser = OutlineParser()
        
        text = """
主线：拯救世界
支线：寻找失踪的家人
伏笔：神秘人物的真正身份
"""
        result = parser.extract_plot_threads(text)
        
        assert len(result) == 3
        types = {t["type"] for t in result}
        assert "main" in types
        assert "side" in types
        assert "foreshadowing" in types

    def test_extract_with_colon_variations(self) -> None:
        """Test extracting with different colon styles."""
        parser = OutlineParser()
        
        text1 = "主线：内容"
        text2 = "主线:内容"
        
        result1 = parser.extract_plot_threads(text1)
        result2 = parser.extract_plot_threads(text2)
        
        assert len(result1) == 1
        assert len(result2) == 1

    def test_no_plot_threads(self) -> None:
        """Test text with no plot threads."""
        parser = OutlineParser()
        
        text = "这是普通的故事内容，没有任何情节标记。"
        result = parser.extract_plot_threads(text)
        
        assert len(result) == 0

    def test_all_keyword_types(self) -> None:
        """Test all plot keyword types."""
        parser = OutlineParser()
        
        keywords = list(PLOT_KEYWORDS.keys())
        text_parts = [f"{kw}：内容{i}" for i, kw in enumerate(keywords)]
        text = "\n".join(text_parts)
        
        result = parser.extract_plot_threads(text)
        
        assert len(result) == len(keywords)


class TestDetectCharacterAppearances:
    """Tests for character appearance detection."""

    def test_single_character(self) -> None:
        """Test detecting a single character."""
        parser = OutlineParser()
        
        text = "林晚走在街上，遇到了丞相。"
        result = parser.detect_character_appearances(text, ["林晚", "丞相"])
        
        assert len(result) == 2
        
        names = {r["character_name"] for r in result}
        assert "林晚" in names
        assert "丞相" in names

    def test_multiple_appearances(self) -> None:
        """Test detecting multiple appearances of same character."""
        parser = OutlineParser()
        
        text = "林晚去了市场。林晚买了东西。林晚回家了。"
        result = parser.detect_character_appearances(text, ["林晚"])
        
        assert len(result) == 3

    def test_context_extraction(self) -> None:
        """Test that context is extracted correctly."""
        parser = OutlineParser()
        
        text = "这是一个很长的故事背景，林晚出现在中间位置，后面还有很多内容。"
        result = parser.detect_character_appearances(text, ["林晚"])
        
        assert len(result) == 1
        assert "林晚" in result[0]["context"]

    def test_empty_character_list(self) -> None:
        """Test with empty character list."""
        parser = OutlineParser()
        
        text = "任意文本"
        result = parser.detect_character_appearances(text, [])
        
        assert len(result) == 0

    def test_character_not_found(self) -> None:
        """Test when character is not in text."""
        parser = OutlineParser()
        
        text = "这是一个故事"
        result = parser.detect_character_appearances(text, ["张三"])
        
        assert len(result) == 0

    def test_compound_names_first(self) -> None:
        """Test that compound names are matched before shorter names."""
        parser = OutlineParser()
        
        text = "林晚晴出现在故事中"
        result = parser.detect_character_appearances(text, ["林晚", "林晚晴"])
        
        assert len(result) == 1
        assert result[0]["character_name"] == "林晚晴"


class TestExtractTimelineEvents:
    """Tests for timeline event extraction."""

    def test_extract_date_pattern(self) -> None:
        """Test extracting date patterns."""
        parser = OutlineParser()
        
        text = "2024年3月9日，林晚出发了。"
        result = parser.extract_timeline_events(text)
        
        assert len(result) >= 1
        assert any(e["time"] == "2024年3月9日" for e in result)

    def test_extract_relative_time(self) -> None:
        """Test extracting relative time markers."""
        parser = OutlineParser()
        
        text = "次日，他们继续前进。"
        result = parser.extract_timeline_events(text)
        
        assert len(result) >= 1
        assert any(e["time"] == "次日" for e in result)

    def test_extract_multiple_times(self) -> None:
        """Test extracting multiple time markers."""
        parser = OutlineParser()
        
        text = """
第一天，他们出发了。
三天后，他们到达目的地。
当夜，发生了意外。
"""
        result = parser.extract_timeline_events(text)
        
        times = [e["time"] for e in result if e["time"]]
        assert len(times) >= 2

    def test_no_time_markers(self) -> None:
        """Test text without time markers."""
        parser = OutlineParser()
        
        text = "这是一个普通的故事，没有时间标记。"
        result = parser.extract_timeline_events(text)
        
        assert len(result) >= 1
        assert all(e["time"] is None for e in result)

    def test_chinese_date_pattern(self) -> None:
        """Test Chinese date pattern."""
        parser = OutlineParser()
        
        text = "三月九日，春天来了。"
        result = parser.extract_timeline_events(text)
        
        assert any("三月" in (e["time"] or "") for e in result)


class TestParseOutline:
    """Tests for the main parse_outline method."""

    def test_parse_complete_outline(self) -> None:
        """Test parsing a complete outline."""
        parser = OutlineParser()
        
        outline = """
第一章 命运的开端
林晚在京城遇见了丞相，开始了他的冒险。
主线：林晚发现丞相的秘密
伏笔：丞相的真实身份

第二章 风起云涌
次日，林晚调查丞相府。
支线：结识新朋友
"""
        result = parser.parse_outline(outline)
        
        assert "chapters" in result
        assert "plot_threads" in result
        assert "timeline" in result
        assert "raw_text" in result
        
        assert len(result["chapters"]) == 2
        assert len(result["plot_threads"]) == 3
        assert len(result["timeline"]) >= 1

    def test_parse_assigns_chapters_to_threads(self) -> None:
        """Test that chapters are assigned to plot threads."""
        parser = OutlineParser()
        
        outline = """
第一章 开始
主线：第一个主线

第二章 继续
主线：第二个主线
"""
        result = parser.parse_outline(outline)
        
        threads = result["plot_threads"]
        assert len(threads) == 2
        assert threads[0]["chapter"] == 1
        assert threads[1]["chapter"] == 2

    def test_parse_empty_outline(self) -> None:
        """Test parsing empty outline."""
        parser = OutlineParser()
        
        result = parser.parse_outline("")
        
        assert len(result["chapters"]) == 0
        assert len(result["plot_threads"]) == 0


class TestGetChapterContent:
    """Tests for get_chapter_content method."""

    def test_get_existing_chapter(self) -> None:
        """Test getting an existing chapter's content."""
        parser = OutlineParser()
        
        outline = """
第一章 开始
这是第一章的内容。

第二章 结束
这是第二章的内容。
"""
        content = parser.get_chapter_content(outline, 1)
        
        assert content is not None
        assert "第一章" in content
        assert "这是第一章的内容" in content

    def test_get_nonexistent_chapter(self) -> None:
        """Test getting a nonexistent chapter."""
        parser = OutlineParser()
        
        outline = "第一章 开始\n内容"
        content = parser.get_chapter_content(outline, 99)
        
        assert content is None


class TestFindPlotThreadsByType:
    """Tests for find_plot_threads_by_type method."""

    def test_filter_by_main_plot(self) -> None:
        """Test filtering by main plot type."""
        parser = OutlineParser()
        
        threads = [
            {"type": "main", "content": "主线1"},
            {"type": "side", "content": "支线1"},
            {"type": "main", "content": "主线2"},
        ]
        
        result = parser.find_plot_threads_by_type(threads, "main")
        
        assert len(result) == 2
        assert all(t["type"] == "main" for t in result)

    def test_filter_no_matches(self) -> None:
        """Test filtering with no matches."""
        parser = OutlineParser()
        
        threads = [
            {"type": "main", "content": "主线"},
        ]
        
        result = parser.find_plot_threads_by_type(threads, "side")
        
        assert len(result) == 0


class TestGetChapterPlotThreads:
    """Tests for get_chapter_plot_threads method."""

    def test_get_threads_for_chapter(self) -> None:
        """Test getting threads for a specific chapter."""
        parser = OutlineParser()
        
        threads = [
            {"type": "main", "content": "主线", "chapter": 1},
            {"type": "side", "content": "支线", "chapter": 1},
            {"type": "main", "content": "主线", "chapter": 2},
        ]
        
        result = parser.get_chapter_plot_threads(threads, 1)
        
        assert len(result) == 2
        assert all(t["chapter"] == 1 for t in result)

    def test_get_threads_no_chapter(self) -> None:
        """Test getting threads when chapter has none."""
        parser = OutlineParser()
        
        threads = [
            {"type": "main", "content": "主线", "chapter": 1},
        ]
        
        result = parser.get_chapter_plot_threads(threads, 2)
        
        assert len(result) == 0


class TestDataclasses:
    """Tests for dataclass structures."""

    def test_chapter_info(self) -> None:
        """Test ChapterInfo dataclass."""
        info = ChapterInfo(
            number=1,
            title="标题",
            content="内容",
            start_position=0,
            end_position=100,
        )
        
        assert info.number == 1
        assert info.title == "标题"
        assert info.content == "内容"

    def test_plot_thread(self) -> None:
        """Test PlotThread dataclass."""
        thread = PlotThread(
            thread_type="main",
            content="主线内容",
            chapter=1,
            position=50,
        )
        
        assert thread.thread_type == "main"
        assert thread.chapter == 1

    def test_timeline_event(self) -> None:
        """Test TimelineEvent dataclass."""
        event = TimelineEvent(
            event="发生的事情",
            time="次日",
            chapter=1,
            position=0,
        )
        
        assert event.event == "发生的事情"
        assert event.time == "次日"

    def test_character_appearance(self) -> None:
        """Test CharacterAppearance dataclass."""
        appearance = CharacterAppearance(
            character_name="林晚",
            position=10,
            context="这是林晚的上下文",
            chapter=1,
        )
        
        assert appearance.character_name == "林晚"
        assert appearance.chapter == 1


class TestPatternConstants:
    """Tests for pattern constants."""

    def test_chapter_patterns_exist(self) -> None:
        """Test that chapter patterns are defined."""
        assert len(CHAPTER_PATTERNS) > 0
        assert any("章" in p for p in CHAPTER_PATTERNS)

    def test_plot_keywords_exist(self) -> None:
        """Test that plot keywords are defined."""
        assert len(PLOT_KEYWORDS) > 0
        assert "主线" in PLOT_KEYWORDS
        assert "支线" in PLOT_KEYWORDS

    def test_time_patterns_exist(self) -> None:
        """Test that time patterns are defined."""
        assert len(TIME_PATTERNS) > 0
        assert any("年" in p for p in TIME_PATTERNS)
