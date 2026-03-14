"""Auto-fixing system for novel content inconsistencies.

This module provides automated detection and fixing of inconsistencies
in generated chapter content through an iterative verification-regeneration loop.

Enhanced with Wave 2 validators integration:
- TimelineValidator
- ReferenceValidator
- HallucinationDetector
- ChapterTransitionChecker
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.novel_agent.novel.consistency_verifier import ConsistencyVerifier, Inconsistency, VerificationResult
from src.novel_agent.novel.continuity import StoryState

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Types of fix suggestions."""

    REMOVE_CONTRADICTION = "remove_contradiction"
    UPDATE_LOCATION = "update_location"
    FIX_TIMELINE = "fix_timeline"
    CORRECT_CHARACTER_STATE = "correct_character_state"
    ADD_MISSING_CONTEXT = "add_missing_context"
    REWRITE_PASSAGE = "rewrite_passage"
    FIX_HALLUCINATION = "fix_hallucination"
    FIX_REFERENCE = "fix_reference"
    FIX_TRANSITION = "fix_transition"


class FixPriority(str, Enum):
    """Priority levels for fix suggestions."""

    CRITICAL = "critical"  # Must fix before proceeding
    HIGH = "high"  # Should fix, affects story quality
    MEDIUM = "medium"  # Recommended fix
    LOW = "low"  # Optional improvement


@dataclass
class FixSuggestion:
    """Represents a suggested fix for an inconsistency.

    Attributes:
        suggestion_type: Type of fix needed
        description: Human-readable description of the issue
        fix_prompt: LLM prompt to guide the fix
        priority: Priority level for this fix
        target_content: Content that needs to be fixed
        related_inconsistency: The original inconsistency
        metadata: Additional metadata
    """

    suggestion_type: SuggestionType
    description: str
    fix_prompt: str
    priority: FixPriority
    target_content: str = ""
    related_inconsistency: Inconsistency | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "suggestion_type": self.suggestion_type.value,
            "description": self.description,
            "fix_prompt": self.fix_prompt,
            "priority": self.priority.value,
            "target_content": self.target_content,
            "related_inconsistency": (
                self.related_inconsistency.to_dict() if self.related_inconsistency else None
            ),
            "metadata": self.metadata,
        }


@dataclass
class RepairAttempt:
    """Records a single repair attempt.

    Attributes:
        attempt_number: Which attempt this is (1-3)
        timestamp: When the attempt was made
        issues_before: Issues before this attempt
        issues_after: Issues after this attempt
        strategy_used: What fix strategy was used
        llm_prompt: The prompt sent to LLM
        success: Whether this attempt reduced issues
        metadata: Additional metadata
    """

    attempt_number: int
    timestamp: str
    issues_before: list[dict[str, Any]]
    issues_after: list[dict[str, Any]] | None = None
    strategy_used: str = ""
    llm_prompt: str = ""
    success: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp,
            "issues_before": self.issues_before,
            "issues_after": self.issues_after,
            "strategy_used": self.strategy_used,
            "llm_prompt": self.llm_prompt,
            "success": self.success,
            "metadata": self.metadata,
        }


@dataclass
class RepairHistory:
    """Complete history of repair attempts for a chapter.

    Attributes:
        chapter_number: Chapter being repaired
        started_at: When repair process started
        completed_at: When repair process completed
        attempts: List of repair attempts
        final_status: Final status (success, partial, failed, manual_review)
        validators_used: Which validators were used
        total_issues_found: Total issues found across all validators
        issues_fixed: Issues that were successfully fixed
        issues_remaining: Issues that couldn't be fixed
        escalation_reason: Why escalation happened (if any)
    """

    chapter_number: int
    started_at: str
    completed_at: str = ""
    attempts: list[RepairAttempt] = field(default_factory=list)
    final_status: str = "in_progress"
    validators_used: list[str] = field(default_factory=list)
    total_issues_found: int = 0
    issues_fixed: int = 0
    issues_remaining: int = 0
    escalation_reason: str = ""

    def add_attempt(self, attempt: RepairAttempt) -> None:
        """Add a repair attempt to history."""
        self.attempts.append(attempt)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chapter_number": self.chapter_number,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "final_status": self.final_status,
            "validators_used": self.validators_used,
            "total_issues_found": self.total_issues_found,
            "issues_fixed": self.issues_fixed,
            "issues_remaining": self.issues_remaining,
            "escalation_reason": self.escalation_reason,
            "attempts": [a.to_dict() for a in self.attempts],
            "attempt_count": len(self.attempts),
        }


