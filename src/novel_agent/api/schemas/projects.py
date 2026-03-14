"""Project-related Pydantic schemas for the API."""

from enum import Enum

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status values."""
    PLANNING = "planning"
    WRITING = "writing"
    PAUSED = "paused"
    COMPLETED = "completed"


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    title: str = Field(..., min_length=1, max_length=200)
    genre: str = Field(default="General", max_length=100)
    language: str = Field(default="en", max_length=10)
    premise: str = Field(default="", max_length=2000)
    themes: list[str] = Field(default_factory=list)
    pov: str = Field(default="first")
    tone: str = Field(default="balanced")
    target_audience: str = Field(default="young_adult")
    story_structure: str = Field(default="three_act")
    content_rating: str = Field(default="teen")
    target_chapters: int = Field(default=100, ge=1)
    target_words: int = Field(default=300000, ge=1000)
    platforms: list[str] = Field(default_factory=list)
    user_id: str | None = Field(default=None, max_length=50)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    title: str | None = None
    genre: str | None = None
    language: str | None = None
    status: ProjectStatus | None = None
    premise: str | None = None
    themes: list[str] | None = None
    pov: str | None = None
    tone: str | None = None
    target_audience: str | None = None
    story_structure: str | None = None
    content_rating: str | None = None
    target_chapters: int | None = None
    target_words: int | None = None
    platforms: list[str] | None = None


class ProjectResponse(BaseModel):
    """Schema for project response data."""

    id: str
    title: str
    genre: str
    language: str
    status: str
    premise: str
    themes: list[str]
    pov: str
    tone: str
    target_audience: str
    story_structure: str
    content_rating: str
    sensitive_handling: str
    target_chapters: int
    completed_chapters: int
    total_words: int
    target_words: int
    progress_percent: float
    created_at: str
    updated_at: str
    platforms: list[str]
    published_chapters: int
    user_id: str | None = None

    # Analytics
    total_reads: int
    total_votes: int
    total_comments: int
    followers: int
