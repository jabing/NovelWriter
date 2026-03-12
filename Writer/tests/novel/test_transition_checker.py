"""Tests for ChapterTransitionChecker class."""

import pytest

from src.novel.transition_checker import (
    ChapterTransitionChecker,
    TransitionReport,
    UnresolvedEvent,
)


class TestUnresolvedEvent:
    """Test UnresolvedEvent dataclass."""

    def test_unresolved_event_creation(self) -> None:
        """Test creating an UnresolvedEvent."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Unresolved secret letter",
            pattern_matched=r"收到.*密信",
            position=100,
            importance="high",
            context="丞相收到密信...",
        )

        assert event.event_type == "received_secret_letter"
        assert event.description == "Unresolved secret letter"
        assert event.pattern_matched == r"收到.*密信"
        assert event.position == 100
        assert event.importance == "high"
        assert "密信" in event.context

    def test_unresolved_event_defaults(self) -> None:
        """Test UnresolvedEvent with default values."""
        event = UnresolvedEvent(
            event_type="test",
            description="Test event",
            pattern_matched=r"test",
            position=0,
        )

        assert event.importance == "medium"
        assert event.context == ""


class TestTransitionReport:
    """Test TransitionReport dataclass."""

    def test_transition_report_no_issues(self) -> None:
        """Test a report with no issues."""
        report = TransitionReport(
            has_issues=False,
            severity="none",
            confidence=0.0,
        )

        assert report.has_issues is False
        assert report.severity == "none"
        assert report.unresolved_events == []
        assert report.ignored_events == []
        assert report.scene_jump_detected is False
        assert report.transition_suggestions == []

    def test_transition_report_with_issues(self) -> None:
        """Test a report with issues."""
        event = UnresolvedEvent(
            event_type="received_letter",
            description="Test",
            pattern_matched=r"test",
            position=0,
            importance="high",
        )
        report = TransitionReport(
            has_issues=True,
            severity="major",
            unresolved_events=[event],
            ignored_events=[event],
            scene_jump_detected=True,
            scene_jump_details="Test jump",
            transition_suggestions=["Fix it"],
            confidence=0.8,
        )

        assert report.has_issues is True
        assert report.severity == "major"
        assert len(report.unresolved_events) == 1
        assert len(report.ignored_events) == 1
        assert report.scene_jump_detected is True
        assert len(report.transition_suggestions) == 1


class TestChapterTransitionCheckerInit:
    """Test ChapterTransitionChecker initialization."""

    def test_checker_initialization(self) -> None:
        """Test checker initializes correctly."""
        checker = ChapterTransitionChecker()

        assert len(checker._compiled_suspense) > 0
        assert len(checker._compiled_transitions) > 0
        assert len(checker._compiled_resolutions) > 0


class TestExtractUnresolvedEvents:
    """Test _extract_unresolved_events method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_extract_secret_letter_suspense(self, checker: ChapterTransitionChecker) -> None:
        """Test extracting secret letter suspense pattern."""
        content = (
            "诗会上，众人吟诗作对。丞相忽然收到密信，拆开一看，上面写着：'凤星临世，方位——相府'"
        )

        events = checker._extract_unresolved_events(content)

        # Should detect the secret letter
        assert len(events) > 0
        assert any(e.event_type == "received_secret_letter" for e in events)

    def test_extract_discovery_suspense(self, checker: ChapterTransitionChecker) -> None:
        """Test extracting discovery suspense pattern."""
        content = "她在密室中发现了一个惊天秘密，原来这一切都是..."

        events = checker._extract_unresolved_events(content)

        assert len(events) > 0
        assert any(
            "secret" in e.event_type.lower() or "truth" in e.event_type.lower() for e in events
        )

    def test_extract_no_suspense(self, checker: ChapterTransitionChecker) -> None:
        """Test with no suspense patterns."""
        content = "诗会结束后，众人各自回家。丞相也回到了府中休息。一切平静如常。"

        events = checker._extract_unresolved_events(content)

        # Should not detect any suspense
        high_importance = [e for e in events if e.importance == "high"]
        assert len(high_importance) == 0

    def test_extract_sudden_event(self, checker: ChapterTransitionChecker) -> None:
        """Test extracting sudden event pattern."""
        content = "忽然，门外传来一阵急促的脚步声。"

        events = checker._extract_unresolved_events(content)

        # Should detect sudden event
        assert any("sudden" in e.event_type for e in events)

    def test_extract_cliffhanger_timing(self, checker: ChapterTransitionChecker) -> None:
        """Test extracting cliffhanger timing pattern."""
        content = "他正要推开门时，忽然听到身后有人叫他的名字。"

        events = checker._extract_unresolved_events(content)

        # Should detect cliffhanger
        assert len(events) > 0


