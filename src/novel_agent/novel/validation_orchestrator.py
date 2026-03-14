"""Validation orchestrator for coordinating all QA validators.

This module provides the ValidationOrchestrator class that integrates all
validators (CharacterProfileManager, ReferenceValidator, HallucinationDetector,
TimelineValidator, ChapterTransitionChecker) into a unified validation pipeline.

The orchestrator runs validators in parallel for performance and aggregates
results into a unified ValidationResult with:
- Unified issue reporting
- Low-confidence flagging
- Performance metrics
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.novel_agent.db.pinecone_client import VectorStore
    from src.novel_agent.db.postgres_client import PostgresClient
    from src.novel_agent.novel.character_profile import CharacterProfileManager
    from src.novel_agent.novel.hallucination_detector import HallucinationDetector
    from src.novel_agent.novel.knowledge_graph import KnowledgeGraph
    from src.novel_agent.novel.reference_validator import ReferenceValidator
    from src.novel_agent.novel.timeline_validator import TimelineValidator
    from src.novel_agent.novel.transition_checker import ChapterTransitionChecker

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A single validation issue found during validation.

    Attributes:
        category: Category of validator (character, reference, hallucination, timeline, transition)
        severity: Issue severity (critical, major, minor, info)
        message: Human-readable description
        chapter: Chapter number where issue was found
        confidence: Confidence score for this issue (0.0-1.0)
        is_low_confidence: Whether this issue needs manual review
        suggestion: Optional suggestion for fixing the issue
        metadata: Additional issue-specific data
    """

    category: str
    severity: str
    message: str
    chapter: int
    confidence: float = 1.0
    is_low_confidence: bool = False
    suggestion: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "chapter": self.chapter,
            "confidence": self.confidence,
            "is_low_confidence": self.is_low_confidence,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }


@dataclass
class ValidationResult:
    """Aggregated result from all validators.

    Attributes:
        chapter_num: Chapter number that was validated
        is_valid: Whether the chapter passed all critical validations
        character_issues: Issues from CharacterProfileManager
        reference_issues: Issues from ReferenceValidator
        hallucination_issues: Issues from HallucinationDetector
        timeline_issues: Issues from TimelineValidator
        transition_issues: Issues from ChapterTransitionChecker
        low_confidence_items: Items flagged for manual review
        validation_time_ms: Total validation time in milliseconds
        validators_run: List of validators that were executed
        summary: Human-readable summary of validation results
    """

    chapter_num: int
    is_valid: bool
    character_issues: list[ValidationIssue] = field(default_factory=list)
    reference_issues: list[ValidationIssue] = field(default_factory=list)
    hallucination_issues: list[ValidationIssue] = field(default_factory=list)
    timeline_issues: list[ValidationIssue] = field(default_factory=list)
    transition_issues: list[ValidationIssue] = field(default_factory=list)
    low_confidence_items: list[ValidationIssue] = field(default_factory=list)
    validation_time_ms: float = 0.0
    validators_run: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def total_issues(self) -> int:
        """Get total number of issues across all categories."""
        return (
            len(self.character_issues)
            + len(self.reference_issues)
            + len(self.hallucination_issues)
            + len(self.timeline_issues)
            + len(self.transition_issues)
        )

    @property
    def critical_issues(self) -> int:
        """Get count of critical severity issues."""
        all_issues = (
            self.character_issues
            + self.reference_issues
            + self.hallucination_issues
            + self.timeline_issues
            + self.transition_issues
        )
        return sum(1 for i in all_issues if i.severity == "critical")

    @property
    def major_issues(self) -> int:
        """Get count of major severity issues."""
        all_issues = (
            self.character_issues
            + self.reference_issues
            + self.hallucination_issues
            + self.timeline_issues
            + self.transition_issues
        )
        return sum(1 for i in all_issues if i.severity == "major")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chapter_num": self.chapter_num,
            "is_valid": self.is_valid,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "major_issues": self.major_issues,
            "character_issues": [i.to_dict() for i in self.character_issues],
            "reference_issues": [i.to_dict() for i in self.reference_issues],
            "hallucination_issues": [i.to_dict() for i in self.hallucination_issues],
            "timeline_issues": [i.to_dict() for i in self.timeline_issues],
            "transition_issues": [i.to_dict() for i in self.transition_issues],
            "low_confidence_items": [i.to_dict() for i in self.low_confidence_items],
            "validation_time_ms": self.validation_time_ms,
            "validators_run": self.validators_run,
            "summary": self.summary,
        }


