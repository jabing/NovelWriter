"""Hierarchical story state management for 100+ chapter novels.

This module provides a three-tier memory architecture:
- Global state (always in memory, ~500 tokens)
- Arc summaries (LRU cached, 10 chapters each, ~400 tokens each)
- Chapter summaries (LRU cached, ~250 tokens each)

The hierarchical approach allows efficient context management for very long
novels while keeping memory usage bounded.
"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.novel_agent.novel.compression import COMPRESSION_THRESHOLDS, SummaryCompressor
from src.novel_agent.novel.continuity import CharacterState, PlotThread
from src.novel_agent.novel.summaries import ArcSummary, ChapterSummary
from src.novel_agent.novel.token_budget import ContextSlice, TokenBudget, TokenBudgetManager

logger = logging.getLogger(__name__)

# Constants for hierarchical state management
CHAPTERS_PER_ARC = 10  # Each arc covers 10 chapters
MAX_CACHED_CHAPTERS = 10  # Maximum chapter summaries in memory
MAX_CACHED_ARCS = 3  # Maximum arc summaries in memory


@dataclass
class GlobalStoryState:
    """Persistent global state across all chapters.

    This state is always kept in memory (~500 tokens) and contains the
    essential information needed for continuity across the entire novel.

    Attributes:
        novel_id: Unique identifier for the novel
        genre: Genre of the novel (fantasy, scifi, romance, etc.)
        main_characters: Dictionary of main character states
        world_rules: Dictionary of world-building rules
        main_plot_threads: List of main plot threads
        current_arc: Current arc number (1-indexed)
        total_chapters: Total chapters written so far
        style_guide: Writing style guidelines
        created_at: When this state was created
        updated_at: When this state was last updated
    """

    novel_id: str
    genre: str
    main_characters: dict[str, CharacterState] = field(default_factory=dict)
    world_rules: dict[str, Any] = field(default_factory=dict)
    main_plot_threads: list[PlotThread] = field(default_factory=list)
    current_arc: int = 1
    total_chapters: int = 0
    style_guide: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class HierarchicalStoryState:
    """Three-tier story state with lazy loading and LRU caching.

    This class manages story state across potentially 100+ chapters by using
    a hierarchical approach:

    1. Global state: Always in memory, contains essential continuity info
    2. Arc summaries: Cached summaries of 10-chapter arcs
    3. Chapter summaries: Cached individual chapter summaries

    The LRU caching ensures memory usage stays bounded while providing
    fast access to recently used content.

    Attributes:
        storage_path: Base path for storing state files
        global_state: The global story state (always loaded)
        current_chapter: The current chapter being processed
    """

    def __init__(
        self,
        storage_path: Path,
        novel_id: str,
        maxsize_chapters: int = MAX_CACHED_CHAPTERS,
        maxsize_arcs: int = MAX_CACHED_ARCS,
        enable_compression: bool = True,
        compressor: SummaryCompressor | None = None,
    ) -> None:
        """Initialize hierarchical story state.

        Args:
            storage_path: Base directory for storing state files
            novel_id: Unique identifier for the novel
            maxsize_chapters: Maximum number of chapter summaries to cache
            maxsize_arcs: Maximum number of arc summaries to cache
            enable_compression: Whether to enable summary compression
            compressor: Optional SummaryCompressor instance
        """
        self.storage_path = storage_path / novel_id
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Store cache limits
        self._maxsize_chapters = maxsize_chapters
        self._maxsize_arcs = maxsize_arcs

        # Compression settings
        self._enable_compression = enable_compression
        self._compressor = compressor or SummaryCompressor(enable_llm=False)

        # Create subdirectories for organization
        (self.storage_path / "arcs").mkdir(exist_ok=True)
        (self.storage_path / "chapters").mkdir(exist_ok=True)

        # Global state (always in memory)
        self.global_state: GlobalStoryState | None = None

        # Cached summaries (LRU - least recently used eviction)
        self._arc_cache: OrderedDict[int, ArcSummary] = OrderedDict()
        self._chapter_cache: OrderedDict[int, ChapterSummary] = OrderedDict()

        # Current chapter being processed
        self.current_chapter: int = 0

        # Load or initialize global state
        self._load_global_state()

    def _load_global_state(self) -> None:
        """Load global state from disk or initialize new state."""
        global_path = self.storage_path / "global_state.json"
        if global_path.exists():
            with open(global_path, encoding="utf-8") as f:
                data = json.load(f)
                self.global_state = self._deserialize_global_state(data)
        else:
            self.global_state = GlobalStoryState(
                novel_id=self.storage_path.name,
                genre="fantasy",
            )

    def _deserialize_global_state(self, data: dict[str, Any]) -> GlobalStoryState:
        """Deserialize global state from dictionary.

        Args:
            data: Dictionary containing serialized global state

        Returns:
            Deserialized GlobalStoryState object
        """
        # Convert character states
        main_characters: dict[str, CharacterState] = {}
        for name, state_dict in data.get("main_characters", {}).items():
            main_characters[name] = CharacterState(**state_dict)

        # Convert plot threads
        plot_threads = [PlotThread(**pt) for pt in data.get("main_plot_threads", [])]

        return GlobalStoryState(
            novel_id=data.get("novel_id", ""),
            genre=data.get("genre", "fantasy"),
            main_characters=main_characters,
            world_rules=data.get("world_rules", {}),
            main_plot_threads=plot_threads,
            current_arc=data.get("current_arc", 1),
            total_chapters=data.get("total_chapters", 0),
            style_guide=data.get("style_guide", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )

    def save_global_state(self) -> None:
        """Save global state to disk."""
        if self.global_state is None:
            return

        global_path = self.storage_path / "global_state.json"

        # Serialize character states
        main_characters = {
            name: {
                "name": cs.name,
                "status": cs.status,
                "location": cs.location,
                "physical_form": cs.physical_form,
                "relationships": cs.relationships,
            }
            for name, cs in self.global_state.main_characters.items()
        }

        # Serialize plot threads
        plot_threads = [
            {"name": pt.name, "status": pt.status} for pt in self.global_state.main_plot_threads
        ]

        data = {
            "novel_id": self.global_state.novel_id,
            "genre": self.global_state.genre,
            "main_characters": main_characters,
            "world_rules": self.global_state.world_rules,
            "main_plot_threads": plot_threads,
            "current_arc": self.global_state.current_arc,
            "total_chapters": self.global_state.total_chapters,
            "style_guide": self.global_state.style_guide,
            "created_at": self.global_state.created_at.isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_arc_number(self, chapter: int) -> int:
        """Calculate which arc a chapter belongs to.

        Args:
            chapter: Chapter number (1-indexed)

        Returns:
            Arc number (1-indexed)
        """
        return ((chapter - 1) // CHAPTERS_PER_ARC) + 1

    def get_arc_summary(self, arc_number: int) -> ArcSummary | None:
        """Get arc summary with LRU caching.

        Args:
            arc_number: Arc number to retrieve

        Returns:
            ArcSummary if exists, None otherwise
        """
        # Check cache first
        if arc_number in self._arc_cache:
            self._arc_cache.move_to_end(arc_number)
            return self._arc_cache[arc_number]

        # Load from disk
        arc_path = self.storage_path / "arcs" / f"arc_{arc_number:03d}.json"
        if not arc_path.exists():
            return None

        with open(arc_path, encoding="utf-8") as f:
            data = json.load(f)
            summary = ArcSummary.from_dict(data)

        # Add to cache with LRU eviction
        self._arc_cache[arc_number] = summary
        if len(self._arc_cache) > self._maxsize_arcs:
            self._arc_cache.popitem(last=False)

        return summary

    def save_arc_summary(self, summary: ArcSummary) -> None:
        """Save arc summary to disk and update cache.

        Args:
            summary: ArcSummary to save
        """
        # Compress if enabled and needed
        if self._enable_compression and self._compressor.should_compress_arc(
            summary, COMPRESSION_THRESHOLDS["arc_summary"]
        ):
            summary = self._compressor.compress_arc_summary(
                summary, COMPRESSION_THRESHOLDS["arc_summary"]
            )
            logger.debug(f"Compressed arc {summary.arc_number} summary before saving")

        arc_path = self.storage_path / "arcs" / f"arc_{summary.arc_number:03d}.json"
        with open(arc_path, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)

        # Update cache with LRU eviction
        self._arc_cache[summary.arc_number] = summary
        if len(self._arc_cache) > self._maxsize_arcs:
            self._arc_cache.popitem(last=False)

    def get_chapter_summary(self, chapter: int) -> ChapterSummary | None:
        """Get chapter summary with LRU caching.

        Args:
            chapter: Chapter number to retrieve

        Returns:
            ChapterSummary if exists, None otherwise
        """
        # Check cache first
        if chapter in self._chapter_cache:
            self._chapter_cache.move_to_end(chapter)
            return self._chapter_cache[chapter]

        # Load from disk
        chapter_path = self.storage_path / "chapters" / f"chapter_{chapter:04d}.json"
        if not chapter_path.exists():
            return None

        with open(chapter_path, encoding="utf-8") as f:
            data = json.load(f)
            summary = ChapterSummary.from_dict(data)

        # Add to cache with LRU eviction
        self._chapter_cache[chapter] = summary
        if len(self._chapter_cache) > self._maxsize_chapters:
            self._chapter_cache.popitem(last=False)

        return summary

    def save_chapter_summary(self, summary: ChapterSummary) -> None:
        """Save chapter summary to disk and update cache.

        Args:
            summary: ChapterSummary to save
        """
        # Compress if enabled and needed
        if self._enable_compression and self._compressor.should_compress_chapter(
            summary, COMPRESSION_THRESHOLDS["chapter_summary"]
        ):
            summary = self._compressor.compress_chapter_summary(
                summary, COMPRESSION_THRESHOLDS["chapter_summary"]
            )
            logger.debug(f"Compressed chapter {summary.chapter_number} summary before saving")

        chapter_path = self.storage_path / "chapters" / f"chapter_{summary.chapter_number:04d}.json"
        with open(chapter_path, "w", encoding="utf-8") as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)

        # Update cache with LRU eviction
        self._chapter_cache[summary.chapter_number] = summary
        if len(self._chapter_cache) > self._maxsize_chapters:
            self._chapter_cache.popitem(last=False)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get current cache statistics.

        Returns:
            Dictionary with cache size information
        """
        return {
            "chapter_cache_size": len(self._chapter_cache),
            "chapter_cache_maxsize": self._maxsize_chapters,
            "arc_cache_size": len(self._arc_cache),
            "arc_cache_maxsize": self._maxsize_arcs,
        }

    def get_context_for_chapter(
        self, chapter: int, budget_manager: TokenBudgetManager | None = None
    ) -> str:
        """Build hierarchical context for chapter generation with token budget management.

        This method constructs a context string optimized for LLM consumption,
        containing information from multiple hierarchy levels with intelligent
        truncation based on token budget.

        Hierarchy:
        1. Global state (priority 1 - must)
        2. Current arc summary (priority 1 - must)
        3. Previous chapter detail (priority 2 - important)
        4. Recent chapters (priority 3 - optional)

        Args:
            chapter: Chapter number to generate context for
            budget_manager: Optional TokenBudgetManager for context allocation

        Returns:
            Context string for LLM consumption
        """
        # Create budget manager if not provided
        from src.novel_agent.novel.token_budget import TokenBudget

        if budget_manager is None:
            budget = TokenBudget(total=8000, reserved_for_generation=500)
            budget_manager = TokenBudgetManager(budget)

        # Progressive context loading with pre-fetching
        # Ensure frequently accessed arcs are cached
        self._ensure_frequent_arcs_cached()

        # Pre-load next arc if approaching arc boundary
        self._preload_next_arc(chapter)

        # Get context slices using detailed method
        slices = self._get_detailed_chapter_context(chapter, budget_manager.budget)

        # Allocate based on budget
        allocated = budget_manager.allocate_context(slices, strict_priority=True)

        # Build final context
        return budget_manager.build_context(allocated)

    def _build_global_context(self) -> str:
        """Build global state context string for LLM.

        Returns:
            Formatted context string
        """
        if self.global_state is None:
            return "【全局状态】\n未初始化"

        gs = self.global_state
        parts = ["【全局状态】"]

        # Main characters with status
        if gs.main_characters:
            chars = []
            for name, cs in gs.main_characters.items():
                chars.append(f"{name}({cs.status})")
            parts.append(f"主要角色: {', '.join(chars)}")

        # Plot threads with status
        if gs.main_plot_threads:
            threads = [f"{pt.name}({pt.status})" for pt in gs.main_plot_threads]
            parts.append(f"主线剧情: {', '.join(threads)}")

        # Stats
        parts.append(f"总章数: {gs.total_chapters}, 当前卷: {gs.current_arc}")

        return "\n".join(parts)

    def update_after_chapter(self, chapter: int, summary: ChapterSummary) -> None:
        """Update state after chapter generation.

        This method should be called after each chapter is generated to
        persist the chapter summary and update global state counters.

        Args:
            chapter: Chapter number that was just generated
            summary: Summary of the generated chapter
        """
        if self.global_state is None:
            return

        self.current_chapter = chapter
        self.global_state.total_chapters = max(self.global_state.total_chapters, chapter)
        self.global_state.current_arc = self.get_arc_number(chapter)

        # Update main characters from chapter summary
        if hasattr(summary, "characters"):
            for char_name, char_state in summary.characters.items():
                if char_name not in self.global_state.main_characters:
                    self.global_state.main_characters[char_name] = char_state
                else:
                    # Update existing character state
                    existing = self.global_state.main_characters[char_name]
                    if hasattr(char_state, "status"):
                        existing.status = char_state.status
                    if hasattr(char_state, "location"):
                        existing.location = char_state.location

        # Update main plot threads from chapter summary
        if hasattr(summary, "plot_threads"):
            for thread in summary.plot_threads:
                # Find existing thread or add new
                existing_thread = next(
                    (t for t in self.global_state.main_plot_threads if t.name == thread.name), None
                )
                if existing_thread:
                    existing_thread.status = thread.status
                else:
                    self.global_state.main_plot_threads.append(thread)

        # Save chapter summary
        self.save_chapter_summary(summary)

        # Persist global state
        self.save_global_state()

        logger.info(f"Updated hierarchical state for chapter {chapter}")

    def _get_detailed_chapter_context(
        self, chapter: int, budget: TokenBudget
    ) -> list[ContextSlice]:
        """Get detailed chapter context with budget-aware truncation.

        Args:
            chapter: Chapter number
            budget: Token budget manager

        Returns:
            List of context slices ordered by priority
        """
        slices: list[ContextSlice] = []

        # Priority 1: Global state (required)
        if self.global_state:
            global_context = self._build_global_context()
            slices.append(
                ContextSlice(
                    name="global_state", content=global_context, priority=1, estimated_tokens=0
                )
            )

        # Priority 1: Current arc summary (required)
        current_arc = self.get_arc_number(chapter)
        arc_summary = self.get_arc_summary(current_arc)
        if arc_summary:
            slices.append(
                ContextSlice(
                    name="current_arc",
                    content=arc_summary.get_context_string(),
                    priority=1,
                    estimated_tokens=0,
                )
            )

        # Priority 2: Previous chapter detail (important)
        if chapter > 1:
            prev_chapter = self.get_chapter_summary(chapter - 1)
            if prev_chapter:
                slices.append(
                    ContextSlice(
                        name="previous_chapter",
                        content=prev_chapter.get_context_string(),
                        priority=1,
                        estimated_tokens=0,
                    )
                )
        start_chapter = max(1, chapter - 5)
        for i in range(start_chapter, chapter - 1):  # Exclude chapter-1 (already added)
            ch_summary = self.get_chapter_summary(i)
            if ch_summary:
                slices.append(
                    ContextSlice(
                        name=f"chapter_{i}",
                        content=ch_summary.get_context_string(),
                        priority=3,
                        estimated_tokens=0,
                    )
                )

        return slices

    def clear_cache(self) -> None:
        """Clear all cached summaries to free memory."""
        self._arc_cache.clear()
        self._chapter_cache.clear()
        logger.debug("Cleared all cached summaries")

    def _preload_next_arc(self, current_chapter: int) -> None:
        """Pre-load the next arc summary in the background.

        This method pre-fetches the next arc summary to optimize context generation
        for subsequent chapters, reducing I/O latency.

        Args:
            current_chapter: Current chapter number being processed
        """
        current_arc = self.get_arc_number(current_chapter)
        chapters_in_current_arc = current_chapter % CHAPTERS_PER_ARC

        # Only preload if we're in the last 3 chapters of the current arc
        if chapters_in_current_arc >= CHAPTERS_PER_ARC - 3:
            next_arc = current_arc + 1
            # Check if next arc is not already cached
            if next_arc not in self._arc_cache:
                # Load next arc (this will cache it via get_arc_summary)
                next_arc_summary = self.get_arc_summary(next_arc)
                if next_arc_summary:
                    logger.debug(f"Pre-loaded arc {next_arc} for chapter {current_chapter}")

    def _get_frequently_accessed_arcs(self, access_threshold: int = 3) -> list[int]:
        """Get list of frequently accessed arc numbers.

        Args:
            access_threshold: Minimum number of accesses to be considered frequent

        Returns:
            List of arc numbers that are accessed frequently
        """
        # For now, return current arc and previous arc as frequently accessed
        # This can be enhanced with actual access tracking if needed
        if self.global_state is None:
            return []

        current_arc = self.global_state.current_arc
        frequent_arcs = [current_arc]

        if current_arc > 1:
            frequent_arcs.append(current_arc - 1)

        return frequent_arcs

    def _ensure_frequent_arcs_cached(self) -> None:
        """Ensure frequently accessed arcs are cached.

        This method proactively loads arcs that are accessed frequently
        to optimize performance.
        """
        frequent_arcs = self._get_frequently_accessed_arcs()

        for arc_num in frequent_arcs:
            if arc_num not in self._arc_cache:
                arc_summary = self.get_arc_summary(arc_num)
                if arc_summary:
                    logger.debug(f"Pre-cached frequently accessed arc {arc_num}")
