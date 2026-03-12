"""Timeline validator for temporal consistency in novels.

This module provides the TimelineValidator class for validating temporal
consistency in novel content by checking event ordering, detecting time conflicts,
validating intervals, and generating timeline reports.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.db.postgres_client import PostgresClient
from src.db.postgres_models import (
    CharacterProfile,
    EventType,
)
from src.db.postgres_models import (
    TimelineEvent as DBTimelineEvent,
)

logger = logging.getLogger(__name__)

__all__ = [
    "TimeConflict",
    "TimeConflictType",
    "OrderViolation",
    "IntervalWarning",
    "TimelineReport",
    "TimelineValidator",
    "TimelineEventData",
    "Severity",
]


# =============================================================================
# Severity Levels
# =============================================================================


class Severity(str, Enum):
    """Severity level for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# =============================================================================
# Conflict Types
# =============================================================================


class TimeConflictType(str, Enum):
    """Types of time conflicts that can be detected."""

    DEAD_CHARACTER_ACTION = "dead_character_action"
    """Character performs action after death."""

    MISSING_CHARACTER_ACTION = "missing_character_action"
    """Character acts before introduction/birth."""

    BORN_AFTER_DEATH = "born_after_death"
    """Character born after they died (logical impossibility)."""

    MARRIED_BEFORE_MEETING = "married_before_meeting"
    """Characters married before they met."""

    IMPOSSIBLE_SEQUENCE = "impossible_sequence"
    """Events in logically impossible order (e.g., child before parent)."""


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class TimelineEventData:
    """Represents a timeline event for validation purposes.

    This is a lightweight wrapper around the database TimelineEvent model
    for easier testing and validation.
    """

    event_id: str
    chapter: int
    event_type: str
    description: str
    character_id: int | None = None
    character_name: str | None = None
    importance: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_id": self.event_id,
            "character_id": self.character_id,
            "character_name": self.character_name,
            "chapter": self.chapter,
            "event_type": self.event_type,
            "description": self.description,
            "importance": self.importance,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_db_event(
        cls, db_event: DBTimelineEvent, character_name: str | None = None
    ) -> "TimelineEventData":
        """Create from database TimelineEvent model."""
        return cls(
            event_id=str(db_event.id),
            character_id=db_event.character_id,
            character_name=character_name,
            chapter=db_event.chapter,
            event_type=db_event.event_type,
            description=db_event.description,
            importance=db_event.importance,
            metadata=json.loads(db_event.meta_data) if db_event.meta_data else {},
            created_at=db_event.created_at or datetime.now(),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineEventData":
        """Create from dictionary."""
        created_at_raw = data.get("created_at")
        if isinstance(created_at_raw, str):
            created_at = datetime.fromisoformat(created_at_raw)
        else:
            created_at = datetime.now()

        return cls(
            event_id=data["event_id"],
            character_id=data.get("character_id"),
            character_name=data.get("character_name"),
            chapter=data["chapter"],
            event_type=data["event_type"],
            description=data["description"],
            importance=data.get("importance", "medium"),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


@dataclass
class TimeConflict:
    """Represents a detected time conflict."""

    conflict_type: str
    character_name: str
    chapter: int
    event_description: str
    reason: str
    severity: Severity
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_type": self.conflict_type,
            "character_name": self.character_name,
            "chapter": self.chapter,
            "event_description": self.event_description,
            "reason": self.reason,
            "severity": self.severity.value,
            "evidence": self.evidence,
        }


@dataclass
class OrderViolation:
    """Represents an ordering violation in events."""

    earlier_event: str
    later_event: str
    earlier_chapter: int
    later_chapter: int
    reason: str
    severity: Severity

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "earlier_event": self.earlier_event,
            "later_event": self.later_event,
            "earlier_chapter": self.earlier_chapter,
            "later_chapter": self.later_chapter,
            "reason": self.reason,
            "severity": self.severity.value,
        }


@dataclass
class IntervalWarning:
    """Represents a warning about event intervals."""

    warning_type: str
    chapter_start: int
    chapter_end: int
    event_count: int
    description: str
    severity: Severity
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "warning_type": self.warning_type,
            "chapter_start": self.chapter_start,
            "chapter_end": self.chapter_end,
            "event_count": self.event_count,
            "description": self.description,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
        }


