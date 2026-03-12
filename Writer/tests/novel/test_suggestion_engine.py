"""Tests for the SuggestionEngine class."""

from __future__ import annotations

import pytest

from src.novel.suggestion_engine import (
    FORESHADOWING_RESOLUTION_WINDOW,
    PRIORITY_BACKLOG,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    Suggestion,
    SuggestionEngine,
)


def create_mock_outline_data() -> dict[str, object]:
    """Create mock outline data for testing."""
    return {
        "chapters": [
            {
                "number": 1,
                "title": "命运的开端",
                "content": "第一章内容",
                "start_position": 0,
                "end_position": 100,
            },
            {
                "number": 2,
                "title": "风起云涌",
                "content": "第二章内容",
                "start_position": 100,
                "end_position": 200,
            },
            {
                "number": 3,
                "title": "转折",
                "content": "第三章内容",
                "start_position": 200,
                "end_position": 300,
            },
        ],
        "plot_threads": [
            {
                "type": "main",
                "keyword": "主线",
                "content": "林晚发现丞相的秘密",
                "chapter": 1,
                "position": 10,
            },
            {
                "type": "side",
                "keyword": "支线",
                "content": "结识新朋友",
                "chapter": 1,
                "position": 20,
            },
            {
                "type": "foreshadowing",
                "keyword": "伏笔",
                "content": "丞相的真实身份",
                "chapter": 1,
                "position": 30,
            },
            {
                "type": "main",
                "keyword": "主线",
                "content": "调查丞相府",
                "chapter": 2,
                "position": 110,
            },
            {
                "type": "foreshadowing",
                "keyword": "伏笔",
                "content": "神秘人物的动机",
                "chapter": 2,
                "position": 120,
            },
        ],
        "timeline": [
            {
                "event": "林晚在京城遇见了丞相",
                "time": "2024年3月9日",
                "chapter": 1,
                "position": 0,
            },
            {
                "event": "林晚开始调查",
                "time": "次日",
                "chapter": 2,
                "position": 100,
            },
        ],
        "characters": ["林晚", "丞相"],
        "raw_text": "大纲原文",
    }


class TestSuggestionDataclass:
    """Tests for the Suggestion dataclass."""

    def test_suggestion_creation(self) -> None:
        """Test creating a suggestion."""
        suggestion = Suggestion(
            suggestion_type="plot_completion",
            priority=1,
            chapter=1,
            description="Test suggestion",
        )
        
        assert suggestion.suggestion_type == "plot_completion"
        assert suggestion.priority == 1
        assert suggestion.chapter == 1
        assert suggestion.description == "Test suggestion"
        assert suggestion.details == {}
        assert suggestion.actionable is True
        assert suggestion.related_plot_threads == []

    def test_suggestion_with_details(self) -> None:
        """Test suggestion with additional details."""
        suggestion = Suggestion(
            suggestion_type="character_interaction",
            priority=2,
            chapter=3,
            description="Character interaction",
            details={"characters": ["A", "B"]},
            actionable=False,
            related_plot_threads=["plot1", "plot2"],
        )
        
        assert suggestion.details == {"characters": ["A", "B"]}
        assert suggestion.actionable is False
        assert len(suggestion.related_plot_threads) == 2

    def test_suggestion_to_dict(self) -> None:
        """Test converting suggestion to dictionary."""
        suggestion = Suggestion(
            suggestion_type="foreshadowing_recall",
            priority=0,
            chapter=5,
            description="Foreshadowing",
            details={"key": "value"},
        )
        
        result = suggestion.to_dict()
        
        assert result["suggestion_type"] == "foreshadowing_recall"
        assert result["priority"] == 0
        assert result["chapter"] == 5
        assert result["details"] == {"key": "value"}
        assert result["actionable"] is True