class ValidationOrchestrator:
    """Orchestrates all validators for comprehensive chapter validation.

    This class coordinates the execution of all validators, runs them in
    parallel for performance, and aggregates results into a unified report.

    Example:
        >>> orchestrator = ValidationOrchestrator(
        ...     character_manager=char_mgr,
        ...     reference_validator=ref_val,
        ...     hallucination_detector=hall_det,
        ...     timeline_validator=time_val,
        ...     transition_checker=trans_check,
        ... )
        >>> result = await orchestrator.validate_chapter(
        ...     chapter_content="...",
        ...     chapter_num=5,
        ...     world_context="...",
        ...     prev_chapter_content="...",
        ... )
        >>> if not result.is_valid:
        ...     print(f"Validation failed: {result.summary}")
    """

    # Confidence threshold for flagging items for manual review
    LOW_CONFIDENCE_THRESHOLD = 0.7

    def __init__(
        self,
        character_manager: CharacterProfileManager | None = None,
        reference_validator: ReferenceValidator | None = None,
        hallucination_detector: HallucinationDetector | None = None,
        timeline_validator: TimelineValidator | None = None,
        transition_checker: ChapterTransitionChecker | None = None,
        low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
    ) -> None:
        """Initialize the validation orchestrator.

        Args:
            character_manager: Optional CharacterProfileManager for character validation
            reference_validator: Optional ReferenceValidator for reference validation
            hallucination_detector: Optional HallucinationDetector for hallucination detection
            timeline_validator: Optional TimelineValidator for timeline validation
            transition_checker: Optional ChapterTransitionChecker for transition validation
            low_confidence_threshold: Threshold below which items are flagged for manual review
        """
        self.character_manager = character_manager
        self.reference_validator = reference_validator
        self.hallucination_detector = hallucination_detector
        self.timeline_validator = timeline_validator
        self.transition_checker = transition_checker
        self.low_confidence_threshold = low_confidence_threshold

        logger.info(
            f"ValidationOrchestrator initialized with "
            f"character={character_manager is not None}, "
            f"reference={reference_validator is not None}, "
            f"hallucination={hallucination_detector is not None}, "
            f"timeline={timeline_validator is not None}, "
            f"transition={transition_checker is not None}"
        )

    async def validate_chapter(
        self,
        chapter_content: str,
        chapter_num: int,
        world_context: str,
        prev_chapter_content: str | None = None,
        novel_id: str | None = None,
    ) -> ValidationResult:
        """Validate a chapter using all available validators.

        Runs validators in parallel for performance and aggregates results.
        Does NOT block on validation failures - all issues are recorded.

        Args:
            chapter_content: The chapter text to validate
            chapter_num: Chapter number
            world_context: World-building context for validation
            prev_chapter_content: Optional previous chapter content for transition checking
            novel_id: Optional novel ID for timeline validation

        Returns:
            ValidationResult with aggregated validation results
        """
        start_time = time.time()
        validators_run: list[str] = []

        logger.info(f"Starting validation for chapter {chapter_num}")

        # Run all validators in parallel
        tasks: dict[str, asyncio.Task] = {}

        # Character validation
        if self.character_manager:
            tasks["character"] = asyncio.create_task(
                self._run_character_validation(chapter_content, chapter_num)
            )

        # Reference validation
        if self.reference_validator:
            tasks["reference"] = asyncio.create_task(
                self._run_reference_validation(chapter_content, chapter_num)
            )

        # Hallucination detection
        if self.hallucination_detector:
            tasks["hallucination"] = asyncio.create_task(
                self._run_hallucination_detection(chapter_content, chapter_num, world_context)
            )

        # Timeline validation
        if self.timeline_validator and novel_id:
            tasks["timeline"] = asyncio.create_task(
                self._run_timeline_validation(novel_id, chapter_num)
            )

        # Transition checking
        if self.transition_checker and prev_chapter_content:
            tasks["transition"] = asyncio.create_task(
                self._run_transition_check(prev_chapter_content, chapter_content, chapter_num)
            )

        # Wait for all tasks and collect results
        character_issues: list[ValidationIssue] = []
        reference_issues: list[ValidationIssue] = []
        hallucination_issues: list[ValidationIssue] = []
        timeline_issues: list[ValidationIssue] = []
        transition_issues: list[ValidationIssue] = []

        for name, task in tasks.items():
            try:
                result = await task
                validators_run.append(name)

                if name == "character":
                    character_issues = result
                elif name == "reference":
                    reference_issues = result
                elif name == "hallucination":
                    hallucination_issues = result
                elif name == "timeline":
                    timeline_issues = result
                elif name == "transition":
                    transition_issues = result

            except Exception as e:
                logger.error(f"Validator '{name}' failed: {e}")
                validators_run.append(f"{name}_failed")

        # Identify low-confidence items
        low_confidence_items = self._identify_low_confidence_items(
            character_issues,
            reference_issues,
            hallucination_issues,
            timeline_issues,
            transition_issues,
        )

        # Determine overall validity (fail on critical or major issues)
        all_issues = (
            character_issues
            + reference_issues
            + hallucination_issues
            + timeline_issues
            + transition_issues
        )
        is_valid = not any(i.severity in ("critical", "major") for i in all_issues)

        # Calculate validation time
        validation_time_ms = (time.time() - start_time) * 1000

        # Generate summary
        summary = self._generate_summary(
            is_valid,
            character_issues,
            reference_issues,
            hallucination_issues,
            timeline_issues,
            transition_issues,
            low_confidence_items,
        )

        result = ValidationResult(
            chapter_num=chapter_num,
            is_valid=is_valid,
            character_issues=character_issues,
            reference_issues=reference_issues,
            hallucination_issues=hallucination_issues,
            timeline_issues=timeline_issues,
            transition_issues=transition_issues,
            low_confidence_items=low_confidence_items,
            validation_time_ms=validation_time_ms,
            validators_run=validators_run,
            summary=summary,
        )

        logger.info(
            f"Validation complete for chapter {chapter_num}: "
            f"valid={is_valid}, issues={result.total_issues}, "
            f"low_confidence={len(low_confidence_items)}, "
            f"time={validation_time_ms:.1f}ms"
        )

        return result

    async def _run_character_validation(
        self,
        chapter_content: str,
        chapter_num: int,
    ) -> list[ValidationIssue]:
        """Run character profile validation.

        Args:
            chapter_content: Chapter text to validate
            chapter_num: Chapter number

        Returns:
            List of ValidationIssue objects
        """
        issues: list[ValidationIssue] = []

        if not self.character_manager:
            return issues

        try:
            # Extract events from chapter
            events = self.character_manager.extract_events_from_chapter(
                chapter_content, chapter_num
            )

            # Check each extracted event for potential issues
            for event in events:
                char_name = event.metadata.get("character_name", "")
                if not char_name:
                    continue

                # Check for timeline conflicts
                conflicts = await self.character_manager.detect_timeline_conflicts(char_name)

                for conflict in conflicts:
                    # Map conflict severity to validation severity
                    severity_map = {
                        "critical": "critical",
                        "major": "major",
                        "minor": "minor",
                    }
                    severity = severity_map.get(conflict.severity, "minor")

                    issues.append(
                        ValidationIssue(
                            category="character",
                            severity=severity,
                            message=conflict.description,
                            chapter=chapter_num,
                            confidence=0.9,
                            is_low_confidence=False,
                            suggestion=conflict.suggested_resolution or "",
                            metadata={
                                "conflict_type": conflict.conflict_type.value,
                                "character_name": char_name,
                            },
                        )
                    )

            logger.debug(
                f"Character validation found {len(issues)} issues in chapter {chapter_num}"
            )

        except Exception as e:
            logger.error(f"Character validation failed: {e}")
            issues.append(
                ValidationIssue(
                    category="character",
                    severity="info",
                    message=f"Character validation error: {str(e)}",
                    chapter=chapter_num,
                    confidence=0.5,
                    is_low_confidence=True,
                )
            )

        return issues

    async def _run_reference_validation(
        self,
        chapter_content: str,
        chapter_num: int,
    ) -> list[ValidationIssue]:
        """Run reference validation.

        Args:
            chapter_content: Chapter text to validate
            chapter_num: Chapter number

        Returns:
            List of ValidationIssue objects
        """
        issues: list[ValidationIssue] = []

        if not self.reference_validator:
            return issues

        try:
            # Validate all references in the chapter
            verifications = await self.reference_validator.validate_chapter_references(
                chapter_content, chapter_num
            )

            for verification in verifications:
                if not verification.is_valid:
                    # Determine severity based on confidence
                    if verification.confidence < 0.3:
                        severity = "critical"
                    elif verification.confidence < 0.5:
                        severity = "major"
                    else:
                        severity = "minor"

                    # Build issue message
                    message = f"Invalid reference: {verification.reference.text[:100]}"
                    if verification.issues:
                        message += f" - {verification.issues[0]}"

                    suggestions = []
                    if verification.similar_facts:
                        suggestions.append("Similar content found in world context")

                    issues.append(
                        ValidationIssue(
                            category="reference",
                            severity=severity,
                            message=message,
                            chapter=chapter_num,
                            confidence=verification.confidence,
                            is_low_confidence=verification.confidence
                            < self.low_confidence_threshold,
                            suggestion=suggestions[0] if suggestions else "",
                            metadata={
                                "reference_text": verification.reference.text,
                                "speaker": verification.reference.speaker,
                                "issues": verification.issues,
                            },
                        )
                    )

            logger.debug(
                f"Reference validation found {len(issues)} issues in chapter {chapter_num}"
            )

        except Exception as e:
            logger.error(f"Reference validation failed: {e}")
            issues.append(
                ValidationIssue(
                    category="reference",
                    severity="info",
                    message=f"Reference validation error: {str(e)}",
                    chapter=chapter_num,
                    confidence=0.5,
                    is_low_confidence=True,
                )
            )

        return issues

    async def _run_hallucination_detection(
        self,
        chapter_content: str,
        chapter_num: int,
        world_context: str,
    ) -> list[ValidationIssue]:
        """Run hallucination detection.

        Args:
            chapter_content: Chapter text to validate
            chapter_num: Chapter number
            world_context: World context for validation

        Returns:
            List of ValidationIssue objects
        """
        issues: list[ValidationIssue] = []

        if not self.hallucination_detector:
            return issues

        try:
            # Detect hallucinations
            report = await self.hallucination_detector.detect_hallucinations(
                generated_chapter=chapter_content,
                world_context=world_context,
            )

            # Process factual hallucinations (these are real issues)
            for hallucination in report.factual_hallucinations:
                # Determine severity based on confidence
                if hallucination.confidence >= 0.9:
                    severity = "critical"
                elif hallucination.confidence >= 0.7:
                    severity = "major"
                else:
                    severity = "minor"

                issues.append(
                    ValidationIssue(
                        category="hallucination",
                        severity=severity,
                        message=f"Hallucination detected: {hallucination.reason}",
                        chapter=chapter_num,
                        confidence=hallucination.confidence,
                        is_low_confidence=hallucination.confidence < self.low_confidence_threshold,
                        suggestion=hallucination.suggestions[0]
                        if hallucination.suggestions
                        else "",
                        metadata={
                            "hallucination_type": hallucination.hallucination_type.value,
                            "text_snippet": hallucination.text[:200],
                            "context_snippet": hallucination.context_snippet,
                        },
                    )
                )

            logger.debug(
                f"Hallucination detection found {len(issues)} issues in chapter {chapter_num}"
            )

        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            issues.append(
                ValidationIssue(
                    category="hallucination",
                    severity="info",
                    message=f"Hallucination detection error: {str(e)}",
                    chapter=chapter_num,
                    confidence=0.5,
                    is_low_confidence=True,
                )
            )

        return issues

    async def _run_timeline_validation(
        self,
        novel_id: str,
        chapter_num: int,
    ) -> list[ValidationIssue]:
        """Run timeline validation.

        Args:
            novel_id: Novel ID for timeline lookup
            chapter_num: Chapter number

        Returns:
            List of ValidationIssue objects
        """
        issues: list[ValidationIssue] = []

        if not self.timeline_validator:
            return issues

        try:
            # Validate timeline
            report = await self.timeline_validator.validate_timeline(novel_id)

            # Process conflicts
            for conflict in report.conflicts:
                # Map severity
                severity_map = {
                    "critical": "critical",
                    "error": "major",
                    "warning": "minor",
                    "info": "info",
                }
                severity = severity_map.get(conflict.severity.value, "minor")

                issues.append(
                    ValidationIssue(
                        category="timeline",
                        severity=severity,
                        message=f"Timeline conflict: {conflict.reason}",
                        chapter=conflict.chapter,
                        confidence=0.85,
                        is_low_confidence=False,
                        suggestion=f"Review {conflict.character_name}'s timeline",
                        metadata={
                            "conflict_type": conflict.conflict_type,
                            "character_name": conflict.character_name,
                            "evidence": conflict.evidence,
                        },
                    )
                )

            # Process order violations
            for violation in report.order_violations:
                severity_map = {
                    "critical": "critical",
                    "error": "major",
                    "warning": "minor",
                    "info": "info",
                }
                severity = severity_map.get(violation.severity.value, "minor")

                issues.append(
                    ValidationIssue(
                        category="timeline",
                        severity=severity,
                        message=f"Order violation: {violation.reason}",
                        chapter=violation.later_chapter,
                        confidence=0.8,
                        is_low_confidence=False,
                        metadata={
                            "earlier_chapter": violation.earlier_chapter,
                            "later_chapter": violation.later_chapter,
                            "earlier_event": violation.earlier_event,
                            "later_event": violation.later_event,
                        },
                    )
                )

            logger.debug(f"Timeline validation found {len(issues)} issues for novel {novel_id}")

        except Exception as e:
            logger.error(f"Timeline validation failed: {e}")
            issues.append(
                ValidationIssue(
                    category="timeline",
                    severity="info",
                    message=f"Timeline validation error: {str(e)}",
                    chapter=chapter_num,
                    confidence=0.5,
                    is_low_confidence=True,
                )
            )

        return issues

    async def _run_transition_check(
        self,
        prev_chapter_content: str,
        current_chapter_content: str,
        chapter_num: int,
    ) -> list[ValidationIssue]:
        """Run transition checking.

        Args:
            prev_chapter_content: Previous chapter content
            current_chapter_content: Current chapter content
            chapter_num: Current chapter number

        Returns:
            List of ValidationIssue objects
        """
        issues: list[ValidationIssue] = []

        if not self.transition_checker:
            return issues

        try:
            # Check transition
            report = self.transition_checker.check_transition(
                prev_chapter_content=prev_chapter_content,
                current_chapter_content=current_chapter_content,
                chapter_num=chapter_num,
            )

            if report.has_issues:
                # Map severity
                severity_map = {
                    "critical": "critical",
                    "major": "major",
                    "minor": "minor",
                    "none": "info",
                }
                severity = severity_map.get(report.severity, "minor")

                # Create issue for scene jump
                if report.scene_jump_detected:
                    issues.append(
                        ValidationIssue(
                            category="transition",
                            severity=severity,
                            message=f"Scene jump detected: {report.scene_jump_details[:200]}",
                            chapter=chapter_num,
                            confidence=report.confidence,
                            is_low_confidence=report.confidence < self.low_confidence_threshold,
                            suggestion=(
                                report.transition_suggestions[0]
                                if report.transition_suggestions
                                else ""
                            ),
                            metadata={
                                "scene_jump": True,
                                "ignored_events": len(report.ignored_events),
                            },
                        )
                    )

                # Create issues for ignored events
                for event in report.ignored_events[:3]:  # Limit to top 3
                    issues.append(
                        ValidationIssue(
                            category="transition",
                            severity=severity,
                            message=f"Unresolved event from previous chapter: {event.description[:100]}",
                            chapter=chapter_num,
                            confidence=report.confidence,
                            is_low_confidence=report.confidence < self.low_confidence_threshold,
                            suggestion=(
                                report.transition_suggestions[0]
                                if report.transition_suggestions
                                else ""
                            ),
                            metadata={
                                "event_type": event.event_type,
                                "importance": event.importance,
                            },
                        )
                    )

            logger.debug(f"Transition check found {len(issues)} issues for chapter {chapter_num}")

        except Exception as e:
            logger.error(f"Transition check failed: {e}")
            issues.append(
                ValidationIssue(
                    category="transition",
                    severity="info",
                    message=f"Transition check error: {str(e)}",
                    chapter=chapter_num,
                    confidence=0.5,
                    is_low_confidence=True,
                )
            )

        return issues

    def _identify_low_confidence_items(
        self,
        character_issues: list[ValidationIssue],
        reference_issues: list[ValidationIssue],
        hallucination_issues: list[ValidationIssue],
        timeline_issues: list[ValidationIssue],
        transition_issues: list[ValidationIssue],
    ) -> list[ValidationIssue]:
        """Identify issues that need manual review.

        Args:
            character_issues: Character validation issues
            reference_issues: Reference validation issues
            hallucination_issues: Hallucination detection issues
            timeline_issues: Timeline validation issues
            transition_issues: Transition check issues

        Returns:
            List of issues flagged for manual review
        """
        low_confidence: list[ValidationIssue] = []

        all_issues = (
            character_issues
            + reference_issues
            + hallucination_issues
            + timeline_issues
            + transition_issues
        )

        for issue in all_issues:
            if issue.is_low_confidence or issue.confidence < self.low_confidence_threshold:
                low_confidence.append(issue)

        return low_confidence

    def _generate_summary(
        self,
        is_valid: bool,
        character_issues: list[ValidationIssue],
        reference_issues: list[ValidationIssue],
        hallucination_issues: list[ValidationIssue],
        timeline_issues: list[ValidationIssue],
        transition_issues: list[ValidationIssue],
        low_confidence_items: list[ValidationIssue],
    ) -> str:
        """Generate a human-readable summary of validation results.

        Args:
            is_valid: Overall validation result
            character_issues: Character validation issues
            reference_issues: Reference validation issues
            hallucination_issues: Hallucination detection issues
            timeline_issues: Timeline validation issues
            transition_issues: Transition check issues
            low_confidence_items: Items needing manual review

        Returns:
            Human-readable summary string
        """
        if is_valid:
            total = (
                len(character_issues)
                + len(reference_issues)
                + len(hallucination_issues)
                + len(timeline_issues)
                + len(transition_issues)
            )
            if total == 0:
                return "Validation passed with no issues."
            else:
                return f"Validation passed with {total} minor issues."

        # Count issues by severity
        all_issues = (
            character_issues
            + reference_issues
            + hallucination_issues
            + timeline_issues
            + transition_issues
        )

        critical = sum(1 for i in all_issues if i.severity == "critical")
        major = sum(1 for i in all_issues if i.severity == "major")
        minor = sum(1 for i in all_issues if i.severity == "minor")

        parts: list[str] = []

        if critical > 0:
            parts.append(f"{critical} critical")
        if major > 0:
            parts.append(f"{major} major")
        if minor > 0:
            parts.append(f"{minor} minor")

        summary = f"Validation failed: {', '.join(parts)} issue(s)"

        if low_confidence_items:
            summary += f". {len(low_confidence_items)} item(s) need manual review."

        return summary


