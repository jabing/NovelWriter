"""Outlines API router for outline management and AI generation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.novel_agent.api.dependencies import get_state
from src.novel_agent.api.schemas.outlines import (
    OutlineChapterResponse,
    OutlineGenerateRequest,
    OutlineListResponse,
    OutlineResponse,
    OutlineUpdate,
)
from src.novel_agent.llm.deepseek import DeepSeekLLM
from src.novel_agent.novel.outline_generator import OutlineGenerator
from src.novel_agent.studio.core.state import StudioState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["outlines"], redirect_slashes=False)


def _get_outlines_dir(novel_id: str) -> Path:
    """Get the outlines directory for a novel."""
    return Path(f"data/openviking/memory/novels/{novel_id}/outlines")


def _get_llm_client() -> DeepSeekLLM:
    """Create and return a DeepSeek LLM client."""
    try:
        return DeepSeekLLM()
    except ValueError as e:
        logger.error(f"Failed to initialize DeepSeek LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Please check API key configuration.",
        )


@router.get(
    "/novels/{novel_id}/outlines",
    response_model=OutlineListResponse,
)
def list_outlines(
    novel_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> OutlineListResponse:
    """List all outlines for a novel.
    
    Args:
        novel_id: The novel identifier
        state: Studio state dependency
    
    Returns:
        List of outline metadata
    
    Raises:
        HTTPException: If novel doesn't exist
    """
    # Validate novel exists
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )
    
    outlines_dir = _get_outlines_dir(novel_id)
    outlines: list[dict[str, str]] = []
    
    if outlines_dir.exists():
        for outline_file in sorted(outlines_dir.glob("outline_*.json")):
            try:
                with open(outline_file, encoding="utf-8") as f:
                    data = json.load(f)
                
                outlines.append({
                    "outline_id": outline_file.stem,
                    "title": data.get("title", f"Outline {outline_file.stem}"),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception as e:
                logger.warning(f"Failed to load outline {outline_file}: {e}")
                continue
    
    return OutlineListResponse(
        novel_id=novel_id,
        outlines=outlines,
        total_count=len(outlines),
    )


@router.post(
    "/novels/{novel_id}/outlines/generate",
    response_model=OutlineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_outline(
    novel_id: str,
    request: OutlineGenerateRequest,
    state: Annotated[StudioState, Depends(get_state)],
) -> OutlineResponse:
    """Generate an outline using AI based on story idea.
    
    Args:
        novel_id: The novel identifier
        request: Outline generation request with story idea and chapter count
        state: Studio state dependency
    
    Returns:
        Generated outline with chapter details
    
    Raises:
        HTTPException: If novel doesn't exist or generation fails
    """
    # Validate novel exists
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )
    
    # Create outlines directory
    outlines_dir = _get_outlines_dir(novel_id)
    outlines_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize LLM and outline generator
        llm = _get_llm_client()
        generator = OutlineGenerator(llm)
        
        # Build story idea with genre if provided
        story_idea = request.story_idea
        if request.genre:
            story_idea = f"{request.genre} story: {story_idea}"
        
        # Generate outline using AI
        logger.info(f"Generating outline for novel {novel_id} with {request.num_chapters} chapters")
        chapter_specs = await generator.generate_outline(
            story_idea=story_idea,
            num_chapters=request.num_chapters,
        )
        
        if not chapter_specs:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate outline. Please try again.",
            )
        
        # Convert chapter specs to response format
        chapters = []
        for chapter_spec in chapter_specs:
            plot_events = []
            for event in chapter_spec.plot_events:
                plot_events.append({
                    "description": event.description,
                    "characters_involved": ", ".join(event.characters_involved) if event.characters_involved else "",
                    "location": event.location,
                    "time_of_day": event.time_of_day,
                })
            
            chapters.append({
                "number": chapter_spec.number,
                "title": chapter_spec.title,
                "summary": chapter_spec.summary,
                "plot_events": plot_events,
                "state_changes": chapter_spec.state_changes,
                "characters": chapter_spec.characters,
                "location": chapter_spec.location,
            })
        
        # Generate outline ID and timestamps
        outline_id = f"outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        # Save outline to file
        outline_data: dict[str, Any] = {
            "outline_id": outline_id,
            "novel_id": novel_id,
            "title": f"Generated Outline - {request.genre or 'General'}",
            "genre": request.genre,
            "story_idea": request.story_idea,
            "chapters": chapters,
            "total_chapters": len(chapters),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        
        outline_file = outlines_dir / f"{outline_id}.json"
        with open(outline_file, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully generated outline {outline_id} for novel {novel_id}")
        
        return OutlineResponse(
            novel_id=novel_id,
            outline_id=outline_id,
            chapters=[OutlineChapterResponse(**ch) for ch in chapters],
            total_chapters=len(chapters),
            created_at=timestamp,
            updated_at=timestamp,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating outline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outline generation failed: {str(e)}",
        )


@router.put(
    "/outlines/{outline_id}",
    response_model=OutlineResponse,
)
def update_outline(
    outline_id: str,
    outline_data: OutlineUpdate,
    state: Annotated[StudioState, Depends(get_state)],
) -> OutlineResponse:
    """Update an existing outline.
    
    Args:
        outline_id: The outline identifier (format: novel_id/outline_*)
        outline_data: Update data (title, chapters, notes - all optional)
        state: Studio state dependency
    
    Returns:
        Updated outline
    
    Raises:
        HTTPException: If outline doesn't exist or update fails
    """
    # Parse outline_id to extract novel_id
    # Expected format: "novel_id/outline_timestamp" or just "outline_timestamp"
    if "/" in outline_id:
        novel_id, outline_name = outline_id.split("/", 1)
    else:
        # If no novel_id in outline_id, we can't proceed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid outline_id format. Expected: novel_id/outline_name",
        )
    
    # Validate novel exists
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )
    
    outlines_dir = _get_outlines_dir(novel_id)
    outline_file = outlines_dir / f"{outline_name}.json"
    
    if not outline_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outline {outline_name} not found for novel {novel_id}",
        )
    
    # Load existing outline
    try:
        with open(outline_file, encoding="utf-8") as f:
            existing_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load outline",
        )
    
    # Apply updates
    update_dict = outline_data.model_dump(exclude_unset=True)
    
    if "title" in update_dict and update_dict["title"] is not None:
        existing_data["title"] = update_dict["title"]
    
    if "chapters" in update_dict and update_dict["chapters"] is not None:
        existing_data["chapters"] = update_dict["chapters"]
        existing_data["total_chapters"] = len(update_dict["chapters"])
    
    if "notes" in update_dict and update_dict["notes"] is not None:
        existing_data["notes"] = update_dict["notes"]
    
    # Update timestamp
    existing_data["updated_at"] = datetime.now().isoformat()
    
    # Save updated outline
    try:
        with open(outline_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save outline",
        )
    
    # Build response
    chapters = []
    for ch_data in existing_data.get("chapters", []):
        chapters.append(OutlineChapterResponse(
            number=ch_data.get("number", 0),
            title=ch_data.get("title", ""),
            summary=ch_data.get("summary", ""),
            plot_events=ch_data.get("plot_events", []),
            state_changes=ch_data.get("state_changes", {}),
            characters=ch_data.get("characters", []),
            location=ch_data.get("location", ""),
        ))
    
    return OutlineResponse(
        novel_id=novel_id,
        outline_id=outline_name,
        chapters=chapters,
        total_chapters=existing_data.get("total_chapters", len(chapters)),
        created_at=existing_data.get("created_at"),
        updated_at=existing_data.get("updated_at"),
    )


@router.delete(
    "/outlines/{outline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_outline(
    outline_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> None:
    """Delete an outline.
    
    Args:
        outline_id: The outline identifier (format: novel_id/outline_*)
        state: Studio state dependency
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException: If outline doesn't exist or deletion fails
    """
    # Parse outline_id to extract novel_id
    if "/" in outline_id:
        novel_id, outline_name = outline_id.split("/", 1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid outline_id format. Expected: novel_id/outline_name",
        )
    
    # Validate novel exists
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )
    
    outlines_dir = _get_outlines_dir(novel_id)
    outline_file = outlines_dir / f"{outline_name}.json"
    
    if not outline_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outline {outline_name} not found for novel {novel_id}",
        )
    
    try:
        outline_file.unlink()
        logger.info(f"Deleted outline {outline_name} for novel {novel_id}")
    except Exception as e:
        logger.error(f"Failed to delete outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete outline",
        )
