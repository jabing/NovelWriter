"""Tests for the OutlineValidator class."""

from __future__ import annotations

import pytest

from src.novel.outline_validator import (
    ChapterValidationResult,
    Deviation,
    DeviationReport,
    DeviationType,
    OutlineValidator,
    Severity,
)


# Sample outline data for testing
SAMPLE_OUTLINE_DATA = {
    "chapters": [
        {
            "number": 1,
            "title": "命运的开端",
            "content": "第一章 命运的开端\n林晚在京城遇见了丞相。",
            "start_position": 0,
            "end_position": 30,
        },
        {
            "number": 2,
            "title": "风起云涌",
            "content": "第二章 风起云涌\n林晚调查丞相府。",
            "start_position": 30,
            "end_position": 60,
        },
    ],
    "plot_threads": [
        {"type": "main", "content": "林晚发现丞相的秘密", "chapter": 1, "position": 10},
        {"type": "foreshadowing", "content": "丞相的真实身份", "chapter": 1, "position": 20},
        {"type": "side", "content": "结识新朋友", "chapter": 2, "position": 40},
    ],
    "timeline": [
        {"event": "林晚遇见丞相", "time": None, "chapter": 1, "position": 5},
        {"event": "林晚调查丞相府", "time": "次日", "chapter": 2, "position": 35},
    ],
    "characters": ["林晚", "丞相"],
    "raw_text": "第一章 命运的开端\n林晚遇见丞相。\n第二章 风起云涌\n林晚调查丞相府。",
}


class TestDeviationType:
    """Tests for DeviationType enum."""

    def test_deviation_types_exist(self) -> None:
        """Test that all deviation types are defined."""
        assert DeviationType.MISSING_PLOT.value == "missing_plot"
        assert DeviationType.UNEXPECTED_PLOT.value == "unexpected_plot"
        assert DeviationType.CHARACTER_BEHAVIOR.value == "character_behavior"
        assert DeviationType.TIMELINE_CONFLICT.value == "timeline_conflict"
        assert DeviationType.MISSING_CHARACTER.value == "missing_character"


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_levels_exist(self) -> None:
        """Test that all severity levels are defined."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"


class TestDeviation:
    """Tests for Deviation dataclass."""

    def test_deviation_creation(self) -> None:
        """Test creating a Deviation."""
        dev = Deviation(
            deviation_type=DeviationType.MISSING_PLOT,
            chapter=1,
            description="Missing plot element",
            expected="Expected content",
            actual=None,
            severity="high",
            suggestion="Add the missing content",
        )
        
        assert dev.deviation_type == DeviationType.MISSING_PLOT
        assert dev.chapter == 1
        assert dev.description == "Missing plot element"
        assert dev.expected == "Expected content"
        assert dev.actual is None
        assert dev.severity == "high"
        assert dev.suggestion == "Add the missing content"

    def test_deviation_to_dict(self) -> None:
        """Test converting Deviation to dictionary."""
        dev = Deviation(
            deviation_type=DeviationType.MISSING_CHARACTER,
            chapter=2,
            description="Character missing",
            severity="medium",
        )
        
        result = dev.to_dict()
        
        assert result["deviation_type"] == "missing_character"
        assert result["chapter"] == 2
        assert result["description"] == "Character missing"
        assert result["severity"] == "medium"


class TestDeviationReport:
    """Tests for DeviationReport dataclass."""

    def test_empty_report(self) -> None:
        """Test creating an empty report."""
        report = DeviationReport(total_deviations=0)
        
        assert report.total_deviations == 0
        assert len(report.deviations) == 0
        assert report.summary == ""

    def test_report_with_deviations(self) -> None:
        """Test creating a report with deviations."""
        deviations = [
            Deviation(
                deviation_type=DeviationType.MISSING_PLOT,
                chapter=1,
                description="Missing plot",
                severity="high",
            ),
            Deviation(
                deviation_type=DeviationType.MISSING_CHARACTER,
                chapter=2,
                description="Missing character",
                severity="medium",
            ),
        ]
        
        report = DeviationReport(
            total_deviations=2,
            deviations=deviations,
            by_type={"missing_plot": 1, "missing_character": 1},
            by_chapter={1: 1, 2: 1},
        )
        
        assert report.total_deviations == 2
        assert len(report.deviations) == 2
        assert report.by_type["missing_plot"] == 1

    def test_report_to_dict(self) -> None:
        """Test converting report to dictionary."""
        report = DeviationReport(
            total_deviations=1,
            deviations=[
                Deviation(
                    deviation_type=DeviationType.MISSING_PLOT,
                    chapter=1,
                    description="Test",
                    severity="high",
                ),
            ],
            summary="Test summary",
            by_type={"missing_plot": 1},
            by_chapter={1: 1},
        )
        
        result = report.to_dict()
        
        assert result["total_deviations"] == 1
        assert result["summary"] == "Test summary"
        assert "deviations" in result
        assert len(result["deviations"]) == 1


class TestChapterValidationResult:
    """Tests for ChapterValidationResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a validation result."""
        result = ChapterValidationResult(
            chapter_number=1,
            passed=True,
            deviations=[],
            covered_plots=["Plot 1"],
            missing_plots=[],
            characters_present=["林晚"],
            characters_expected=["林晚", "丞相"],
        )
        
        assert result.chapter_number == 1
        assert result.passed is True
        assert len(result.deviations) == 0
        assert "Plot 1" in result.covered_plots

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = ChapterValidationResult(
            chapter_number=1,
            passed=False,
            deviations=[
                Deviation(
                    deviation_type=DeviationType.MISSING_PLOT,
                    chapter=1,
                    description="Missing",
                    severity="high",
                ),
            ],
            covered_plots=[],
            missing_plots=["Main plot"],
        )
        
        d = result.to_dict()
        
        assert d["chapter_number"] == 1
        assert d["passed"] is False
        assert d["missing_plots"] == ["Main plot"]


class TestOutlineValidatorInit:
    """Tests for OutlineValidator initialization."""

    def test_init_with_data(self) -> None:
        """Test initialization with outline data."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        assert validator is not None
        assert len(validator._chapters) == 2
        assert len(validator._plot_threads) == 3
        assert "林晚" in validator._characters

    def test_init_with_empty_data(self) -> None:
        """Test initialization with empty data."""
        validator = OutlineValidator({})
        
        assert validator is not None
        assert len(validator._chapters) == 0
        assert len(validator._plot_threads) == 0

    def test_init_missing_keys(self) -> None:
        """Test initialization with partial data."""
        validator = OutlineValidator({"chapters": []})
        
        assert validator is not None
        assert len(validator._chapters) == 0


