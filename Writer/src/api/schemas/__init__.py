"""Pydantic schemas for the API layer."""

from src.api.schemas.agents import (
    AgentStatusResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)
from src.api.schemas.chapters import (
    ChapterListResponse,
    ChapterResponse,
)
from src.api.schemas.characters import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
)
from src.api.schemas.outlines import (
    OutlineGenerateRequest,
    OutlineListResponse,
    OutlineResponse,
)
from src.api.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from src.api.schemas.publishing import (
    CommentListResponse,
    CommentResponse,
    PlatformInfo,
    PublishRequest,
    PublishResponse,
)

__all__ = [
    # Projects
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    # Chapters
    "ChapterResponse",
    "ChapterListResponse",
    # Characters
    "CharacterCreate",
    "CharacterResponse",
    "CharacterListResponse",
    # Outlines
    "OutlineGenerateRequest",
    "OutlineResponse",
    "OutlineListResponse",
    # Publishing
    "PlatformInfo",
    "PublishRequest",
    "PublishResponse",
    "CommentResponse",
    "CommentListResponse",
    # Agents/Tasks
    "TaskCreate",
    "TaskResponse",
    "TaskListResponse",
    "AgentStatusResponse",
]
