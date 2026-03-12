"""Chapter transition checker for detecting narrative discontinuities.

This module provides the ChapterTransitionChecker class that detects:
- Unresolved suspense at chapter endings
- Scene jumps between chapters
- Missing transition markers

The checker is designed to identify the Chapter 3→4 transition problem
where suspense (密信) is not properly addressed in the next chapter.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UnresolvedEvent:
    """Represents an unresolved suspense event at a chapter ending.

    Attributes:
        event_type: Type of unresolved event (suspense, cliffhanger, question)
        description: Description of the unresolved event
        pattern_matched: The regex pattern that matched this event
        position: Character position in the text
        importance: Importance level (high, medium, low)
        context: Surrounding context text
    """

    event_type: str
    description: str
    pattern_matched: str
    position: int
    importance: str = "medium"
    context: str = ""


@dataclass
class TransitionReport:
    """Report on chapter transition quality.

    Attributes:
        has_issues: Whether transition issues were detected
        severity: Overall severity (critical, major, minor, none)
        unresolved_events: List of unresolved events from previous chapter
        ignored_events: Events that were addressed in current chapter
        scene_jump_detected: Whether a scene jump was detected
        scene_jump_details: Details about detected scene jump
        transition_suggestions: Suggestions for fixing transition issues
        confidence: Confidence score for the detection (0.0-1.0)
    """

    has_issues: bool
    severity: str
    unresolved_events: list[UnresolvedEvent] = field(default_factory=list)
    ignored_events: list[UnresolvedEvent] = field(default_factory=list)
    scene_jump_detected: bool = False
    scene_jump_details: str = ""
    transition_suggestions: list[str] = field(default_factory=list)
    confidence: float = 0.0


class ChapterTransitionChecker:
    """Checker for detecting narrative discontinuities between chapters.

    This class performs various checks to ensure:
    - Unresolved suspense is addressed or continued
    - Scene transitions are smooth
    - No abrupt context shifts without explanation

    Example:
        >>> checker = ChapterTransitionChecker()
        >>> report = checker.check_transition(prev_content, curr_content, 4)
        >>> if report.has_issues:
        ...     print(f"Transition issues: {report.severity}")
    """

    # Patterns that indicate unresolved suspense at chapter endings
    SUSPENSE_PATTERNS = [
        # Letter/message suspense patterns (Chinese)
        (r"收到.{0,20}信.{0,50}(?!\s*(明日|次日|后来|第二天|翌日))", "received_letter", "high"),
        (r"收到.{0,20}密信", "received_secret_letter", "high"),
        (r"收到.{0,20}消息", "received_message", "medium"),
        (r"收到.{1,20}密信", "received_secret_letter", "high"),
        (r"收到.{1,20}消息", "received_message", "medium"),
        # Discovery patterns
        (r"发现.{1,30}秘密", "discovered_secret", "high"),
        (r"发现.{1,30}真相", "discovered_truth", "high"),
        (r"意外发现", "accidental_discovery", "medium"),
        # Sudden event patterns
        (r"忽然.{1,30}(?!\s*(明白|发现|意识到))", "sudden_event", "medium"),
        (r"突然.{1,30}(?!\s*(明白|发现|意识到))", "sudden_event_alt", "medium"),
        # Cliffhanger patterns
        (
            r"(站在|停在|停在|停顿)在.{1,20}(门口|门前|窗前|门口|窗边)$",
            "cliffhanger_stance",
            "medium",
        ),
        (r"正要.{1,30}时$", "cliffhanger_timing", "high"),
        (r"(忽然|突然|猛然)听到.{1,30}$", "cliffhanger_sound", "high"),
        # Question patterns
        (r"(为何|为什么|怎么会|究竟).{1,30}\?$", "unanswered_question", "medium"),
        # Mysterious arrival patterns
        (r"(来人|使者|信使).{1,30}(送来|带来|传来).{1,30}$", "mysterious_arrival", "high"),
    ]

    # Patterns that indicate scene transitions
    TRANSITION_MARKERS = [
        # Time transitions
        r"次日",
        r"翌日",
        r"第二[天日]",
        r"三[天日]后",
        r"数[天日]后",
        r"几天后",
        r"过了.{1,10}天",
        r"明日",
        r"(清晨|黄昏|傍晚|午时|深夜)",
        # Location transitions
        r"来到.{1,20}(门前|府前|门口)",
        r"到了.{1,20}",
        r"回到.{1,20}",
        r"抵达.{1,20}",
        # Narrative transitions
        r"话说",
        r"且说",
        r"再说",
        r"却说",
    ]

    # Patterns that indicate event resolution
    RESOLUTION_PATTERNS = [
        # Opening letter/message
        (r"(拆开|打开|展开).{1,20}信", "opened_letter"),
        (r"信.{1,10}(写道|写着|内容)", "letter_content"),
        (r"(读完|看完).{1,20}信", "finished_reading"),
        # Understanding context
        (r"(原来|才知|方知|终于知道)", "understanding_reached"),
        # Action taken
        (r"(立即|立刻|马上|当即).{1,30}(行动|出发|派人)", "action_taken"),
        # Response to event
        (r"(于是|因此|便|遂).{1,30}", "response_to_event"),
    ]

    def __init__(self) -> None:
        """Initialize the transition checker."""
        self._compiled_suspense: list[tuple[re.Pattern[str], str, str]] = []
        self._compiled_transitions: list[re.Pattern[str]] = []
        self._compiled_resolutions: list[tuple[re.Pattern[str], str]] = []

        # Compile patterns for performance
        for pattern, event_type, importance in self.SUSPENSE_PATTERNS:
            try:
                self._compiled_suspense.append(
                    (re.compile(pattern, re.MULTILINE), event_type, importance)
                )
            except re.error as e:
                logger.warning(f"Invalid suspense pattern '{pattern}': {e}")

        for pattern in self.TRANSITION_MARKERS:
            try:
                self._compiled_transitions.append(re.compile(pattern))
            except re.error as e:
                logger.warning(f"Invalid transition pattern '{pattern}': {e}")

        for pattern, resolution_type in self.RESOLUTION_PATTERNS:
            try:
                self._compiled_resolutions.append((re.compile(pattern), resolution_type))
            except re.error as e:
                logger.warning(f"Invalid resolution pattern '{pattern}': {e}")

    def check_transition(
        self,
        prev_chapter_content: str,
        current_chapter_content: str,
        chapter_num: int,
    ) -> TransitionReport:
        """Check transition between two chapters.

        Args:
            prev_chapter_content: Content of the previous chapter
            current_chapter_content: Content of the current chapter
            chapter_num: Current chapter number

        Returns:
            TransitionReport with detection results
        """
        logger.debug(f"Checking transition to chapter {chapter_num}")

        # Extract unresolved events from previous chapter ending
        unresolved = self._extract_unresolved_events(prev_chapter_content)

        # Check which unresolved events are ignored (not addressed in current chapter)
        ignored = self._check_if_ignored(unresolved, current_chapter_content)

        # Detect scene jump
        scene_jump, scene_details = self._detect_scene_jump(
            prev_chapter_content, current_chapter_content
        )

        # Calculate severity
        severity = self._calculate_severity(ignored, scene_jump)

        # Generate suggestions
        suggestions = self._generate_suggestions(ignored, scene_jump, scene_details)

        # Calculate confidence
        confidence = self._calculate_confidence(unresolved, ignored, scene_jump)

        # Determine if there are issues
        has_issues = len(ignored) > 0 or scene_jump

        return TransitionReport(
            has_issues=has_issues,
            severity=severity,
            unresolved_events=unresolved,
            ignored_events=ignored,
            scene_jump_detected=scene_jump,
            scene_jump_details=scene_details,
            transition_suggestions=suggestions,
            confidence=confidence,
        )

    def _extract_unresolved_events(self, content: str) -> list[UnresolvedEvent]:
        """Extract unresolved suspense events from chapter content.

        Focuses on the last 500 characters (chapter ending).

        Args:
            content: Chapter content to analyze

        Returns:
            List of unresolved events found
        """
        events: list[UnresolvedEvent] = []

        # Focus on last portion of chapter (typical cliffhanger location)
        ending_portion = content[-1000:] if len(content) > 1000 else content

        for pattern, event_type, importance in self._compiled_suspense:
            for match in pattern.finditer(ending_portion):
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(ending_portion), match.end() + 50)
                context = ending_portion[start:end]

                event = UnresolvedEvent(
                    event_type=event_type,
                    description=f"Unresolved {event_type.replace('_', ' ')}: {match.group()[:50]}...",
                    pattern_matched=pattern.pattern,
                    position=match.start(),
                    importance=importance,
                    context=context,
                )
                events.append(event)

        # Sort by importance (high first) and position (later first)
        importance_order = {"high": 0, "medium": 1, "low": 2}
        events.sort(key=lambda e: (importance_order.get(e.importance, 2), -e.position))

        return events

    def _check_if_ignored(
        self,
        events: list[UnresolvedEvent],
        current_content: str,
    ) -> list[UnresolvedEvent]:
        """Check which unresolved events are ignored in current chapter.

        An event is considered ignored if:
        1. It's a high-importance suspense event
        2. There's no resolution pattern match in the first 1000 chars
        3. The event type isn't mentioned or addressed

        Args:
            events: List of unresolved events from previous chapter
            current_content: Content of current chapter

        Returns:
            List of events that appear to be ignored
        """
        ignored: list[UnresolvedEvent] = []

        # Check beginning of chapter for resolution
        beginning_portion = (
            current_content[:1500] if len(current_content) > 1500 else current_content
        )

        # Check for resolution patterns
        has_resolution = False
        for pattern, _resolution_type in self._compiled_resolutions:
            if pattern.search(beginning_portion):
                has_resolution = True
                break

        # Check for transition markers
        has_transition = any(
            pattern.search(beginning_portion) for pattern in self._compiled_transitions
        )

        for event in events:
            # High importance events require explicit resolution
            if event.importance == "high":
                # Check if event is mentioned in current chapter beginning
                event_keywords = self._extract_keywords(event)

                # Look for keywords in beginning
                found_keywords = sum(1 for kw in event_keywords if kw in beginning_portion)

                # If no keywords found and no resolution/transition, it's ignored
                if found_keywords == 0 and not has_resolution:
                    # But if there's a clear time transition, allow some slack
                    if not has_transition:
                        ignored.append(event)
                    elif found_keywords == 0:
                        # Even with transition, high importance events should be mentioned
                        ignored.append(event)

            # Medium importance - check if mentioned
            elif event.importance == "medium":
                event_keywords = self._extract_keywords(event)
                found_keywords = sum(1 for kw in event_keywords if kw in beginning_portion)
                if found_keywords == 0 and not has_resolution:
                    ignored.append(event)

        return ignored

    def _extract_keywords(self, event: UnresolvedEvent) -> list[str]:
        """Extract important keywords from an event.

        Args:
            event: The unresolved event

        Returns:
            List of keywords to search for
        """
        keywords: list[str] = []

        # Event type specific keywords
        type_keywords = {
            "received_letter": ["信", "信件", "信使"],
            "received_secret_letter": ["密信", "秘密", "信"],
            "received_message": ["消息", "传讯"],
            "discovered_secret": ["秘密", "发现"],
            "discovered_truth": ["真相", "发现"],
            "sudden_event": ["忽然", "突然"],
            "cliffhanger_timing": ["正要", "即将"],
            "mysterious_arrival": ["来人", "使者", "信使"],
        }

        keywords.extend(type_keywords.get(event.event_type, []))

        # Add words from context (simplified - just look for Chinese characters)
        context_words = re.findall(r"[\u4e00-\u9fff]{2,4}", event.context)
        keywords.extend(context_words[:5])  # Limit to prevent noise

        return list(set(keywords))  # Deduplicate

    def _detect_scene_jump(
        self,
        prev_content: str,
        current_content: str,
    ) -> tuple[bool, str]:
        """Detect sudden scene jump between chapters.

        Args:
            prev_content: Previous chapter content
            current_content: Current chapter content

        Returns:
            Tuple of (is_scene_jump, details)
        """
        # Get endings and beginnings
        prev_ending = prev_content[-500:] if len(prev_content) > 500 else prev_content
        curr_beginning = current_content[:500] if len(current_content) > 500 else current_content

        # Check for transition marker in current chapter beginning
        has_transition = any(
            pattern.search(curr_beginning) for pattern in self._compiled_transitions
        )

        # Check for unresolved events in previous ending
        unresolved = self._extract_unresolved_events(prev_content)
        high_importance_unresolved = [e for e in unresolved if e.importance == "high"]

        if high_importance_unresolved and not has_transition:
            # Extract key context from previous ending
            prev_context = prev_ending[-200:]

            details = (
                f"Scene jump detected: Previous chapter ends with unresolved "
                f"'{high_importance_unresolved[0].event_type}' "
                f"but current chapter starts without transition marker. "
                f"Previous ending context: '{prev_context[:100]}...'"
            )
            return True, details

        # Check for sudden location/time change without explanation
        if not has_transition:
            # Look for location indicators
            prev_locations = self._extract_locations(prev_ending)
            curr_locations = self._extract_locations(curr_beginning)

            if prev_locations and curr_locations:
                # Check if locations are completely different
                if not set(prev_locations).intersection(set(curr_locations)):
                    details = (
                        f"Potential scene jump: Location changed from "
                        f"{prev_locations} to {curr_locations} without transition"
                    )
                    return True, details

        return False, ""

    def _extract_locations(self, text: str) -> list[str]:
        """Extract location names from text.

        Uses common Chinese location patterns.

        Args:
            text: Text to extract locations from

        Returns:
            List of potential location names
        """
        locations: list[str] = []

        # Common location patterns
        patterns = [
            r"([^\s]{2,6})(府|宫|殿|阁|楼|院|堂|房|门)",
            r"在([^\s]{2,6})(中|内|里)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    location = "".join(match)
                else:
                    location = match
                if len(location) >= 2:
                    locations.append(location)

        return list(set(locations))[:5]  # Limit and deduplicate

    def _calculate_severity(
        self,
        ignored_events: list[UnresolvedEvent],
        scene_jump: bool,
    ) -> str:
        """Calculate overall severity of transition issues.

        Args:
            ignored_events: List of ignored events
            scene_jump: Whether a scene jump was detected

        Returns:
            Severity level (critical, major, minor, none)
        """
        if not ignored_events and not scene_jump:
            return "none"

        # Count high importance events
        high_importance = sum(1 for e in ignored_events if e.importance == "high")

        if high_importance >= 2 or (high_importance >= 1 and scene_jump):
            return "critical"
        elif high_importance == 1 or scene_jump:
            return "major"
        elif ignored_events:
            return "minor"
        else:
            return "none"

    def _generate_suggestions(
        self,
        ignored_events: list[UnresolvedEvent],
        scene_jump: bool,
        scene_details: str,
    ) -> list[str]:
        """Generate suggestions for fixing transition issues.

        Args:
            ignored_events: List of ignored events
            scene_jump: Whether scene jump detected
            scene_details: Details about scene jump

        Returns:
            List of suggestion strings
        """
        suggestions: list[str] = []

        if scene_jump:
            suggestions.append(
                "Consider adding a transition marker at the beginning of the chapter "
                "(e.g., '次日', '翌日', '第二日') to indicate time passage."
            )

        for event in ignored_events[:3]:  # Limit to top 3
            if event.event_type == "received_secret_letter":
                suggestions.append(
                    "Address the secret letter in the next chapter: "
                    "either open it, mention its contents, or show the character's reaction."
                )
            elif event.event_type == "discovered_secret":
                suggestions.append(
                    "Follow up on the discovered secret: show the character's "
                    "reaction or the implications of the discovery."
                )
            elif event.event_type == "sudden_event":
                suggestions.append(
                    "Continue or resolve the sudden event from the previous chapter."
                )
            elif "cliffhanger" in event.event_type:
                suggestions.append(
                    "Resolve or continue the cliffhanger situation from the previous chapter."
                )
            else:
                suggestions.append(
                    f"Consider addressing the unresolved '{event.event_type}' "
                    f"event from the previous chapter ending."
                )

        if scene_jump and ignored_events:
            suggestions.append(
                "The combination of scene jump and unresolved events suggests "
                "a missing narrative bridge between chapters."
            )

        return suggestions

    def _calculate_confidence(
        self,
        unresolved: list[UnresolvedEvent],
        ignored: list[UnresolvedEvent],
        scene_jump: bool,
    ) -> float:
        """Calculate confidence score for the detection.

        Higher confidence when:
        - More unresolved events detected
        - More events confirmed as ignored
        - Scene jump is detected

        Args:
            unresolved: All unresolved events found
            ignored: Events confirmed as ignored
            scene_jump: Whether scene jump detected

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not unresolved:
            return 0.0

        # Base confidence from unresolved events
        base_confidence = min(0.3, len(unresolved) * 0.1)

        # Increase confidence if events are confirmed ignored
        ignore_confidence = min(0.4, len(ignored) * 0.2)

        # Increase confidence if scene jump detected
        jump_confidence = 0.3 if scene_jump else 0.0

        total = base_confidence + ignore_confidence + jump_confidence

        return min(1.0, total)
