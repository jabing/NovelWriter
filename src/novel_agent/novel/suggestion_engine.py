"""Suggestion Engine Module

Provides intelligent writing suggestions based on outline data and chapter content.

This module analyzes outline data, plot threads, character appearances, and
foreshadowing elements to generate actionable suggestions for writers.

Suggestion types:
- Plot completion: Suggests plot elements that should be covered
- Character interaction: Suggests expected character interactions
- Foreshadowing recall: Reminds about unresolved foreshadowing
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.novel_agent.novel.cognitive_graph import CognitiveGraph

logger = logging.getLogger(__name__)


# Priority levels
PRIORITY_CRITICAL = 0    # Missing main plot element
PRIORITY_HIGH = 1        # Missing expected character, unresolved foreshadowing due
PRIORITY_MEDIUM = 2      # Optional plot enhancement
PRIORITY_LOW = 3         # Minor suggestion
PRIORITY_BACKLOG = 4     # Future consideration

# Foreshadowing resolution distance (chapters)
FORESHADOWING_RESOLUTION_WINDOW = 5


@dataclass
class Suggestion:
    """A single writing suggestion.
    
    Attributes:
        suggestion_type: Type of suggestion ("plot_completion", "character_interaction", "foreshadowing_recall")
        priority: Priority level (0-4, 0 = critical)
        chapter: Chapter number this suggestion applies to
        description: Human-readable description of the suggestion
        details: Additional details about the suggestion
        actionable: Whether this suggestion can be acted upon immediately
        related_plot_threads: List of plot thread IDs/content related to this suggestion
    """
    suggestion_type: str
    priority: int
    chapter: int
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    actionable: bool = True
    related_plot_threads: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the suggestion
        """
        return {
            "suggestion_type": self.suggestion_type,
            "priority": self.priority,
            "chapter": self.chapter,
            "description": self.description,
            "details": self.details,
            "actionable": self.actionable,
            "related_plot_threads": self.related_plot_threads,
        }


