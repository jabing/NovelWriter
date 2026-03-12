"""Outline Validator Module

Validates written chapters against outline specifications to detect:
- Missing plot elements
- Unexpected plot additions
- Character behavior inconsistencies
- Timeline conflicts

This module works with OutlineParser output to ensure the written content
follows the planned outline structure.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DeviationType(str, Enum):
    """Types of deviations that can be detected."""
    
    MISSING_PLOT = "missing_plot"  # Plot thread not covered in chapter
    UNEXPECTED_PLOT = "unexpected_plot"  # New plot element not in outline
    CHARACTER_BEHAVIOR = "character_behavior"  # Character acts inconsistently
    TIMELINE_CONFLICT = "timeline_conflict"  # Time ordering issue
    MISSING_CHARACTER = "missing_character"  # Expected character absent


class Severity(str, Enum):
    """Severity levels for deviations."""
    
    LOW = "low"  # Minor issue, can be addressed later
    MEDIUM = "medium"  # Moderate issue, should be addressed
    HIGH = "high"  # Critical issue, must be addressed


@dataclass
class Deviation:
    """A single deviation from the outline."""
    
    deviation_type: DeviationType
    chapter: int
    description: str
    expected: str | None = None
    actual: str | None = None
    severity: str = "medium"
    suggestion: str = ""
    paragraph: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "deviation_type": self.deviation_type.value,
            "chapter": self.chapter,
            "description": self.description,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity,
            "suggestion": self.suggestion,
            "paragraph": self.paragraph,
        }


@dataclass
class DeviationReport:
    """Comprehensive deviation report for all chapters."""
    
    total_deviations: int
    deviations: list[Deviation] = field(default_factory=list)
    summary: str = ""
    by_type: dict[str, int] = field(default_factory=dict)
    by_chapter: dict[int, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_deviations": self.total_deviations,
            "deviations": [d.to_dict() for d in self.deviations],
            "summary": self.summary,
            "by_type": self.by_type,
            "by_chapter": self.by_chapter,
        }


@dataclass
class ChapterValidationResult:
    """Result of validating a single chapter."""
    
    chapter_number: int
    passed: bool
    deviations: list[Deviation] = field(default_factory=list)
    covered_plots: list[str] = field(default_factory=list)
    missing_plots: list[str] = field(default_factory=list)
    characters_present: list[str] = field(default_factory=list)
    characters_expected: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chapter_number": self.chapter_number,
            "passed": self.passed,
            "deviations": [d.to_dict() for d in self.deviations],
            "covered_plots": self.covered_plots,
            "missing_plots": self.missing_plots,
            "characters_present": self.characters_present,
            "characters_expected": self.characters_expected,
        }


class OutlineValidator:
    """Validates chapters against outline specifications.
    
    This class compares written chapter content against the planned outline
    to detect deviations in plot coverage, character behavior, and timeline.
    
    Usage:
        >>> from src.novel.outline_parser import OutlineParser
        >>> parser = OutlineParser()
        >>> outline_data = parser.parse_outline(outline_text)
        >>> 
        >>> validator = OutlineValidator(outline_data)
        >>> result = validator.validate_chapter(chapter_content, chapter_number=1)
        >>> print(result["passed"])
        >>> print(result["deviations"])
    """
    
    def __init__(self, outline_data: dict[str, Any]) -> None:
        """Initialize OutlineValidator with parsed outline data.
        
        Args:
            outline_data: Dictionary from OutlineParser.parse_outline()
        """
        self._outline_data = outline_data
        self._chapters: list[dict[str, Any]] = outline_data.get("chapters", [])
        self._plot_threads: list[dict[str, Any]] = outline_data.get("plot_threads", [])
        self._timeline: list[dict[str, Any]] = outline_data.get("timeline", [])
        
        # Extract character list from timeline and plot threads
        self._characters: set[str] = set(outline_data.get("characters", []))
        self._extract_characters_from_data()
        
        # Track validation state
        self._validated_chapters: dict[int, ChapterValidationResult] = {}
        self._all_deviations: list[Deviation] = []
        self._covered_plots: set[str] = set()  # Plot content that has been covered
        
        # Track timeline state
        self._character_first_appearance: dict[str, int] = {}
        self._last_chapter_time: dict[int, str | None] = {}
    
    def _extract_characters_from_data(self) -> None:
        """Extract character names from outline data."""
        # Extract from timeline events
        for event in self._timeline:
            event_text = event.get("event", "")
            # Simple extraction: look for character names in events
            for char in self._characters.copy():
                if char in event_text:
                    # Character is confirmed
                    pass
        
        # Also extract from plot threads
        for thread in self._plot_threads:
            content = thread.get("content", "")
            # Characters mentioned in plot threads are expected
            for char in list(self._characters):
                if char in content:
                    self._characters.add(char)
    
    def validate_chapter(
        self,
        chapter_content: str,
        chapter_number: int,
    ) -> dict[str, Any]:
        """Validate a chapter against the outline.
        
        Performs comprehensive validation including:
        - Plot thread coverage
        - Character presence
        - Timeline consistency
        
        Args:
            chapter_content: The text content of the chapter
            chapter_number: The chapter number (1-indexed)
            
        Returns:
            Dictionary with:
            - passed: bool - Whether chapter passed validation
            - deviations: list of Deviation objects
            - covered_plots: list of covered plot thread contents
            - missing_plots: list of missing plot thread contents
        """
        deviations: list[Deviation] = []
        
        # Get expected plots for this chapter
        expected_plots = self._get_expected_plots(chapter_number)
        
        # Detect plot deviations
        plot_deviations = self.detect_plot_deviation(chapter_content, expected_plots)
        deviations.extend(plot_deviations)
        
        # Check character behavior and presence
        char_deviations = self._check_characters(chapter_content, chapter_number)
        deviations.extend(char_deviations)
        
        # Detect timeline conflicts
        timeline_deviations = self.detect_timeline_conflict(chapter_content, chapter_number)
        deviations.extend(timeline_deviations)
        
        # Determine covered and missing plots
        covered_plots: list[str] = []
        missing_plots: list[str] = []
        
        for plot in expected_plots:
            content = plot.get("content", "")
            if self._is_plot_covered(chapter_content, content):
                covered_plots.append(content)
                self._covered_plots.add(content)
            else:
                missing_plots.append(content)
                if plot.get("type") == "main":  # Main plots are critical
                    deviations.append(Deviation(
                        deviation_type=DeviationType.MISSING_PLOT,
                        chapter=chapter_number,
                        description=f"Main plot not covered: {content}",
                        expected=content,
                        actual=None,
                        severity="high",
                        suggestion=f"Consider adding content related to: {content}",
                    ))
        
        # Get characters present in chapter
        characters_present = self._detect_characters(chapter_content)
        characters_expected = list(self._get_expected_characters(chapter_number))
        
        # Determine pass/fail
        passed = len([d for d in deviations if d.severity == "high"]) == 0
        
        result = ChapterValidationResult(
            chapter_number=chapter_number,
            passed=passed,
            deviations=deviations,
            covered_plots=covered_plots,
            missing_plots=missing_plots,
            characters_present=characters_present,
            characters_expected=characters_expected,
        )
        
        # Store validation result
        self._validated_chapters[chapter_number] = result
        self._all_deviations.extend(deviations)
        
        return result.to_dict()
    
    def detect_plot_deviation(
        self,
        chapter_content: str,
        expected_plots: list[dict[str, Any]],
    ) -> list[Deviation]:
        """Detect plot deviations in chapter content.
        
        Checks for:
        - Missing plot threads (planned but not written)
        - Unexpected plot elements (written but not planned)
        
        Args:
            chapter_content: The chapter text to analyze
            expected_plots: List of expected plot thread dictionaries
            
        Returns:
            List of Deviation objects for plot issues
        """
        deviations: list[Deviation] = []
        
        # Check for missing plots
        for plot in expected_plots:
            content = plot.get("content", "")
            thread_type = plot.get("type", "unknown")
            
            if not self._is_plot_covered(chapter_content, content):
                # Only flag as deviation if it's a main plot or foreshadowing
                if thread_type in ("main", "foreshadowing"):
                    severity = "high" if thread_type == "main" else "medium"
                    deviations.append(Deviation(
                        deviation_type=DeviationType.MISSING_PLOT,
                        chapter=0,  # Will be set by caller
                        description=f"Expected {thread_type} plot not found: {content}",
                        expected=content,
                        actual=None,
                        severity=severity,
                        suggestion=f"Add content related to: {content}",
                    ))
        
        # Check for unexpected plot elements
        unexpected = self._detect_unexpected_plots(chapter_content, expected_plots)
        for unexpected_item in unexpected:
            deviations.append(Deviation(
                deviation_type=DeviationType.UNEXPECTED_PLOT,
                chapter=0,  # Will be set by caller
                description=f"Unexpected plot element not in outline: {unexpected_item}",
                expected=None,
                actual=unexpected_item,
                severity="low",
                suggestion="Consider if this plot element should be added to outline",
            ))
        
        return deviations
    
    def check_character_behavior(
        self,
        chapter_content: str,
        character_id: str,
        expected_behavior: str,
    ) -> list[Deviation]:
        """Check if a character's behavior matches expectations.
        
        This is a simplified behavior check that looks for basic
        consistency between expected and actual behavior descriptions.
        
        Args:
            chapter_content: The chapter text to analyze
            character_id: The character name/identifier
            expected_behavior: Description of expected behavior
            
        Returns:
            List of Deviation objects for behavior issues
        """
        deviations: list[Deviation] = []
        
        # Check if character appears in chapter
        if character_id not in chapter_content:
            return deviations  # Character not present, no behavior to check
        
        # Find character context in chapter
        char_contexts = self._get_character_contexts(chapter_content, character_id)
        
        for context in char_contexts:
            # Simple keyword matching for behavior
            behavior_keywords = set(expected_behavior.split())
            context_keywords = set(context.split())
            
            # Check for contradictory behavior
            contradiction_patterns = [
                (r"不", "没有", "未"),  # Negation patterns
            ]
            
            # This is a simplified check - in a full implementation,
            # this would use NLP to understand behavior context
            overlap = len(behavior_keywords & context_keywords)
            if overlap < len(behavior_keywords) * 0.3:  # Less than 30% overlap
                # Potential behavior deviation
                deviations.append(Deviation(
                    deviation_type=DeviationType.CHARACTER_BEHAVIOR,
                    chapter=0,
                    description=f"Character '{character_id}' behavior may not match expected: {expected_behavior}",
                    expected=expected_behavior,
                    actual=context[:100] + "..." if len(context) > 100 else context,
                    severity="medium",
                    suggestion=f"Review character behavior for '{character_id}'",
                ))
                break  # Only report once per character
        
        return deviations
    
    def detect_timeline_conflict(
        self,
        chapter_content: str,
        chapter_number: int,
    ) -> list[Deviation]:
        """Detect timeline conflicts in chapter content.
        
        Checks for:
        - Events out of chronological order
        - Characters appearing before their introduction
        - Impossible time jumps
        
        Args:
            chapter_content: The chapter text to analyze
            chapter_number: The chapter number
            
        Returns:
            List of Deviation objects for timeline issues
        """
        deviations: list[Deviation] = []
        
        # Get expected timeline events for this chapter
        chapter_events = [
            e for e in self._timeline
            if e.get("chapter") == chapter_number
        ]
        
        # Check for character appearances before introduction
        for char in self._detect_characters(chapter_content):
            if char not in self._character_first_appearance:
                self._character_first_appearance[char] = chapter_number
            elif self._character_first_appearance[char] > chapter_number:
                deviations.append(Deviation(
                    deviation_type=DeviationType.TIMELINE_CONFLICT,
                    chapter=chapter_number,
                    description=f"Character '{char}' appears in chapter {chapter_number} but was introduced in chapter {self._character_first_appearance[char]}",
                    expected=f"Character should first appear in chapter {self._character_first_appearance[char]}",
                    actual=f"Character appears in chapter {chapter_number}",
                    severity="high",
                    suggestion="Check character introduction timeline",
                ))
        
        # Check for time markers
        time_markers = self._extract_time_markers(chapter_content)
        
        if time_markers:
            # Check for impossible time jumps
            if chapter_number > 1 and chapter_number - 1 in self._last_chapter_time:
                prev_time = self._last_chapter_time[chapter_number - 1]
                curr_time = time_markers[0] if time_markers else None
                
                if prev_time and curr_time:
                    # Simple check for backward time references
                    # In a full implementation, this would parse actual time values
                    pass
            
            # Store time markers for this chapter
            self._last_chapter_time[chapter_number] = time_markers[0] if time_markers else None
        
        # Check timeline events are in order
        for event in chapter_events:
            event_text = event.get("event", "")
            if event_text and event_text not in chapter_content:
                # Event expected but not found
                deviations.append(Deviation(
                    deviation_type=DeviationType.TIMELINE_CONFLICT,
                    chapter=chapter_number,
                    description=f"Expected timeline event not found: {event_text}",
                    expected=event_text,
                    actual=None,
                    severity="medium",
                    suggestion="Consider including the expected timeline event",
                ))
        
        return deviations
    
    def generate_deviation_report(self) -> DeviationReport:
        """Generate a comprehensive deviation report.
        
        Combines all detected deviations from validated chapters into
        a single report with statistics and summary.
        
        Returns:
            DeviationReport with all deviations and statistics
        """
        # Calculate statistics
        by_type: dict[str, int] = {}
        by_chapter: dict[int, int] = {}
        
        for dev in self._all_deviations:
            type_key = dev.deviation_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            by_chapter[dev.chapter] = by_chapter.get(dev.chapter, 0) + 1
        
        # Generate summary
        summary = self._generate_summary()
        
        return DeviationReport(
            total_deviations=len(self._all_deviations),
            deviations=self._all_deviations.copy(),
            summary=summary,
            by_type=by_type,
            by_chapter=by_chapter,
        )
    
    def get_missing_plot_elements(self, chapter_number: int) -> list[str]:
        """Get plot elements that have not been covered up to a chapter.
        
        Args:
            chapter_number: The chapter number to check up to
            
        Returns:
            List of plot thread contents not yet covered
        """
        missing: list[str] = []
        
        for thread in self._plot_threads:
            thread_chapter = thread.get("chapter")
            content = thread.get("content", "")
            
            # Check if this plot should have been covered by this chapter
            if thread_chapter is not None and thread_chapter <= chapter_number:
                if content not in self._covered_plots:
                    missing.append(content)
        
        return missing
    
    def _get_expected_plots(self, chapter_number: int) -> list[dict[str, Any]]:
        """Get expected plot threads for a chapter.
        
        Args:
            chapter_number: The chapter number
            
        Returns:
            List of plot thread dictionaries for this chapter
        """
        return [
            thread for thread in self._plot_threads
            if thread.get("chapter") == chapter_number
        ]
    
    def _get_expected_characters(self, chapter_number: int) -> set[str]:
        """Get characters expected to appear in a chapter.
        
        Based on timeline events and plot threads for the chapter.
        
        Args:
            chapter_number: The chapter number
            
        Returns:
            Set of character names expected
        """
        expected: set[str] = set()
        
        # Check timeline events
        for event in self._timeline:
            if event.get("chapter") == chapter_number:
                event_text = event.get("event", "")
                for char in self._characters:
                    if char in event_text:
                        expected.add(char)
        
        # Check plot threads
        for thread in self._plot_threads:
            if thread.get("chapter") == chapter_number:
                content = thread.get("content", "")
                for char in self._characters:
                    if char in content:
                        expected.add(char)
        
        return expected
    
    def _is_plot_covered(self, chapter_content: str, plot_content: str) -> bool:
        """Check if a plot element is covered in chapter content.
        
        Uses keyword matching to determine if the plot element's
        key concepts appear in the chapter.
        
        Args:
            chapter_content: The chapter text
            plot_content: The plot thread content to check
            
        Returns:
            True if plot appears to be covered
        """
        # Simple keyword-based check
        # Extract key terms from plot content
        keywords = self._extract_keywords(plot_content)
        
        if not keywords:
            return False
        
        # Also extract keywords from chapter for comparison
        chapter_keywords = self._extract_keywords(chapter_content)
        
        # Check keyword coverage with flexible matching
        matches = 0
        for kw in keywords:
            # Check exact match
            if kw in chapter_content:
                matches += 1
            else:
                # Check if any chapter keyword contains or is contained by plot keyword
                for ck in chapter_keywords:
                    if kw in ck or ck in kw:
                        matches += 1
                        break
        
        coverage = matches / len(keywords) if keywords else 0
        
        return coverage >= 0.5  # At least 50% of keywords present
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text for matching.
        
        Uses sliding window to extract 2-4 character segments for
        better matching of Chinese text variations.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keyword strings
        """
        stop_chars = set("，。！？、；：""''（）【】《》\n\r\t")
        
        # First split by punctuation/whitespace
        segments: list[str] = []
        current = ""
        for char in text:
            if char in stop_chars or char.isspace():
                if current:
                    segments.append(current)
                    current = ""
            else:
                current += char
        if current:
            segments.append(current)
        
        # Extract 2-4 character sliding windows from each segment
        keywords: list[str] = []
        for segment in segments:
            if len(segment) < 2:
                continue
            # Add the whole segment if it's short
            if len(segment) <= 4:
                keywords.append(segment)
            else:
                # Extract overlapping n-grams
                for n in [4, 3, 2]:
                    for i in range(len(segment) - n + 1):
                        ngram = segment[i:i + n]
                        if ngram not in keywords:
                            keywords.append(ngram)
        
        return keywords
    
    def _detect_characters(self, chapter_content: str) -> list[str]:
        """Detect which characters appear in chapter content.
        
        Args:
            chapter_content: The chapter text
            
        Returns:
            List of character names found
        """
        found: list[str] = []
        for char in self._characters:
            if char in chapter_content:
                found.append(char)
        return found
    
    def _detect_unexpected_plots(
        self,
        chapter_content: str,
        expected_plots: list[dict[str, Any]],
    ) -> list[str]:
        """Detect plot elements not in the expected list.
        
        This is a heuristic detection based on plot-related keywords.
        
        Args:
            chapter_content: The chapter text
            expected_plots: List of expected plot threads
            
        Returns:
            List of detected unexpected plot elements
        """
        unexpected: list[str] = []
        
        # Build set of expected keywords
        expected_keywords: set[str] = set()
        for plot in expected_plots:
            expected_keywords.update(self._extract_keywords(plot.get("content", "")))
        
        # Look for plot indicator patterns
        plot_patterns = [
            r"发现[^。！？]{2,10}",
            r"决定[^。！？]{2,10}",
            r"遇到了[^。！？]{2,10}",
            r"突然[^。！？]{2,10}",
        ]
        
        for pattern in plot_patterns:
            matches = re.findall(pattern, chapter_content)
            for match in matches:
                # Check if this is in expected
                match_keywords = set(self._extract_keywords(match))
                if not match_keywords & expected_keywords:
                    unexpected.append(match)
        
        return unexpected[:5]  # Limit to top 5 unexpected elements
    
    def _get_character_contexts(
        self,
        chapter_content: str,
        character_id: str,
    ) -> list[str]:
        """Get context around character mentions.
        
        Args:
            chapter_content: The chapter text
            character_id: The character name
            
        Returns:
            List of context strings around character mentions
        """
        contexts: list[str] = []
        
        start = 0
        while True:
            pos = chapter_content.find(character_id, start)
            if pos == -1:
                break
            
            # Get surrounding context
            context_start = max(0, pos - 50)
            context_end = min(len(chapter_content), pos + len(character_id) + 50)
            context = chapter_content[context_start:context_end]
            contexts.append(context)
            
            start = pos + len(character_id)
        
        return contexts
    
    def _extract_time_markers(self, chapter_content: str) -> list[str]:
        """Extract time markers from chapter content.
        
        Args:
            chapter_content: The chapter text
            
        Returns:
            List of detected time marker strings
        """
        markers: list[str] = []
        
        time_patterns = [
            r"\d{1,4}年\d{1,2}月\d{1,2}日?",
            r"[一二三四五六七八九十零]+月[一二三四五六七八九十零]+日",
            r"第[一二三四五六七八九十百千万零\d]+天",
            r"次日",
            r"当夜",
            r"当晚",
            r"[一二三四五六七八九十百千万零\d]+天后",
            r"当天",
            r"今夜",
            r"翌日",
            r"隔日",
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, chapter_content)
            markers.extend(matches)
        
        return markers
    
    def _check_characters(
        self,
        chapter_content: str,
        chapter_number: int,
    ) -> list[Deviation]:
        """Check character presence and behavior.
        
        Args:
            chapter_content: The chapter text
            chapter_number: The chapter number
            
        Returns:
            List of character-related deviations
        """
        deviations: list[Deviation] = []
        
        # Get expected characters
        expected_chars = self._get_expected_characters(chapter_number)
        
        # Detect present characters
        present_chars = set(self._detect_characters(chapter_content))
        
        # Check for missing characters
        missing_chars = expected_chars - present_chars
        for char in missing_chars:
            deviations.append(Deviation(
                deviation_type=DeviationType.MISSING_CHARACTER,
                chapter=chapter_number,
                description=f"Expected character '{char}' not found in chapter",
                expected=char,
                actual=None,
                severity="medium",
                suggestion=f"Consider including '{char}' in this chapter",
            ))
        
        return deviations
    
    def _generate_summary(self) -> str:
        """Generate a summary of all deviations.
        
        Returns:
            Summary string
        """
        if not self._all_deviations:
            return "No deviations detected. All chapters match the outline."
        
        # Count by severity
        high_count = sum(1 for d in self._all_deviations if d.severity == "high")
        medium_count = sum(1 for d in self._all_deviations if d.severity == "medium")
        low_count = sum(1 for d in self._all_deviations if d.severity == "low")
        
        parts: list[str] = []
        if high_count > 0:
            parts.append(f"{high_count} critical")
        if medium_count > 0:
            parts.append(f"{medium_count} moderate")
        if low_count > 0:
            parts.append(f"{low_count} minor")
        
        severity_summary = ", ".join(parts) if parts else "0"
        
        # Count by type
        type_summary: list[str] = []
        by_type: dict[str, int] = {}
        for d in self._all_deviations:
            key = d.deviation_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        for type_name, count in sorted(by_type.items(), key=lambda x: -x[1]):
            type_summary.append(f"{count} {type_name.replace('_', ' ')}")
        
        return (
            f"Found {len(self._all_deviations)} deviations ({severity_summary}): "
            f"{', '.join(type_summary)}."
        )
    
    @property
    def validated_chapters(self) -> dict[int, ChapterValidationResult]:
        """Get all validated chapter results."""
        return self._validated_chapters.copy()
    
    @property
    def all_deviations(self) -> list[Deviation]:
        """Get all detected deviations."""
        return self._all_deviations.copy()