@dataclass
class TimelineReport:
    """Complete timeline validation report."""

    novel_id: str
    total_events: int
    conflicts: list[TimeConflict] = field(default_factory=list)
    order_violations: list[OrderViolation] = field(default_factory=list)
    interval_warnings: list[IntervalWarning] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    summary: str = ""

    @property
    def total_conflicts(self) -> int:
        """Get total number of conflicts."""
        return len(self.conflicts)

    @property
    def total_order_violations(self) -> int:
        """Get total number of order violations."""
        return len(self.order_violations)

    @property
    def total_interval_warnings(self) -> int:
        """Get total number of interval warnings."""
        return len(self.interval_warnings)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "novel_id": self.novel_id,
            "total_events": self.total_events,
            "total_conflicts": self.total_conflicts,
            "total_order_violations": self.total_order_violations,
            "total_interval_warnings": self.total_interval_warnings,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "order_violations": [v.to_dict() for v in self.order_violations],
            "interval_warnings": [w.to_dict() for w in self.interval_warnings],
            "validated_at": self.validated_at.isoformat(),
            "summary": self.summary,
        }

    def get_critical_count(self) -> int:
        """Get count of critical severity issues."""
        return sum(1 for c in self.conflicts if c.severity == Severity.CRITICAL)

    def get_error_count(self) -> int:
        """Get count of error severity issues."""
        return (
            sum(1 for c in self.conflicts if c.severity == Severity.ERROR)
            + sum(1 for v in self.order_violations if v.severity == Severity.ERROR)
            + sum(1 for w in self.interval_warnings if w.severity == Severity.ERROR)
        )

    def has_issues(self) -> bool:
        """Check if there are any issues (warnings or worse)."""
        return (
            self.total_conflicts > 0
            or self.total_order_violations > 0
            or self.total_interval_warnings > 0
        )


@dataclass
class Configuration:
    """Configuration for TimelineValidator."""

    min_chapter_gap: int = 1
    max_chapter_gap: int = 50
    dead_character_action_threshold: int = 5
    missing_character_threshold: int = 2
    min_event_gap: int = 0
    max_event_gap: int = 20

    @classmethod
    def default(cls) -> "Configuration":
        """Create default configuration."""
        return cls()


