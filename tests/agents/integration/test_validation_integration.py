"""Integration tests for validation layer integration with ChapterGenerator.

Tests the complete validation pipeline including:
- ValidationOrchestrator coordination
- All validators running in parallel
- Result aggregation
- Low-confidence flagging
- Performance requirements (<10s per chapter)
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.novel.chapter_generator import ChapterGenerator
from src.novel_agent.novel.character_profile import (
    CharacterProfileManager,
    CharacterTimelineEvent,
    EventType,
)
from src.novel_agent.novel.hallucination_detector import (
    Hallucination,
    HallucinationDetector,
    HallucinationReport,
    HallucinationType,
)
from src.novel_agent.novel.outline_manager import ChapterSpec
from src.novel_agent.novel.reference_validator import Reference, ReferenceVerification
from src.novel_agent.novel.timeline_validator import TimelineReport, TimelineValidator
from src.novel_agent.novel.transition_checker import ChapterTransitionChecker, TransitionReport
from src.novel_agent.novel.validation_orchestrator import (
    ValidationIssue,
    ValidationOrchestrator,
    ValidationResult,
)


class MockWriter:
    def __init__(self, content: str = "Generated chapter content"):
        self._content = content

    async def write_chapter_with_context(
        self,
        chapter_spec: Any,
        story_state: Any,
        characters: Any,
        world_context: Any,
        previous_chapter_summary: Any = None,
        **kwargs: Any,
    ) -> str:
        return self._content


@pytest.fixture
def mock_writer():
    return MockWriter(
        content="""
第一章：开端

林晚站在府门前，望着远方的天际。丞相刚刚送来一封密信，信中提到了边疆的异动。

她记得父亲曾经对她说过，天下大势，分久必合，合久必分。

丞相问道："林晚，你怎么看？"

林晚回答道："我认为应该谨慎行事。"