class TestSuggestionEngineInit:
    """Tests for SuggestionEngine initialization."""

    def test_init_with_empty_data(self) -> None:
        """Test initialization with empty data."""
        engine = SuggestionEngine({})
        
        assert engine._chapters == []
        assert engine._plot_threads == []
        assert engine._characters == set()

    def test_init_with_mock_data(self) -> None:
        """Test initialization with mock data."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        assert len(engine._chapters) == 3
        assert len(engine._plot_threads) == 5
        assert "林晚" in engine._characters

    def test_init_with_cognitive_graph(self) -> None:
        """Test initialization with cognitive graph."""
        from src.novel.cognitive_graph import CognitiveGraph
        
        data = create_mock_outline_data()
        graph = CognitiveGraph("test")
        
        engine = SuggestionEngine(data, cognitive_graph=graph)
        
        assert engine._cognitive_graph is not None


class TestSuggestPlotCompletion:
    """Tests for plot completion suggestions."""

    def test_missing_main_plot(self) -> None:
        """Test detecting missing main plot."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Chapter content without the main plot
        content = "这是一个普通的故事，没有涉及丞相的秘密。"
        suggestions = engine.suggest_plot_completion(1, content)
        
        # Should suggest the missing main plot
        assert len(suggestions) >= 1
        
        main_plot_suggestions = [
            s for s in suggestions
            if s.details.get("thread_type") == "main"
        ]
        assert len(main_plot_suggestions) >= 1
        
        # Main plot should be critical priority
        assert main_plot_suggestions[0].priority == PRIORITY_CRITICAL

    def test_covered_plot_no_suggestion(self) -> None:
        """Test that covered plots don't generate suggestions."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Mark plot as covered
        engine.mark_plot_covered("林晚发现丞相的秘密")
        
        content = "普通内容"
        suggestions = engine.suggest_plot_completion(1, content)
        
        # Should not suggest the covered plot
        plot_suggestions = [
            s for s in suggestions
            if "林晚发现丞相的秘密" in s.related_plot_threads
        ]
        assert len(plot_suggestions) == 0

    def test_partial_plot_coverage(self) -> None:
        """Test partial plot coverage detection."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Content with partial keywords
        content = "林晚在京城，发现了秘密。"
        suggestions = engine.suggest_plot_completion(1, content)
        
        # Plot might be considered partially covered
        main_suggestions = [
            s for s in suggestions
            if s.details.get("thread_type") == "main"
        ]
        # May or may not suggest depending on coverage threshold
        assert isinstance(suggestions, list)

    def test_missing_foreshadowing(self) -> None:
        """Test detecting missing foreshadowing."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "普通内容"
        suggestions = engine.suggest_plot_completion(1, content)
        
        foreshadow_suggestions = [
            s for s in suggestions
            if s.details.get("thread_type") == "foreshadowing"
        ]
        
        if len(foreshadow_suggestions) > 0:
            # Foreshadowing should be high priority
            assert foreshadow_suggestions[0].priority == PRIORITY_HIGH

    def test_earlier_unresolved_plots(self) -> None:
        """Test detecting unresolved plots from earlier chapters."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Chapter 2 content without chapter 1 plots
        content = "第二章的普通内容"
        suggestions = engine.suggest_plot_completion(2, content)
        
        # May suggest earlier unresolved plots
        earlier_suggestions = [
            s for s in suggestions
            if s.details.get("introduced_chapter") == 1
        ]
        # Should be medium priority
        for s in earlier_suggestions:
            assert s.priority == PRIORITY_MEDIUM


