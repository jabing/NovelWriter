"""Novel generation and continuity management module.

This module provides classes for managing story continuity, generating
chapters with context, and validating story consistency.
"""

from src.novel.chapter_generator import ChapterGenerator
from src.novel.constitution import ConstitutionValidator, RuleDomain, get_constitution_summary
from src.novel.continuity import (
    CharacterState,
    ContinuityManager,
    PlotThread,
    StateChange,
    StoryState,
)
from src.novel.glossary import GlossaryManager, TermStatus
from src.novel.knowledge_graph import KnowledgeGraph, create_knowledge_graph
from src.novel.outline_generator import DetailedChapterSpec, OutlineGenerator, PlotEvent
from src.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel.schemas import AgentType, Genre, Language, VersionMetadata
from src.novel.structured_input import (
    CharacterInScene,
    LocationSpec,
    StructuredInputSystem,
    StructuredTask,
)
from src.novel.timeline_manager import (
    TemporalRelation,
    TimelineEvent,
    TimelineManager,
    TimeUnit,
    create_timeline_manager,
)
from src.novel.validators import (
    ContinuityValidator,
    ValidationError,
    ValidationResult,
)
from src.novel.version_control import (
    VersionChangeType,
    VersionControlSystem,
    create_version_control,
)

__all__ = [
    "CharacterState",
    "ContinuityManager",
    "PlotThread",
    "StateChange",
    "StoryState",
    "ChapterSpec",
    "DetailedOutline",
    "DetailedChapterSpec",
    "OutlineGenerator",
    "PlotEvent",
    "ContinuityValidator",
    "ValidationError",
    "ValidationResult",
    "ChapterGenerator",
    # New modules
    "ConstitutionValidator",
    "get_constitution_summary",
    "RuleDomain",
    "GlossaryManager",
    "TermStatus",
    "AgentType",
    "Genre",
    "Language",
    "VersionMetadata",
    "StructuredInputSystem",
    "StructuredTask",
    "CharacterInScene",
    "LocationSpec",
    "VersionControlSystem",
    "VersionChangeType",
    "create_version_control",
    "KnowledgeGraph",
    "create_knowledge_graph",
    "TimelineManager",
    "TimelineEvent",
    "TimeUnit",
    "TemporalRelation",
    "create_timeline_manager",
]
