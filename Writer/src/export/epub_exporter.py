# src/export/epub_exporter.py
"""EPUB exporter for novels."""

import logging
from typing import Any

from ebooklib import epub

from src.export.base import BaseExporter, ChapterContent, ExportFormat, ExportResult

logger = logging.getLogger(__name__)


class EpubExporter(BaseExporter):
    """Export novels to EPUB format."""

    format = ExportFormat.EPUB

    def export(
        self,
        title: str,
        author: str,
        chapters: list[ChapterContent],
        metadata: dict[str, Any] | None = None,
    ) -> ExportResult:
        """Export novel to EPUB.

        Args:
            title: Novel title
            author: Author name
            chapters: List of chapter contents
            metadata: Optional metadata

        Returns:
            ExportResult with epub file path
        """
        try:
            book = epub.EpubBook()

            # Set metadata
            book.set_identifier(f"novel_{title.lower().replace(' ', '_')}")
            book.set_title(title)
            book.set_language(metadata.get("language", "en") if metadata else "en")
            book.add_author(author)

            # Add additional metadata
            if metadata:
                if metadata.get("description"):
                    book.add_metadata("DC", "description", metadata["description"])
                if metadata.get("genre"):
                    book.add_metadata("DC", "subject", metadata["genre"])
                if metadata.get("tags"):
                    for tag in metadata["tags"]:
                        book.add_metadata("DC", "subject", tag)

            # Create chapters
            epub_chapters = []
            toc = []
            total_words = 0

            for chapter in chapters:
                # Create chapter file
                chapter_file = f"chapter_{chapter.number:03d}.xhtml"
                epub_chapter = epub.EpubHtml(
                    title=chapter.title,
                    file_name=chapter_file,
                    lang=metadata.get("language", "en") if metadata else "en",
                )

                # Format content with paragraph tags
                paragraphs = chapter.content.split("\n\n")
                html_content = ""
                for p in paragraphs:
                    p = p.strip()
                    if p:
                        html_content += f"<p>{p}</p>\n"

                epub_chapter.content = f"<h1>{chapter.title}</h1>\n{html_content}"
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
                toc.append(epub_chapter)
                total_words += chapter.word_count

            # Table of contents
            book.toc = tuple(toc)

            # Add navigation files
            book.add_item(epub.Ncx())
            book.add_item(epub.Nav())

            # Spine
            book.spine = ["nav"] + epub_chapters

            # Write EPUB file
            output_path = self._get_output_path(title, "epub")
            epub.write_epub(str(output_path), book, {})

            logger.info(f"EPUB exported: {output_path}")

            return ExportResult(
                success=True,
                file_path=str(output_path),
                chapters=len(chapters),
                words=total_words,
            )

        except Exception as e:
            logger.error(f"EPUB export failed: {e}")
            return ExportResult(
                success=False,
                error=str(e),
            )