class TimelineValidator:
    """Validator for temporal consistency in novels.

    This validator checks for time conflicts, ordering violations, and interval
    issues in a story timeline. It generates reports with severity-based issues.

    Usage:
        >>> validator = TimelineValidator(postgres_client)
        >>> report = await validator.validate_timeline("novel_001")
        >>> if report.has_issues():
        ...     print(f"Found {report.total_conflicts} conflicts")
    """

    def __init__(
        self,
        postgres_client: PostgresClient | None = None,
        config: Configuration | None = None,
    ) -> None:
        """Initialize TimelineValidator.

        Args:
            postgres_client: Optional PostgreSQL client for database queries
            config: Optional configuration for validation thresholds
        """
        self.postgres_client = postgres_client
        self.config = config or Configuration.default()

        # Track loaded characters and their states
        self._character_states: dict[str, dict[str, Any]] = {}

        # Conflict patterns for detection
        self._death_patterns = [
            "died",
            "killed",
            "perished",
            "sacrificed",
            "dead",
            "was killed",
            "slain",
            "deceased",
            "no longer",
            "passed away",
        ]

        self._action_patterns = [
            "spoke",
            "said",
            "moved",
            "went",
            "arrived",
            "fought",
            "met",
            "discovered",
            "found",
            "created",
            "built",
            "attacked",
            "defended",
        ]

        self._birth_patterns = [
            "born",
            "birth",
            "introduced",
            "first appeared",
            "entered the story",
        ]

        self._marriage_patterns = [
            "married",
            "wedding",
            "became husband",
            "became wife",
            "tied the knot",
        ]

        logger.info("TimelineValidator initialized")

    async def validate_timeline(self, novel_id: str) -> TimelineReport:
        """Validate the timeline for a novel.

        This is the main entry point for timeline validation. It performs
        all checks and generates a comprehensive report.

        Args:
            novel_id: Identifier for the novel to validate

        Returns:
            TimelineReport with all validation results
        """
        logger.info(f"Validating timeline for novel: {novel_id}")

        # Step 1: Load timeline events from database
        events = await self._load_events(novel_id)

        # Step 2: Load character states
        await self._load_character_states()

        # Step 3: Detect time conflicts
        conflicts = self.detect_time_conflicts(events)

        # Step 4: Validate event ordering
        order_violations = self.validate_event_order(events)

        # Step 5: Validate intervals
        interval_warnings = self.validate_intervals(events)

        # Step 6: Generate report
        report = TimelineReport(
            novel_id=novel_id,
            total_events=len(events),
            conflicts=conflicts,
            order_violations=order_violations,
            interval_warnings=interval_warnings,
            summary=self._generate_summary(conflicts, order_violations, interval_warnings),
        )

        # Log results
        if report.has_issues():
            logger.warning(
                f"Timeline validation found issues: "
                f"{report.total_conflicts} conflicts, "
                f"{report.total_order_violations} order violations, "
                f"{report.total_interval_warnings} interval warnings"
            )
        else:
            logger.info("Timeline validation passed with no issues")

        return report

    def detect_time_conflicts(self, events: list[TimelineEventData]) -> list[TimeConflict]:
        """Detect time conflicts in events.

        Checks for:
        - Dead characters performing actions
        - Characters acting before introduction
        - Born after death (logical impossibility)
        - Married before meeting
        - Impossible sequences (child before parent, etc.)

        Args:
            events: List of timeline events to check

        Returns:
            List of detected TimeConflict objects
        """
        conflicts = []

        for event in events:
            # Check for dead character actions
            conflict = self._check_dead_character_action(event)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for missing character actions
            conflict = self._check_missing_character_action(event)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for born after death
            conflict = self._check_born_after_death(event)
            if conflict:
                conflicts.append(conflict)
                continue

            # Check for married before meeting
            conflict = self._check_married_before_meeting(event)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    def validate_event_order(self, events: list[TimelineEventData]) -> list[OrderViolation]:
        """Validate event ordering.

        Checks for:
        - Events happening in non-chronological order
        - Impossible sequences (e.g., resurrection without explanation)

        Args:
            events: List of timeline events to check

        Returns:
            List of detected OrderViolation objects
        """
        violations = []

        # Sort events by chapter
        sorted_events = sorted(events, key=lambda e: e.chapter)

        # Check for time flowing backwards within character arcs
        character_events: dict[str, list[TimelineEventData]] = {}
        for event in sorted_events:
            if event.character_name:
                if event.character_name not in character_events:
                    character_events[event.character_name] = []
                character_events[event.character_name].append(event)

        # Check each character's timeline for ordering issues
        for char_name, char_events in character_events.items():
            for i in range(len(char_events) - 1):
                current = char_events[i]
                next_event = char_events[i + 1]

                # Check for resurrection without explanation
                if self._is_resurrection_without_explanation(current, next_event):
                    violations.append(
                        OrderViolation(
                            earlier_event=f"{current.event_type}: {current.description}",
                            later_event=f"{next_event.event_type}: {next_event.description}",
                            earlier_chapter=current.chapter,
                            later_chapter=next_event.chapter,
                            reason=f"Character '{char_name}' appears to die and then reappear "
                            f"without explanation in chapter {next_event.chapter}",
                            severity=Severity.ERROR,
                        )
                    )

        return violations

    def validate_intervals(self, events: list[TimelineEventData]) -> list[IntervalWarning]:
        """Validate time intervals between events.

        Checks for:
        - Too short intervals (impossibly fast events)
        - Too long gaps (missing context)
        - Inconsistent pacing

        Args:
            events: List of timeline events to check

        Returns:
            List of detected IntervalWarning objects
        """
        warnings: list[IntervalWarning] = []

        if len(events) < 2:
            return warnings

        # Sort events by chapter
        sorted_events = sorted(events, key=lambda e: e.chapter)

        # Group events by character for interval analysis
        character_events: dict[str, list[TimelineEventData]] = {}
        for event in sorted_events:
            if event.character_name:
                if event.character_name not in character_events:
                    character_events[event.character_name] = []
                character_events[event.character_name].append(event)

        # Check intervals for each character
        for char_name, char_events in character_events.items():
            if len(char_events) < 2:
                continue

            for i in range(len(char_events) - 1):
                current = char_events[i]
                next_event = char_events[i + 1]

                gap = next_event.chapter - current.chapter

                # Check for too short intervals (impossibly fast)
                if self._is_impossibly_fast(current, next_event, gap):
                    warnings.append(
                        IntervalWarning(
                            warning_type="too_short_interval",
                            chapter_start=current.chapter,
                            chapter_end=next_event.chapter,
                            event_count=2,
                            description=f"Events for '{char_name}' happen too quickly: "
                            f"'{current.description[:50]}...' followed immediately by "
                            f"'{next_event.description[:50]}...'",
                            severity=Severity.WARNING,
                            suggestion="Consider adding more development or time passage between these events",
                        )
                    )

                # Check for too long gaps
                elif gap > self.config.max_event_gap:
                    warnings.append(
                        IntervalWarning(
                            warning_type="too_long_gap",
                            chapter_start=current.chapter,
                            chapter_end=next_event.chapter,
                            event_count=len(
                                [
                                    e
                                    for e in char_events
                                    if current.chapter <= e.chapter <= next_event.chapter
                                ]
                            ),
                            description=f"Large gap ({gap} chapters) between events for '{char_name}'",
                            severity=Severity.INFO,
                            suggestion="Consider checking for missing events or ensuring continuity is maintained",
                        )
                    )

        # Check for overall pacing
        if len(sorted_events) >= 3:
            pacing_warning = self._check_pacing(sorted_events)
            if pacing_warning:
                warnings.append(pacing_warning)

        return warnings

    async def _load_events(self, novel_id: str) -> list[TimelineEventData]:
        """Load timeline events from database.

        Args:
            novel_id: Novel identifier

        Returns:
            List of TimelineEventData objects
        """
        if not self.postgres_client:
            logger.warning("No PostgreSQL client, returning empty events list")
            return []

        try:
            # Get all timeline events with character names
            async with self.postgres_client.session() as session:
                te = aliased(DBTimelineEvent)
                cp = aliased(CharacterProfile)

                query = (
                    select(te, cp.name.label("character_name"))
                    .select_from(te)
                    .outerjoin(cp, te.character_id == cp.id)
                    .order_by(te.chapter)
                )

                result = await session.execute(query)
                rows = result.fetchall()

                events = []
                for row in rows:
                    db_event = row[0]
                    character_name = row[1]
                    events.append(TimelineEventData.from_db_event(db_event, character_name))

                logger.info(f"Loaded {len(events)} timeline events from database")
                return events

        except Exception as e:
            logger.error(f"Error loading events: {e}")
            return []

    async def _load_character_states(self) -> None:
        """Load character states from database.

        Populates self._character_states with birth and death information.
        """
        if not self.postgres_client:
            return

        try:
            characters = await self.postgres_client.list_characters()

            for char in characters:
                self._character_states[char.name] = {
                    "birth_chapter": char.birth_chapter,
                    "death_chapter": char.death_chapter,
                    "status": char.status,
                }

            logger.debug(f"Loaded states for {len(characters)} characters")

        except Exception as e:
            logger.error(f"Error loading character states: {e}")

    def _check_dead_character_action(self, event: TimelineEventData) -> TimeConflict | None:
        """Check if a dead character is performing an action."""
        if not event.character_name:
            return None

        char_state = self._character_states.get(event.character_name)
        if not char_state:
            return None

        death_chapter = char_state.get("death_chapter")
        if not death_chapter:
            return None

        # Check if event is an action after death
        if event.chapter > death_chapter:
            # Allow memorial references (mentions, memories, dreams)
            if self._is_memorial_reference(event):
                return None

            # Check if it's an actual action
            if self._is_character_action(event):
                return TimeConflict(
                    conflict_type=TimeConflictType.DEAD_CHARACTER_ACTION.value,
                    character_name=event.character_name,
                    chapter=event.chapter,
                    event_description=event.description,
                    reason=f"Character '{event.character_name}' performs action in chapter {event.chapter} "
                    f"but died in chapter {death_chapter}",
                    severity=Severity.ERROR,
                    evidence=f"Event type: {event.event_type}",
                )

        return None

    def _check_missing_character_action(self, event: TimelineEventData) -> TimeConflict | None:
        """Check if a character acts before introduction."""
        if not event.character_name:
            return None

        char_state = self._character_states.get(event.character_name)
        if not char_state:
            return None

        birth_chapter = char_state.get("birth_chapter")
        if not birth_chapter:
            return None

        # Check if event happens before birth
        if event.chapter < birth_chapter:
            # Check if it's a significant action (not just a mention)
            if self._is_character_action(event):
                return TimeConflict(
                    conflict_type=TimeConflictType.MISSING_CHARACTER_ACTION.value,
                    character_name=event.character_name,
                    chapter=event.chapter,
                    event_description=event.description,
                    reason=f"Character '{event.character_name}' acts in chapter {event.chapter} "
                    f"but was introduced in chapter {birth_chapter}",
                    severity=Severity.WARNING,
                    evidence=f"Event type: {event.event_type}",
                )

        return None

    def _check_born_after_death(self, event: TimelineEventData) -> TimeConflict | None:
        """Check if a character is born after they died."""
        if not event.character_name:
            return None

        if event.event_type != EventType.BIRTH.value:
            return None

        char_state = self._character_states.get(event.character_name)
        if not char_state:
            return None

        birth_chapter = char_state.get("birth_chapter")
        death_chapter = char_state.get("death_chapter")

        if birth_chapter is None or death_chapter is None:
            return None

        if birth_chapter > death_chapter:
            return TimeConflict(
                conflict_type=TimeConflictType.BORN_AFTER_DEATH.value,
                character_name=event.character_name,
                chapter=event.chapter,
                event_description=event.description,
                reason=f"Character '{event.character_name}' was born in chapter {birth_chapter} "
                f"but died in chapter {death_chapter} (impossible timeline)",
                severity=Severity.CRITICAL,
                evidence=f"Birth chapter: {birth_chapter}, Death chapter: {death_chapter}",
            )

        return None

    def _check_married_before_meeting(self, event: TimelineEventData) -> TimeConflict | None:
        """Check if characters married before they met.

        Note: This is a simplified check. A full implementation would track
        relationships between characters and check for marriage events in context.
        """
        if event.event_type != EventType.RELATIONSHIP_CHANGE.value:
            return None

        # Check if this is a marriage event
        is_marriage = any(
            pattern in event.description.lower() for pattern in self._marriage_patterns
        )

        if not is_marriage:
            return None

        # For a simplified check, we would need to track when characters first met
        # This requires additional relationship tracking which is out of scope for this version
        return None

    def _is_memorial_reference(self, event: TimelineEventData) -> bool:
        """Check if event is a memorial reference (allowed for dead characters)."""
        memorial_keywords = [
            "remembered",
            "memory of",
            "dream of",
            "thought of",
            "missed",
            "ghost of",
            "spirit of",
            "in memory",
            "legacy",
            "honor",
        ]

        description_lower = event.description.lower()
        return any(kw in description_lower for kw in memorial_keywords)

    def _is_character_action(self, event: TimelineEventData) -> bool:
        """Check if event represents an actual character action (not passive)."""
        # Action event types
        action_types = [
            EventType.APPEARANCE.value,
            EventType.MAJOR_EVENT.value,
            EventType.LOCATION_CHANGE.value,
            EventType.RELATIONSHIP_CHANGE.value,
        ]

        # Death events are not actions
        if event.event_type == EventType.DEATH.value:
            return False

        # Check event type
        if event.event_type in action_types:
            return True

        # Check description for action verbs
        description_lower = event.description.lower()
        return any(kw in description_lower for kw in self._action_patterns)

    def _is_resurrection_without_explanation(
        self, current: TimelineEventData, next_event: TimelineEventData
    ) -> bool:
        """Check if there's an unexplained resurrection."""
        # Check if current is death and next is appearance
        if current.event_type != EventType.DEATH.value:
            return False

        if next_event.event_type not in [
            EventType.APPEARANCE.value,
            EventType.MAJOR_EVENT.value,
        ]:
            return False

        # Check if next event explains the resurrection
        resurrection_keywords = [
            "resurrected",
            "brought back",
            "returned to life",
            "came back to life",
            "not really dead",
            "healed",
            "revived",
            "miracle",
            "magic",
        ]

        next_description = next_event.description.lower()
        return not any(kw in next_description for kw in resurrection_keywords)

    def _is_impossibly_fast(
        self, current: TimelineEventData, next_event: TimelineEventData, gap: int
    ) -> bool:
        """Check if events happen impossibly fast."""
        # Certain event types shouldn't happen in the same chapter
        incompatible_same_chapter = [
            (EventType.BIRTH.value, EventType.DEATH.value),
            (EventType.APPEARANCE.value, EventType.DEATH.value),
        ]

        if gap == 0:
            for type1, type2 in incompatible_same_chapter:
                if current.event_type == type1 and next_event.event_type == type2:
                    return True

        return False

    def _check_pacing(self, events: list[TimelineEventData]) -> IntervalWarning | None:
        """Check for overall pacing issues."""
        if len(events) < 3:
            return None

        # Calculate average events per chapter
        chapters = {e.chapter for e in events}
        avg_events_per_chapter = len(events) / len(chapters) if chapters else 0

        # Check for chapters with unusually high or low event density
        chapter_counts: dict[int, int] = {}
        for event in events:
            chapter_counts[event.chapter] = chapter_counts.get(event.chapter, 0) + 1

        for chapter, count in chapter_counts.items():
            if count > avg_events_per_chapter * 3:
                return IntervalWarning(
                    warning_type="high_event_density",
                    chapter_start=chapter,
                    chapter_end=chapter,
                    event_count=count,
                    description=f"Chapter {chapter} has {count} events "
                    f"(average: {avg_events_per_chapter:.1f})",
                    severity=Severity.INFO,
                    suggestion="Consider splitting events across chapters for better pacing",
                )
            elif count == 0 and avg_events_per_chapter > 1:
                # Only warn about empty chapters if average is > 1
                return IntervalWarning(
                    warning_type="low_event_density",
                    chapter_start=chapter,
                    chapter_end=chapter,
                    event_count=0,
                    description=f"Chapter {chapter} has no events (average: {avg_events_per_chapter:.1f})",
                    severity=Severity.INFO,
                    suggestion="Consider adding events or checking for missing content",
                )

        return None

    def _generate_summary(
        self,
        conflicts: list[TimeConflict],
        violations: list[OrderViolation],
        warnings: list[IntervalWarning],
    ) -> str:
        """Generate a summary of the validation."""
        if not conflicts and not violations and not warnings:
            return "Timeline validation passed with no issues."

        parts: list[str] = []

        critical_count = sum(1 for c in conflicts if c.severity == Severity.CRITICAL)
        error_count = sum(1 for c in conflicts if c.severity == Severity.ERROR)

        if critical_count > 0:
            parts.append(f"{critical_count} critical issue(s)")
        if error_count > 0:
            parts.append(f"{error_count} error(s)")

        warning_count = (
            sum(1 for c in conflicts if c.severity == Severity.WARNING)
            + sum(1 for v in violations if v.severity == Severity.WARNING)
            + sum(1 for w in warnings if w.severity == Severity.WARNING)
        )

        if warning_count > 0:
            parts.append(f"{warning_count} warning(s)")

        info_count = (
            sum(1 for c in conflicts if c.severity == Severity.INFO)
            + sum(1 for v in violations if v.severity == Severity.INFO)
            + sum(1 for w in warnings if w.severity == Severity.INFO)
        )

        if info_count > 0:
            parts.append(f"{info_count} info note(s)")

        return f"Timeline validation found: {', '.join(parts)}"


# Factory function
def create_timeline_validator(
    postgres_client: PostgresClient | None = None,
    config: Configuration | None = None,
) -> TimelineValidator:
    """Create a TimelineValidator instance.

    Args:
        postgres_client: Optional PostgreSQL client
        config: Optional configuration

    Returns:
        Configured TimelineValidator instance
    """
    return TimelineValidator(postgres_client, config)
