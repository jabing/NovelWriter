"""Chapters API router for chapters listing and content retrieval."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from src.novel_agent.api.schemas.chapters import ChapterCreate, ChapterListResponse, ChapterResponse, ChapterUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/novels", tags=["chapters"], redirect_slashes=False)


def _extract_chapter_number_from_filename(p: Path) -> int | None:
    # Expect filenames like chapter_001.json or chapter_001.md
    try:
        stem = p.stem  # e.g., 'chapter_001'
        parts = stem.split("_")
        if len(parts) >= 2:
            return int(parts[1])
    except Exception:
        pass
    return None


def _mk_chapter_from_json(p: Path) -> ChapterResponse | None:
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    number = data.get("number")
    if isinstance(number, int):
        chapter_num = number
    else:
        chapter_num = _extract_chapter_number_from_filename(p) or 0

    title = data.get("title") or f"Chapter {chapter_num}"
    content = data.get("content") if isinstance(data.get("content"), str) else None
    word_count = len(content.split()) if isinstance(content, str) else 0
    summary = data.get("author_notes")
    return ChapterResponse(
        chapter_number=chapter_num,
        title=title,
        word_count=word_count,
        status="published",
        content=content,
        summary=summary,
        created_at=None,
        updated_at=None,
    )


def _mk_chapter_from_md(p: Path) -> ChapterResponse:
    chapter_num = _extract_chapter_number_from_filename(p) or 0
    title = f"Chapter {chapter_num}"
    try:
        with open(p, encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("#"):
                title = first_line.lstrip("#").strip()
    except Exception:
        pass
    return ChapterResponse(
        chapter_number=chapter_num,
        title=title,
        word_count=0,
        status="published",
        content=None,
        summary=None,
        created_at=None,
        updated_at=None,
    )


@router.get("/{novel_id}/chapters", response_model=ChapterListResponse)
def list_chapters(novel_id: str) -> ChapterListResponse:
    chapters_dir = Path(f"data/openviking/memory/novels/{novel_id}/chapters")
    if not chapters_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel or chapters not found")

    chapters_by_num: dict[int, ChapterResponse] = {}

    # Load JSON chapters first (rich metadata/content)
    for p in sorted(chapters_dir.glob("chapter_*.json")):
        ch = _mk_chapter_from_json(p)
        if ch:
            chapters_by_num[ch.chapter_number] = ch

    # Overlay/augment with MD chapters if they don't exist from JSON
    for p in sorted(chapters_dir.glob("chapter_*.md")):
        num = _extract_chapter_number_from_filename(p)
        if num is None:
            continue
        if num in chapters_by_num:
            continue
        chapters_by_num[num] = _mk_chapter_from_md(p)

    chapters = [chapters_by_num[n] for n in sorted(chapters_by_num.keys()) if chapters_by_num[n] is not None]

    total_count = len(chapters)
    completed_count = total_count

    return ChapterListResponse(
        project_id=novel_id,
        chapters=chapters,
        total_count=total_count,
        completed_count=completed_count,
    )


@router.get("/{novel_id}/chapters/{num}", response_model=ChapterResponse)
def get_chapter(novel_id: str, num: int) -> ChapterResponse:
    chapters_dir = Path(f"data/openviking/memory/novels/{novel_id}/chapters")
    if not chapters_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel or chapters not found")

    json_path = chapters_dir / f"chapter_{num:03d}.json"
    if json_path.exists():
        ch = _mk_chapter_from_json(json_path)
        if ch:
            return ch

    md_path = chapters_dir / f"chapter_{num:03d}.md"
    if md_path.exists():
        return _mk_chapter_from_md(md_path)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter {num} not found for novel {novel_id}")


@router.post("/{novel_id}/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
def create_chapter(novel_id: str, chapter: ChapterCreate) -> ChapterResponse:
    """Create a new chapter for a novel.
    
    Args:
        novel_id: The novel identifier
        chapter: Chapter creation data (title, content, order, status)
    
    Returns:
        The created chapter with assigned chapter_number and timestamps
    
    Raises:
        HTTPException: If novel directory doesn't exist or chapter creation fails
    """
    # Validate novel exists by checking if novel directory exists
    novel_dir = Path(f"data/openviking/memory/novels/{novel_id}")
    if not novel_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    
    # Create chapters directory if it doesn't exist
    chapters_dir = novel_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    # Find next chapter number
    existing_chapters: list[int] = []
    for p in chapters_dir.glob("chapter_*.json"):
        num = _extract_chapter_number_from_filename(p)
        if num is not None:
            existing_chapters.append(num)
    
    next_chapter_num = max(existing_chapters, default=0) + 1
    
    # Create chapter data
    chapter_data: dict[str, Any] = {
        "number": next_chapter_num,
        "title": chapter.title,
        "content": chapter.content,
        "order": chapter.order,
        "status": chapter.status,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    # Save chapter to file
    chapter_file = chapters_dir / f"chapter_{next_chapter_num:03d}.json"
    try:
        with open(chapter_file, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save chapter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save chapter"
        )
    
    # Return created chapter
    word_count = len(chapter.content.split()) if chapter.content else 0
    return ChapterResponse(
        chapter_number=next_chapter_num,
        title=chapter.title,
        word_count=word_count,
        status=chapter.status,
        content=chapter.content,
        summary=None,
        created_at=chapter_data["created_at"],
        updated_at=chapter_data["updated_at"],
    )


@router.put("/{novel_id}/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(novel_id: str, chapter_id: str, chapter: ChapterUpdate) -> ChapterResponse:
    """Update an existing chapter for a novel.
    
    Args:
        novel_id: The novel identifier
        chapter_id: The chapter identifier (e.g., 'chapter-001' or '1')
        chapter: Chapter update data (title, content, order, status - all optional)
    
    Returns:
        The updated chapter with timestamps
    
    Raises:
        HTTPException: If novel or chapter doesn't exist or update fails
    """
    novel_dir = Path(f"data/openviking/memory/novels/{novel_id}")
    if not novel_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    
    chapters_dir = novel_dir / "chapters"
    if not chapters_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    
    chapter_num = None
    if chapter_id.startswith("chapter-"):
        try:
            chapter_num = int(chapter_id.split("-")[1])
        except (ValueError, IndexError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    else:
        try:
            chapter_num = int(chapter_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    
    chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.json"
    md_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
    
    if not chapter_file.exists() and not md_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter {chapter_num} not found")
    
    existing_data: dict[str, Any] = {}
    use_md = False
    
    if chapter_file.exists():
        try:
            with open(chapter_file, encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load chapter: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load chapter")
        use_md = False
    else:
        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else f"Chapter {chapter_num}"
                existing_data = {
                    "number": chapter_num,
                    "title": title,
                    "content": content,
                    "order": 0,
                    "status": "published",
                }
        except Exception as e:
            logger.error(f"Failed to load MD chapter: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load chapter")
        use_md = True
    
    if chapter.title is not None:
        existing_data["title"] = chapter.title
    if chapter.content is not None:
        existing_data["content"] = chapter.content
    if chapter.order is not None:
        existing_data["order"] = chapter.order
    if chapter.status is not None:
        existing_data["status"] = chapter.status
    
    existing_data["updated_at"] = datetime.now().isoformat()
    
    try:
        if use_md and md_file.exists():
            md_file.unlink()
        
        with open(chapter_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save chapter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save chapter")
    
    word_count = len(existing_data.get("content", "").split()) if existing_data.get("content") else 0
    return ChapterResponse(
        chapter_number=existing_data.get("number", chapter_num),
        title=existing_data.get("title", f"Chapter {chapter_num}"),
        word_count=word_count,
        status=existing_data.get("status", "draft"),
        order=existing_data.get("order", 0),
        content=existing_data.get("content"),
        summary=existing_data.get("author_notes"),
        created_at=existing_data.get("created_at"),
        updated_at=existing_data.get("updated_at"),
    )


@router.delete("/{novel_id}/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(novel_id: str, chapter_id: str) -> None:
    """Delete an existing chapter from a novel.
    
    Args:
        novel_id: The novel identifier
        chapter_id: The chapter identifier (e.g., 'chapter-001' or '1')
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException: If novel or chapter doesn't exist or deletion fails
    """
    novel_dir = Path(f"data/openviking/memory/novels/{novel_id}")
    if not novel_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    
    chapters_dir = novel_dir / "chapters"
    if not chapters_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    
    chapter_num = None
    if chapter_id.startswith("chapter-"):
        try:
            chapter_num = int(chapter_id.split("-")[1])
        except (ValueError, IndexError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    else:
        try:
            chapter_num = int(chapter_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    
    chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.json"
    md_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
    
    if not chapter_file.exists() and not md_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter {chapter_num} not found")
    
    try:
        if chapter_file.exists():
            chapter_file.unlink()
        if md_file.exists():
            md_file.unlink()
    except Exception as e:
        logger.error(f"Failed to delete chapter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete chapter")


@router.put("/{novel_id}/chapters/{chapter_id}/reorder", response_model=ChapterResponse)
def reorder_chapter(novel_id: str, chapter_id: str, reorder_data: dict) -> ChapterResponse:
    """Reorder a chapter within a novel.
    
    Args:
        novel_id: The novel identifier
        chapter_id: The chapter identifier (e.g., 'chapter-001' or '1')
        reorder_data: Dictionary containing 'new_order' (positive integer)
    
    Returns:
        The updated chapter with new order and updated timestamp
    
    Raises:
        HTTPException: If novel or chapter doesn't exist, or if new_order is invalid
    """
    new_order = reorder_data.get("new_order")
    if new_order is None or not isinstance(new_order, int) or new_order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_order must be a positive integer"
        )
    
    novel_dir = Path(f"data/openviking/memory/novels/{novel_id}")
    if not novel_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Novel not found")
    
    chapters_dir = novel_dir / "chapters"
    if not chapters_dir.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    
    chapter_num = None
    if chapter_id.startswith("chapter-"):
        try:
            chapter_num = int(chapter_id.split("-")[1])
        except (ValueError, IndexError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    else:
        try:
            chapter_num = int(chapter_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chapter ID format")
    
    chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.json"
    md_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
    
    if not chapter_file.exists() and not md_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chapter {chapter_num} not found")
    
    existing_data: dict[str, Any] = {}
    use_md = False
    
    if chapter_file.exists():
        try:
            with open(chapter_file, encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load chapter: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load chapter")
        use_md = False
    else:
        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else f"Chapter {chapter_num}"
                existing_data = {
                    "number": chapter_num,
                    "title": title,
                    "content": content,
                    "order": 0,
                    "status": "published",
                }
        except Exception as e:
            logger.error(f"Failed to load MD chapter: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load chapter")
        use_md = True
    
    existing_data["order"] = new_order
    existing_data["updated_at"] = datetime.now().isoformat()
    
    try:
        if use_md and md_file.exists():
            md_file.unlink()
        
        with open(chapter_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save chapter: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save chapter")
    
    word_count = len(existing_data.get("content", "").split()) if existing_data.get("content") else 0
    return ChapterResponse(
        chapter_number=existing_data.get("number", chapter_num),
        title=existing_data.get("title", f"Chapter {chapter_num}"),
        word_count=word_count,
        status=existing_data.get("status", "draft"),
        order=existing_data.get("order", 0),
        content=existing_data.get("content"),
        summary=existing_data.get("author_notes"),
        created_at=existing_data.get("created_at"),
        updated_at=existing_data.get("updated_at"),
    )
