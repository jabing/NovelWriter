"""Pydantic schemas for the API layer."""

from src.novel_agent.api.schemas.agents import (
    AgentStatusResponse,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)
from src.novel_agent.api.schemas.chapters import (
    ChapterListResponse,
    ChapterResponse,
)
from src.novel_agent.api.schemas.characters import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
)
from src.novel_agent.api.schemas.outlines import (
    OutlineGenerateRequest,
    OutlineListResponse,
    OutlineResponse,
)
from src.novel_agent.api.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from src.novel_agent.api.schemas.publishing import (
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