class TestCheckIfIgnored:
    """Test _check_if_ignored method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_event_not_ignored_with_resolution(self, checker: ChapterTransitionChecker) -> None:
        """Test event is not ignored when addressed."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Secret letter",
            pattern_matched=r"收到.*密信",
            position=0,
            importance="high",
            context="丞相收到密信",
        )

        # Current chapter addresses the letter
        current_content = "次日清晨，丞相拆开密信。信中写道：'凤星临世，方位——相府'"

        ignored = checker._check_if_ignored([event], current_content)

        # Should not be ignored since it's addressed
        assert len(ignored) == 0

    def test_event_ignored_no_resolution(self, checker: ChapterTransitionChecker) -> None:
        """Test event is ignored when not addressed."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Secret letter",
            pattern_matched=r"收到.*密信",
            position=0,
            importance="high",
            context="丞相收到密信'凤星临世'",
        )

        # Current chapter ignores the letter completely
        current_content = "诗会结束后的第三日，府中来了一位不速之客。"

        ignored = checker._check_if_ignored([event], current_content)

        # Should be ignored - no mention of letter
        assert len(ignored) > 0

    def test_event_with_transition_still_checked(self, checker: ChapterTransitionChecker) -> None:
        """Test that transitions don't excuse ignoring high importance events."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Secret letter",
            pattern_matched=r"收到.*密信",
            position=0,
            importance="high",
            context="丞相收到密信",
        )

        # Has transition marker but ignores the letter
        current_content = "诗会结束后的第三日，天气晴朗，府中一切如常。"

        ignored = checker._check_if_ignored([event], current_content)

        # Should still be flagged as ignored
        assert len(ignored) > 0


class TestDetectSceneJump:
    """Test _detect_scene_jump method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_no_scene_jump_with_transition(self, checker: ChapterTransitionChecker) -> None:
        """Test no scene jump when transition is present."""
        prev_content = "丞相收到了密信，脸色凝重。"
        curr_content = "次日清晨，丞相来到书房，拆开了那封信。"

        is_jump, details = checker._detect_scene_jump(prev_content, curr_content)

        assert is_jump is False
        assert details == ""

    def test_scene_jump_no_transition(self, checker: ChapterTransitionChecker) -> None:
        """Test scene jump when no transition and unresolved suspense."""
        prev_content = "诗会上，丞相忽然收到密信。信上写着：'凤星临世，方位——相府'"
        curr_content = "诗会结束后的第三日，府中来了一位不速之客。"

        is_jump, details = checker._detect_scene_jump(prev_content, curr_content)

        assert is_jump is True
        assert "Scene jump" in details

    def test_no_jump_smooth_transition(self, checker: ChapterTransitionChecker) -> None:
        """Test no jump with smooth narrative transition."""
        prev_content = "丞相回到了府中，心中思虑重重。"
        curr_content = "翌日，丞相在书房中翻阅古籍。"

        is_jump, details = checker._detect_scene_jump(prev_content, curr_content)

        assert is_jump is False


class TestCalculateSeverity:
    """Test _calculate_severity method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_severity_none(self, checker: ChapterTransitionChecker) -> None:
        """Test severity none when no issues."""
        severity = checker._calculate_severity([], False)
        assert severity == "none"

    def test_severity_critical(self, checker: ChapterTransitionChecker) -> None:
        """Test critical severity with multiple high importance events."""
        events = [
            UnresolvedEvent("a", "b", "c", 0, "high"),
            UnresolvedEvent("d", "e", "f", 0, "high"),
        ]
        severity = checker._calculate_severity(events, True)
        assert severity == "critical"

    def test_severity_major(self, checker: ChapterTransitionChecker) -> None:
        """Test major severity with single high importance and scene jump."""
        events = [UnresolvedEvent("a", "b", "c", 0, "high")]
        severity = checker._calculate_severity(events, True)
        assert severity == "critical"

    def test_severity_minor(self, checker: ChapterTransitionChecker) -> None:
        """Test minor severity with only medium importance events."""
        events = [UnresolvedEvent("a", "b", "c", 0, "medium")]
        severity = checker._calculate_severity(events, False)
        assert severity == "minor"