@dataclass
class AutoFixResult:
    """Result of the auto-fix process.

    Attributes:
        success: Whether the fix process completed successfully
        iteration_count: Number of fix iterations performed
        final_content: The final fixed content
        issues_remaining: List of issues that couldn't be auto-fixed
        all_iterations: History of content through iterations
        manual_review_required: Whether manual review is needed
        repair_history: Detailed repair history
        metadata: Additional metadata about the process
    """

    success: bool
    iteration_count: int
    final_content: str
    issues_remaining: list[Inconsistency]
    all_iterations: list[dict[str, Any]] = field(default_factory=list)
    manual_review_required: bool = False
    repair_history: RepairHistory | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_fully_fixed(self) -> bool:
        """Check if all issues were resolved."""
        return self.success and len(self.issues_remaining) == 0

    @property
    def remaining_critical_count(self) -> int:
        """Count remaining critical issues (severity >= 4)."""
        return len([i for i in self.issues_remaining if i.severity >= 4])

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "iteration_count": self.iteration_count,
            "final_content": self.final_content,
            "issues_remaining": [i.to_dict() for i in self.issues_remaining],
            "all_iterations": self.all_iterations,
            "manual_review_required": self.manual_review_required,
            "is_fully_fixed": self.is_fully_fixed,
            "remaining_critical_count": self.remaining_critical_count,
            "repair_history": self.repair_history.to_dict() if self.repair_history else None,
            "metadata": self.metadata,
        }


