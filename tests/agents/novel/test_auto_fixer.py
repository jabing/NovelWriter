"""Tests for auto_fixer module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.novel_agent.llm.base import LLMResponse
from src.novel_agent.novel.auto_fixer import (
    AutoFixer,
    AutoFixResult,
    FixPriority,
    FixSuggestion,
    SuggestionType,
)
from src.novel_agent.novel.consistency_verifier import (
    ConsistencyVerifier,
    Inconsistency,
    InconsistencyType,
    VerificationResult,
)
from src.novel_agent.novel.continuity import CharacterState, StoryState


class TestFixSuggestion:
    """Test FixSuggestion dataclass."""

    def test_fix_suggestion_creation(self):
        """Test creating FixSuggestion."""
        suggestion = FixSuggestion(
            suggestion_type=SuggestionType.CORRECT_CHARACTER_STATE,
            description="Character is dead but appearing",
            fix_prompt="Remove the dead character's appearance",
            priority=FixPriority.CRITICAL,
            target_content="Chapter 5, paragraph 3",
            metadata={"severity": 5, "character": "Villain"},
        )

        assert suggestion.suggestion_type == SuggestionType.CORRECT_CHARACTER_STATE
        assert suggestion.description == "Character is dead but appearing"
        assert suggestion.fix_prompt == "Remove the dead character's appearance"
        assert suggestion.priority == FixPriority.CRITICAL
        assert suggestion.target_content == "Chapter 5, paragraph 3"
        assert suggestion.metadata["severity"] == 5
        assert suggestion.related_inconsistency is None

    def test_fix_suggestion_to_dict(self):
        """Test FixSuggestion serialization."""
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.DEAD_CHARACTER_APPEARANCE,
            severity=5,
            description="Test inconsistency",
        )
        suggestion = FixSuggestion(
            suggestion_type=SuggestionType.CORRECT_CHARACTER_STATE,
            description="Test description",
            fix_prompt="Test fix",
            priority=FixPriority.HIGH,
            related_inconsistency=inconsistency,
        )

        data = suggestion.to_dict()

        assert data["suggestion_type"] == "correct_character_state"
        assert data["description"] == "Test description"
        assert data["priority"] == "high"
        assert data["related_inconsistency"] is not None
        assert data["related_inconsistency"]["inconsistency_type"] == "dead_character_appearance"

    def test_fix_suggestion_with_inconsistency(self):
        """Test FixSuggestion with related inconsistency."""
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.LOCATION_MISMATCH,
            severity=3,
            description="Character location mismatch",
            entities=["Hero", "Castle", "Forest"],
        )

        suggestion = FixSuggestion(
            suggestion_type=SuggestionType.UPDATE_LOCATION,
            description="Fix location mismatch",
            fix_prompt="Update character location",
            priority=FixPriority.HIGH,
            related_inconsistency=inconsistency,
        )

        assert suggestion.related_inconsistency == inconsistency
        assert suggestion.related_inconsistency.entities == ["Hero", "Castle", "Forest"]


class TestAutoFixerInitialization:
    """Test AutoFixer setup."""

    def test_init_with_llm(self):
        """Test initialization with LLM."""
        mock_llm = MagicMock()
        fixer = AutoFixer(llm=mock_llm)

        assert fixer.llm == mock_llm
        assert fixer.verifier is not None
        assert isinstance(fixer.verifier, ConsistencyVerifier)
        assert fixer.regenerator is None

    def test_init_with_custom_verifier(self):
        """Test initialization with custom verifier."""
        mock_llm = MagicMock()
        custom_verifier = MagicMock(spec=ConsistencyVerifier)
        fixer = AutoFixer(verifier=custom_verifier, llm=mock_llm)

        assert fixer.verifier == custom_verifier

    def test_init_with_custom_regenerator(self):
        """Test initialization with custom regenerator."""
        mock_regenerator = MagicMock()
        fixer = AutoFixer(regenerator=mock_regenerator)

        assert fixer.regenerator == mock_regenerator

    def test_init_default(self):
        """Test default initialization."""
        fixer = AutoFixer()

        assert fixer.llm is None
        assert fixer.verifier is not None
        assert isinstance(fixer.verifier, ConsistencyVerifier)


class TestAutoFixResult:
    """Test AutoFixResult dataclass."""

    def test_is_fully_fixed_property(self):
        """Test is_fully_fixed property."""
        result = AutoFixResult(
            success=True,
            iteration_count=2,
            final_content="Fixed content",
            issues_remaining=[],
        )
        assert result.is_fully_fixed is True

    def test_is_not_fully_fixed(self):
        """Test when not fully fixed."""
        issue = Inconsistency(
            inconsistency_type=InconsistencyType.TIMELINE_ERROR,
            severity=3,
            description="Timeline issue",
        )
        result = AutoFixResult(
            success=True,
            iteration_count=2,
            final_content="Partially fixed",
            issues_remaining=[issue],
        )
        assert result.is_fully_fixed is False

    def test_remaining_critical_count(self):
        """Test remaining_critical_count property."""
        issues = [
            Inconsistency(InconsistencyType.DEAD_CHARACTER_APPEARANCE, 5, "Critical"),
            Inconsistency(InconsistencyType.CHARACTER_STATE_CONTRADICTION, 4, "High"),
            Inconsistency(InconsistencyType.LOCATION_MISMATCH, 3, "Medium"),
        ]
        result = AutoFixResult(
            success=False,
            iteration_count=3,
            final_content="Content",
            issues_remaining=issues,
        )
        assert result.remaining_critical_count == 2  # severity >= 4

    def test_to_dict(self):
        """Test serialization."""
        result = AutoFixResult(
            success=True,
            iteration_count=1,
            final_content="Fixed",
            issues_remaining=[],
            manual_review_required=False,
        )
        data = result.to_dict()

        assert data["success"] is True
        assert data["iteration_count"] == 1
        assert data["is_fully_fixed"] is True
        assert data["remaining_critical_count"] == 0
        assert data["manual_review_required"] is False


class TestVerifyMethod:
    """Test the verify method."""

    def test_verify_content(self):
        """Test verifying content."""
        fixer = AutoFixer()
        story_state = StoryState(
            chapter=1,
            location="Castle",
            active_characters=["Hero"],
            character_states={
                "Hero": CharacterState("Hero", "alive", "Castle", "human"),
            },
        )

        result = fixer.verify(
            content="Hero walks through the Castle.",
            chapter_number=1,
            story_state=story_state,
        )

        assert isinstance(result, VerificationResult)
        assert result.chapter_number == 1

    def test_verify_without_story_state(self):
        """Test verifying without story state."""
        fixer = AutoFixer()

        result = fixer.verify(
            content="Some chapter content",
            chapter_number=5,
        )

        assert isinstance(result, VerificationResult)
        assert result.chapter_number == 5


class TestGenerateFixSuggestions:
    """Test suggestion generation."""

    def test_dead_character_suggestion(self):
        """Test suggestion for dead character."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.DEAD_CHARACTER_APPEARANCE,
            severity=5,
            description="Dead character Villain is speaking",
            entities=["Villain"],
            location="Chapter 5",
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.CORRECT_CHARACTER_STATE
        assert suggestions[0].priority == FixPriority.CRITICAL
        assert "Villain" in suggestions[0].fix_prompt

    def test_location_mismatch_suggestion(self):
        """Test suggestion for location mismatch."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.LOCATION_MISMATCH,
            severity=3,
            description="Character Hero is in Forest but should be in Castle",
            entities=["Hero", "Castle", "Forest"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.UPDATE_LOCATION
        assert suggestions[0].priority == FixPriority.HIGH
        assert "位置" in suggestions[0].fix_prompt

    def test_timeline_error_suggestion(self):
        """Test suggestion for timeline error."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.TIMELINE_ERROR,
            severity=3,
            description="References chapter 6 in chapter 5",
            entities=["第6章"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.FIX_TIMELINE
        assert suggestions[0].priority == FixPriority.HIGH

    def test_character_state_contradiction_suggestion(self):
        """Test suggestion for character state contradiction."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.CHARACTER_STATE_CONTRADICTION,
            severity=5,
            description="Character status contradiction",
            entities=["Hero"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.CORRECT_CHARACTER_STATE
        assert suggestions[0].priority == FixPriority.CRITICAL

    def test_missing_character_suggestion(self):
        """Test suggestion for missing character."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.MISSING_CHARACTER,
            severity=2,
            description="New character appears without introduction",
            entities=["Stranger"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.ADD_MISSING_CONTEXT
        assert suggestions[0].priority == FixPriority.MEDIUM

    def test_relationship_contradiction_suggestion(self):
        """Test suggestion for relationship contradiction."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.RELATIONSHIP_CONTRADICTION,
            severity=3,
            description="Character relationships don't match",
            entities=["Hero", "Villain"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.REMOVE_CONTRADICTION
        assert suggestions[0].priority == FixPriority.HIGH

    def test_world_rule_violation_suggestion(self):
        """Test suggestion for world rule violation."""
        fixer = AutoFixer()
        inconsistency = Inconsistency(
            inconsistency_type=InconsistencyType.WORLD_RULE_VIOLATION,
            severity=5,
            description="Magic used without mana",
            entities=["Hero"],
        )

        suggestions = fixer.generate_fix_suggestions([inconsistency])

        assert len(suggestions) == 1
        assert suggestions[0].suggestion_type == SuggestionType.REMOVE_CONTRADICTION
        assert suggestions[0].priority == FixPriority.CRITICAL

    def test_unknown_inconsistency_type(self):
        """Test handling of unknown inconsistency type."""
        fixer = AutoFixer()
        # When given an empty list, should return empty suggestions
        suggestions = fixer.generate_fix_suggestions([])
        assert suggestions == []

        # Test with unknown type by creating a mock-like inconsistency
        # The implementation should gracefully handle types not in mapping
        from unittest.mock import MagicMock
        mock_inconsistency = MagicMock()
        mock_inconsistency.inconsistency_type = "unknown_type"
        mock_inconsistency.description = "Unknown issue"
        mock_inconsistency.severity = 3
        mock_inconsistency.entities = []
        mock_inconsistency.location = ""
        mock_inconsistency.suggestion = ""

        suggestions = fixer.generate_fix_suggestions([mock_inconsistency])
        # Should return empty list for unknown types (filtered out)
        assert suggestions == []
    def test_priority_sorting(self):
        """Test suggestions sorted by priority."""
        fixer = AutoFixer()
        inconsistencies = [
            Inconsistency(InconsistencyType.LOCATION_MISMATCH, 3, "Low priority"),
            Inconsistency(InconsistencyType.DEAD_CHARACTER_APPEARANCE, 5, "Critical"),
            Inconsistency(InconsistencyType.MISSING_CHARACTER, 2, "Medium priority"),
        ]

        suggestions = fixer.generate_fix_suggestions(inconsistencies)

        assert len(suggestions) == 3
        # Should be sorted: CRITICAL first, then HIGH, then MEDIUM
        assert suggestions[0].priority == FixPriority.CRITICAL
        assert suggestions[1].priority == FixPriority.HIGH
        assert suggestions[2].priority == FixPriority.MEDIUM

    def test_multiple_suggestions_same_priority(self):
        """Test handling multiple suggestions with same priority."""
        fixer = AutoFixer()
        inconsistencies = [
            Inconsistency(InconsistencyType.LOCATION_MISMATCH, 3, "Location 1"),
            Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Timeline 1"),
            Inconsistency(InconsistencyType.RELATIONSHIP_CONTRADICTION, 3, "Relation 1"),
        ]

        suggestions = fixer.generate_fix_suggestions(inconsistencies)

        assert len(suggestions) == 3
        # All should have HIGH priority
        for s in suggestions:
            assert s.priority == FixPriority.HIGH


class TestBuildFixPrompt:
    """Test fix prompt building."""

    def test_build_fix_prompt(self):
        """Test building fix prompt from suggestions."""
        fixer = AutoFixer()
        suggestions = [
            FixSuggestion(
                suggestion_type=SuggestionType.CORRECT_CHARACTER_STATE,
                description="Fix 1",
                fix_prompt="Fix prompt 1",
                priority=FixPriority.CRITICAL,
            ),
            FixSuggestion(
                suggestion_type=SuggestionType.UPDATE_LOCATION,
                description="Fix 2",
                fix_prompt="Fix prompt 2",
                priority=FixPriority.HIGH,
            ),
        ]

        prompt = fixer._build_fix_prompt(suggestions)

        assert "请修改以下内容以修复以下问题" in prompt
        assert "Fix 1" in prompt
        assert "Fix 2" in prompt
        # Check for enum repr format (SuggestionType.CORRECT_CHARACTER_STATE)
        assert "CORRECT_CHARACTER_STATE" in prompt

    def test_build_empty_fix_prompt(self):
        """Test building fix prompt with no suggestions."""
        fixer = AutoFixer()
        prompt = fixer._build_fix_prompt([])

        assert "请修改以下内容以修复以下问题" in prompt


class TestValidateFix:
    """Test fix validation."""

    def test_validate_similar_content(self):
        """Test validation with similar content."""
        fixer = AutoFixer()
        original = "This is the original chapter content."
        fixed = "This is the original chapter content."  # Identical

        result = fixer.validate_fix(original, fixed)

        assert result["is_valid"] is True
        assert result["similarity_ratio"] == 1.0
        assert result["length_change_ratio"] == 0.0

    def test_validate_dissimilar_content(self):
        """Test validation with very different content."""
        fixer = AutoFixer()
        original = "This is the original chapter content about dragons."
        fixed = "Something completely different about spaceships and aliens."

        result = fixer.validate_fix(original, fixed, min_similarity=0.7)

        assert result["is_valid"] is False
        assert result["similarity_ratio"] < 0.7

    def test_validate_length_change(self):
        """Test validation tracks length changes."""
        fixer = AutoFixer()
        original = "Short content."
        fixed = "This is much longer content that has many more words than the original ever had."

        result = fixer.validate_fix(original, fixed)

        assert result["original_length"] == len(original)
        assert result["fixed_length"] == len(fixed)
        assert result["length_change_ratio"] > 0

    def test_validate_generates_diff(self):
        """Test validation generates diff."""
        fixer = AutoFixer()
        original = "Line 1\nLine 2\nLine 3"
        fixed = "Line 1\nLine 2 modified\nLine 3"

        result = fixer.validate_fix(original, fixed)

        assert result["diff_line_count"] > 0
        assert "diff_sample" in result


class TestGetFixSummary:
    """Test fix summary generation."""

    def test_summary_success(self):
        """Test summary for successful fix."""
        fixer = AutoFixer()
        result = AutoFixResult(
            success=True,
            iteration_count=2,
            final_content="Fixed",
            issues_remaining=[],
        )

        summary = fixer.get_fix_summary(result)

        assert "成功" in summary
        assert "迭代次数：2" in summary
        assert "完全修复：是" in summary

    def test_summary_partial(self):
        """Test summary for partial fix."""
        fixer = AutoFixer()
        result = AutoFixResult(
            success=False,
            iteration_count=3,
            final_content="Partial",
            issues_remaining=[
                Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue 1"),
                Inconsistency(InconsistencyType.DEAD_CHARACTER_APPEARANCE, 5, "Critical"),
            ],
            manual_review_required=True,
        )

        summary = fixer.get_fix_summary(result)

        assert "部分完成" in summary
        assert "完全修复：否" in summary
        assert "剩余问题：2 个" in summary
        assert "其中严重问题：1 个" in summary
        assert "需要人工审核：是" in summary

    def test_summary_no_issues(self):
        """Test summary with no remaining issues."""
        fixer = AutoFixer()
        result = AutoFixResult(
            success=True,
            iteration_count=1,
            final_content="Fixed",
            issues_remaining=[],
        )

        summary = fixer.get_fix_summary(result)

        assert "严重问题" not in summary  # Should not mention critical issues if none


class TestVerifyRegenerateLoop:
    """Test the core verify-regenerate loop."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.mark.asyncio
    async def test_successful_fix(self, mock_llm):
        """Test successful auto-fix."""
        # First verification: has issues
        # After fix: no issues
        fixer = AutoFixer(llm=mock_llm)

        # Mock verification to fail once then succeed
        with patch.object(fixer, "verify") as mock_verify:
            mock_verify.side_effect = [
                VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(InconsistencyType.TIMELINE_ERROR, 2, "Timeline issue"),
                    ],
                    chapter_number=5,
                ),
                VerificationResult(
                    is_consistent=True,
                    inconsistencies=[],
                    chapter_number=5,
                ),
            ]

            mock_llm.generate_with_system.return_value = LLMResponse(
                content="Fixed content without timeline issues",
                tokens_used=100,
                model="test",
            )

            result = await fixer.fix_and_regenerate(
                content="Original content with issues",
                verification_result=VerificationResult(
                    is_consistent=False,
                    inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 2, "Issue")],
                    chapter_number=5,
                ),
            )

            assert result.success is True
            assert result.iteration_count == 2  # 2 iterations total
            assert result.is_fully_fixed is True
            assert result.manual_review_required is False
            assert result.final_content == "Fixed content without timeline issues"

    @pytest.mark.asyncio
    async def test_fix_dead_character_issue(self, mock_llm):
        """Test fixing dead character appearance."""
        fixer = AutoFixer(llm=mock_llm)

        mock_llm.generate_with_system.return_value = LLMResponse(
            content="Content where Villain is only mentioned, not speaking",
            tokens_used=100,
            model="test",
        )

        with patch.object(fixer, "verify") as mock_verify:
            mock_verify.side_effect = [
                VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(
                            InconsistencyType.DEAD_CHARACTER_APPEARANCE,
                            5,
                            "Dead character speaking",
                            entities=["Villain"],
                        ),
                    ],
                    chapter_number=5,
                ),
                VerificationResult(
                    is_consistent=True,
                    inconsistencies=[],
                    chapter_number=5,
                ),
            ]

            result = await fixer.fix_and_regenerate(
                content="Villain says: I am back!",
                verification_result=VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(
                            InconsistencyType.DEAD_CHARACTER_APPEARANCE,
                            5,
                            "Dead character speaking",
                            entities=["Villain"],
                        ),
                    ],
                    chapter_number=5,
                ),
            )

            assert result.success is True
            assert (
                "Villain" not in result.final_content or "mentioned" in result.final_content.lower()
            )

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, mock_llm):
        """Test max iterations enforced."""
        fixer = AutoFixer(llm=mock_llm)

        mock_llm.generate_with_system.return_value = LLMResponse(
            content="Still has issues",
            tokens_used=100,
            model="test",
        )

        with patch.object(fixer, "verify") as mock_verify:
            # Always return inconsistent (never fixed)
            mock_verify.return_value = VerificationResult(
                is_consistent=False,
                inconsistencies=[
                    Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Persistent issue"),
                ],
                chapter_number=5,
            )

            result = await fixer.fix_and_regenerate(
                content="Content with persistent issues",
                verification_result=VerificationResult(
                    is_consistent=False,
                    inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue")],
                    chapter_number=5,
                ),
                max_iterations=3,
            )

            assert result.success is False
            assert result.iteration_count == 3
            assert result.manual_review_required is True
            assert len(result.issues_remaining) == 1

    @pytest.mark.asyncio
    async def test_manual_review_flag(self, mock_llm):
        """Test manual review flag set when max iterations reached."""
        fixer = AutoFixer(llm=mock_llm)

        mock_llm.generate_with_system.return_value = LLMResponse(
            content="Content",
            tokens_used=100,
            model="test",
        )

        with patch.object(fixer, "verify") as mock_verify:
            mock_verify.return_value = VerificationResult(
                is_consistent=False,
                inconsistencies=[
                    Inconsistency(InconsistencyType.WORLD_RULE_VIOLATION, 5, "Serious issue"),
                ],
                chapter_number=5,
            )

            result = await fixer.fix_and_regenerate(
                content="Content",
                verification_result=VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(InconsistencyType.WORLD_RULE_VIOLATION, 5, "Issue")
                    ],
                    chapter_number=5,
                ),
                max_iterations=2,
            )

            assert result.manual_review_required is True
            assert result.success is False
            assert result.remaining_critical_count == 1

    @pytest.mark.asyncio
    async def test_no_llm_available(self):
        """Test behavior when no LLM is available."""
        fixer = AutoFixer(llm=None)

        result = await fixer.fix_and_regenerate(
            content="Content",
            verification_result=VerificationResult(
                is_consistent=False,
                inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue")],
                chapter_number=5,
            ),
        )

        assert result.success is False
        assert result.iteration_count == 0
        assert result.manual_review_required is True
        assert result.metadata.get("reason") == "no_llm_available"

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, mock_llm):
        """Test handling of LLM errors."""
        fixer = AutoFixer(llm=mock_llm)

        mock_llm.generate_with_system.side_effect = Exception("LLM API error")

        result = await fixer.fix_and_regenerate(
            content="Content",
            verification_result=VerificationResult(
                is_consistent=False,
                inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue")],
                chapter_number=5,
            ),
        )

        assert result.success is False
        assert result.manual_review_required is True
        assert "error" in result.metadata
        assert "LLM API error" in result.metadata["error"]

    @pytest.mark.asyncio
    async def test_iteration_history_tracking(self, mock_llm):
        """Test that iteration history is tracked."""
        fixer = AutoFixer(llm=mock_llm)

        mock_llm.generate_with_system.return_value = LLMResponse(
            content="Fixed content",
            tokens_used=100,
            model="test",
        )

        with patch.object(fixer, "verify") as mock_verify:
            mock_verify.side_effect = [
                VerificationResult(
                    is_consistent=False,
                    inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue 1")],
                    chapter_number=5,
                ),
                VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(InconsistencyType.LOCATION_MISMATCH, 3, "Issue 2")
                    ],
                    chapter_number=5,
                ),
                VerificationResult(
                    is_consistent=True,
                    inconsistencies=[],
                    chapter_number=5,
                ),
            ]

            result = await fixer.fix_and_regenerate(
                content="Original",
                verification_result=VerificationResult(
                    is_consistent=False,
                    inconsistencies=[Inconsistency(InconsistencyType.TIMELINE_ERROR, 3, "Issue")],
                    chapter_number=5,
                ),
                max_iterations=5,
            )

            assert len(result.all_iterations) == 3  # 3 iterations before success
            for i, iteration in enumerate(result.all_iterations):
                assert iteration["iteration"] == i + 1


