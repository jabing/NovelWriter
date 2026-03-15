"""FastAPI application for NovelWriter API.

This module provides the main FastAPI application instance with CORS middleware
for the Vue3 web frontend.
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from src.novel_agent.api.rate_limit import RateLimitMiddleware, rate_limiter
from src.novel_agent.api.websocket import manager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NovelWriter API",
    description="API for AI-powered novel writing and publishing system",
    version="1.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    limiter=rate_limiter,
)


# Import routers (only those in plan - Wave 2)
from src.novel_agent.api.routers import (
    agents,
    chapters,
    characters,
    graph,
    monitoring,
    projects,
    publishing,
    tasks,
)

# Include routers in app
app.include_router(agents.router)
app.include_router(chapters.router)
app.include_router(characters.router)
app.include_router(graph.router)
app.include_router(monitoring.router)
app.include_router(projects.router)
app.include_router(publishing.router)
app.include_router(tasks.router)

__all__ = [
    "agents_router",
    "chapters_router",
    "characters_router",
    "graph_router",
    "monitoring_router",
    "projects_router",
    "publishing_router",
    "tasks_router",
]


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc) if not isinstance(exc, HTTPException) else exc.detail,
            "path": str(request.url)
        }
    )


@app.websocket("/ws/agents")
async def websocket_agent_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent status updates.

    Message format:
    {
        "type": "agent_status",
        "data": {
            "agent_type": "plot",
            "status": "running",
            "progress": 0.5,
            "message": "Processing..."
        }
    }
    """
    await manager.connect(websocket)
    try:
        await manager.send_personal_message(
            {"type": "connected", "message": "WebSocket connected for agent status updates"},
            websocket
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)

            except asyncio.TimeoutError:
                await manager.send_personal_message({"type": "heartbeat"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from agent status WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_agent_status(agent_type: str, status: str, progress: float = 0.0, message: str = "") -> None:
    """
    Broadcast agent status update to all connected WebSocket clients.

    Args:
        agent_type: Type of agent (e.g., "plot", "character", "worldbuilding")
        status: Current status (e.g., "idle", "running", "completed", "failed")
        progress: Progress percentage (0.0 to 1.0)
        message: Optional status message
    """
    await manager.broadcast({
        "type": "agent_status",
        "data": {
            "agent_type": agent_type,
            "status": status,
            "progress": progress,
            "message": message
        }
    })


@app.get("/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """Get rate limit status for the current client."""
    from src.novel_agent.api.rate_limit import rate_limiter

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return rate_limiter.get_client_status(client_ip)


# =============================================================================
# Workflow Progress Broadcasting Integration
# =============================================================================

# Import from websocket for.broadcast functions
from src.novel_agent.api.websocket import (
    broadcast_progress as _broadcast_progress,
    broadcast_workflow_start as _broadcast_workflow_start,
    broadcast_workflow_complete as _broadcast_workflow_complete,
    broadcast_workflow_error as _broadcast_workflow_error,
    broadcast_workflow_step_complete as _broadcast_workflow_step_complete,
)

__all__.extend([
    "manager",
    "broadcast_progress",
    "broadcast_workflow_start",
    "broadcast_workflow_complete",
    "broadcast_workflow_error",
    "broadcast_workflow_step_complete",
])


async def broadcast_progress(
    task_id: str,
    progress: int,
    current_step: str,
    project_id: str | None = None,
    additional_data: dict[str, Any] | None = None
) -> None:
    await _broadcast_progress(task_id, progress, current_step, project_id, additional_data)


async def broadcast_workflow_start(
    task_id: str,
    project_id: str,
    workflow_type: str = "chapter_generation",
    total_steps: int = 10
) -> None:
    await _broadcast_workflow_start(task_id, project_id, workflow_type, total_steps)


async def broadcast_workflow_complete(
    task_id: str,
    project_id: str,
    results: dict[str, Any] | None = None
) -> None:
    await _broadcast_workflow_complete(task_id, project_id, results)


async def broadcast_workflow_error(
    task_id: str,
    project_id: str,
    error_message: str,
    step: str | None = None
) -> None:
    await _broadcast_workflow_error(task_id, project_id, error_message, step)


async def broadcast_workflow_step_complete(
    task_id: str,
    project_id: str,
    step_name: str,
    progress: int
) -> None:
    await _broadcast_workflow_step_complete(task_id, project_id, step_name, progress)
