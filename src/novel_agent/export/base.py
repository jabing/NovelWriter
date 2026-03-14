# src/export/base.py
"""Base exporter classes for novel export functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ExportFormat(str, Enum):
    """Supported export formats."""
    EPUB = "epub"
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    DOCX = "docx"


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    file_path: str | None = None
    error: str | None = None
    pages: int = 0
    chapters: int = 0
    words: int = 0


@dataclass
class ChapterContent:
    """Chapter content for export."""
    number: int
    title: str
    content: str
    word_count: int = 0

    def __post_init__(self) -> None:
        if self.word_count == 0:
            self.word_count = len(self.content.split())


class BaseExporter(ABC):
    """Base class for all exporters."""

    format: ExportFormat

    def __init__(self, output_dir: str = "exports") -> None:
        """Initialize exporter.

        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export(
        self,
        title: str,
        author: str,
        chapters: list[ChapterContent],
        metadata: dict[str, Any] | None = None,
    ) -> ExportResult:
        """Export novel to file.

        Args:
            title: Novel title
            author: Author name
            chapters: List of chapter contents
            metadata: Optional metadata (genre, description, etc.)

        Returns:
            ExportResult with file path or error
        """
        pass

    def _get_output_path(self, title: str, extension: str) -> Path:
        """Generate output file path.

        Args:
            title: Novel title
            extension: File extension (without dot)

        Returns:
            Path to output file
        """
        # Sanitize title for filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
        safe_title = safe_title.strip().replace(" ", "_")
        return self.output_dir / f"{safe_title}.{extension}"
