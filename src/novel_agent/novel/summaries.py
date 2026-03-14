"""Summary data structures for hierarchical story state.

This module provides dataclasses for chapter and arc summaries used in the
hierarchical memory system for 100+ chapter novel generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ChapterSummary:
    """Summary of a single chapter for hierarchical state.

    Attributes:
        chapter_number: Chapter number (1-indexed)
        title: Chapter title
        summary: ~200 word summary of chapter content
        key_events: List of key events in this chapter
        character_changes: Dict mapping character names to their changes
        location: Primary location of this chapter
        plot_threads_advanced: List of plot threads that advanced
        plot_threads_resolved: List of plot threads resolved in this chapter
        sentiment: Overall mood/tone (neutral, dark, hopeful, etc.)
        word_count: Word count of the chapter
        created_at: When this summary was created
    """

    chapter_number: int
    title: str
    summary: str  # ~200 words
    key_events: list[str] = field(default_factory=list)
    character_changes: dict[str, str] = field(default_factory=dict)
    location: str = ""
    plot_threads_advanced: list[str] = field(default_factory=list)
    plot_threads_resolved: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "summary": self.summary,
            "key_events": self.key_events,
            "character_changes": self.character_changes,
            "location": self.location,
            "plot_threads_advanced": self.plot_threads_advanced,
            "plot_threads_resolved": self.plot_threads_resolved,
            "sentiment": self.sentiment,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChapterSummary":
        """Deserialize from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def get_context_string(self) -> str:
        """Generate context string for LLM."""
        parts = [
            f"【第{self.chapter_number}章：{self.title}】",
            f"摘要：{self.summary}",
        ]
        if self.key_events:
            parts.append(f"关键事件：{', '.join(self.key_events[:5])}")
        if self.character_changes:
            changes = [f"{k}: {v}" for k, v in self.character_changes.items()]
            parts.append(f"角色变化：{'; '.join(changes[:3])}")
        if self.plot_threads_advanced:
            parts.append(f"剧情推进：{', '.join(self.plot_threads_advanced[:3])}")
        if self.plot_threads_resolved:
            parts.append(f"剧情结束：{', '.join(self.plot_threads_resolved)}")
        return "\n".join(parts)


@dataclass
class ArcSummary:
    """Summary of a story arc (10 chapters = 1 volume).

    Attributes:
        arc_number: Arc number (1-indexed)
        start_chapter: First chapter number in this arc
        end_chapter: Last chapter number in this arc
        title: Arc title
        summary: ~500 word summary covering all chapters in the arc
        major_events: List of major events across the arc
        character_arcs: Dict mapping character names to their arc descriptions
        world_changes: List of significant world state changes
        plot_threads_status: Dict mapping plot thread names to status
        themes: List of themes explored in this arc
        created_at: When this summary was created
    """

    arc_number: int
    start_chapter: int
    end_chapter: int
    title: str
    summary: str  # ~500 words covering all 10 chapters
    major_events: list[str] = field(default_factory=list)
    character_arcs: dict[str, str] = field(default_factory=dict)
    world_changes: list[str] = field(default_factory=list)
    plot_threads_status: dict[str, str] = field(default_factory=dict)
    themes: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def chapter_range(self) -> range:
        """Get range of chapters in this arc."""
        return range(self.start_chapter, self.end_chapter + 1)

    def contains_chapter(self, chapter: int) -> bool:
        """Check if a chapter is in this arc."""
        return self.start_chapter <= chapter <= self.end_chapter

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "arc_number": self.arc_number,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "title": self.title,
            "summary": self.summary,
            "major_events": self.major_events,
            "character_arcs": self.character_arcs,
            "world_changes": self.world_changes,
            "plot_threads_status": self.plot_threads_status,
            "themes": self.themes,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArcSummary":
        """Deserialize from dictionary."""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def get_context_string(self) -> str:
        """Generate context string for LLM."""
        parts = [
            f"【第{self.arc_number}卷：{self.title}】",
            f"章节范围：{self.start_chapter}-{self.end_chapter}",
            f"概要：{self.summary}",
        ]
        if self.major_events:
            parts.append(f"重大事件：{', '.join(self.major_events[:10])}")
        if self.character_arcs:
            arcs = [f"{k}: {v}" for k, v in self.character_arcs.items()]
            parts.append(f"角色成长：{'; '.join(arcs[:5])}")
        if self.plot_threads_status:
            threads = [f"{k}({v})" for k, v in self.plot_threads_status.items()]
            parts.append(f"剧情线：{', '.join(threads)}")
        return "\n".join(parts)