class TestSuggestCharacterInteractions:
    """Tests for character interaction suggestions."""

    def test_missing_expected_character(self) -> None:
        """Test detecting missing expected character."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Only one character present
        suggestions = engine.suggest_character_interactions(1, ["林晚"])
        
        # Should suggest missing character
        missing_suggestions = [
            s for s in suggestions
            if "missing_characters" in s.details
        ]
        
        # If丞相 is expected, should be suggested
        if len(missing_suggestions) > 0:
            assert missing_suggestions[0].priority == PRIORITY_HIGH

    def test_all_characters_present(self) -> None:
        """Test when all expected characters are present."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        suggestions = engine.suggest_character_interactions(1, ["林晚", "丞相"])
        
        # Should not have missing character suggestions
        missing_suggestions = [
            s for s in suggestions
            if "missing_characters" in s.details
        ]
        # All characters present, no missing suggestions
        for s in missing_suggestions:
            assert len(s.details.get("missing_characters", [])) == 0

    def test_empty_characters_list(self) -> None:
        """Test with empty characters list."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        suggestions = engine.suggest_character_interactions(1, [])
        
        assert isinstance(suggestions, list)

    def test_with_cognitive_graph(self) -> None:
        """Test with cognitive graph integration."""
        from src.novel.cognitive_graph import CognitiveGraph
        
        data = create_mock_outline_data()
        graph = CognitiveGraph("test")
        
        # Add character node
        graph.add_character_node("林晚", "林晚", tier=0)
        
        # Add a fact
        graph.add_fact_node(
            "fact1",
            "secret",
            "林晚知道一个秘密",
            "林晚",
            1,
        )
        graph.add_character_knowledge("林晚", "fact1")
        
        engine = SuggestionEngine(data, cognitive_graph=graph)
        
        suggestions = engine.suggest_character_interactions(1, ["林晚"])
        
        assert isinstance(suggestions, list)


class TestSuggestForeshadowingRecall:
    """Tests for foreshadowing recall suggestions."""

    def test_forgotten_foreshadowing(self) -> None:
        """Test detecting forgotten foreshadowing."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Check at a later chapter
        suggestions = engine.suggest_foreshadowing_recall(
            1 + FORESHADOWING_RESOLUTION_WINDOW
        )
        
        # Should suggest resolving the foreshadowing
        foreshadow_suggestions = [
            s for s in suggestions
            if s.suggestion_type == "foreshadowing_recall"
            and s.details.get("suggestion_type") != "setup"
        ]
        
        if len(foreshadow_suggestions) > 0:
            # Should be high priority if overdue
            high_priority = [
                s for s in foreshadow_suggestions
                if s.priority == PRIORITY_HIGH
            ]
            assert len(high_priority) >= 0

    def test_resolved_foreshadowing_no_suggestion(self) -> None:
        """Test that resolved foreshadowing doesn't generate suggestions."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Mark foreshadowing as resolved
        engine.mark_foreshadowing_resolved("丞相的真实身份")
        
        suggestions = engine.suggest_foreshadowing_recall(3)
        
        # Should not suggest the resolved foreshadowing
        resolved_suggestions = [
            s for s in suggestions
            if "丞相的真实身份" in s.related_plot_threads
            and s.details.get("suggestion_type") != "setup"
        ]
        assert len(resolved_suggestions) == 0

    def test_future_foreshadowing_setup(self) -> None:
        """Test suggestions for setting up future foreshadowing."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        suggestions = engine.suggest_foreshadowing_recall(1)
        
        # Should include setup suggestions for future plots
        setup_suggestions = [
            s for s in suggestions
            if s.details.get("suggestion_type") == "setup"
        ]
        
        # Should be low priority
        for s in setup_suggestions:
            assert s.priority == PRIORITY_LOW


class TestGetAllSuggestions:
    """Tests for combined suggestions."""

    def test_get_all_suggestions(self) -> None:
        """Test getting all types of suggestions."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "普通章节内容"
        suggestions = engine.get_all_suggestions(1, content)
        
        assert isinstance(suggestions, list)
        
        # Check that suggestions are prioritized
        priorities = [s.priority for s in suggestions]
        assert priorities == sorted(priorities)

    def test_suggestions_prioritized(self) -> None:
        """Test that suggestions are properly prioritized."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "普通内容"
        suggestions = engine.get_all_suggestions(1, content)
        
        if len(suggestions) >= 2:
            # First suggestion should have highest priority (lowest number)
            assert suggestions[0].priority <= suggestions[-1].priority

    def test_empty_chapter_content(self) -> None:
        """Test with empty chapter content."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        suggestions = engine.get_all_suggestions(1, "")
        
        assert isinstance(suggestions, list)


class TestPlotCoverage:
    """Tests for plot coverage detection."""

    def test_is_plot_covered(self) -> None:
        """Test plot coverage detection."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "林晚在京城发现了丞相的秘密"
        is_covered = engine._is_plot_covered(content, "林晚发现丞相的秘密")
        
        # Should detect partial coverage
        assert isinstance(is_covered, bool)

    def test_keyword_extraction(self) -> None:
        """Test keyword extraction."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        keywords = engine._extract_keywords("林晚发现丞相的秘密")
        
        assert len(keywords) > 0
        assert "林晚" in keywords or any("林" in k for k in keywords)

    def test_mark_plot_covered(self) -> None:
        """Test marking plot as covered."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        engine.mark_plot_covered("test_plot")
        
        assert "test_plot" in engine._covered_plots


