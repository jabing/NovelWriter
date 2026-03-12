"""Consistency Verifier for double-layer consistency checking.

This module implements the ConsistencyVerifier class which integrates:
- CognitiveGraph: Graph storage for nodes and relationships
- GlobalFactLayer: Global fact management with timeline/location checks
- CharacterKnowledge: Character-specific knowledge tracking

The double-layer verification checks:
1. Global Layer: Fact conflicts, timeline ordering, location consistency
2. Character Layer: Cognitive conflicts, knowledge scope violations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.novel.character_knowledge import CharacterKnowledge, CognitiveConflict
from src.novel.cognitive_graph import CognitiveGraph
from src.novel.global_fact_layer import (
    Conflict,
    ConflictSeverity,
    GlobalFactLayer,
)

logger = logging.getLogger(__name__)


class InconsistencyType(str, Enum):
    """Types of inconsistencies that can be detected."""

    DEAD_CHARACTER_APPEARANCE = "dead_character_appearance"
    LOCATION_MISMATCH = "location_mismatch"
    TIMELINE_ERROR = "timeline_error"
    CHARACTER_STATE_CONTRADICTION = "character_state_contradiction"
    MISSING_CHARACTER = "missing_character"
    RELATIONSHIP_CONTRADICTION = "relationship_contradiction"
    WORLD_RULE_VIOLATION = "world_rule_violation"


@dataclass
class Inconsistency:
    """A single inconsistency detected in the story."""

    inconsistency_type: InconsistencyType
    severity: int
    description: str
    chapter: int = 0
    character: str = ""
    location: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "inconsistency_type": self.inconsistency_type.value,
            "severity": self.severity,
            "description": self.description,
            "chapter": self.chapter,
            "character": self.character,
            "location": self.location,
            "details": self.details,
        }


@dataclass
class VerificationResult:
    """Result of verifying content for inconsistencies."""

    is_consistent: bool
    inconsistencies: list[Inconsistency] = field(default_factory=list)
    chapter: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "inconsistencies": [i.to_dict() for i in self.inconsistencies],
            "chapter": self.chapter,
            "summary": self.summary,
        }


@dataclass
class LayerVerificationResult:
    """Result of verifying a single layer."""

    layer_name: str
    passed: bool
    issues: list[dict[str, Any]] = field(default_factory=list)
    issue_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "layer_name": self.layer_name,
            "passed": self.passed,
            "issues": self.issues,
            "issue_count": self.issue_count,
        }


@dataclass
class DoubleLayerResult:
    """Result of double-layer verification for a single fact."""

    fact_id: str
    global_layer: LayerVerificationResult
    character_layer: LayerVerificationResult
    overall_passed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "fact_id": self.fact_id,
            "global_layer": self.global_layer.to_dict(),
            "character_layer": self.character_layer.to_dict(),
            "overall_passed": self.overall_passed,
        }


@dataclass
class ChapterVerificationResult:
    """Result of verifying a chapter."""

    chapter_number: int
    passed: bool
    global_conflicts: list[Conflict] = field(default_factory=list)
    cognitive_conflicts: list[CognitiveConflict] = field(default_factory=list)
    facts_checked: int = 0
    characters_checked: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chapter_number": self.chapter_number,
            "passed": self.passed,
            "global_conflicts": [c.to_dict() for c in self.global_conflicts],
            "cognitive_conflicts": [c.to_dict() for c in self.cognitive_conflicts],
            "facts_checked": self.facts_checked,
            "characters_checked": self.characters_checked,
            "summary": self.summary,
        }


@dataclass
class VerificationReport:
    """Comprehensive verification report combining all layers."""

    total_facts: int
    total_characters: int
    global_conflicts: list[Conflict] = field(default_factory=list)
    cognitive_conflicts: list[CognitiveConflict] = field(default_factory=list)
    timeline_issues: list[Conflict] = field(default_factory=list)
    location_issues: list[Conflict] = field(default_factory=list)
    double_layer_results: list[DoubleLayerResult] = field(default_factory=list)
    summary: str = ""
    passed: bool = True
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_issues(self) -> int:
        """Get total number of issues."""
        return (
            len(self.global_conflicts)
            + len(self.cognitive_conflicts)
            + len(self.timeline_issues)
            + len(self.location_issues)
        )

    @property
    def critical_count(self) -> int:
        """Get count of critical issues."""
        return sum(
            1 for c in self.global_conflicts if c.severity == ConflictSeverity.CRITICAL
        )

    @property
    def error_count(self) -> int:
        """Get count of error-level issues."""
        return sum(
            1 for c in self.global_conflicts if c.severity == ConflictSeverity.ERROR
        )

    @property
    def warning_count(self) -> int:
        """Get count of warning-level issues."""
        return sum(
            1 for c in self.global_conflicts if c.severity == ConflictSeverity.WARNING
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_facts": self.total_facts,
            "total_characters": self.total_characters,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "global_conflicts": [c.to_dict() for c in self.global_conflicts],
            "cognitive_conflicts": [c.to_dict() for c in self.cognitive_conflicts],
            "timeline_issues": [c.to_dict() for c in self.timeline_issues],
            "location_issues": [c.to_dict() for c in self.location_issues],
            "double_layer_results": [r.to_dict() for r in self.double_layer_results],
            "summary": self.summary,
            "passed": self.passed,
            "generated_at": self.generated_at.isoformat(),
        }


class ConsistencyVerifier:
    """Integrates all consistency checking components.

    This class provides a unified interface for double-layer consistency
    verification, combining global fact checking and character knowledge
    verification.

    Usage:
        >>> graph = CognitiveGraph()
        >>> # Add nodes and facts...
        >>> verifier = ConsistencyVerifier(graph)
        >>> report = verifier.get_verification_report()
        >>> print(report.summary)
        >>> print(f"Total issues: {report.total_issues}")
    """

    def __init__(self, cognitive_graph: CognitiveGraph) -> None:
        """Initialize ConsistencyVerifier with a CognitiveGraph.

        Args:
            cognitive_graph: The cognitive graph containing all nodes and facts
        """
        self._graph = cognitive_graph
        self._global_layer = GlobalFactLayer(cognitive_graph)
        self._character_knowledge: dict[str, CharacterKnowledge] = {}

        # Cache for verification results
        self._verification_cache: dict[str, Any] = {}

        # Initialize character knowledge for all existing characters
        self._initialize_character_knowledge()

    def _initialize_character_knowledge(self) -> None:
        """Initialize CharacterKnowledge for all characters in the graph."""
        character_ids = self._graph.get_nodes_by_type("character")
        for char_id in character_ids:
            if char_id not in self._character_knowledge:
                self._character_knowledge[char_id] = CharacterKnowledge(
                    char_id, self._graph
                )
        logger.debug(
            f"Initialized knowledge tracking for {len(self._character_knowledge)} characters"
        )

    def add_character(self, character_id: str) -> CharacterKnowledge:
        """Add a character for knowledge tracking.

        Args:
            character_id: ID of the character to add

        Returns:
            CharacterKnowledge instance for the character
        """
        if character_id not in self._character_knowledge:
            self._character_knowledge[character_id] = CharacterKnowledge(
                character_id, self._graph
            )
        return self._character_knowledge[character_id]

    def verify_chapter(
        self,
        chapter_content: str,
        chapter_number: int,
        character_ids: list[str] | None = None,
    ) -> ChapterVerificationResult:
        """Verify consistency of a chapter.

        This method performs double-layer verification:
        1. Global layer: Check fact conflicts, timeline, location
        2. Character layer: Check cognitive conflicts for each character

        Args:
            chapter_content: The text content of the chapter
            chapter_number: Chapter number being verified
            character_ids: Optional list of characters to check. If None, checks all.

        Returns:
            ChapterVerificationResult with all detected issues
        """
        global_conflicts: list[Conflict] = []
        cognitive_conflicts: list[CognitiveConflict] = []

        # Get facts for this chapter
        chapter_facts = self._global_layer.get_facts_by_chapter(chapter_number)
        facts_checked = len(chapter_facts)

        # 1. Check global layer conflicts for chapter facts
        for fact_data in chapter_facts:
            fact_id = fact_data.get("id", "")
            conflicts = self._global_layer.check_fact_conflict(fact_id)
            global_conflicts.extend(conflicts)

        # 2. Check character cognitive conflicts
        chars_to_check = character_ids or list(self._character_knowledge.keys())
        characters_checked = len(chars_to_check)

        for char_id in chars_to_check:
            if char_id not in self._character_knowledge:
                continue

            ck = self._character_knowledge[char_id]
            conflicts = ck.check_cognitive_conflict(chapter_content, chapter_number)
            cognitive_conflicts.extend(conflicts)

        # Determine overall pass/fail
        passed = len(global_conflicts) == 0 and len(cognitive_conflicts) == 0

        # Generate summary
        summary = self._generate_chapter_summary(
            chapter_number, global_conflicts, cognitive_conflicts
        )

        return ChapterVerificationResult(
            chapter_number=chapter_number,
            passed=passed,
            global_conflicts=global_conflicts,
            cognitive_conflicts=cognitive_conflicts,
            facts_checked=facts_checked,
            characters_checked=characters_checked,
            summary=summary,
        )

    def verify_fact(self, fact_id: str) -> DoubleLayerResult:
        """Verify a single fact using double-layer verification.

        Args:
            fact_id: ID of the fact to verify

        Returns:
            DoubleLayerResult with global and character layer results
        """
        # 1. Global layer verification
        global_issues: list[dict[str, Any]] = []
        global_conflicts = self._global_layer.check_fact_conflict(fact_id)

        for conflict in global_conflicts:
            global_issues.append({
                "type": conflict.conflict_type.value,
                "severity": conflict.severity.value,
                "description": conflict.description,
            })

        global_result = LayerVerificationResult(
            layer_name="global",
            passed=len(global_issues) == 0,
            issues=global_issues,
            issue_count=len(global_issues),
        )

        # 2. Character layer verification
        character_issues: list[dict[str, Any]] = []
        fact_data = self._graph.get_node(fact_id)

        if fact_data:
            fact_content = fact_data.get("content", "")
            chapter = fact_data.get("chapter", 0)

            # Check each character's knowledge
            for char_id, ck in self._character_knowledge.items():
                # Check if this character has cognitive conflicts related to this fact
                if ck.knows_fact(fact_id):
                    # Character knows this fact - check if it makes sense
                    conflicts = ck.check_cognitive_conflict(fact_content, chapter)
                    for conflict in conflicts:
                        if conflict.fact_id == fact_id:
                            character_issues.append({
                                "character_id": char_id,
                                "type": conflict.conflict_type,
                                "description": conflict.description,
                            })

        character_result = LayerVerificationResult(
            layer_name="character",
            passed=len(character_issues) == 0,
            issues=character_issues,
            issue_count=len(character_issues),
        )

        overall_passed = global_result.passed and character_result.passed

        return DoubleLayerResult(
            fact_id=fact_id,
            global_layer=global_result,
            character_layer=character_result,
            overall_passed=overall_passed,
        )

    def verify_character_knowledge(
        self, character_id: str, chapter: int | None = None
    ) -> LayerVerificationResult:
        """Verify a character's knowledge consistency.

        Checks for:
        - Cognitive conflicts (acting on unknown knowledge)
        - Knowledge scope violations
        - Confidence-based conflicts

        Args:
            character_id: ID of the character to verify
            chapter: Optional chapter number for context-specific verification

        Returns:
            LayerVerificationResult with all character-level issues
        """
        issues: list[dict[str, Any]] = []

        if character_id not in self._character_knowledge:
            return LayerVerificationResult(
                layer_name="character",
                passed=True,
                issues=[],
                issue_count=0,
            )

        ck = self._character_knowledge[character_id]

        # Get all facts known by this character
        knowledge = ck.get_knowledge(chapter=chapter)

        # Check for each known fact if there are scope or confidence issues
        for fact_info in knowledge:
            fact_id = fact_info.get("id", "")
            confidence = fact_info.get("confidence", 1.0)
            source = fact_info.get("knowledge_source", "direct")
            learned_chapter = fact_info.get("learned_chapter", 1)

            # Check if character learned this fact too early
            if chapter is not None and learned_chapter > chapter:
                issues.append({
                    "type": "knowledge_timing",
                    "fact_id": fact_id,
                    "description": f"Character knows fact from chapter {learned_chapter} but current chapter is {chapter}",
                    "severity": "error",
                })

            # Check for low confidence hearsay
            if source == "hearsay" and confidence < 0.5:
                issues.append({
                    "type": "low_confidence_hearsay",
                    "fact_id": fact_id,
                    "description": f"Character has low confidence ({confidence:.0%}) hearsay knowledge",
                    "severity": "warning",
                })

        # Check knowledge scope
        scope = ck.get_knowledge_scope()
        scope_issues = self._check_scope_violations(character_id, scope, chapter)
        issues.extend(scope_issues)

        return LayerVerificationResult(
            layer_name="character",
            passed=len(issues) == 0,
            issues=issues,
            issue_count=len(issues),
        )

    def _check_scope_violations(
        self,
        character_id: str,
        scope: dict[str, Any],
        chapter: int | None,
    ) -> list[dict[str, Any]]:
        """Check for knowledge scope violations.

        Args:
            character_id: Character ID
            scope: Character's knowledge scope
            chapter: Optional chapter context

        Returns:
            List of scope violation issues
        """
        issues: list[dict[str, Any]] = []

        # Get character tier
        tier = scope.get("tier", 1)

        # Check if character knows things outside their scope
        # For now, this is a placeholder for more sophisticated scope checking
        # In a full implementation, this would check:
        # - Does a minor character know protagonist-level secrets?
        # - Does a character know about locations they've never visited?
        # - Does a character know about events they didn't witness?

        # Simple heuristic: tier 3 characters shouldn't know tier 0 secrets
        if tier >= 3:
            ck = self._character_knowledge.get(character_id)
            if ck:
                knowledge = ck.get_knowledge(chapter=chapter)
                for fact_info in knowledge:
                    fact_type = fact_info.get("fact_type", "")
                    if fact_type == "secret":
                        # Check if this is a tier 0 (protagonist) secret
                        fact_id = fact_info.get("id", "")
                        fact_node = self._graph.get_node(fact_id)
                        if fact_node:
                            source_char = fact_node.get("source_character", "")
                            source_node = self._graph.get_node(source_char)
                            if source_node and source_node.get("tier", 1) == 0:
                                issues.append({
                                    "type": "scope_violation",
                                    "fact_id": fact_id,
                                    "description": f"Minor character (tier {tier}) knows protagonist secret",
                                    "severity": "warning",
                                })

        return issues

    def get_verification_report(self) -> VerificationReport:
        """Generate a comprehensive verification report.

        This method performs full double-layer verification across all
        facts and characters, combining results from GlobalFactLayer
        and CharacterKnowledge components.

        Returns:
            VerificationReport with all detected issues and summary
        """
        # Get counts
        total_facts = len(self._graph.get_nodes_by_type("fact"))
        total_characters = len(self._graph.get_nodes_by_type("character"))

        # Get global layer conflicts
        global_report = self._global_layer.get_conflict_report()
        global_conflicts = global_report.conflicts
        timeline_issues = global_report.timeline_issues
        location_issues = global_report.location_issues

        # Get character layer conflicts
        cognitive_conflicts: list[CognitiveConflict] = []
        for ck in self._character_knowledge.values():
            # Get knowledge for this character
            knowledge = ck.get_knowledge()

            # Check cognitive conflicts for each known fact
            for fact_info in knowledge:
                fact_content = fact_info.get("content", "")
                learned_chapter = fact_info.get("learned_chapter", 1)

                # Check if the character's action at the learned chapter
                # shows cognitive conflict
                conflicts = ck.check_cognitive_conflict(
                    fact_content, learned_chapter
                )
                cognitive_conflicts.extend(conflicts)

        # Perform double-layer verification for all facts
        double_layer_results: list[DoubleLayerResult] = []
        fact_ids = self._graph.get_nodes_by_type("fact")

        for fact_id in fact_ids:
            result = self.verify_fact(fact_id)
            if not result.overall_passed:
                double_layer_results.append(result)

        # Determine overall pass/fail
        passed = (
            len(global_conflicts) == 0
            and len(cognitive_conflicts) == 0
            and len(double_layer_results) == 0
        )

        # Generate summary
        summary = self._generate_summary(
            total_facts,
            total_characters,
            global_conflicts,
            cognitive_conflicts,
            timeline_issues,
            location_issues,
        )

        return VerificationReport(
            total_facts=total_facts,
            total_characters=total_characters,
            global_conflicts=global_conflicts,
            cognitive_conflicts=cognitive_conflicts,
            timeline_issues=timeline_issues,
            location_issues=location_issues,
            double_layer_results=double_layer_results,
            summary=summary,
            passed=passed,
        )

    def check_double_layer(self, fact_id: str) -> DoubleLayerResult:
        """Check both global and character layer for a fact.

        This is a convenience method that wraps verify_fact() with
        a more explicit name for the double-layer verification.

        Args:
            fact_id: ID of the fact to check

        Returns:
            DoubleLayerResult with verification results from both layers
        """
        return self.verify_fact(fact_id)

    def _generate_chapter_summary(
        self,
        chapter_number: int,
        global_conflicts: list[Conflict],
        cognitive_conflicts: list[CognitiveConflict],
    ) -> str:
        """Generate a summary for chapter verification.

        Args:
            chapter_number: Chapter number
            global_conflicts: List of global layer conflicts
            cognitive_conflicts: List of cognitive conflicts

        Returns:
            Summary string
        """
        total_issues = len(global_conflicts) + len(cognitive_conflicts)

        if total_issues == 0:
            return f"Chapter {chapter_number}: No consistency issues detected."

        parts: list[str] = []

        if global_conflicts:
            parts.append(f"{len(global_conflicts)} global conflict(s)")

        if cognitive_conflicts:
            parts.append(f"{len(cognitive_conflicts)} cognitive conflict(s)")

        return f"Chapter {chapter_number}: Found {', '.join(parts)}."

    def _generate_summary(
        self,
        total_facts: int,
        total_characters: int,
        global_conflicts: list[Conflict],
        cognitive_conflicts: list[CognitiveConflict],
        timeline_issues: list[Conflict],
        location_issues: list[Conflict],
    ) -> str:
        """Generate a comprehensive summary.

        Args:
            total_facts: Total number of facts
            total_characters: Total number of characters
            global_conflicts: List of global conflicts
            cognitive_conflicts: List of cognitive conflicts
            timeline_issues: List of timeline issues
            location_issues: List of location issues

        Returns:
            Summary string
        """
        total_issues = (
            len(global_conflicts)
            + len(cognitive_conflicts)
            + len(timeline_issues)
            + len(location_issues)
        )

        if total_issues == 0:
            return (
                f"Verification passed. {total_facts} facts and {total_characters} characters "
                f"checked with no issues detected."
            )

        parts: list[str] = []

        # Count by severity
        critical = sum(
            1 for c in global_conflicts if c.severity == ConflictSeverity.CRITICAL
        )
        errors = sum(
            1 for c in global_conflicts if c.severity == ConflictSeverity.ERROR
        )
        warnings = sum(
            1 for c in global_conflicts if c.severity == ConflictSeverity.WARNING
        )

        if critical > 0:
            parts.append(f"{critical} critical")
        if errors > 0:
            parts.append(f"{errors} error(s)")
        if warnings > 0:
            parts.append(f"{warnings} warning(s)")

        # Count by type
        type_parts: list[str] = []
        if timeline_issues:
            type_parts.append(f"{len(timeline_issues)} timeline")
        if location_issues:
            type_parts.append(f"{len(location_issues)} location")
        if global_conflicts:
            content_count = len(global_conflicts) - len(timeline_issues) - len(location_issues)
            if content_count > 0:
                type_parts.append(f"{content_count} content")
        if cognitive_conflicts:
            type_parts.append(f"{len(cognitive_conflicts)} cognitive")

        summary = (
            f"Verification found {', '.join(parts)} across {total_facts} facts "
            f"and {total_characters} characters."
        )

        if type_parts:
            summary += f" By type: {', '.join(type_parts)}."

        return summary

    def learn_fact_for_character(
        self,
        character_id: str,
        fact_id: str,
        chapter: int,
        source: str = "direct",
        confidence: float = 1.0,
        context: str = "",
    ) -> bool:
        """Record that a character learned a fact.

        This is a convenience method to add knowledge to a character.

        Args:
            character_id: ID of the character learning the fact
            fact_id: ID of the fact being learned
            chapter: Chapter when the fact was learned
            source: How the fact was learned ("direct", "hearsay", etc.)
            confidence: Confidence level (0.0-1.0)
            context: Optional context about how it was learned

        Returns:
            True if successfully recorded, False otherwise
        """
        if character_id not in self._character_knowledge:
            _ = self.add_character(character_id)

        return self._character_knowledge[character_id].learn_fact(
            fact_id=fact_id,
            chapter=chapter,
            source=source,
            confidence=confidence,
            context=context,
        )

    def get_character_knowledge(
        self, character_id: str
    ) -> CharacterKnowledge | None:
        """Get the CharacterKnowledge instance for a character.

        Args:
            character_id: ID of the character

        Returns:
            CharacterKnowledge instance or None if not tracked
        """
        return self._character_knowledge.get(character_id)

    @property
    def graph(self) -> CognitiveGraph:
        """Get the underlying cognitive graph."""
        return self._graph

    @property
    def global_layer(self) -> GlobalFactLayer:
        """Get the global fact layer."""
        return self._global_layer

    @property
    def character_ids(self) -> list[str]:
        """Get list of tracked character IDs."""
        return list(self._character_knowledge.keys())