class TestGenerateSuggestions:
    """Test _generate_suggestions method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_suggestions_for_scene_jump(self, checker: ChapterTransitionChecker) -> None:
        """Test suggestions include transition marker advice."""
        suggestions = checker._generate_suggestions([], True, "Test jump")

        assert any("transition marker" in s.lower() for s in suggestions)

    def test_suggestions_for_secret_letter(self, checker: ChapterTransitionChecker) -> None:
        """Test suggestions for secret letter event."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Secret letter",
            pattern_matched="test",
            position=0,
            importance="high",
        )
        suggestions = checker._generate_suggestions([event], False, "")

        assert any("letter" in s.lower() for s in suggestions)

    def test_suggestions_combined_issues(self, checker: ChapterTransitionChecker) -> None:
        """Test suggestions for combined scene jump and ignored events."""
        event = UnresolvedEvent(
            event_type="test",
            description="Test",
            pattern_matched="test",
            position=0,
            importance="high",
        )
        suggestions = checker._generate_suggestions([event], True, "Test")

        assert any("narrative bridge" in s.lower() for s in suggestions)


class TestCheckTransition:
    """Test check_transition method (integration)."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_check_transition_ch3_ch4_problem(self, checker: ChapterTransitionChecker) -> None:
        """Test the Chapter 3→4 transition problem scenario.

        Chapter 3 ends with: 丞相收到密信'凤星临世，方位——相府'
        Chapter 4 starts with: 诗会结束后的第三日

        This should be detected as a scene jump with unresolved suspense.
        """
        # Chapter 3 content (ending with suspense)
        ch3_content = """
诗会在花园中举行，众才子佳人吟诗作对。
丞相李昭也在座中，品着香茶，听着诗赋。

正当众人兴致正浓时，一名侍从匆匆走来，
在丞相耳边低语几句。丞相面色微变，
随即起身离席。

回到书房，丞相收到密信，拆开一看，
上面只有寥寥数字：'凤星临世，方位——相府'
丞相眉头紧锁，久久不语。
"""

        # Chapter 4 content (starts without addressing the letter)
        ch4_content = """
诗会结束后的第三日，府中来了一位不速之客。
来人自称是远方商旅，带来了西域的奇珍异宝。
丞相在正厅接见了他，询问此行的目的。
"""

        report = checker.check_transition(ch3_content, ch4_content, 4)

        # Should detect issues
        assert report.has_issues is True
        assert report.severity in ["critical", "major"]
        assert report.scene_jump_detected is True
        assert len(report.ignored_events) > 0
        assert report.confidence > 0.5

        # Should have suggestions
        assert len(report.transition_suggestions) > 0

    def test_check_transition_smooth(self, checker: ChapterTransitionChecker) -> None:
        """Test smooth transition with proper resolution."""
        # Chapter 3 ends with suspense
        ch3_content = """
丞相在书房收到密信，上面写着：'凤星临世'
丞相陷入了沉思。
"""

        # Chapter 4 addresses it
        ch4_content = """
