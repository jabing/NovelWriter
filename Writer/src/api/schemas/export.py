"""Export-related Pydantic schemas for the API."""

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Schema for export request data."""

    chapter_numbers: list[int] | None = Field(
        default=None,
        description="List of chapter numbers to export. If None, exports all chapters."
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata (title, author, summary) in export."
    )


class ExportResponse(BaseModel):
    """Schema for export operation response."""

    success: bool
    message: str
    novel_id: str
    format: str
    file_size: int = 0
    chapter_count: int = 0


class SingleChapterExportRequest(BaseModel):
    """Schema for single chapter export request."""

    include_metadata: bool = Field(
        default=True,
        description="Include metadata (title, author notes) in export."
    )
    format: str = Field(
        default="txt",
        description="Export format: txt, epub, or pdf."
    )