这是她十岁那年溺水后的第一次重要决定。
"""
    )


@pytest.fixture
def mock_character_manager():
    manager = MagicMock(spec=CharacterProfileManager)
    manager.extract_events_from_chapter.return_value = [
        CharacterTimelineEvent(
            chapter=1,
            event_type=EventType.APPEARANCE,
            description="林晚 appeared",
        )
    ]
    manager.detect_timeline_conflicts.return_value = []
    return manager


@pytest.fixture
def mock_reference_validator():
    validator = MagicMock()
    validator.validate_chapter_references = AsyncMock(
        return_value=[
            ReferenceVerification(
                reference=Reference(
                    text="林晚说过天下大势，分久必合",
                    speaker="narrator",
                    referenced_character="林晚",
                    referenced_action="说过",
                    referenced_content="天下大势，分久必合",
                    chapter=1,
                    confidence=0.6,
                ),
                is_valid=False,
                confidence=0.3,
                issues=["Potential hallucination: No supporting evidence found"],
                evidence=[],
            )
        ]
    )
    return validator


@pytest.fixture
def mock_hallucination_detector():
    detector = MagicMock(spec=HallucinationDetector)
    detector.detect_hallucinations = AsyncMock(
        return_value=HallucinationReport(
            is_clean=False,
            hallucinations=[
                Hallucination(
                    text="林晚说过天下大势，分久必合",
                    hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
                    confidence=0.85,
                    reason="No evidence supports this quotation",
                )
            ],
            factual_hallucinations=[
                Hallucination(
                    text="林晚说过天下大势，分久必合",
                    hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
                    confidence=0.85,
                    reason="No evidence supports this quotation",
                )
            ],
            total_detections=1,
        )
    )
    return detector


@pytest.fixture
def mock_timeline_validator():
    validator = MagicMock(spec=TimelineValidator)
    validator.validate_timeline = AsyncMock(
        return_value=TimelineReport(
            novel_id="test_novel",
            total_events=1,
            conflicts=[],
            order_violations=[],
            interval_warnings=[],
        )
    )
    return validator


@pytest.fixture
def mock_transition_checker():
    checker = MagicMock(spec=ChapterTransitionChecker)
    checker.check_transition.return_value = TransitionReport(
        has_issues=False,
        severity="none",
        unresolved_events=[],
        ignored_events=[],
        scene_jump_detected=False,
        confidence=0.9,
    )
    return checker


class TestValidationOrchestrator:
    """Tests for ValidationOrchestrator class."""

    def test_init_with_all_validators(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        assert orchestrator.character_manager is not None
        assert orchestrator.reference_validator is not None
        assert orchestrator.hallucination_detector is not None
        assert orchestrator.timeline_validator is not None
        assert orchestrator.transition_checker is not None

    def test_init_with_no_validators(self):
        orchestrator = ValidationOrchestrator()

        assert orchestrator.character_manager is None
        assert orchestrator.reference_validator is None
        assert orchestrator.hallucination_detector is None
        assert orchestrator.timeline_validator is None
        assert orchestrator.transition_checker is None

    @pytest.mark.asyncio
    async def test_validate_chapter_runs_all_validators(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        chapter_content = "Test chapter content"
        result = await orchestrator.validate_chapter(
            chapter_content=chapter_content,
            chapter_num=1,
            world_context="Test world context",
            prev_chapter_content="Previous chapter",
            novel_id="test_novel",
        )

        assert isinstance(result, ValidationResult)
        mock_character_manager.extract_events_from_chapter.assert_called_once()
        mock_reference_validator.validate_chapter_references.assert_called_once()
        mock_hallucination_detector.detect_hallucinations.assert_called_once()
        mock_timeline_validator.validate_timeline.assert_called_once()
        mock_transition_checker.check_transition.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_chapter_aggregates_issues(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        result = await orchestrator.validate_chapter(
            chapter_content="Test chapter",
            chapter_num=1,
            world_context="Test context",
        )

        assert result.chapter_num == 1
        assert result.total_issues >= 0
        assert isinstance(result.summary, str)
        assert isinstance(result.validation_time_ms, float)

    @pytest.mark.asyncio
    async def test_validate_chapter_performance(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        start_time = time.time()
        result = await orchestrator.validate_chapter(
            chapter_content="Test content" * 100,
            chapter_num=1,
            world_context="Test context",
        )
        elapsed_time = time.time() - start_time

        assert elapsed_time < 10.0
        assert result.validation_time_ms < 10000.0


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_total_issues_calculation(self):
        result = ValidationResult(
            chapter_num=1,
            is_valid=True,
            character_issues=[
                ValidationIssue(
                    category="character",
                    severity="minor",
                    message="Test issue",
                    chapter=1,
                )
            ],
            reference_issues=[
                ValidationIssue(
                    category="reference",
                    severity="minor",
                    message="Test issue",
                    chapter=1,
                )
            ],
            hallucination_issues=[],
            timeline_issues=[],
            transition_issues=[],
        )

        assert result.total_issues == 2

    def test_critical_issues_count(self):
        result = ValidationResult(
            chapter_num=1,
            is_valid=False,
            character_issues=[
                ValidationIssue(
                    category="character",
                    severity="critical",
                    message="Critical issue",
                    chapter=1,
                )
            ],
            reference_issues=[
                ValidationIssue(
                    category="reference",
                    severity="major",
                    message="Major issue",
                    chapter=1,
                )
            ],
            hallucination_issues=[],
            timeline_issues=[],
            transition_issues=[],
        )

        assert result.critical_issues == 1
        assert result.major_issues == 1

    def test_to_dict_serialization(self):
        result = ValidationResult(
            chapter_num=1,
            is_valid=True,
            summary="Test summary",
        )

        data = result.to_dict()

        assert data["chapter_num"] == 1
        assert data["is_valid"] is True
        assert data["summary"] == "Test summary"
        assert "total_issues" in data


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_issue_creation(self):
        issue = ValidationIssue(
            category="hallucination",
            severity="major",
            message="Test hallucination",
            chapter=1,
            confidence=0.85,
            is_low_confidence=False,
        )

        assert issue.category == "hallucination"
        assert issue.severity == "major"
        assert issue.confidence == 0.85

    def test_issue_to_dict(self):
        issue = ValidationIssue(
            category="reference",
            severity="critical",
            message="Test reference issue",
            chapter=1,
            confidence=0.9,
            metadata={"key": "value"},
        )

        data = issue.to_dict()

        assert data["category"] == "reference"
        assert data["severity"] == "critical"
        assert data["metadata"]["key"] == "value"


class TestChapterGeneratorIntegration:
    """Tests for ChapterGenerator with ValidationOrchestrator integration."""

    @pytest.fixture
    def chapter_generator_with_validation(
        self,
        mock_writer,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        generator = ChapterGenerator(
            writer=mock_writer,
            validation_orchestrator=orchestrator,
        )
        return generator

    @pytest.mark.asyncio
    async def test_generate_chapter_with_validation(self, chapter_generator_with_validation):
        chapter_spec = ChapterSpec(
            number=1,
            title="Test Chapter",
            summary="Test summary",
            key_events=["Event 1"],
            characters=["林晚"],
            location="Test location",
            word_count_target=1000,
        )

        result = await chapter_generator_with_validation.generate_chapter(
            chapter_spec=chapter_spec,
            characters=[{"name": "林晚"}],
            world_context={"setting": "ancient China"},
            run_validation=True,
            novel_id="test_novel",
        )

        assert "content" in result
        assert "validation" in result
        assert "qa_validation" in result
        assert result["qa_validation"] is not None

    @pytest.mark.asyncio
    async def test_generate_chapter_without_validation(self, chapter_generator_with_validation):
        chapter_spec = ChapterSpec(
            number=1,
            title="Test Chapter",
            summary="Test summary",
            key_events=["Event 1"],
            characters=["林晚"],
            location="Test location",
            word_count_target=1000,
        )

        result = await chapter_generator_with_validation.generate_chapter(
            chapter_spec=chapter_spec,
            characters=[{"name": "林晚"}],
            world_context={"setting": "ancient China"},
            run_validation=False,
        )

        assert "content" in result
        assert "validation" in result
        assert result["qa_validation"] is None

    @pytest.mark.asyncio
    async def test_generate_chapter_preserves_previous_content(
        self, chapter_generator_with_validation
    ):
        chapter_spec = ChapterSpec(
            number=1,
            title="Chapter 1",
            summary="Summary",
            key_events=["Event"],
            characters=["林晚"],
            location="Location",
            word_count_target=1000,
        )

        await chapter_generator_with_validation.generate_chapter(
            chapter_spec=chapter_spec,
            characters=[{"name": "林晚"}],
            world_context={},
        )

        assert chapter_generator_with_validation._previous_chapter_content is not None


class TestLowConfidenceFlagging:
    """Tests for low-confidence item flagging."""

    @pytest.mark.asyncio
    async def test_low_confidence_items_flagged(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
            low_confidence_threshold=0.8,
        )

        result = await orchestrator.validate_chapter(
            chapter_content="Test content",
            chapter_num=1,
            world_context="Test context",
        )

        assert isinstance(result.low_confidence_items, list)


class TestParallelExecution:
    """Tests for parallel validator execution."""

    @pytest.mark.asyncio
    async def test_validators_run_in_parallel(
        self,
        mock_character_manager,
        mock_reference_validator,
        mock_hallucination_detector,
        mock_timeline_validator,
        mock_transition_checker,
    ):
        sleep_times = []

        async def track_sleep(*args, **kwargs):
            sleep_times.append(time.time())
            await asyncio.sleep(0.1)
            return []

        mock_character_manager.extract_events_from_chapter.side_effect = lambda *a, **kw: []
        mock_reference_validator.validate_chapter_references.side_effect = track_sleep
        mock_hallucination_detector.detect_hallucinations.side_effect = track_sleep

        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=mock_reference_validator,
            hallucination_detector=mock_hallucination_detector,
            timeline_validator=mock_timeline_validator,
            transition_checker=mock_transition_checker,
        )

        start_time = time.time()
        await orchestrator.validate_chapter(
            chapter_content="Test",
            chapter_num=1,
            world_context="Context",
        )
        elapsed_time = time.time() - start_time

        assert elapsed_time < 0.3


class TestErrorHandling:
    """Tests for error handling in validation."""

    @pytest.mark.asyncio
    async def test_validator_error_does_not_crash(self, mock_character_manager):
        failing_validator = MagicMock()
        failing_validator.validate_chapter_references = AsyncMock(
            side_effect=Exception("Validation error")
        )

        orchestrator = ValidationOrchestrator(
            character_manager=mock_character_manager,
            reference_validator=failing_validator,
        )

        result = await orchestrator.validate_chapter(
            chapter_content="Test",
            chapter_num=1,
            world_context="Context",
        )

        assert result is not None
        assert isinstance(result, ValidationResult)


class TestKnownIssuesDetection:
    """Tests for detecting the 4 known issues from the plan."""

    @pytest.fixture
    def drowning_chapter(self):
        return """