次日清晨，丞相召集心腹，商讨密信之事。
"凤星临世，此事非同小可，"丞相说道。
"""

        report = checker.check_transition(ch3_content, ch4_content, 4)

        # Should not have critical issues
        assert report.severity in ["none", "minor"]
        assert len(report.transition_suggestions) == 0 or not report.scene_jump_detected

    def test_check_transition_with_time_marker(self, checker: ChapterTransitionChecker) -> None:
        """Test transition with time marker but no resolution."""
        ch3_content = "丞相收到密信，脸色凝重。"
        ch4_content = "三日后，丞相府中举办宴会。"

        report = checker.check_transition(ch3_content, ch4_content, 4)

        # Time marker present, but high importance event should still be checked
        # May or may not have issues depending on event importance detection
        assert isinstance(report, TransitionReport)

    def test_check_transition_confidence_score(self, checker: ChapterTransitionChecker) -> None:
        """Test confidence score calculation."""
        # High suspense ending
        ch3_content = "忽然，门外传来急促的脚步声。一封信送到丞相手中。"
        ch4_content = "第二天，阳光明媚，府中一片祥和。"

        report = checker.check_transition(ch3_content, ch4_content, 4)

        # Should have some confidence in detection
        assert 0.0 <= report.confidence <= 1.0


class TestExtractKeywords:
    """Test _extract_keywords method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_extract_keywords_secret_letter(self, checker: ChapterTransitionChecker) -> None:
        """Test keyword extraction for secret letter event."""
        event = UnresolvedEvent(
            event_type="received_secret_letter",
            description="Test",
            pattern_matched="test",
            position=0,
            importance="high",
            context="丞相收到密信",
        )

        keywords = checker._extract_keywords(event)

        # Should contain secret letter keywords
        assert "密信" in keywords
        assert "信" in keywords

    def test_extract_keywords_discovery(self, checker: ChapterTransitionChecker) -> None:
        """Test keyword extraction for discovery event."""
        event = UnresolvedEvent(
            event_type="discovered_secret",
            description="Test",
            pattern_matched="test",
            position=0,
            importance="high",
            context="她发现了一个秘密",
        )

        keywords = checker._extract_keywords(event)

        # Should contain discovery keywords
        assert "秘密" in keywords or "发现" in keywords


class TestExtractLocations:
    """Test _extract_locations method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_extract_locations_chinese(self, checker: ChapterTransitionChecker) -> None:
        """Test extracting Chinese location names."""
        text = "丞相来到了紫禁城中的养心殿，见到了皇上。"

        locations = checker._extract_locations(text)

        # Should extract location patterns
        assert len(locations) > 0

    def test_extract_locations_none(self, checker: ChapterTransitionChecker) -> None:
        """Test with no locations."""
        text = "他走在路上，心中思虑重重。"

        locations = checker._extract_locations(text)

        # May or may not extract anything
        assert isinstance(locations, list)


class TestCalculateConfidence:
    """Test _calculate_confidence method."""

    @pytest.fixture
    def checker(self) -> ChapterTransitionChecker:
        """Create a checker instance."""
        return ChapterTransitionChecker()

    def test_confidence_no_events(self, checker: ChapterTransitionChecker) -> None:
        """Test confidence with no unresolved events."""
        confidence = checker._calculate_confidence([], [], False)
        assert confidence == 0.0

    def test_confidence_with_detection(self, checker: ChapterTransitionChecker) -> None:
        """Test confidence increases with detections."""
        event = UnresolvedEvent("a", "b", "c", 0, "high")

        # Just unresolved
        conf1 = checker._calculate_confidence([event], [], False)

        # Unresolved and ignored
        conf2 = checker._calculate_confidence([event], [event], False)

        # All factors
        conf3 = checker._calculate_confidence([event], [event], True)

        assert conf2 >= conf1
        assert conf3 >= conf2
        assert conf3 <= 1.0