class TestIntegrationWithSummaryManager:
    """Test integration with SummaryManager."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.mark.asyncio
    async def test_process_chapter_with_autofix(self, tmp_path, mock_llm):
        """Test end-to-end with SummaryManager."""
        from src.novel_agent.novel.summary_manager import SummaryManager

        # Setup mock responses
        mock_llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "Chapter summary", "key_events": ["Event 1"], "sentiment": "neutral"}',
            tokens_used=100,
            model="test",
        )

        manager = SummaryManager(tmp_path, "test", mock_llm, use_auto_fix=True)

        # Setup global state with character
        from src.novel_agent.novel.continuity import CharacterState, PlotThread

        manager.update_global_characters(
            {
                "Villain": CharacterState(
                    name="Villain",
                    status="dead",
                    location="Grave",
                    physical_form="none",
                )
            }
        )
        manager.update_global_plot_threads(
            [
                PlotThread(name="Main Plot", status="active"),
            ]
        )

        # Create content with dead character issue
        content = "Villain说：我回来了！"

        summary, verification, auto_fix = await manager.process_chapter_with_autofix(
            chapter_number=5,
            title="Test Chapter",
            content=content,
        )

        # Assertions
        assert summary is not None
        assert verification is not None
        assert summary.chapter_number == 5
        assert summary.title == "Test Chapter"

    @pytest.mark.asyncio
    async def test_process_chapter_no_issues(self, tmp_path, mock_llm):
        """Test processing chapter with no issues."""
        from src.novel_agent.novel.summary_manager import SummaryManager

        mock_llm.generate_with_system.return_value = LLMResponse(
            content='{"summary": "Good chapter", "key_events": [], "sentiment": "positive"}',
            tokens_used=100,
            model="test",
        )

        manager = SummaryManager(tmp_path, "test", mock_llm, use_auto_fix=True)

        # Setup with alive character
        from src.novel_agent.novel.continuity import CharacterState

        manager.update_global_characters(
            {
                "Hero": CharacterState(
                    name="Hero",
                    status="alive",
                    location="Castle",
                    physical_form="human",
                )
            }
        )

        # Content with no issues
        content = "Hero walked through the Castle halls."

        summary, verification, auto_fix = await manager.process_chapter_with_autofix(
            chapter_number=1,
            title="Chapter 1",
            content=content,
        )

        assert summary is not None
        assert verification is not None
        # When there are no issues, auto_fix should be None
        assert auto_fix is None
    @pytest.mark.asyncio
    async def test_integration_with_fixed_content(self, tmp_path, mock_llm):
        """Test that fixed content is used for summary generation."""
        from src.novel_agent.novel.summary_manager import SummaryManager

        # The summary should be generated from fixed content, not original
        mock_llm.generate_with_system.side_effect = [
            # First call: fix the content
            LLMResponse(
                content="Fixed content without dead character speaking",
                tokens_used=100,
                model="test",
            ),
            # Second call: summarize the fixed content
            LLMResponse(
                content='{"summary": "Fixed chapter summary", "key_events": ["Fix applied"], "sentiment": "neutral"}',
                tokens_used=100,
                model="test",
            ),
        ]

        manager = SummaryManager(tmp_path, "test", mock_llm, use_auto_fix=True)

        from src.novel_agent.novel.continuity import CharacterState

        manager.update_global_characters(
            {
                "Villain": CharacterState(
                    name="Villain",
                    status="dead",
                    location="Grave",
                    physical_form="none",
                )
            }
        )

        content = "Villain says: I am alive!"

        from unittest.mock import patch
        with patch.object(manager, 'auto_fixer') as mock_auto_fixer:
            # Setup mock auto_fixer methods
            mock_auto_fixer.verify.side_effect = [
                # First verification: has issues
                VerificationResult(
                    is_consistent=False,
                    inconsistencies=[
                        Inconsistency(
                            InconsistencyType.DEAD_CHARACTER_APPEARANCE,
                            5,
                            "Dead character speaking",
                            entities=["Villain"],
                        ),
                    ],
                    chapter_number=5,
                ),
                # Second verification: fixed
                VerificationResult(
                    is_consistent=True,
                    inconsistencies=[],
                    chapter_number=5,
                ),
            ]
            # Make fix_and_regenerate an async mock
            async def mock_fix_and_regenerate(*args, **kwargs):
                return AutoFixResult(
                    success=True,
                    iteration_count=1,
                    final_content="Fixed content without dead character speaking",
                    issues_remaining=[],
                )
            mock_auto_fixer.fix_and_regenerate = mock_fix_and_regenerate

            summary, verification, auto_fix = await manager.process_chapter_with_autofix(
                chapter_number=5,
                title="Test Chapter",
                content=content,
            )

            assert summary is not None
            assert auto_fix is not None
            assert auto_fix.success is True
            assert verification.is_consistent is True  # Should be re-verified as consistent