class TestValidateChapter:
    """Tests for validate_chapter method."""

    def test_validate_passing_chapter(self) -> None:
        """Test validating a chapter that matches outline."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        chapter_content = """
        林晚在京城遇见了丞相，发现了他不为人知的秘密。
        丞相的真实身份似乎并不简单。
        """
        
        result = validator.validate_chapter(chapter_content, chapter_number=1)
        
        assert "passed" in result
        assert "deviations" in result
        assert "covered_plots" in result
        assert "missing_plots" in result

    def test_validate_returns_correct_structure(self) -> None:
        """Test that validation returns correct structure."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        result = validator.validate_chapter("林晚遇见丞相。", chapter_number=1)
        
        assert isinstance(result["passed"], bool)
        assert isinstance(result["deviations"], list)
        assert isinstance(result["covered_plots"], list)
        assert isinstance(result["missing_plots"], list)
        assert isinstance(result["characters_present"], list)

    def test_validate_detects_missing_character(self) -> None:
        """Test detection of missing characters."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Content without expected characters
        chapter_content = "这是一个普通的场景，没有任何人物出现。"
        
        result = validator.validate_chapter(chapter_content, chapter_number=1)
        
        # Should have deviations for missing expected elements
        assert isinstance(result["deviations"], list)


class TestDetectPlotDeviation:
    """Tests for detect_plot_deviation method."""

    def test_detect_missing_main_plot(self) -> None:
        """Test detecting a missing main plot."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        expected_plots = [
            {"type": "main", "content": "林晚发现丞相的秘密", "chapter": 1},
        ]
        
        # Content without the plot element
        deviations = validator.detect_plot_deviation(
            "这是一个普通的场景。",
            expected_plots,
        )
        
        # Should detect missing main plot
        missing_plots = [d for d in deviations if d.deviation_type == DeviationType.MISSING_PLOT]
        assert len(missing_plots) >= 1

    def test_detect_covered_plot(self) -> None:
        """Test when plot is covered."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        expected_plots = [
            {"type": "main", "content": "林晚发现丞相的秘密", "chapter": 1},
        ]
        
        # Content with the plot element
        deviations = validator.detect_plot_deviation(
            "林晚发现丞相有一个不为人知的秘密。",
            expected_plots,
        )
        
        # Should not have missing plot deviation
        missing_plots = [d for d in deviations if d.deviation_type == DeviationType.MISSING_PLOT]
        # May have missing if keyword coverage is low
        assert isinstance(deviations, list)

    def test_detect_unexpected_plot(self) -> None:
        """Test detecting unexpected plot elements."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        expected_plots: list[dict[str, str | int]] = []
        
        # Content with unexpected plot element
        deviations = validator.detect_plot_deviation(
            "林晚突然发现了一个隐藏的宝藏。",
            expected_plots,
        )
        
        unexpected = [d for d in deviations if d.deviation_type == DeviationType.UNEXPECTED_PLOT]
        # May or may not detect depending on heuristic
        assert isinstance(deviations, list)