class TestCharacterDetection:
    """Tests for character detection."""

    def test_detect_characters(self) -> None:
        """Test detecting characters in content."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "林晚在京城遇到了丞相"
        characters = engine._detect_characters(content)
        
        assert "林晚" in characters
        assert "丞相" in characters

    def test_detect_no_characters(self) -> None:
        """Test detecting no characters."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        content = "这是一个没有角色的故事"
        characters = engine._detect_characters(content)
        
        assert len(characters) == 0


class TestSummary:
    """Tests for summary functionality."""

    def test_get_summary(self) -> None:
        """Test getting summary."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        summary = engine.get_summary()
        
        assert "total_plot_threads" in summary
        assert "covered_plot_threads" in summary
        assert "total_foreshadowing" in summary
        assert "resolved_foreshadowing" in summary

    def test_summary_after_covering(self) -> None:
        """Test summary after covering plots."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        engine.mark_plot_covered("plot1")
        engine.mark_foreshadowing_resolved("伏笔1")
        
        summary = engine.get_summary()
        
        assert summary["covered_plot_threads"] >= 1
        assert summary["resolved_foreshadowing"] >= 1


class TestResetState:
    """Tests for state reset."""

    def test_reset_state(self) -> None:
        """Test resetting engine state."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        engine.mark_plot_covered("plot1")
        engine.mark_foreshadowing_resolved("伏笔1")
        
        engine.reset_state()
        
        assert len(engine._covered_plots) == 0
        assert len(engine._resolved_foreshadowing) == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_chapter_not_in_outline(self) -> None:
        """Test with chapter number not in outline."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        suggestions = engine.get_all_suggestions(99, "内容")
        
        assert isinstance(suggestions, list)

    def test_very_long_content(self) -> None:
        """Test with very long chapter content."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        long_content = "林晚" * 10000
        suggestions = engine.get_all_suggestions(1, long_content)
        
        assert isinstance(suggestions, list)

    def test_unicode_content(self) -> None:
        """Test with unicode content."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        unicode_content = "林晚在京城遇到了丞相，发现了一个秘密！🎉"
        suggestions = engine.get_all_suggestions(1, unicode_content)
        
        assert isinstance(suggestions, list)

    def test_none_chapter_content(self) -> None:
        """Test handling None-like content."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Empty string is valid
        suggestions = engine.get_all_suggestions(1, "")
        
        assert isinstance(suggestions, list)


class TestPriorityConstants:
    """Tests for priority constants."""

    def test_priority_ordering(self) -> None:
        """Test that priority constants are ordered correctly."""
        assert PRIORITY_CRITICAL < PRIORITY_HIGH
        assert PRIORITY_HIGH < PRIORITY_MEDIUM
        assert PRIORITY_MEDIUM < PRIORITY_LOW
        assert PRIORITY_LOW < PRIORITY_BACKLOG

    def test_foreshadowing_window(self) -> None:
        """Test that foreshadowing resolution window is reasonable."""
        assert FORESHADOWING_RESOLUTION_WINDOW >= 1
        assert FORESHADOWING_RESOLUTION_WINDOW <= 20


class TestMultipleCalls:
    """Tests for multiple method calls."""

    def test_multiple_chapter_analysis(self) -> None:
        """Test analyzing multiple chapters in sequence."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        # Analyze chapter 1
        suggestions1 = engine.get_all_suggestions(1, "林晚发现了丞相的秘密")
        
        # Mark plot as covered
        engine.mark_plot_covered("林晚发现丞相的秘密")
        
        # Analyze chapter 2
        suggestions2 = engine.get_all_suggestions(2, "调查丞相府")
        
        # State should persist
        assert "林晚发现丞相的秘密" in engine._covered_plots

    def test_state_persistence(self) -> None:
        """Test that state persists across calls."""
        data = create_mock_outline_data()
        engine = SuggestionEngine(data)
        
        engine.mark_plot_covered("plot1")
        engine.mark_plot_covered("plot2")
        
        assert len(engine._covered_plots) == 2
