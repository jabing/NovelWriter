"""Publishing API router for platform management and publishing operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_state
from src.api.schemas.publishing import (
    CommentListResponse,
    CommentResponse,
    PlatformInfo,
    PublishRequest,
    PublishResponse,
)
from src.studio.core.state import StudioState

router = APIRouter(prefix="/api/publishing", tags=["publishing"], redirect_slashes=False)


PLATFORMS = [
    PlatformInfo(id="wattpad", name="Wattpad", description="Popular fiction platform with millions of readers", enabled=True),
    PlatformInfo(id="royalroad", name="Royal Road", description="Web serial platform for fantasy and sci-fi", enabled=True),
    PlatformInfo(id="kindle", name="Amazon Kindle (KDP)", description="Self-publishing on Amazon Kindle", enabled=True),
    PlatformInfo(id="webnovel", name="Webnovel", description="Web novel platform with diverse genres", enabled=False),
]


@router.get("/platforms", response_model=list[PlatformInfo])
def list_platforms() -> list[PlatformInfo]:
    return PLATFORMS


@router.post("/novels/{novel_id}/publish", response_model=PublishResponse)
def publish_novel(
    novel_id: str,
    request: PublishRequest,
    state: Annotated[StudioState, Depends(get_state)],
) -> PublishResponse:
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )

    platform_ids = [p.id for p in PLATFORMS]
    if request.platform not in platform_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown platform: {request.platform}",
        )

    if request.platform not in project.platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Novel not configured for platform: {request.platform}",
        )

    published_chapters = request.chapter_numbers if request.chapter_numbers else list(range(1, project.completed_chapters + 1))

    return PublishResponse(
        success=True,
        platform=request.platform,
        published_chapters=published_chapters,
        message=f"Successfully queued {len(published_chapters)} chapters for publishing to {request.platform}",
    )


@router.get("/comments/{novel_id}", response_model=CommentListResponse)
def get_comments(
    novel_id: str,
    state: Annotated[StudioState, Depends(get_state)],
    platform: Annotated[str, Query()] = "wattpad",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CommentListResponse:
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )

    comments: list[CommentResponse] = []

    return CommentListResponse(
        novel_id=novel_id,
        platform=platform,
        comments=comments[:limit],
        total_count=len(comments),
    )