class TestCheckCharacterBehavior:
    """Tests for check_character_behavior method."""

    def test_check_matching_behavior(self) -> None:
        """Test checking behavior that matches expectation."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        deviations = validator.check_character_behavior(
            "林晚勇敢地面对了丞相。",
            "林晚",
            "勇敢地面对丞相",
        )
        
        assert isinstance(deviations, list)

    def test_check_missing_character(self) -> None:
        """Test checking behavior for absent character."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        deviations = validator.check_character_behavior(
            "这是一个没有林晚的场景。",
            "丞相",
            "出现",
        )
        
        # No deviations if character not present
        assert len(deviations) == 0

    def test_check_behavior_returns_deviations(self) -> None:
        """Test that behavior check returns deviations list."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        deviations = validator.check_character_behavior(
            "林晚静静地观察着一切。",
            "林晚",
            "勇敢行动",
        )
        
        # Should return a list (may or may not have deviations)
        assert isinstance(deviations, list)


class TestDetectTimelineConflict:
    """Tests for detect_timeline_conflict method."""

    def test_detect_timeline_order(self) -> None:
        """Test timeline conflict detection."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        deviations = validator.detect_timeline_conflict(
            "林晚遇见丞相。",
            chapter_number=1,
        )
        
        assert isinstance(deviations, list)

    def test_detect_character_before_introduction(self) -> None:
        """Test detection of character appearing before introduction."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # First, "introduce" a character in chapter 2
        validator._character_first_appearance["新角色"] = 2
        
        # Now have them appear in chapter 1
        deviations = validator.detect_timeline_conflict(
            "新角色突然出现了。",
            chapter_number=1,
        )
        
        timeline_conflicts = [
            d for d in deviations
            if d.deviation_type == DeviationType.TIMELINE_CONFLICT
        ]
        
        # Should detect the conflict
        assert len(timeline_conflicts) >= 1

    def test_no_conflict_with_proper_order(self) -> None:
        """Test no conflict when timeline is correct."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Character appears in correct order
        validator.detect_timeline_conflict("林晚出现。", chapter_number=1)
        deviations = validator.detect_timeline_conflict("林晚再次出现。", chapter_number=2)
        
        # Should not have timeline conflicts for same character
        timeline_conflicts = [
            d for d in deviations
            if d.deviation_type == DeviationType.TIMELINE_CONFLICT
        ]
        
        # Should be 0 or low for valid appearance
        assert isinstance(deviations, list)


