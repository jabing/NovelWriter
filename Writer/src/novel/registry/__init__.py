# src/novel/registry/__init__.py
"""Centralized story registry for tracking all story elements."""

from src.novel.registry.story_registry import (
    ChapterRecord,
    EventRecord,
    StoryRegistry,
)

__all__ = [
    "StoryRegistry",
    "ChapterRecord",
    "EventRecord",
]
