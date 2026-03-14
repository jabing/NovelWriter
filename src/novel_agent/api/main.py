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


class ConnectionManager:
    """Manages active WebSocket connections for agent status updates."""

    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self._active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        if not self._active_connections:
            return

        message_json = json.dumps(message)
        disconnected: list[WebSocket] = []

        for connection in self._active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()


# Import routers
from src.novel_agent.api.routers import projects, chapters, characters, agents, monitoring, outlines, publishing, tasks, export, auth, search, backup

app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(characters.router)
app.include_router(agents.router)
app.include_router(monitoring.router)
app.include_router(outlines.router)
app.include_router(publishing.router)
app.include_router(tasks.router)
app.include_router(export.router)
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(backup.router)


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