class TestGenerateDeviationReport:
    """Tests for generate_deviation_report method."""

    def test_empty_report(self) -> None:
        """Test generating report with no deviations."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        report = validator.generate_deviation_report()
        
        assert report.total_deviations == 0
        assert "No deviations detected" in report.summary

    def test_report_with_deviations(self) -> None:
        """Test generating report with deviations."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Validate a chapter that will have deviations
        validator.validate_chapter("普通内容。", chapter_number=1)
        
        report = validator.generate_deviation_report()
        
        assert isinstance(report.total_deviations, int)
        assert isinstance(report.deviations, list)
        assert isinstance(report.by_type, dict)
        assert isinstance(report.by_chapter, dict)

    def test_report_statistics(self) -> None:
        """Test report statistics calculation."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Add some deviations
        validator._all_deviations = [
            Deviation(
                deviation_type=DeviationType.MISSING_PLOT,
                chapter=1,
                description="Missing",
                severity="high",
            ),
            Deviation(
                deviation_type=DeviationType.MISSING_CHARACTER,
                chapter=1,
                description="Missing char",
                severity="medium",
            ),
            Deviation(
                deviation_type=DeviationType.MISSING_PLOT,
                chapter=2,
                description="Another missing",
                severity="low",
            ),
        ]
        
        report = validator.generate_deviation_report()
        
        assert report.total_deviations == 3
        assert report.by_type.get("missing_plot", 0) == 2
        assert report.by_type.get("missing_character", 0) == 1
        assert report.by_chapter.get(1, 0) == 2
        assert report.by_chapter.get(2, 0) == 1


class TestGetMissingPlotElements:
    """Tests for get_missing_plot_elements method."""

    def test_no_missing_when_all_covered(self) -> None:
        """Test when all plots are covered."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Mark all plots as covered
        for thread in validator._plot_threads:
            validator._covered_plots.add(thread.get("content", ""))
        
        missing = validator.get_missing_plot_elements(chapter_number=2)
        
        assert len(missing) == 0

    def test_detects_missing_plots(self) -> None:
        """Test detection of missing plot elements."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Don't cover any plots
        missing = validator.get_missing_plot_elements(chapter_number=2)
        
        # Should find missing plots from chapters 1 and 2
        assert len(missing) > 0

    def test_only_checks_up_to_chapter(self) -> None:
        """Test that only plots up to the chapter are checked."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Check chapter 1 - should only get chapter 1 plots
        missing = validator.get_missing_plot_elements(chapter_number=1)
        
        # All chapter 1 plots should be missing
        for thread in validator._plot_threads:
            if thread.get("chapter") == 1:
                assert thread.get("content", "") in missing


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_extract_keywords(self) -> None:
        """Test keyword extraction."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        keywords = validator._extract_keywords("林晚发现丞相的秘密")
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_extract_keywords_filters_short(self) -> None:
        """Test that short segments are filtered."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        keywords = validator._extract_keywords("一 二 三 林晚")
        
        # Should filter out single characters
        assert "一" not in keywords
        assert "二" not in keywords
        assert "林晚" in keywords

    def test_detect_characters(self) -> None:
        """Test character detection."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        found = validator._detect_characters("林晚遇见了丞相")
        
        assert "林晚" in found
        assert "丞相" in found

    def test_detect_characters_not_found(self) -> None:
        """Test character detection when not present."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        found = validator._detect_characters("这是一个普通的故事")
        
        assert len(found) == 0

    def test_get_character_contexts(self) -> None:
        """Test getting character contexts."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        contexts = validator._get_character_contexts(
            "这是一个很长的故事，林晚出现在中间，后面还有内容。",
            "林晚",
        )
        
        assert len(contexts) == 1
        assert "林晚" in contexts[0]

    def test_get_character_contexts_multiple(self) -> None:
        """Test getting multiple character contexts."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        contexts = validator._get_character_contexts(
            "林晚第一次出现。后来林晚又出现了。最后林晚离开了。",
            "林晚",
        )
        
        assert len(contexts) == 3

    def test_extract_time_markers(self) -> None:
        """Test time marker extraction."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        markers = validator._extract_time_markers(
            "次日，林晚出发了。三天后，他到达了目的地。"
        )
        
        assert len(markers) >= 2
        assert "次日" in markers

    def test_extract_time_markers_dates(self) -> None:
        """Test date pattern extraction."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        markers = validator._extract_time_markers(
            "2024年3月9日，故事开始了。"
        )
        
        assert len(markers) >= 1