class AutoFixer:
    """Automated fixing system for novel content inconsistencies.

    The AutoFixer follows this enhanced flow:
    1. Run multiple validators (ConsistencyVerifier, TimelineValidator, etc.)
    2. Aggregate all issues
    3. Generate comprehensive fix suggestions
    4. Attempt repair with LLM (max 3 retries)
    5. Track repair history
    6. Apply degradation strategy if needed
    7. Flag for manual review if unrecoverable
    """

    def __init__(
        self,
        verifier: ConsistencyVerifier | None = None,
        regenerator: Callable[[str, list[FixSuggestion]], str] | None = None,
        llm: Any | None = None,
        timeline_validator: Any | None = None,
        reference_validator: Any | None = None,
        hallucination_detector: Any | None = None,
        transition_checker: Any | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize the auto-fixer.

        Args:
            verifier: Consistency verifier instance (creates default if None)
            regenerator: Function to regenerate content with fix suggestions
            llm: LLM instance for content regeneration
            timeline_validator: TimelineValidator instance (Wave 2)
            reference_validator: ReferenceValidator instance (Wave 2)
            hallucination_detector: HallucinationDetector instance (Wave 2)
            transition_checker: ChapterTransitionChecker instance (Wave 2)
            max_retries: Maximum number of repair attempts (default: 3)
        """
        self.verifier = verifier or ConsistencyVerifier()
        self.regenerator = regenerator
        self.llm = llm
        self.timeline_validator = timeline_validator
        self.reference_validator = reference_validator
        self.hallucination_detector = hallucination_detector
        self.transition_checker = transition_checker
        self.max_retries = max_retries

        # Global repair history
        self._repair_history: list[RepairHistory] = []

        # Degradation thresholds
        self._critical_threshold = 2  # More than 2 critical issues -> manual review
        self._hallucination_threshold = 0.9  # High confidence hallucination -> manual review
        self._timeline_confidence_threshold = (
            0.85  # High confidence timeline issue -> manual review
        )

    def verify(
        self,
        content: str,
        chapter_number: int,
        story_state: StoryState | None = None,
    ) -> VerificationResult:
        """Verify content for inconsistencies.

        Args:
            content: The chapter content to verify
            chapter_number: Chapter number for context
            story_state: Current story state for consistency checking

        Returns:
            VerificationResult with detected inconsistencies
        """
        logger.info(f"Verifying chapter {chapter_number} for inconsistencies")

        result = self.verifier.verify(
            chapter_content=content,
            chapter_number=chapter_number,
            story_state=story_state,
        )

        logger.info(
            f"Verification complete: {len(result.inconsistencies)} issues found, "
            f"is_consistent={result.is_consistent}"
        )

        return result

    async def verify_with_all_validators(
        self,
        content: str,
        chapter_number: int,
        prev_chapter_content: str | None = None,
        world_context: str = "",
    ) -> dict[str, Any]:
        """Run all available validators and aggregate issues.

        Args:
            content: Chapter content to verify
            chapter_number: Chapter number
            prev_chapter_content: Previous chapter content for transition checks
            world_context: World context for hallucination detection

        Returns:
            Dictionary with aggregated issues from all validators
        """
        all_issues: list[Inconsistency] = []
        validator_results: dict[str, Any] = {}
        validators_used: list[str] = []

        # 1. Run ConsistencyVerifier
        try:
            result = self.verifier.verify(content, chapter_number)
            all_issues.extend(result.inconsistencies)
            validator_results["consistency"] = result
            validators_used.append("ConsistencyVerifier")
        except Exception as e:
            logger.error(f"ConsistencyVerifier failed: {e}")

        # 2. Run TimelineValidator if available
        if self.timeline_validator:
            try:
                # TimelineValidator needs novel_id, so we use a placeholder
                # In real usage, this would be passed in
                timeline_report = await self.timeline_validator.validate_timeline(
                    f"chapter_{chapter_number}"
                )

                # Convert timeline conflicts to Inconsistency format
                for conflict in timeline_report.conflicts:
                    inconsistency = Inconsistency(
                        inconsistency_type=self._map_timeline_conflict_type(conflict.conflict_type),
                        severity=self._map_severity(conflict.severity.value),
                        description=conflict.reason,
                        location=f"Chapter {conflict.chapter}",
                        entities=[conflict.character_name],
                        metadata={"timeline_conflict": conflict.to_dict()},
                    )
                    all_issues.append(inconsistency)

                validator_results["timeline"] = timeline_report
                validators_used.append("TimelineValidator")
            except Exception as e:
                logger.error(f"TimelineValidator failed: {e}")

        # 3. Run ReferenceValidator if available
        if self.reference_validator:
            try:
                ref_verifications = await self.reference_validator.validate_chapter_references(
                    content, chapter_number
                )

                # Convert reference issues to Inconsistency format
                for verification in ref_verifications:
                    if not verification.is_valid:
                        inconsistency = Inconsistency(
                            inconsistency_type="reference_issue",
                            severity=3 if verification.confidence > 0.5 else 4,
                            description=f"Invalid reference: {verification.reference.text[:100]}",
                            location=f"Chapter {chapter_number}",
                            entities=[verification.reference.speaker],
                            metadata={"reference_verification": verification},
                        )
                        all_issues.append(inconsistency)

                validator_results["reference"] = ref_verifications
                validators_used.append("ReferenceValidator")
            except Exception as e:
                logger.error(f"ReferenceValidator failed: {e}")

        # 4. Run HallucinationDetector if available
        if self.hallucination_detector and world_context:
            try:
                hallucination_report = await self.hallucination_detector.detect_hallucinations(
                    content, world_context
                )

                # Convert hallucinations to Inconsistency format
                for hallucination in hallucination_report.factual_hallucinations:
                    inconsistency = Inconsistency(
                        inconsistency_type="hallucination",
                        severity=4 if hallucination.confidence > 0.8 else 3,
                        description=f"Hallucination detected: {hallucination.text[:100]}",
                        location=f"Chapter {chapter_number}",
                        metadata={"hallucination": hallucination},
                    )
                    all_issues.append(inconsistency)

                validator_results["hallucination"] = hallucination_report
                validators_used.append("HallucinationDetector")
            except Exception as e:
                logger.error(f"HallucinationDetector failed: {e}")

        # 5. Run ChapterTransitionChecker if available
        if self.transition_checker and prev_chapter_content:
            try:
                transition_report = self.transition_checker.check_transition(
                    prev_chapter_content, content, chapter_number
                )

                # Convert transition issues to Inconsistency format
                if transition_report.has_issues:
                    for event in transition_report.ignored_events:
                        inconsistency = Inconsistency(
                            inconsistency_type="transition_issue",
                            severity=4 if event.importance == "high" else 3,
                            description=f"Unresolved event from previous chapter: {event.description}",
                            location=f"Chapter {chapter_number}",
                            metadata={"transition_event": event},
                        )
                        all_issues.append(inconsistency)

                validator_results["transition"] = transition_report
                validators_used.append("ChapterTransitionChecker")
            except Exception as e:
                logger.error(f"ChapterTransitionChecker failed: {e}")

        return {
            "issues": all_issues,
            "validator_results": validator_results,
            "validators_used": validators_used,
            "is_consistent": len(all_issues) == 0,
        }

    def generate_fix_suggestions(
        self,
        inconsistencies: list[Inconsistency],
    ) -> list[FixSuggestion]:
        """Convert inconsistencies to fix suggestions.

        Args:
            inconsistencies: List of detected inconsistencies

        Returns:
            List of fix suggestions sorted by priority
        """
        suggestions: list[FixSuggestion] = []

        for inconsistency in inconsistencies:
            suggestion = self._convert_inconsistency_to_suggestion(inconsistency)
            if suggestion:
                suggestions.append(suggestion)

        # Sort by priority (critical first)
        priority_order = {
            FixPriority.CRITICAL: 0,
            FixPriority.HIGH: 1,
            FixPriority.MEDIUM: 2,
            FixPriority.LOW: 3,
        }
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 99))

        logger.info(f"Generated {len(suggestions)} fix suggestions")
        return suggestions

    def _convert_inconsistency_to_suggestion(
        self,
        inconsistency: Inconsistency,
    ) -> FixSuggestion | None:
        """Convert a single inconsistency to a fix suggestion.

        Args:
            inconsistency: The inconsistency to convert

        Returns:
            FixSuggestion or None if cannot be auto-fixed
        """
        from src.novel_agent.novel.consistency_verifier import InconsistencyType

        # Map inconsistency types to suggestion types and priorities
        type_mapping: dict[
            str,  # Can be InconsistencyType or string (for Wave 2 validators)
            tuple[SuggestionType, FixPriority, str],
        ] = {
            InconsistencyType.DEAD_CHARACTER_APPEARANCE.value: (
                SuggestionType.CORRECT_CHARACTER_STATE,
                FixPriority.CRITICAL,
                "角色已被标记为死亡，但仍然在章节中表现出主动行为。"
                "请将此角色的行为改为回忆、提及或完全移除。",
            ),
            InconsistencyType.LOCATION_MISMATCH.value: (
                SuggestionType.UPDATE_LOCATION,
                FixPriority.HIGH,
                "角色位置与之前章节的状态不一致。"
                "请确认并更正角色的当前位置，或添加位置转移的过渡描述。",
            ),
            InconsistencyType.TIMELINE_ERROR.value: (
                SuggestionType.FIX_TIMELINE,
                FixPriority.HIGH,
                "时间线存在逻辑错误。请检查章节中的时间顺序，确保事件按正确的时间顺序发生。",
            ),
            InconsistencyType.CHARACTER_STATE_CONTRADICTION.value: (
                SuggestionType.CORRECT_CHARACTER_STATE,
                FixPriority.CRITICAL,
                "角色状态与之前章节的描述矛盾。请确保角色状态与之前章节保持一致。",
            ),
            InconsistencyType.MISSING_CHARACTER.value: (
                SuggestionType.ADD_MISSING_CONTEXT,
                FixPriority.MEDIUM,
                "角色出现在章节中，但缺乏必要的上下文介绍。请添加角色的简要介绍或重新引入。",
            ),
            InconsistencyType.RELATIONSHIP_CONTRADICTION.value: (
                SuggestionType.REMOVE_CONTRADICTION,
                FixPriority.HIGH,
                "角色关系描述与之前章节矛盾。请更正关系描述以保持与故事设定一致。",
            ),
            InconsistencyType.WORLD_RULE_VIOLATION.value: (
                SuggestionType.REMOVE_CONTRADICTION,
                FixPriority.CRITICAL,
                "内容违反了世界规则设定。请修改内容以符合已建立的世界规则。",
            ),
            # Wave 2 validator types
            "hallucination": (
                SuggestionType.FIX_HALLUCINATION,
                FixPriority.HIGH,
                "检测到可能的虚构内容。请验证此内容是否与已建立的世界观一致，或添加适当的标记。",
            ),
            "reference_issue": (
                SuggestionType.FIX_REFERENCE,
                FixPriority.HIGH,
                "引用内容无法在已建立的上下文中找到证据支持。请验证引用的准确性。",
            ),
            "transition_issue": (
                SuggestionType.FIX_TRANSITION,
                FixPriority.MEDIUM,
                "上一章的悬念或事件未得到适当处理。请在章节开头添加过渡或说明。",
            ),
            "timeline_conflict": (
                SuggestionType.FIX_TIMELINE,
                FixPriority.CRITICAL,
                "时间线冲突检测到。请检查事件的时序逻辑。",
            ),
        }

        # Get inconsistency type value (handle both enum and string)
        inconsistency_type_value = (
            inconsistency.inconsistency_type.value
            if hasattr(inconsistency.inconsistency_type, "value")
            else str(inconsistency.inconsistency_type)
        )

        # Get mapping for this inconsistency type
        mapping = type_mapping.get(inconsistency_type_value)
        if not mapping:
            logger.warning(f"No auto-fix mapping for {inconsistency.inconsistency_type}")
            return None

        suggestion_type, priority, default_prompt = mapping

        # Build the fix prompt
        fix_prompt = f"""问题描述：{inconsistency.description}

建议修复：{inconsistency.suggestion or default_prompt}

严重程度：{inconsistency.severity}/5
相关实体：{", ".join(inconsistency.entities) if inconsistency.entities else "无"}

请根据以上信息修改章节内容，解决该一致性问题。保持原有叙事风格，只修正不一致之处。"""

        return FixSuggestion(
            suggestion_type=suggestion_type,
            description=inconsistency.description,
            fix_prompt=fix_prompt,
            priority=priority,
            target_content=inconsistency.location,
            related_inconsistency=inconsistency,
            metadata={
                "severity": inconsistency.severity,
                "entities": inconsistency.entities,
            },
        )

    async def fix_and_regenerate(
        self,
        content: str,
        verification_result: VerificationResult,
        max_iterations: int | None = None,
        prev_chapter_content: str | None = None,
        world_context: str = "",
    ) -> AutoFixResult:
        """Main auto-fix loop: verify → fix → regenerate → re-verify.

        Args:
            content: Original chapter content
            verification_result: Initial verification with issues
            max_iterations: Maximum fix attempts (default: self.max_retries)
            prev_chapter_content: Previous chapter for transition checks
            world_context: World context for hallucination detection

        Returns:
            AutoFixResult with final content and fix history
        """
        max_iterations = max_iterations or self.max_retries

        # Initialize repair history
        repair_history = RepairHistory(
            chapter_number=verification_result.chapter_number,
            started_at=datetime.now().isoformat(),
        )

        iterations = []
        current_content = content

        for iteration in range(max_iterations):
            # 1. Run all validators to get comprehensive issue list
            if iteration == 0 and isinstance(verification_result, VerificationResult):
                # Use existing verification result for first iteration
                issues = verification_result.inconsistencies
                validators_used = ["ConsistencyVerifier"]
            else:
                # Run all validators for subsequent iterations
                validation_result = await self.verify_with_all_validators(
                    current_content,
                    verification_result.chapter_number,
                    prev_chapter_content,
                    world_context,
                )
                issues = [
                    self._dict_to_inconsistency(i) if isinstance(i, dict) else i
                    for i in validation_result["issues"]
                ]
                validators_used = validation_result["validators_used"]

            repair_history.validators_used = list(
                set(repair_history.validators_used + validators_used)
            )

            if not issues:
                break  # No issues to fix

            # Record attempt start
            attempt = RepairAttempt(
                attempt_number=iteration + 1,
                timestamp=datetime.now().isoformat(),
                issues_before=[i.to_dict() for i in issues],
            )

            # 2. Generate fix suggestions
            suggestions = self.generate_fix_suggestions(issues)

            if not suggestions:
                break  # No suggestions available

            # 3. Build fix prompt
            fix_prompt = self._build_fix_prompt(suggestions)
            attempt.strategy_used = f"llm_regeneration_with_{len(suggestions)}_suggestions"
            attempt.llm_prompt = fix_prompt

            # 4. Call LLM to regenerate
            if self.llm:
                try:
                    system_prompt = (
                        "You are an expert editor fixing inconsistencies in novel content."
                    )
                    response = await self.llm.generate_with_system(
                        system=system_prompt,
                        prompt=f"{fix_prompt}\n\n原始内容:\n{current_content}",
                    )
                    current_content = (
                        response.content if hasattr(response, "content") else str(response)
                    )
                except Exception as e:
                    logger.error(f"LLM regeneration failed: {e}")
                    attempt.success = False
                    repair_history.add_attempt(attempt)
                    return AutoFixResult(
                        success=False,
                        iteration_count=iteration + 1,
                        final_content=current_content,
                        issues_remaining=issues,
                        all_iterations=iterations,
                        manual_review_required=True,
                        repair_history=repair_history,
                        metadata={"error": str(e)},
                    )
            else:
                logger.warning("No LLM provided, cannot auto-fix content")
                attempt.success = False
                repair_history.add_attempt(attempt)
                return AutoFixResult(
                    success=False,
                    iteration_count=0,
                    final_content=content,
                    issues_remaining=issues,
                    all_iterations=iterations,
                    manual_review_required=True,
                    repair_history=repair_history,
                    metadata={"reason": "no_llm_available"},
                )

            # 5. Re-verify to check if fixed
            new_result = self.verify(
                current_content,
                verification_result.chapter_number,
            )

            attempt.issues_after = [i.to_dict() for i in new_result.inconsistencies]
            attempt.success = len(new_result.inconsistencies) < len(issues)

            repair_history.add_attempt(attempt)

            iterations.append(
                {
                    "iteration": iteration + 1,
                    "suggestions": [s.to_dict() for s in suggestions],
                    "issues_before": len(issues),
                    "issues_after": len(new_result.inconsistencies),
                    "attempt_success": attempt.success,
                }
            )

            # 6. Check if fixed
            if new_result.is_consistent:
                repair_history.final_status = "success"
                repair_history.issues_fixed = len(issues)
                repair_history.issues_remaining = 0
                repair_history.completed_at = datetime.now().isoformat()

                return AutoFixResult(
                    success=True,
                    iteration_count=iteration + 1,
                    final_content=current_content,
                    issues_remaining=[],
                    all_iterations=iterations,
                    manual_review_required=False,
                    repair_history=repair_history,
                )

            # Prepare for next iteration
            verification_result = new_result

        # Max iterations reached, check degradation strategy
        final_issues = (
            verification_result.inconsistencies
            if hasattr(verification_result, "inconsistencies")
            else issues
        )
        escalation_needed, escalation_reason = self._should_escalate_to_manual_review(final_issues)

        repair_history.final_status = "manual_review" if escalation_needed else "partial"
        repair_history.issues_fixed = repair_history.total_issues_found - len(final_issues)
        repair_history.issues_remaining = len(final_issues)
        repair_history.escalation_reason = escalation_reason
        repair_history.completed_at = datetime.now().isoformat()

        # Store in global history
        self._repair_history.append(repair_history)

        return AutoFixResult(
            success=False,
            iteration_count=max_iterations,
            final_content=current_content,
            issues_remaining=final_issues,
            all_iterations=iterations,
            manual_review_required=escalation_needed,
            repair_history=repair_history,
        )

    def _build_fix_prompt(self, suggestions: list[FixSuggestion]) -> str:
        """Build combined fix prompt from suggestions."""
        parts = ["请修改以下内容以修复以下问题：\n"]
        for i, s in enumerate(suggestions, 1):
            parts.append(f"{i}. [{s.suggestion_type.value}] {s.description}")
            parts.append(f"   建议: {s.fix_prompt}\n")
        return "\n".join(parts)

    def _should_escalate_to_manual_review(self, issues: list[Inconsistency]) -> tuple[bool, str]:
        """Determine if issues should be escalated to manual review.

        Implements degradation strategy:
        1. Escalate if too many critical issues
        2. Escalate if high-confidence hallucinations
        3. Escalate if high-confidence timeline conflicts
        4. Otherwise, allow partial fix

        Args:
            issues: List of remaining issues

        Returns:
            Tuple of (should_escalate, reason)
        """
        if not issues:
            return False, ""

        # Count critical issues
        critical_count = sum(1 for i in issues if i.severity >= 4)
        if critical_count > self._critical_threshold:
            return True, f"Too many critical issues ({critical_count} > {self._critical_threshold})"

        # Check for high-confidence hallucinations
        for issue in issues:
            if (
                issue.inconsistency_type == "hallucination"
                or str(issue.inconsistency_type) == "hallucination"
            ):
                hallucination_meta = issue.metadata.get("hallucination")
                if hallucination_meta and hasattr(hallucination_meta, "confidence"):
                    if hallucination_meta.confidence > self._hallucination_threshold:
                        return (
                            True,
                            f"High-confidence hallucination detected (>{self._hallucination_threshold})",
                        )

        # Check for high-confidence timeline conflicts
        for issue in issues:
            if "timeline" in str(issue.inconsistency_type).lower():
                timeline_meta = issue.metadata.get("timeline_conflict")
                if timeline_meta:
                    return True, "Timeline conflict requires manual verification"

        # Allow partial fix
        return False, ""

    def validate_fix(
        self,
        original_content: str,
        fixed_content: str,
        min_similarity: float = 0.7,
    ) -> dict[str, Any]:
        """Validate that the fix preserves the original content's essence.

        Args:
            original_content: Original chapter content
            fixed_content: Fixed chapter content
            min_similarity: Minimum similarity ratio (0-1)

        Returns:
            Validation result with metrics
        """
        import difflib

        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(
            None,
            original_content,
            fixed_content,
        ).ratio()

        # Calculate length change
        original_len = len(original_content)
        fixed_len = len(fixed_content)
        length_change_ratio = (fixed_len - original_len) / max(original_len, 1)

        # Check for content preservation
        is_valid = similarity >= min_similarity

        # Generate diff for reporting
        diff = list(
            difflib.unified_diff(
                original_content.splitlines(keepends=True),
                fixed_content.splitlines(keepends=True),
                fromfile="original",
                tofile="fixed",
            )
        )

        result = {
            "is_valid": is_valid,
            "similarity_ratio": round(similarity, 4),
            "min_similarity_required": min_similarity,
            "original_length": original_len,
            "fixed_length": fixed_len,
            "length_change_ratio": round(length_change_ratio, 4),
            "diff_line_count": len(diff),
            "diff_sample": "".join(diff[:50]) if diff else "",
        }

        logger.info(
            f"Fix validation: similarity={similarity:.2%}, "
            f"valid={is_valid}, length_change={length_change_ratio:+.1%}"
        )

        return result

    def get_fix_summary(self, result: AutoFixResult) -> str:
        """Generate a human-readable summary of the fix process.

        Args:
            result: AutoFixResult to summarize

        Returns:
            Summary string
        """
        lines = [
            f"自动修复结果：{'成功' if result.success else '部分完成'}",
            f"迭代次数：{result.iteration_count}",
            f"完全修复：{'是' if result.is_fully_fixed else '否'}",
        ]

        if result.issues_remaining:
            lines.append(f"剩余问题：{len(result.issues_remaining)} 个")
            critical = result.remaining_critical_count
            if critical > 0:
                lines.append(f"  - 其中严重问题：{critical} 个")

        if result.manual_review_required:
            lines.append("需要人工审核：是")
            if result.repair_history and result.repair_history.escalation_reason:
                lines.append(f"  - 原因：{result.repair_history.escalation_reason}")

        if result.repair_history:
            lines.append(f"使用的验证器：{', '.join(result.repair_history.validators_used)}")
            lines.append(f"修复尝试次数：{len(result.repair_history.attempts)}")

        return "\n".join(lines)

    def get_repair_statistics(self) -> dict[str, Any]:
        """Get statistics about all repair attempts.

        Returns:
            Dictionary with repair statistics
        """
        if not self._repair_history:
            return {
                "total_repairs": 0,
                "successful_repairs": 0,
                "failed_repairs": 0,
                "manual_reviews": 0,
                "average_iterations": 0,
            }

        successful = sum(1 for h in self._repair_history if h.final_status == "success")
        failed = sum(1 for h in self._repair_history if h.final_status == "failed")
        manual = sum(1 for h in self._repair_history if h.final_status == "manual_review")
        total_iterations = sum(len(h.attempts) for h in self._repair_history)

        return {
            "total_repairs": len(self._repair_history),
            "successful_repairs": successful,
            "failed_repairs": failed,
            "manual_reviews": manual,
            "average_iterations": total_iterations / len(self._repair_history)
            if self._repair_history
            else 0,
            "success_rate": successful / len(self._repair_history) if self._repair_history else 0,
        }

    def _map_timeline_conflict_type(self, conflict_type: str) -> str:
        """Map TimelineValidator conflict type to InconsistencyType."""
        mapping = {
            "dead_character_action": "dead_character_appearance",
            "missing_character_action": "missing_character",
            "born_after_death": "timeline_error",
            "married_before_meeting": "timeline_error",
            "impossible_sequence": "timeline_error",
        }
        return mapping.get(conflict_type, "timeline_error")

    def _map_severity(self, severity_str: str) -> int:
        """Map severity string to numeric value."""
        mapping = {
            "critical": 5,
            "error": 4,
            "warning": 3,
            "info": 2,
        }
        return mapping.get(severity_str.lower(), 3)

    def _dict_to_inconsistency(self, data: dict[str, Any]) -> Inconsistency:
        """Convert dictionary to Inconsistency object."""
        from src.novel_agent.novel.consistency_verifier import InconsistencyType

        # Handle both enum and string inconsistency types
        inconsistency_type_str = data.get("inconsistency_type", "unknown")
        try:
            inconsistency_type = InconsistencyType(inconsistency_type_str)
        except ValueError:
            # Create a mock enum-like object for unknown types
            inconsistency_type = type(
                "DynamicInconsistencyType", (), {"value": inconsistency_type_str}
            )()

        return Inconsistency(
            inconsistency_type=inconsistency_type,
            severity=data.get("severity", 3),
            description=data.get("description", ""),
            location=data.get("location", ""),
            suggestion=data.get("suggestion", ""),
            entities=data.get("entities", []),
            metadata=data.get("metadata", {}),
        )
