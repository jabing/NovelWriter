"""Projects API router for CRUD operations."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.novel_agent.api.dependencies import get_current_user_id, get_state
from src.novel_agent.api.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from src.novel_agent.api.routers.tasks import get_task_store
from src.novel_agent.api.schemas.workflow import (
    InitializeResponse,
    WorkflowStatus,
    WorkflowTaskResponse,
)
from src.novel_agent.api.websocket import broadcast_workflow_step_complete
from src.novel_agent.llm.deepseek import DeepSeekLLM
from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, StudioState
from src.novel_agent.utils.config import get_settings
from src.novel_agent.workflow.generate_workflow import create_generate_workflow
from src.novel_agent.workflow.plan_workflow import create_plan_workflow

router = APIRouter(prefix="/api/projects", tags=["projects"], redirect_slashes=False)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> list[ProjectResponse]:
    projects = state.get_projects()
    user_projects = [p for p in projects if p.user_id == user_id]
    return [_project_to_response(p) for p in user_projects]


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> ProjectResponse:
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    project = NovelProject(
        id=project_id,
        title=project_data.title,
        genre=project_data.genre,
        language=project_data.language,
        status=ProjectStatus.PLANNING,
        user_id=user_id,
        premise=project_data.premise,
        themes=project_data.themes,
        pov=project_data.pov,
        tone=project_data.tone,
        target_audience=project_data.target_audience,
        story_structure=project_data.story_structure,
        content_rating=project_data.content_rating,
        target_chapters=project_data.target_chapters,
        target_words=project_data.target_words,
        platforms=project_data.platforms,
        created_at=now,
        updated_at=now,
    )

    state.add_project(project)
    return _project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> ProjectResponse:
    """Get a specific project by ID."""
    project = state.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: this project does not belong to you",
        )
    return _project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> ProjectResponse:
    """Update an existing project."""
    project = state.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: this project does not belong to you",
        )

    update_data = project_data.model_dump(exclude_unset=True)

    if "title" in update_data:
        project.title = update_data["title"]
    if "genre" in update_data:
        project.genre = update_data["genre"]
    if "language" in update_data:
        project.language = update_data["language"]
    if "status" in update_data:
        project.status = ProjectStatus(update_data["status"].value)
    if "premise" in update_data:
        project.premise = update_data["premise"]
    if "themes" in update_data:
        project.themes = update_data["themes"]
    if "pov" in update_data:
        project.pov = update_data["pov"]
    if "tone" in update_data:
        project.tone = update_data["tone"]
    if "target_audience" in update_data:
        project.target_audience = update_data["target_audience"]
    if "story_structure" in update_data:
        project.story_structure = update_data["story_structure"]
    if "content_rating" in update_data:
        project.content_rating = update_data["content_rating"]
    if "target_chapters" in update_data:
        project.target_chapters = update_data["target_chapters"]
    if "target_words" in update_data:
        project.target_words = update_data["target_words"]
    if "platforms" in update_data:
        project.platforms = update_data["platforms"]

    state.update_project(project)
    return _project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> None:
    """Delete a project."""
    project = state.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: this project does not belong to you",
        )
    deleted = state.delete_project(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )



@router.post(
    "/{project_id}/generate-chapters",
    response_model=WorkflowTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_chapters(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
    start_chapter: int = 1,
    count: int = 1,
    resume: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> WorkflowTaskResponse:
    project = state.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: this project does not belong to you",
        )

    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        _run_chapter_generation,
        project_id=project_id,
        start_chapter=start_chapter,
        count=count,
        resume=resume,
        state=state,
    )

    return WorkflowTaskResponse(task_id=task_id, status="queued")


async def _run_chapter_generation(
    project_id: str,
    start_chapter: int,
    count: int,
    resume: bool,
    state: StudioState,
) -> None:
    settings = get_settings()
    llm = DeepSeekLLM(api_key=settings.deepseek_api_key.get_secret_value())

    workflow = create_generate_workflow(
        name="chapter_generator",
        llm=llm,
        genre="fantasy",
    )

    project = state.get_project(project_id)
    if project is None:
        return

    result = await workflow.execute(
        project_id=project_id,
        start_chapter=start_chapter,
        count=count,
        storage_path=Path("data/openviking/memory"),
        resume=resume,
    )

    if result.success and result.chapters_generated > 0:
        project.completed_chapters += result.chapters_generated
        state.update_project(project)



def _project_to_response(project: NovelProject) -> ProjectResponse:
    """Convert a NovelProject to a ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        title=project.title,
        genre=project.genre,
        language=project.language,
        status=project.status.value,
        user_id=project.user_id,
        premise=project.premise,
        themes=project.themes,
        pov=project.pov,
        tone=project.tone,
        target_audience=project.target_audience,
        story_structure=project.story_structure,
        content_rating=project.content_rating,
        sensitive_handling=project.sensitive_handling,
        target_chapters=project.target_chapters,
        completed_chapters=project.completed_chapters,
        total_words=project.total_words,
        target_words=project.target_words,
        progress_percent=project.progress_percent,
        created_at=project.created_at,
        updated_at=project.updated_at,
        platforms=project.platforms,
        published_chapters=project.published_chapters,
        total_reads=project.total_reads,
        total_votes=project.total_votes,
        total_comments=project.total_comments,
        followers=project.followers,
    )