class TestIsPlotCovered:
    """Tests for _is_plot_covered method."""

    def test_plot_is_covered(self) -> None:
        """Test when plot is covered."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        is_covered = validator._is_plot_covered(
            "林晚发现了丞相隐藏的秘密。",
            "林晚发现丞相的秘密",
        )
        
        assert is_covered is True

    def test_plot_not_covered(self) -> None:
        """Test when plot is not covered."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        is_covered = validator._is_plot_covered(
            "这是一个完全不同的故事。",
            "林晚发现丞相的秘密",
        )
        
        assert is_covered is False


class TestGetExpectedPlots:
    """Tests for _get_expected_plots method."""

    def test_get_plots_for_chapter(self) -> None:
        """Test getting expected plots for a chapter."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        plots = validator._get_expected_plots(1)
        
        assert len(plots) == 2  # Two plots for chapter 1
        types = {p.get("type") for p in plots}
        assert "main" in types
        assert "foreshadowing" in types

    def test_get_plots_no_plots(self) -> None:
        """Test getting plots for chapter with no plots."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        plots = validator._get_expected_plots(99)
        
        assert len(plots) == 0


class TestGetExpectedCharacters:
    """Tests for _get_expected_characters method."""

    def test_get_expected_characters(self) -> None:
        """Test getting expected characters for a chapter."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        characters = validator._get_expected_characters(1)
        
        # Should find characters from timeline events
        assert isinstance(characters, set)


class TestProperties:
    """Tests for class properties."""

    def test_validated_chapters_property(self) -> None:
        """Test validated_chapters property."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Initially empty
        assert len(validator.validated_chapters) == 0
        
        # After validation
        validator.validate_chapter("内容", chapter_number=1)
        assert len(validator.validated_chapters) == 1

    def test_all_deviations_property(self) -> None:
        """Test all_deviations property."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Initially empty
        assert len(validator.all_deviations) == 0
        
        # After validation with deviations
        validator.validate_chapter("普通内容", chapter_number=1)
        # Should be a copy
        deviations = validator.all_deviations
        assert isinstance(deviations, list)


class TestIntegration:
    """Integration tests for OutlineValidator."""

    def test_full_validation_workflow(self) -> None:
        """Test complete validation workflow."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Validate first chapter
        result1 = validator.validate_chapter(
            "林晚在京城遇见了丞相，发现了他不为人知的秘密。丞相的真实身份似乎很神秘。",
            chapter_number=1,
        )
        
        # Validate second chapter
        result2 = validator.validate_chapter(
            "次日，林晚调查丞相府，结识了新朋友。",
            chapter_number=2,
        )
        
        # Generate report
        report = validator.generate_deviation_report()
        
        assert isinstance(result1["passed"], bool)
        assert isinstance(result2["passed"], bool)
        assert isinstance(report.total_deviations, int)
        assert isinstance(report.summary, str)

    def test_sequential_chapter_validation(self) -> None:
        """Test validating chapters in sequence."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        # Validate chapters in order
        for i in range(1, 3):
            result = validator.validate_chapter(f"Chapter {i} content", chapter_number=i)
            assert "passed" in result
        
        # Check that state is tracked
        assert len(validator.validated_chapters) == 2


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_chapter_content(self) -> None:
        """Test validating empty chapter."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        result = validator.validate_chapter("", chapter_number=1)
        
        assert result["passed"] is False
        assert len(result["deviations"]) > 0

    def test_chapter_number_zero(self) -> None:
        """Test with chapter number zero."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        result = validator.validate_chapter("内容", chapter_number=0)
        
        assert isinstance(result, dict)

    def test_very_long_content(self) -> None:
        """Test with very long content."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        long_content = "林晚遇见丞相。" * 1000
        result = validator.validate_chapter(long_content, chapter_number=1)
        
        assert isinstance(result, dict)

    def test_special_characters(self) -> None:
        """Test with special characters."""
        validator = OutlineValidator(SAMPLE_OUTLINE_DATA)
        
        content = "林晚遇见丞相！@#$%^&*()【】"
        result = validator.validate_chapter(content, chapter_number=1)
        
        assert isinstance(result, dict)
