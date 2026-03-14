# src/export/txt_exporter.py
"""TXT exporter for novels."""

import logging
from typing import Any

from src.novel_agent.export.base import BaseExporter, ChapterContent, ExportFormat, ExportResult

logger = logging.getLogger(__name__)


class TxtExporter(BaseExporter):
    """Export novels to plain text format."""

    format = ExportFormat.TXT

    def export(
        self,
        title: str,
        author: str,
        chapters: list[ChapterContent],
        metadata: dict[str, Any] | None = None,
    ) -> ExportResult:
        """Export novel to TXT.

        Args:
            title: Novel title
            author: Author name
            chapters: List of chapter contents
            metadata: Optional metadata

        Returns:
            ExportResult with txt file path
        """
        try:
            output_path = self._get_output_path(title, "txt")
            total_words = 0

            with open(output_path, "w", encoding="utf-8") as f:
                # Title
                f.write(f"{title}\n")
                f.write(f"by {author}\n")
                f.write("=" * 50 + "\n\n")

                # Metadata
                if metadata:
                    if metadata.get("description"):
                        f.write(f"Description: {metadata['description']}\n\n")
                    if metadata.get("genre"):
                        f.write(f"Genre: {metadata['genre']}\n\n")

                # Table of contents
                f.write("TABLE OF CONTENTS\n")
                f.write("-" * 30 + "\n")
                for chapter in chapters:
                    f.write(f"Chapter {chapter.number}: {chapter.title}\n")
                f.write("\n" + "=" * 50 + "\n\n")

                # Chapters
                for chapter in chapters:
                    f.write(f"\n{'#' * 50}\n")
                    f.write(f"# {chapter.title}\n")
                    f.write(f"{'#' * 50}\n\n")
                    f.write(chapter.content)
                    f.write("\n\n")
                    total_words += chapter.word_count

            logger.info(f"TXT exported: {output_path}")

            return ExportResult(
                success=True,
                file_path=str(output_path),
                chapters=len(chapters),
                words=total_words,
            )

        except Exception as e:
            logger.error(f"TXT export failed: {e}")
            return ExportResult(
                success=False,
                error=str(e),
            )