def create_validation_orchestrator(
    knowledge_graph: KnowledgeGraph | None = None,
    vector_store: VectorStore | None = None,
    postgres_client: PostgresClient | None = None,
    low_confidence_threshold: float = 0.7,
) -> ValidationOrchestrator:
    """Factory function to create a fully configured ValidationOrchestrator.

    This creates all validators with their dependencies and returns
    a configured orchestrator.

    Args:
        knowledge_graph: Optional knowledge graph for reference validation
        vector_store: Optional vector store for hallucination detection
        postgres_client: Optional PostgreSQL client for timeline/character validation
        low_confidence_threshold: Threshold for flagging items for manual review

    Returns:
        Configured ValidationOrchestrator instance
    """
    # Import validators lazily to avoid circular imports
    from src.novel_agent.novel.character_profile import CharacterProfileManager
    from src.novel_agent.novel.hallucination_detector import HallucinationDetector
    from src.novel_agent.novel.reference_validator import ReferenceValidator
    from src.novel_agent.novel.timeline_validator import TimelineValidator
    from src.novel_agent.novel.transition_checker import ChapterTransitionChecker

    # Create validators
    character_manager = None
    reference_validator = None
    hallucination_detector = None
    timeline_validator = None
    transition_checker = None

    if postgres_client:
        character_manager = CharacterProfileManager(postgres_client=postgres_client)
        timeline_validator = TimelineValidator(postgres_client=postgres_client)

    if knowledge_graph:
        reference_validator = ReferenceValidator(
            knowledge_graph=knowledge_graph,
            vector_store=vector_store,
        )

    if vector_store:
        hallucination_detector = HallucinationDetector(
            vector_store=vector_store,
            threshold=0.8,
        )

    # Transition checker has no dependencies
    transition_checker = ChapterTransitionChecker()

    return ValidationOrchestrator(
        character_manager=character_manager,
        reference_validator=reference_validator,
        hallucination_detector=hallucination_detector,
        timeline_validator=timeline_validator,
        transition_checker=transition_checker,
        low_confidence_threshold=low_confidence_threshold,
    )


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "ValidationOrchestrator",
    "create_validation_orchestrator",
]
