"""Outline-related Pydantic schemas for the API."""

from pydantic import BaseModel, Field


class OutlineGenerateRequest(BaseModel):
    """Schema for generating an outline using AI."""

    story_idea: str = Field(..., min_length=1, description="The story idea or concept")
    num_chapters: int = Field(..., ge=1, le=100, description="Number of chapters to generate")
    genre: str | None = Field(None, description="Genre of the story (optional)")


class OutlineChapterResponse(BaseModel):
    """Schema for a single chapter in the outline."""

    number: int
    title: str
    summary: str
    plot_events: list[dict[str, str]] = Field(default_factory=list)
    state_changes: dict[str, str] = Field(default_factory=dict)
    characters: list[str] = Field(default_factory=list)
    location: str = ""


class OutlineResponse(BaseModel):
    """Schema for outline response data."""

    novel_id: str
    outline_id: str
    chapters: list[OutlineChapterResponse]
    total_chapters: int
    created_at: str | None = None
    updated_at: str | None = None


class OutlineListResponse(BaseModel):
    """Schema for list of outlines."""

    novel_id: str
    outlines: list[dict[str, str]]  # List of outline metadata (id, title, created_at)
    total_count: int


class OutlineUpdate(BaseModel):
    """Schema for updating an outline (all fields optional for partial updates)."""

    title: str | None = None
    chapters: list[dict] | None = None
    notes: str | None = None
