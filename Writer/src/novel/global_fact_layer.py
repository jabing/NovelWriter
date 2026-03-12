"""Global Fact Layer for double-layer consistency checking.

This module implements the GlobalFactLayer class which wraps CognitiveGraph
for fact storage and adds:
- Timeline validation (time-based fact consistency)
- Geographic/location consistency checks
- Conflict report generation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.novel.cognitive_graph import CognitiveGraph

logger = logging.getLogger(__name__)


class ConflictSeverity(str, Enum):
    """Severity level for detected conflicts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConflictType(str, Enum):
    """Types of conflicts that can be detected."""

    TIMELINE_ORDER = "timeline_order"
    """Fact in later chapter has earlier timestamp."""

    LOCATION_DUPLICATE = "location_duplicate"
    """Character appears in two locations in the same chapter."""

    CONTENT_CONFLICT = "content_conflict"
    """Facts have conflicting content."""

    CHARACTER_LOCATION = "character_location"
    """Character location inconsistency."""


@dataclass
class Conflict:
    """Represents a detected conflict between facts."""

    conflict_type: ConflictType
    severity: ConflictSeverity
    fact_id_1: str
    fact_id_2: str | None = None
    description: str = ""
    chapter: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "fact_id_1": self.fact_id_1,
            "fact_id_2": self.fact_id_2,
            "description": self.description,
            "chapter": self.chapter,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class ConflictReport:
    """Complete conflict report for all detected issues."""

    total_facts: int
    conflicts: list[Conflict] = field(default_factory=list)
    timeline_issues: list[Conflict] = field(default_factory=list)
    location_issues: list[Conflict] = field(default_factory=list)
    content_issues: list[Conflict] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    summary: str = ""

    @property
    def total_conflicts(self) -> int:
        """Get total number of conflicts."""
        return len(self.conflicts)

    @property
    def critical_count(self) -> int:
        """Get count of critical issues."""
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.CRITICAL)

    @property
    def error_count(self) -> int:
        """Get count of error-level issues."""
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Get count of warning-level issues."""
        return sum(1 for c in self.conflicts if c.severity == ConflictSeverity.WARNING)

    def has_issues(self) -> bool:
        """Check if there are any issues."""
        return self.total_conflicts > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_facts": self.total_facts,
            "total_conflicts": self.total_conflicts,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "timeline_issues": [c.to_dict() for c in self.timeline_issues],
            "location_issues": [c.to_dict() for c in self.location_issues],
            "content_issues": [c.to_dict() for c in self.content_issues],
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
        }


class GlobalFactLayer:
    """Global fact layer for managing facts with consistency checking.

    This class wraps CognitiveGraph for fact storage and adds:
    - Timeline validation (facts in chapter order with timestamps)
    - Location consistency (character location tracking)
    - Global conflict report generation

    Usage:
        >>> graph = CognitiveGraph()
        >>> gfl = GlobalFactLayer(graph)
        >>> gfl.add_fact("fact1", "event", "林晚去了京城", chapter=1, location="京城", timestamp=1000)
        >>> conflicts = gfl.check_fact_conflict("fact1")
        >>> report = gfl.get_conflict_report()
    """

    def __init__(self, graph: CognitiveGraph | None = None) -> None:
        """Initialize GlobalFactLayer.

        Args:
            graph: Optional CognitiveGraph instance. If None, a new one is created.
        """
        self.graph = graph or CognitiveGraph()
        # Track character locations per chapter for consistency checks
        self._character_locations: dict[str, dict[int, str]] = {}
        # Track timestamps per chapter for timeline validation
        self._chapter_timestamps: dict[int, list[tuple[str, int]]] = {}

    def add_fact(
        self,
        fact_id: str,
        fact_type: str,
        content: str,
        chapter: int,
        location: str | None = None,
        timestamp: int | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a global fact to the layer.

        Args:
            fact_id: Unique fact identifier
            fact_type: Type of fact (e.g., "event", "secret", "relationship")
            content: The factual content/statement
            chapter: Chapter number where this fact was established
            location: Optional location where this fact occurred
            timestamp: Optional timestamp for timeline ordering
            properties: Additional fact properties
        """
        props = properties or {}

        # Add location and timestamp to properties
        if location is not None:
            props["location"] = location
        if timestamp is not None:
            props["timestamp"] = timestamp

        # Use "global" as source_character for global facts
        self.graph.add_fact_node(
            fact_id=fact_id,
            fact_type=fact_type,
            content=content,
            source_character="global",
            chapter=chapter,
            properties=props,
        )

        # Track character location if mentioned in content
        self._track_character_location(fact_id, content, chapter, location)

        # Track timestamp for timeline validation
        if timestamp is not None:
            if chapter not in self._chapter_timestamps:
                self._chapter_timestamps[chapter] = []
            self._chapter_timestamps[chapter].append((fact_id, timestamp))

        logger.debug(
            f"Added global fact: {fact_id} (type={fact_type}, chapter={chapter}, "
            f"location={location}, timestamp={timestamp})"
        )

    def _track_character_location(
        self,
        fact_id: str,
        content: str,
        chapter: int,
        location: str | None,
    ) -> None:
        """Track character location from fact content.

        This is a simplified implementation that extracts character names
        from common Chinese novel patterns.

        Args:
            fact_id: Fact identifier
            content: Fact content to analyze
            chapter: Chapter number
            location: Location if specified
        """
        if not location:
            return

        # Simple pattern matching for character names in Chinese novels
        # Characters are often mentioned as "某某去了某地" or "某某在某地"
        common_patterns = [
            "去了",  # went to
            "在",  # at/in
            "来到",  # arrived at
            "抵达",  # arrived at
            "身处",  # located at
        ]

        for pattern in common_patterns:
            if pattern in content:
                # Extract potential character name (simplified)
                parts = content.split(pattern)
                if parts:
                    potential_name = parts[0].strip()
                    # Filter out common non-name prefixes
                    if potential_name and len(potential_name) <= 10:
                        if potential_name not in self._character_locations:
                            self._character_locations[potential_name] = {}
                        self._character_locations[potential_name][chapter] = location
                        logger.debug(
                            f"Tracked location: {potential_name} at {location} in chapter {chapter}"
                        )
                break

    def check_fact_conflict(self, fact_id: str) -> list[Conflict]:
        """Check if a fact conflicts with other facts.

        Args:
            fact_id: Fact identifier to check

        Returns:
            List of detected conflicts (empty if no conflicts)
        """
        conflicts: list[Conflict] = []

        # Get fact data
        fact_data = self.graph.get_node(fact_id)
        if not fact_data:
            return conflicts

        # 1. Check content conflicts using CognitiveGraph
        content_conflicts = self.graph.check_consistency(fact_id)
        for conflicting_fact in content_conflicts:
            conflicts.append(
                Conflict(
                    conflict_type=ConflictType.CONTENT_CONFLICT,
                    severity=ConflictSeverity.WARNING,
                    fact_id_1=fact_id,
                    fact_id_2=conflicting_fact.get("id"),
                    description=f"Content conflict detected between facts",
                    chapter=fact_data.get("chapter", 0),
                    evidence={
                        "fact1_content": fact_data.get("content", ""),
                        "fact2_content": conflicting_fact.get("content", ""),
                    },
                )
            )

        # 2. Check timeline conflicts
        timestamp = fact_data.get("timestamp")
        chapter = fact_data.get("chapter", 0)
        if timestamp is not None:
            timeline_conflicts = self._check_timeline_conflict(fact_id, chapter, timestamp)
            conflicts.extend(timeline_conflicts)

        # 3. Check location conflicts
        location = fact_data.get("location")
        if location is not None:
            location_conflicts = self._check_location_conflict(fact_id, chapter, location)
            conflicts.extend(location_conflicts)

        return conflicts

    def _check_timeline_conflict(
        self, fact_id: str, chapter: int, timestamp: int
    ) -> list[Conflict]:
        """Check for timeline conflicts.

        A fact in a later chapter should not have an earlier timestamp
        than a fact in an earlier chapter.

        Args:
            fact_id: Fact identifier
            chapter: Chapter number
            timestamp: Timestamp value

        Returns:
            List of timeline conflicts
        """
        conflicts: list[Conflict] = []

        # Check all chapters
        for other_chapter, fact_timestamps in self._chapter_timestamps.items():
            for other_fact_id, other_timestamp in fact_timestamps:
                if other_fact_id == fact_id:
                    continue

                # Timeline conflict: later chapter has earlier timestamp
                if other_chapter > chapter and other_timestamp < timestamp:
                    conflicts.append(
                        Conflict(
                            conflict_type=ConflictType.TIMELINE_ORDER,
                            severity=ConflictSeverity.ERROR,
                            fact_id_1=fact_id,
                            fact_id_2=other_fact_id,
                            description=f"Timeline order conflict: fact in chapter {other_chapter} "
                            f"has earlier timestamp ({other_timestamp}) than fact in chapter {chapter} ({timestamp})",
                            chapter=chapter,
                            evidence={
                                "fact1_chapter": chapter,
                                "fact1_timestamp": timestamp,
                                "fact2_chapter": other_chapter,
                                "fact2_timestamp": other_timestamp,
                            },
                        )
                    )
                elif other_chapter < chapter and other_timestamp > timestamp:
                    conflicts.append(
                        Conflict(
                            conflict_type=ConflictType.TIMELINE_ORDER,
                            severity=ConflictSeverity.ERROR,
                            fact_id_1=fact_id,
                            fact_id_2=other_fact_id,
                            description=f"Timeline order conflict: fact in chapter {chapter} "
                            f"has earlier timestamp ({timestamp}) than fact in chapter {other_chapter} ({other_timestamp})",
                            chapter=chapter,
                            evidence={
                                "fact1_chapter": chapter,
                                "fact1_timestamp": timestamp,
                                "fact2_chapter": other_chapter,
                                "fact2_timestamp": other_timestamp,
                            },
                        )
                    )

        return conflicts

    def _check_location_conflict(
        self, fact_id: str, chapter: int, location: str
    ) -> list[Conflict]:
        """Check for location conflicts.

        Detects if a character appears in multiple locations in the same chapter.

        Args:
            fact_id: Fact identifier
            chapter: Chapter number
            location: Location value

        Returns:
            List of location conflicts
        """
        conflicts: list[Conflict] = []

        # Check character locations for duplicates in same chapter
        for character_name, chapter_locations in self._character_locations.items():
            if chapter in chapter_locations:
                existing_location = chapter_locations[chapter]
                if existing_location != location:
                    # Character is in two different locations in same chapter
                    conflicts.append(
                        Conflict(
                            conflict_type=ConflictType.LOCATION_DUPLICATE,
                            severity=ConflictSeverity.WARNING,
                            fact_id_1=fact_id,
                            description=f"Character '{character_name}' appears in multiple locations "
                            f"in chapter {chapter}: '{existing_location}' and '{location}'",
                            chapter=chapter,
                            evidence={
                                "character": character_name,
                                "location_1": existing_location,
                                "location_2": location,
                            },
                        )
                    )

        return conflicts

    def check_timeline_consistency(self) -> list[Conflict]:
        """Check all facts for timeline consistency.

        Returns:
            List of timeline-related conflicts
        """
        conflicts: list[Conflict] = []

        # Sort chapters
        sorted_chapters = sorted(self._chapter_timestamps.keys())

        # Track the maximum timestamp seen so far
        max_timestamp: dict[int, int] = {}  # chapter -> max timestamp

        for chapter in sorted_chapters:
            fact_timestamps = self._chapter_timestamps[chapter]

            for fact_id, timestamp in fact_timestamps:
                # Check against previous chapters
                for prev_chapter in sorted_chapters:
                    if prev_chapter >= chapter:
                        continue

                    if prev_chapter in max_timestamp:
                        prev_max = max_timestamp[prev_chapter]
                        if timestamp < prev_max:
                            # Current timestamp is earlier than previous chapter's max
                            conflicts.append(
                                Conflict(
                                    conflict_type=ConflictType.TIMELINE_ORDER,
                                    severity=ConflictSeverity.ERROR,
                                    fact_id_1=fact_id,
                                    description=f"Timestamp {timestamp} in chapter {chapter} is earlier than "
                                    f"maximum timestamp {prev_max} in chapter {prev_chapter}",
                                    chapter=chapter,
                                    evidence={
                                        "current_chapter": chapter,
                                        "current_timestamp": timestamp,
                                        "prev_chapter": prev_chapter,
                                        "prev_max_timestamp": prev_max,
                                    },
                                )
                            )

            # Update max timestamp for this chapter
            if fact_timestamps:
                max_timestamp[chapter] = max(t for _, t in fact_timestamps)

        return conflicts

    def check_location_consistency(self, character_id: str | None = None) -> list[Conflict]:
        """Check location consistency.

        If character_id is provided, checks only that character's locations.
        Otherwise, checks all tracked characters.

        Args:
            character_id: Optional character to check

        Returns:
            List of location-related conflicts
        """
        conflicts: list[Conflict] = []

        if character_id:
            # Check specific character
            if character_id in self._character_locations:
                char_locations = self._character_locations[character_id]
                conflicts.extend(
                    self._check_character_location_conflicts(character_id, char_locations)
                )
        else:
            # Check all characters
            for char_name, char_locations in self._character_locations.items():
                conflicts.extend(
                    self._check_character_location_conflicts(char_name, char_locations)
                )

        return conflicts

    def _check_character_location_conflicts(
        self, character_name: str, locations: dict[int, str]
    ) -> list[Conflict]:
        """Check for location conflicts for a specific character.

        Args:
            character_name: Character name
            locations: Dict of chapter -> location

        Returns:
            List of conflicts
        """
        conflicts: list[Conflict] = []

        # Check for multiple locations in same chapter
        # This should already be detected, but we check again for completeness
        # Group by chapter to detect multiple locations
        chapter_locations: dict[int, list[str]] = {}
        for chapter, location in locations.items():
            if chapter not in chapter_locations:
                chapter_locations[chapter] = []
            chapter_locations[chapter].append(location)

        for chapter, locs in chapter_locations.items():
            unique_locs = list(set(locs))
            if len(unique_locs) > 1:
                conflicts.append(
                    Conflict(
                        conflict_type=ConflictType.LOCATION_DUPLICATE,
                        severity=ConflictSeverity.WARNING,
                        fact_id_1="",
                        description=f"Character '{character_name}' appears in multiple locations "
                        f"in chapter {chapter}: {', '.join(unique_locs)}",
                        chapter=chapter,
                        evidence={
                            "character": character_name,
                            "locations": unique_locs,
                        },
                    )
                )

        return conflicts

    def get_facts_by_chapter(self, chapter: int) -> list[dict[str, Any]]:
        """Get all facts for a specific chapter.

        Args:
            chapter: Chapter number

        Returns:
            List of fact dictionaries with node data
        """
        facts = []
        for node_id, data in self.graph.graph.nodes(data=True):
            if data.get("node_type") == "fact" and data.get("chapter") == chapter:
                facts.append({"id": node_id, **data})
        return facts

    def get_facts_by_location(self, location: str) -> list[dict[str, Any]]:
        """Get all facts related to a location.

        Args:
            location: Location name

        Returns:
            List of fact dictionaries with node data
        """
        facts = []
        for node_id, data in self.graph.graph.nodes(data=True):
            if data.get("node_type") == "fact":
                # Check location property
                if data.get("location") == location:
                    facts.append({"id": node_id, **data})
                # Also check if location is mentioned in content
                elif location in data.get("content", ""):
                    facts.append({"id": node_id, **data})
        return facts

    def get_conflict_report(self) -> ConflictReport:
        """Generate a comprehensive conflict report.

        Returns:
            ConflictReport with all detected issues
        """
        # Get all facts
        total_facts = len(
            [
                n
                for n, d in self.graph.graph.nodes(data=True)
                if d.get("node_type") == "fact"
            ]
        )

        # Collect all conflicts
        all_conflicts: list[Conflict] = []

        # 1. Content conflicts from CognitiveGraph
        graph_conflicts = self.graph.find_conflicts()
        for fact1, fact2 in graph_conflicts:
            all_conflicts.append(
                Conflict(
                    conflict_type=ConflictType.CONTENT_CONFLICT,
                    severity=ConflictSeverity.WARNING,
                    fact_id_1=fact1.get("id", ""),
                    fact_id_2=fact2.get("id", ""),
                    description=f"Content conflict between facts",
                    chapter=min(fact1.get("chapter", 0), fact2.get("chapter", 0)),
                    evidence={
                        "fact1_content": fact1.get("content", ""),
                        "fact2_content": fact2.get("content", ""),
                    },
                )
            )

        # 2. Timeline conflicts
        timeline_conflicts = self.check_timeline_consistency()
        all_conflicts.extend(timeline_conflicts)

        # 3. Location conflicts
        location_conflicts = self.check_location_consistency()
        all_conflicts.extend(location_conflicts)

        # Separate conflicts by type
        timeline_issues = [c for c in all_conflicts if c.conflict_type == ConflictType.TIMELINE_ORDER]
        location_issues = [c for c in all_conflicts if c.conflict_type in (
            ConflictType.LOCATION_DUPLICATE,
            ConflictType.CHARACTER_LOCATION,
        )]
        content_issues = [c for c in all_conflicts if c.conflict_type == ConflictType.CONTENT_CONFLICT]

        # Generate summary
        summary = self._generate_summary(all_conflicts)

        return ConflictReport(
            total_facts=total_facts,
            conflicts=all_conflicts,
            timeline_issues=timeline_issues,
            location_issues=location_issues,
            content_issues=content_issues,
            summary=summary,
        )

    def _generate_summary(self, conflicts: list[Conflict]) -> str:
        """Generate a summary of conflicts.

        Args:
            conflicts: List of detected conflicts

        Returns:
            Summary string
        """
        if not conflicts:
            return "No conflicts detected. All facts are consistent."

        parts: list[str] = []

        critical = sum(1 for c in conflicts if c.severity == ConflictSeverity.CRITICAL)
        errors = sum(1 for c in conflicts if c.severity == ConflictSeverity.ERROR)
        warnings = sum(1 for c in conflicts if c.severity == ConflictSeverity.WARNING)

        if critical > 0:
            parts.append(f"{critical} critical issue(s)")
        if errors > 0:
            parts.append(f"{errors} error(s)")
        if warnings > 0:
            parts.append(f"{warnings} warning(s)")

        # Count by type
        timeline_count = sum(1 for c in conflicts if c.conflict_type == ConflictType.TIMELINE_ORDER)
        location_count = sum(1 for c in conflicts if c.conflict_type in (
            ConflictType.LOCATION_DUPLICATE,
            ConflictType.CHARACTER_LOCATION,
        ))
        content_count = sum(1 for c in conflicts if c.conflict_type == ConflictType.CONTENT_CONFLICT)

        type_parts: list[str] = []
        if timeline_count > 0:
            type_parts.append(f"{timeline_count} timeline")
        if location_count > 0:
            type_parts.append(f"{location_count} location")
        if content_count > 0:
            type_parts.append(f"{content_count} content")

        summary = f"Conflict report: {', '.join(parts)}. "
        if type_parts:
            summary += f"By type: {', '.join(type_parts)}."

        return summary

    def get_fact(self, fact_id: str) -> dict[str, Any] | None:
        """Get a fact by ID.

        Args:
            fact_id: Fact identifier

        Returns:
            Fact dictionary or None if not found
        """
        return self.graph.get_node(fact_id)

    def get_all_facts(self) -> list[dict[str, Any]]:
        """Get all facts in the layer.

        Returns:
            List of all fact dictionaries
        """
        facts = []
        for node_id, data in self.graph.graph.nodes(data=True):
            if data.get("node_type") == "fact":
                facts.append({"id": node_id, **data})
        return facts

    def remove_fact(self, fact_id: str) -> bool:
        """Remove a fact from the layer.

        Args:
            fact_id: Fact identifier

        Returns:
            True if removed, False if not found
        """
        # Get fact data before removal
        fact_data = self.graph.get_node(fact_id)
        if not fact_data:
            return False

        chapter = fact_data.get("chapter", 0)
        timestamp = fact_data.get("timestamp")

        # Remove from graph
        result = self.graph.remove_node(fact_id)

        if result:
            # Clean up tracking structures
            if chapter in self._chapter_timestamps:
                self._chapter_timestamps[chapter] = [
                    (fid, ts) for fid, ts in self._chapter_timestamps[chapter]
                    if fid != fact_id
                ]
                if not self._chapter_timestamps[chapter]:
                    del self._chapter_timestamps[chapter]

            # Clean character locations if needed
            for char_name in list(self._character_locations.keys()):
                if chapter in self._character_locations[char_name]:
                    # Can't easily determine which character to remove
                    # without more context, so we leave it for now
                    pass

        return result

    def clear(self) -> None:
        """Clear all facts and tracking data."""
        self.graph.clear()
        self._character_locations.clear()
        self._chapter_timestamps.clear()

    @property
    def fact_count(self) -> int:
        """Get total number of facts."""
        return len(
            [
                n
                for n, d in self.graph.graph.nodes(data=True)
                if d.get("node_type") == "fact"
            ]
        )
