"""Publishing-related Pydantic schemas for the API."""

from pydantic import BaseModel, Field


class PlatformInfo(BaseModel):
    """Schema for platform information."""

    id: str
    name: str
    description: str = ""
    enabled: bool = True


class PublishRequest(BaseModel):
    """Schema for publish request."""

    platform: str = Field(..., min_length=1)
    chapter_numbers: list[int] = Field(default_factory=list)
    auto_publish: bool = False


class PublishResponse(BaseModel):
    """Schema for publish response."""

    success: bool
    platform: str
    published_chapters: list[int] = Field(default_factory=list)
    message: str = ""


class CommentResponse(BaseModel):
    """Schema for a single comment."""

    id: str
    author: str
    content: str
    chapter_number: int | None = None
    created_at: str = ""
    likes: int = 0


class CommentListResponse(BaseModel):
    """Schema for list of comments."""

    novel_id: str
    platform: str = ""
    comments: list[CommentResponse]
    total_count: int
