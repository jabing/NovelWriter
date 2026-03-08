"""NovelWriter Shared - Common data models and API interfaces.

This package provides shared components for the NovelWriter ecosystem:
- Data models (Character, Chapter, Fact, etc.)
- API interface definitions
- Utility functions
"""

from novelwriter_shared.models import (
    CharacterProfile,
    CharacterStatus,
    CharacterTimelineEvent,
    ConflictType,
    EventImportance,
    EventType,
    Fact,
    FactType,
    TimelineConflict,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CharacterProfile",
    "CharacterStatus",
    "CharacterTimelineEvent",
    "ConflictType",
    "EventImportance",
    "EventType",
    "Fact",
    "FactType",
    "TimelineConflict",
]
