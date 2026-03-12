"""Chapter-related Pydantic schemas for the API."""

from pydantic import BaseModel


class ChapterResponse(BaseModel):
    """Schema for chapter response data."""

    chapter_number: int
    title: str
    word_count: int
    status: str
    order: int = 0
    content: str | None = None
    summary: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ChapterListResponse(BaseModel):
    """Schema for list of chapters."""

    project_id: str
    chapters: list[ChapterResponse]
    total_count: int
    completed_count: int


class ChapterCreate(BaseModel):
    """Schema for creating a new chapter."""

    title: str
    content: str = ""
    order: int = 0
    status: str = "draft"


class ChapterUpdate(BaseModel):
    """Schema for updating an existing chapter.
    
    All fields are optional to support partial updates.
    """

    title: str | None = None
    content: str | None = None
    order: int | None = None
    status: str | None = None
