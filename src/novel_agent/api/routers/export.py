"""Export API router for novel and chapter export operations."""

import io
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from src.novel_agent.api.schemas.export import ExportRequest, ExportResponse, SingleChapterExportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"], redirect_slashes=False)


def _get_novel_chapters(novel_id: str, chapter_numbers: list[int] | None = None) -> list[dict[str, Any]]:
    """Load chapters for a novel.
    
    Args:
        novel_id: The novel identifier
        chapter_numbers: Optional list of specific chapter numbers to load.
                        If None, loads all chapters.
    
    Returns:
        List of chapter data dictionaries with number, title, content
    """
    chapters_dir = Path(f"data/openviking/memory/novels/{novel_id}/chapters")
    if not chapters_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found or has no chapters"
        )
    
    chapters: list[dict[str, Any]] = []
    
    # Load all chapter files
    for chapter_file in sorted(chapters_dir.glob("chapter_*.json")):
        try:
            with open(chapter_file, encoding="utf-8") as f:
                chapter_data = json.load(f)
                chapter_num = chapter_data.get("number", 0)
                
                # Filter by requested chapter numbers if specified
                if chapter_numbers is not None and chapter_num not in chapter_numbers:
                    continue
                
                chapters.append({
                    "number": chapter_num,
                    "title": chapter_data.get("title", f"Chapter {chapter_num}"),
                    "content": chapter_data.get("content", ""),
                })
        except Exception as e:
            logger.warning(f"Failed to load chapter {chapter_file}: {e}")
    
    # Sort by chapter number
    chapters.sort(key=lambda c: c["number"])
    return chapters


def _generate_txt_content(chapters: list[dict[str, Any]], include_metadata: bool = True) -> str:
    """Generate plain text content from chapters."""
    lines: list[str] = []
    
    for chapter in chapters:
        if include_metadata:
            lines.append(f"\n{'='*60}")
            lines.append(f"{chapter['title']}")
            lines.append(f"{'='*60}\n")
        else:
            lines.append(f"\n{chapter['title']}\n")
        
        if chapter["content"]:
            lines.append(chapter["content"])
        
        lines.append("\n")
    
    return "\n".join(lines)


def _generate_epub(novel_id: str, chapters: list[dict[str, Any]], include_metadata: bool = True) -> bytes:
    """Generate EPUB file content.
    
    Note: This is a minimal EPUB implementation. For production use,
    consider using a dedicated EPUB library like ebooklib.
    """
    # For now, return plain text as placeholder
    # In production, this should generate a proper EPUB using ebooklib
    txt_content = _generate_txt_content(chapters, include_metadata)
    return txt_content.encode("utf-8")


def _generate_pdf(novel_id: str, chapters: list[dict[str, Any]], include_metadata: bool = True) -> bytes:
    """Generate PDF file content.
    
    Note: This is a placeholder implementation. For production use,
    consider using a PDF library like reportlab or weasyprint.
    """
    # For now, return plain text as placeholder
    # In production, this should generate a proper PDF
    txt_content = _generate_txt_content(chapters, include_metadata)
    return txt_content.encode("utf-8")


@router.post("/novels/{novel_id}/epub")
def export_novel_epub(novel_id: str, request: ExportRequest) -> StreamingResponse:
    """Export novel chapters as EPUB file.
    
    Args:
        novel_id: The novel identifier
        request: Export request with optional chapter numbers and metadata flag
    
    Returns:
        File download response
    
    Raises:
        HTTPException: If novel not found or export fails
    """
    try:
        chapters = _get_novel_chapters(novel_id, request.chapter_numbers)
        
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chapters found for export"
            )
        
        epub_content = _generate_epub(novel_id, chapters, request.include_metadata)
        file_size = len(epub_content)
        
        return StreamingResponse(
            io.BytesIO(epub_content),
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f"attachment; filename={novel_id}.epub",
                "Content-Length": str(file_size),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EPUB export failed for novel {novel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/novels/{novel_id}/pdf")
def export_novel_pdf(novel_id: str, request: ExportRequest) -> StreamingResponse:
    """Export novel chapters as PDF file.
    
    Args:
        novel_id: The novel identifier
        request: Export request with optional chapter numbers and metadata flag
    
    Returns:
        File download response
    
    Raises:
        HTTPException: If novel not found or export fails
    """
    try:
        chapters = _get_novel_chapters(novel_id, request.chapter_numbers)
        
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chapters found for export"
            )
        
        pdf_content = _generate_pdf(novel_id, chapters, request.include_metadata)
        file_size = len(pdf_content)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={novel_id}.pdf",
                "Content-Length": str(file_size),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed for novel {novel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/novels/{novel_id}/txt")
def export_novel_txt(novel_id: str, request: ExportRequest) -> StreamingResponse:
    """Export novel chapters as plain text file.
    
    Args:
        novel_id: The novel identifier
        request: Export request with optional chapter numbers and metadata flag
    
    Returns:
        File download response
    
    Raises:
        HTTPException: If novel not found or export fails
    """
    try:
        chapters = _get_novel_chapters(novel_id, request.chapter_numbers)
        
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chapters found for export"
            )
        
        txt_content = _generate_txt_content(chapters, request.include_metadata)
        content_bytes = txt_content.encode("utf-8")
        file_size = len(content_bytes)
        
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={novel_id}.txt",
                "Content-Length": str(file_size),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TXT export failed for novel {novel_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/chapters/{chapter_id}")
def export_chapter(chapter_id: str, request: SingleChapterExportRequest) -> StreamingResponse:
    """Export a single chapter in the specified format.
    
    Args:
        chapter_id: The chapter identifier (format: {novel_id}:{chapter_number})
        request: Export request with format and metadata options
    
    Returns:
        File download response
    
    Raises:
        HTTPException: If chapter not found or export fails
    """
    # Parse chapter_id as novel_id:chapter_number
    if ":" not in chapter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chapter_id format. Use: novel_id:chapter_number"
        )
    
    novel_id, chapter_num_str = chapter_id.split(":", 1)
    
    try:
        chapter_num = int(chapter_num_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chapter number in chapter_id"
        )
    
    try:
        chapters = _get_novel_chapters(novel_id, [chapter_num])
        
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_num} not found in novel {novel_id}"
            )
        
        chapter = chapters[0]
        
        # Generate content based on requested format
        format_lower = request.format.lower()
        
        if format_lower == "txt":
            content = _generate_txt_content([chapter], request.include_metadata)
            content_bytes = content.encode("utf-8")
            media_type = "text/plain; charset=utf-8"
            filename = f"chapter_{chapter_num}.txt"
        elif format_lower == "epub":
            content_bytes = _generate_epub(novel_id, [chapter], request.include_metadata)
            media_type = "application/epub+zip"
            filename = f"chapter_{chapter_num}.epub"
        elif format_lower == "pdf":
            content_bytes = _generate_pdf(novel_id, [chapter], request.include_metadata)
            media_type = "application/pdf"
            filename = f"chapter_{chapter_num}.pdf"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {request.format}. Use: txt, epub, or pdf"
            )
        
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content_bytes)),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chapter export failed for {chapter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
