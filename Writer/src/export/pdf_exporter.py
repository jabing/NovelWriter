# src/export/pdf_exporter.py
"""PDF exporter for novels."""

import logging
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from src.export.base import BaseExporter, ChapterContent, ExportFormat, ExportResult

logger = logging.getLogger(__name__)


class PdfExporter(BaseExporter):
    """Export novels to PDF format."""

    format = ExportFormat.PDF

    def __init__(self, output_dir: str = "exports") -> None:
        """Initialize PDF exporter."""
        super().__init__(output_dir)
        self._register_fonts()

    def _register_fonts(self) -> None:
        """Register fonts for Chinese/Japanese support."""
        # Try to register common fonts
        font_paths = [
            # Windows fonts
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simhei.ttf",  # SimHei
            "C:/Windows/Fonts/simsun.ttc",  # SimSun
            # Linux fonts
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            # macOS fonts
            "/System/Library/Fonts/PingFang.ttc",
        ]

        self.chinese_font = None
        for font_path in font_paths:
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                self.chinese_font = "ChineseFont"
                logger.info(f"Registered Chinese font: {font_path}")
                break
            except Exception:
                continue

    def _get_styles(self, language: str = "en") -> dict[str, ParagraphStyle]:
        """Get paragraph styles for PDF.

        Args:
            language: Content language

        Returns:
            Dictionary of styles
        """
        styles = getSampleStyleSheet()

        # Use Chinese font if available and language is Chinese
        font_name = self.chinese_font if language == "zh" and self.chinese_font else "Helvetica"

        # Title style
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
        )

        # Chapter title style
        chapter_style = ParagraphStyle(
            "ChapterTitle",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=18,
            spaceBefore=20,
            spaceAfter=20,
            alignment=1,  # Center
        )

        # Body style
        body_style = ParagraphStyle(
            "BodyText",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=11,
            leading=16,
            spaceBefore=6,
            spaceAfter=6,
            firstLineIndent=24,  # Indent first line
        )

        return {
            "title": title_style,
            "chapter": chapter_style,
            "body": body_style,
        }

    def export(
        self,
        title: str,
        author: str,
        chapters: list[ChapterContent],
        metadata: dict[str, Any] | None = None,
    ) -> ExportResult:
        """Export novel to PDF.

        Args:
            title: Novel title
            author: Author name
            chapters: List of chapter contents
            metadata: Optional metadata

        Returns:
            ExportResult with pdf file path
        """
        try:
            output_path = self._get_output_path(title, "pdf")
            language = metadata.get("language", "en") if metadata else "en"
            styles = self._get_styles(language)

            # Create document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=2 * cm,
                leftMargin=2 * cm,
                topMargin=2 * cm,
                bottomMargin=2 * cm,
            )

            # Build content
            story = []
            total_words = 0

            # Title page
            story.append(Spacer(1, 3 * cm))
            story.append(Paragraph(title, styles["title"]))
            story.append(Spacer(1, 1 * cm))
            story.append(Paragraph(f"by {author}", styles["chapter"]))
            story.append(PageBreak())

            # Table of contents
            story.append(Paragraph("Table of Contents", styles["chapter"]))
            story.append(Spacer(1, 0.5 * cm))
            for chapter in chapters:
                toc_line = f"Chapter {chapter.number}: {chapter.title}"
                story.append(Paragraph(toc_line, styles["body"]))
            story.append(PageBreak())

            # Chapters
            for chapter in chapters:
                # Chapter title
                story.append(Paragraph(chapter.title, styles["chapter"]))
                story.append(Spacer(1, 0.5 * cm))

                # Chapter content - split into paragraphs
                paragraphs = chapter.content.split("\n\n")
                for p in paragraphs:
                    p = p.strip()
                    if p:
                        # Escape special characters for ReportLab
                        p = p.replace("&", "&amp;")
                        p = p.replace("<", "&lt;")
                        p = p.replace(">", "&gt;")
                        story.append(Paragraph(p, styles["body"]))

                story.append(PageBreak())
                total_words += chapter.word_count

            # Build PDF
            doc.build(story)

            logger.info(f"PDF exported: {output_path}")

            return ExportResult(
                success=True,
                file_path=str(output_path),
                chapters=len(chapters),
                words=total_words,
                pages=doc.page,  # type: ignore
            )

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return ExportResult(
                success=False,
                error=str(e),
            )