class SuggestionEngine:
    """Engine for generating intelligent writing suggestions.
    
    Analyzes outline data, plot threads, character appearances, and
    foreshadowing to generate actionable suggestions for writers.
    
    Usage:
        >>> from src.novel_agent.novel.outline_parser import OutlineParser
        >>> parser = OutlineParser()
        >>> outline_data = parser.parse_outline(outline_text)
        >>> 
        >>> engine = SuggestionEngine(outline_data)
        >>> suggestions = engine.get_all_suggestions(chapter_number=1, chapter_content="...")
        >>> for s in suggestions:
        ...     print(f"[{s.priority}] {s.description}")
    """
    
    def __init__(
        self,
        outline_data: dict[str, Any],
        cognitive_graph: CognitiveGraph | None = None,
    ) -> None:
        """Initialize SuggestionEngine with outline data.
        
        Args:
            outline_data: Dictionary from OutlineParser.parse_outline()
            cognitive_graph: Optional CognitiveGraph for character context
        """
        self._outline_data = outline_data
        self._cognitive_graph = cognitive_graph
        
        # Extract data from outline
        self._chapters: list[dict[str, Any]] = outline_data.get("chapters", [])
        self._plot_threads: list[dict[str, Any]] = outline_data.get("plot_threads", [])
        self._timeline: list[dict[str, Any]] = outline_data.get("timeline", [])
        
        # Track state
        self._covered_plots: set[str] = set()
        self._resolved_foreshadowing: set[str] = set()
        self._chapter_characters: dict[int, set[str]] = {}
        
        # Extract character list
        self._characters: set[str] = set(outline_data.get("characters", []))
        self._extract_characters_from_data()
        
        # Build foreshadowing index
        self._foreshadowing_index: dict[str, dict[str, Any]] = {}
        self._build_foreshadowing_index()
    
    def _extract_characters_from_data(self) -> None:
        """Extract character names from outline data."""
        # Extract from timeline events
        for event in self._timeline:
            event_text = event.get("event", "")
            for char in list(self._characters):
                if char in event_text:
                    self._characters.add(char)
        
        # Extract from plot threads
        for thread in self._plot_threads:
            content = thread.get("content", "")
            for char in list(self._characters):
                if char in content:
                    self._characters.add(char)
    
    def _build_foreshadowing_index(self) -> None:
        """Build index of foreshadowing elements."""
        for thread in self._plot_threads:
            if thread.get("type") == "foreshadowing":
                content = thread.get("content", "")
                chapter = thread.get("chapter")
                if content:
                    self._foreshadowing_index[content] = {
                        "thread": thread,
                        "introduced_chapter": chapter,
                        "resolved": False,
                    }
    
    def suggest_plot_completion(
        self,
        chapter_number: int,
        chapter_content: str,
    ) -> list[Suggestion]:
        """Generate suggestions for plot completion.
        
        Analyzes the chapter content against expected plot threads and
        suggests elements that should be covered.
        
        Args:
            chapter_number: The chapter number being analyzed
            chapter_content: The text content of the chapter
            
        Returns:
            List of suggestions for plot completion
        """
        suggestions: list[Suggestion] = []
        
        # Find unresolved plots for this chapter
        unresolved = self._find_unresolved_plots(chapter_number)
        
        for plot_info in unresolved:
            thread = plot_info["thread"]
            content = thread.get("content", "")
            thread_type = thread.get("type", "unknown")
            
            # Check if plot is covered in chapter content
            if not self._is_plot_covered(chapter_content, content):
                # Determine priority based on thread type
                if thread_type == "main":
                    priority = PRIORITY_CRITICAL
                elif thread_type == "foreshadowing":
                    priority = PRIORITY_HIGH
                else:
                    priority = PRIORITY_MEDIUM
                
                suggestion = Suggestion(
                    suggestion_type="plot_completion",
                    priority=priority,
                    chapter=chapter_number,
                    description=f"Expected plot not covered: {content}",
                    details={
                        "thread_type": thread_type,
                        "keyword": thread.get("keyword", ""),
                        "position": thread.get("position", 0),
                    },
                    actionable=True,
                    related_plot_threads=[content],
                )
                suggestions.append(suggestion)
        
        # Check for plot threads from previous chapters not yet covered
        earlier_unresolved = self._find_earlier_unresolved_plots(chapter_number)
        for plot_info in earlier_unresolved:
            content = plot_info["thread"].get("content", "")
            
            if not self._is_plot_covered(chapter_content, content):
                suggestion = Suggestion(
                    suggestion_type="plot_completion",
                    priority=PRIORITY_MEDIUM,
                    chapter=chapter_number,
                    description=f"Earlier plot may need resolution: {content}",
                    details={
                        "introduced_chapter": plot_info["introduced_chapter"],
                        "chapters_ago": chapter_number - plot_info["introduced_chapter"],
                    },
                    actionable=False,
                    related_plot_threads=[content],
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def suggest_character_interactions(
        self,
        chapter_number: int,
        characters_present: list[str],
    ) -> list[Suggestion]:
        """Generate suggestions for character interactions.
        
        Analyzes expected character appearances and suggests interactions
        that should occur in the chapter.
        
        Args:
            chapter_number: The chapter number being analyzed
            characters_present: List of character names present in the chapter
            
        Returns:
            List of suggestions for character interactions
        """
        suggestions: list[Suggestion] = []
        
        # Find expected character interactions
        expected = self._find_expected_character_interactions(chapter_number)
        
        present_set = set(characters_present)
        
        for interaction in expected:
            characters = interaction.get("characters", [])
            interaction_type = interaction.get("type", "unknown")
            description = interaction.get("description", "")
            
            # Check if all characters are present
            missing_chars = set(characters) - present_set
            
            if missing_chars:
                # Suggest adding missing characters
                suggestion = Suggestion(
                    suggestion_type="character_interaction",
                    priority=PRIORITY_HIGH,
                    chapter=chapter_number,
                    description=f"Expected character(s) missing: {', '.join(missing_chars)}",
                    details={
                        "expected_characters": list(characters),
                        "present_characters": list(present_set),
                        "missing_characters": list(missing_chars),
                        "interaction_type": interaction_type,
                    },
                    actionable=True,
                    related_plot_threads=[description],
                )
                suggestions.append(suggestion)
            elif description and interaction_type == "expected":
                # Characters present, suggest the interaction
                suggestion = Suggestion(
                    suggestion_type="character_interaction",
                    priority=PRIORITY_MEDIUM,
                    chapter=chapter_number,
                    description=f"Consider interaction between {', '.join(characters)}: {description}",
                    details={
                        "characters": characters,
                        "interaction_type": interaction_type,
                        "context": description,
                    },
                    actionable=True,
                    related_plot_threads=[],
                )
                suggestions.append(suggestion)
        
        # Use cognitive graph for additional character context
        if self._cognitive_graph:
            graph_suggestions = self._suggest_from_cognitive_graph(
                chapter_number, characters_present
            )
            suggestions.extend(graph_suggestions)
        
        return suggestions
    
    def suggest_foreshadowing_recall(
        self,
        current_chapter: int,
    ) -> list[Suggestion]:
        """Generate suggestions for foreshadowing recall.
        
        Identifies foreshadowing elements that should be resolved
        in the current or upcoming chapters.
        
        Args:
            current_chapter: The current chapter number
            
        Returns:
            List of suggestions for foreshadowing recall
        """
        suggestions: list[Suggestion] = []
        
        # Find forgotten foreshadowing
        forgotten = self._find_forgotten_foreshadowing(current_chapter)
        
        for foreshadow_info in forgotten:
            content = foreshadow_info["content"]
            introduced_chapter = foreshadow_info["introduced_chapter"]
            chapters_since = current_chapter - introduced_chapter if introduced_chapter else 0
            
            # Determine priority based on distance
            if chapters_since >= FORESHADOWING_RESOLUTION_WINDOW:
                priority = PRIORITY_HIGH
            elif chapters_since >= FORESHADOWING_RESOLUTION_WINDOW - 2:
                priority = PRIORITY_MEDIUM
            else:
                priority = PRIORITY_LOW
            
            suggestion = Suggestion(
                suggestion_type="foreshadowing_recall",
                priority=priority,
                chapter=current_chapter,
                description=f"Foreshadowing should be resolved: {content}",
                details={
                    "introduced_chapter": introduced_chapter,
                    "chapters_since_introduction": chapters_since,
                    "original_context": foreshadow_info.get("context", ""),
                },
                actionable=True,
                related_plot_threads=[content],
            )
            suggestions.append(suggestion)
        
        # Suggest setup for future foreshadowing
        future_suggestions = self._suggest_future_foreshadowing(current_chapter)
        suggestions.extend(future_suggestions)
        
        return suggestions
    
    def get_all_suggestions(
        self,
        chapter_number: int,
        chapter_content: str,
    ) -> list[Suggestion]:
        """Get all suggestions for a chapter.
        
        Combines plot completion, character interaction, and
        foreshadowing recall suggestions.
        
        Args:
            chapter_number: The chapter number being analyzed
            chapter_content: The text content of the chapter
            
        Returns:
            List of all suggestions, prioritized
        """
        all_suggestions: list[Suggestion] = []
        
        # Get plot completion suggestions
        plot_suggestions = self.suggest_plot_completion(
            chapter_number, chapter_content
        )
        all_suggestions.extend(plot_suggestions)
        
        # Detect characters in content
        characters_present = self._detect_characters(chapter_content)
        
        # Get character interaction suggestions
        character_suggestions = self.suggest_character_interactions(
            chapter_number, characters_present
        )
        all_suggestions.extend(character_suggestions)
        
        # Get foreshadowing recall suggestions
        foreshadowing_suggestions = self.suggest_foreshadowing_recall(
            chapter_number
        )
        all_suggestions.extend(foreshadowing_suggestions)
        
        # Prioritize and return
        return self._prioritize_suggestions(all_suggestions)
    
    def mark_plot_covered(self, plot_content: str) -> None:
        """Mark a plot element as covered.
        
        Args:
            plot_content: Content of the plot thread to mark as covered
        """
        self._covered_plots.add(plot_content)
    
    def mark_foreshadowing_resolved(self, foreshadowing_content: str) -> None:
        """Mark a foreshadowing element as resolved.
        
        Args:
            foreshadowing_content: Content of the foreshadowing to mark as resolved
        """
        self._resolved_foreshadowing.add(foreshadowing_content)
        if foreshadowing_content in self._foreshadowing_index:
            self._foreshadowing_index[foreshadowing_content]["resolved"] = True
    
    def _find_unresolved_plots(self, chapter_number: int) -> list[dict[str, Any]]:
        """Find plot threads expected for this chapter that are not covered.
        
        Args:
            chapter_number: The chapter number
            
        Returns:
            List of unresolved plot info dictionaries
        """
        unresolved: list[dict[str, Any]] = []
        
        for thread in self._plot_threads:
            thread_chapter = thread.get("chapter")
            content = thread.get("content", "")
            
            if thread_chapter == chapter_number and content not in self._covered_plots:
                unresolved.append({
                    "thread": thread,
                    "introduced_chapter": thread_chapter,
                })
        
        return unresolved
    
    def _find_earlier_unresolved_plots(
        self, chapter_number: int
    ) -> list[dict[str, Any]]:
        """Find plot threads from earlier chapters not yet covered.
        
        Args:
            chapter_number: The current chapter number
            
        Returns:
            List of earlier unresolved plot info dictionaries
        """
        unresolved: list[dict[str, Any]] = []
        
        for thread in self._plot_threads:
            thread_chapter = thread.get("chapter")
            content = thread.get("content", "")
            thread_type = thread.get("type", "")
            
            # Only check main plots and foreshadowing from earlier chapters
            if (
                thread_chapter is not None
                and thread_chapter < chapter_number
                and thread_type in ("main", "foreshadowing")
                and content not in self._covered_plots
            ):
                unresolved.append({
                    "thread": thread,
                    "introduced_chapter": thread_chapter,
                })
        
        return unresolved
    
    def _find_expected_character_interactions(
        self, chapter_number: int
    ) -> list[dict[str, Any]]:
        """Find expected character interactions for a chapter.
        
        Analyzes plot threads and timeline events to determine
        expected character interactions.
        
        Args:
            chapter_number: The chapter number
            
        Returns:
            List of expected interaction dictionaries
        """
        interactions: list[dict[str, Any]] = []
        
        # Get characters expected from plot threads
        thread_characters: set[str] = set()
        for thread in self._plot_threads:
            if thread.get("chapter") == chapter_number:
                content = thread.get("content", "")
                for char in self._characters:
                    if char in content:
                        thread_characters.add(char)
        
        # Get characters expected from timeline
        timeline_characters: set[str] = set()
        for event in self._timeline:
            if event.get("chapter") == chapter_number:
                event_text = event.get("event", "")
                for char in self._characters:
                    if char in event_text:
                        timeline_characters.add(char)
        
        # Combine and create interaction suggestions
        all_expected = thread_characters | timeline_characters
        
        if len(all_expected) >= 2:
            interactions.append({
                "characters": list(all_expected),
                "type": "expected",
                "description": "Characters expected to interact in this chapter",
            })
        elif len(all_expected) == 1:
            interactions.append({
                "characters": list(all_expected),
                "type": "single",
                "description": f"Character expected: {list(all_expected)[0]}",
            })
        
        # Check for expected character pairs from plot relationships
        pair_interactions = self._find_character_pairs(chapter_number)
        interactions.extend(pair_interactions)
        
        return interactions
    
    def _find_character_pairs(self, chapter_number: int) -> list[dict[str, Any]]:
        """Find expected character pairs for interaction.
        
        Args:
            chapter_number: The chapter number
            
        Returns:
            List of character pair interaction dictionaries
        """
        pairs: list[dict[str, Any]] = []
        
        # Look for character pairs in plot threads
        for thread in self._plot_threads:
            if thread.get("chapter") == chapter_number:
                content = thread.get("content", "")
                found_chars = [c for c in self._characters if c in content]
                
                if len(found_chars) >= 2:
                    # Found a potential interaction pair
                    pairs.append({
                        "characters": found_chars[:2],  # Take first two
                        "type": "plot_interaction",
                        "description": content,
                    })
        
        return pairs
    
    def _find_forgotten_foreshadowing(
        self, current_chapter: int
    ) -> list[dict[str, Any]]:
        """Find foreshadowing elements that should be resolved.
        
        Args:
            current_chapter: The current chapter number
            
        Returns:
            List of forgotten foreshadowing info dictionaries
        """
        forgotten: list[dict[str, Any]] = []
        
        for content, info in self._foreshadowing_index.items():
            if info.get("resolved"):
                continue
            
            if content in self._resolved_foreshadowing:
                continue
            
            introduced_chapter = info.get("introduced_chapter")
            
            if introduced_chapter is not None:
                chapters_since = current_chapter - introduced_chapter
                
                # Suggest resolution if it's been a while
                if chapters_since >= FORESHADOWING_RESOLUTION_WINDOW - 2:
                    forgotten.append({
                        "content": content,
                        "introduced_chapter": introduced_chapter,
                        "context": info.get("thread", {}).get("keyword", ""),
                    })
        
        return forgotten
    
    def _suggest_future_foreshadowing(
        self, current_chapter: int
    ) -> list[Suggestion]:
        """Suggest setting up new foreshadowing elements.
        
        Args:
            current_chapter: The current chapter number
            
        Returns:
            List of suggestions for future foreshadowing
        """
        suggestions: list[Suggestion] = []
        
        # Look for plot threads in future chapters that could be foreshadowed
        future_chapters = range(current_chapter + 1, current_chapter + 4)
        
        for future_ch in future_chapters:
            future_threads = [
                t for t in self._plot_threads
                if t.get("chapter") == future_ch and t.get("type") == "main"
            ]
            
            for thread in future_threads:
                content = thread.get("content", "")
                
                # Suggest setting up foreshadowing for main plot
                suggestion = Suggestion(
                    suggestion_type="foreshadowing_recall",
                    priority=PRIORITY_LOW,
                    chapter=current_chapter,
                    description=f"Consider foreshadowing upcoming plot: {content}",
                    details={
                        "future_chapter": future_ch,
                        "suggestion_type": "setup",
                    },
                    actionable=False,
                    related_plot_threads=[content],
                )
                suggestions.append(suggestion)
        
        return suggestions[:3]  # Limit to 3 future suggestions
    
    def _suggest_from_cognitive_graph(
        self,
        chapter_number: int,
        characters_present: list[str],
    ) -> list[Suggestion]:
        """Generate suggestions using cognitive graph.
        
        Args:
            chapter_number: The chapter number
            characters_present: List of character names present
            
        Returns:
            List of suggestions based on cognitive graph analysis
        """
        suggestions: list[Suggestion] = []
        
        if not self._cognitive_graph:
            return suggestions
        
        for char in characters_present:
            # Get character's knowledge
            knowledge = self._cognitive_graph.get_character_knowledge(char)
            
            for fact_data, confidence, source in knowledge:
                # Check if this knowledge could create interesting dynamics
                if confidence > 0.5 and fact_data.get("fact_type") == "secret":
                    suggestion = Suggestion(
                        suggestion_type="character_interaction",
                        priority=PRIORITY_MEDIUM,
                        chapter=chapter_number,
                        description=f"Character {char} knows a secret that could be revealed",
                        details={
                            "character": char,
                            "fact_type": fact_data.get("fact_type"),
                            "confidence": confidence,
                            "source": source,
                        },
                        actionable=False,
                        related_plot_threads=[],
                    )
                    suggestions.append(suggestion)
        
        return suggestions[:5]  # Limit suggestions
    
    def _prioritize_suggestions(
        self, suggestions: list[Suggestion]
    ) -> list[Suggestion]:
        """Sort suggestions by priority.
        
        Args:
            suggestions: List of suggestions to prioritize
            
        Returns:
            Sorted list of suggestions (highest priority first)
        """
        return sorted(suggestions, key=lambda s: s.priority)
    
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
        # Check if already marked as covered
        if plot_content in self._covered_plots:
            return True
        
        # Extract keywords from plot content
        keywords = self._extract_keywords(plot_content)
        
        if not keywords:
            return False
        
        # Check keyword coverage
        matches = 0
        for kw in keywords:
            if kw in chapter_content:
                matches += 1
        
        coverage = matches / len(keywords) if keywords else 0
        
        return coverage >= 0.4  # At least 40% of keywords present
    
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
        
        # Split by punctuation/whitespace
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
        
        # Extract keywords
        keywords: list[str] = []
        for segment in segments:
            if len(segment) < 2:
                continue
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
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the suggestion engine state.
        
        Returns:
            Dictionary with summary statistics
        """
        total_threads = len(self._plot_threads)
        covered_threads = len(self._covered_plots)
        
        total_foreshadowing = len(self._foreshadowing_index)
        resolved_foreshadowing = len(self._resolved_foreshadowing)
        
        return {
            "total_plot_threads": total_threads,
            "covered_plot_threads": covered_threads,
            "uncovered_plot_threads": total_threads - covered_threads,
            "total_foreshadowing": total_foreshadowing,
            "resolved_foreshadowing": resolved_foreshadowing,
            "unresolved_foreshadowing": total_foreshadowing - resolved_foreshadowing,
            "tracked_characters": len(self._characters),
        }
    
    def reset_state(self) -> None:
        """Reset the engine state for a fresh analysis."""
        self._covered_plots.clear()
        self._resolved_foreshadowing.clear()
        self._chapter_characters.clear()
        
        for key in self._foreshadowing_index:
            self._foreshadowing_index[key]["resolved"] = False
