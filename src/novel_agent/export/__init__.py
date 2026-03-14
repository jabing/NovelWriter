# src/export/__init__.py
"""Novel export functionality.

Supported formats:
- EPUB (e-book)
- PDF
- TXT (plain text)
- MD (Markdown)

Usage:
    from src.novel_agent.export import export_novel, ExportFormat

    result = export_novel(
        title="My Novel",
        author="Author Name",
        chapters=[...],
        format=ExportFormat.EPUB,
    )
"""

from pathlib import Path
from typing import Any

from src.novel_agent.export.base import BaseExporter, ChapterContent, ExportFormat, ExportResult
from src.novel_agent.export.epub_exporter import EpubExporter
from src.novel_agent.export.pdf_exporter import PdfExporter
from src.novel_agent.export.txt_exporter import TxtExporter


def get_exporter(format: ExportFormat, output_dir: str = "exports") -> BaseExporter:
    """Get exporter for specified format.

    Args:
        format: Export format
        output_dir: Output directory

    Returns:
        Exporter instance

    Raises:
        ValueError: If format is not supported
    """
    exporters = {
        ExportFormat.EPUB: EpubExporter,
        ExportFormat.PDF: PdfExporter,
        ExportFormat.TXT: TxtExporter,
        ExportFormat.MD: TxtExporter,  # MD uses same logic as TXT
    }

    exporter_class = exporters.get(format)
    if not exporter_class:
        raise ValueError(f"Unsupported export format: {format}")

    return exporter_class(output_dir=output_dir)


def export_novel(
    title: str,
    author: str,
    chapters: list[ChapterContent],
    format: ExportFormat = ExportFormat.EPUB,
    output_dir: str = "exports",
    metadata: dict[str, Any] | None = None,
) -> ExportResult:
    """Export novel to specified format.

    Args:
        title: Novel title
        author: Author name
        chapters: List of chapter contents
        format: Export format (default: EPUB)
        output_dir: Output directory
        metadata: Optional metadata

    Returns:
        ExportResult with file path or error
    """
    exporter = get_exporter(format, output_dir)
    return exporter.export(title, author, chapters, metadata)


def export_from_project(
    project_id: str,
    format: ExportFormat = ExportFormat.EPUB,
    output_dir: str = "exports",
) -> ExportResult:
    """Export novel from project ID.

    Args:
        project_id: Project ID
        format: Export format
        output_dir: Output directory

    Returns:
        ExportResult with file path or error
    """
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()
    project = state.get_project(project_id)

    if not project:
        return ExportResult(
            success=False,
            error=f"Project not found: {project_id}",
        )

    # Load chapters from files
    chapters_dir = Path(f"data/openviking/memory/novels/{project_id}/chapters")
    if not chapters_dir.exists():
        return ExportResult(
            success=False,
            error=f"No chapters found for project: {project_id}",
        )

    chapters = []
    for chapter_file in sorted(chapters_dir.glob("chapter_*.md")):
        with open(chapter_file, encoding="utf-8") as f:
            content = f.read()

        # Extract chapter number from filename
        chapter_num = int(chapter_file.stem.split("_")[1])

        chapters.append(
            ChapterContent(
                number=chapter_num,
                title=f"Chapter {chapter_num}",
                content=content,
            )
        )

    if not chapters:
        return ExportResult(
            success=False,
            error=f"No chapters found for project: {project_id}",
        )

    # Metadata
    metadata = {
        "genre": project.genre,
        "language": project.language,
        "description": project.premise,
    }

    from src.novel_agent.studio.core.settings import get_settings

    settings = get_settings()
    return export_novel(
        title=project.title,
        author=settings.author_name,
        chapters=chapters,
        format=format,
        output_dir=output_dir,
        metadata=metadata,
    )


__all__ = [
    "ExportFormat",
    "ExportResult",
    "ChapterContent",
    "export_novel",
    "export_from_project",
    "get_exporter",
]