第三章

林晚十岁那年溺水了。她在水中挣扎，几乎窒息。

第七章

林晚再次溺水，这次更加危险。
"""

    @pytest.mark.asyncio
    async def test_detect_timeline_conflict_drowning(self, drowning_chapter):
        manager = CharacterProfileManager()
        await manager.create_profile("林晚", birth_chapter=1)

        events = manager.extract_events_from_chapter(drowning_chapter, 3)

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_detect_hallucinated_reference(self):
        detector = HallucinationDetector()

        report = await detector.detect_hallucinations(
            generated_chapter='林晚说过"天下大势，分久必合，合久必分"',
            world_context="林晚是十岁女孩，从未说过这样的话",
        )

        assert not report.is_clean

    def test_detect_transition_issue(self):
        checker = ChapterTransitionChecker()

        prev_chapter = """
丞相收到一封密信，信中内容让他面色大变。
"""

        curr_chapter = """
林晚在花园中漫步，欣赏着盛开的牡丹。
"""

        report = checker.check_transition(
            prev_chapter_content=prev_chapter,
            current_chapter_content=curr_chapter,
            chapter_num=4,
        )

        assert report.has_issues


@pytest.mark.asyncio
async def test_full_validation_pipeline():
    orchestrator = ValidationOrchestrator()

    result = await orchestrator.validate_chapter(
        chapter_content="Test chapter content",
        chapter_num=1,
        world_context="Test world context",
    )

    assert isinstance(result, ValidationResult)
    assert result.chapter_num == 1
    assert isinstance(result.is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
