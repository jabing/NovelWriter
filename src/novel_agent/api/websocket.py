"""WebSocket module for real-time agent status and workflow progress updates.

This module provides:
- ConnectionManager: Manages WebSocket connections with per-project filtering
- broadcast_progress(): Broadcasts workflow progress updates
- Project-specific subscriptions via query parameter
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class ProjectSubscription:
    """Tracks WebSocket connections for a specific project."""
    project_id: str
    connections: set[WebSocket] = field(default_factory=set)
    
    def add_connection(self, websocket: WebSocket) -> None:
        """Add a WebSocket connection to this project subscription."""
        self.connections.add(websocket)
    
    def remove_connection(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from this project subscription."""
        self.connections.discard(websocket)
    
    def count(self) -> int:
        """Return number of active connections."""
        return len(self.connections)


class ConnectionManager:
    """Manages WebSocket connections for agent status and workflow progress updates.
    
    Supports two types of subscriptions:
    1. Global subscriptions - receives all messages
    2. Project-specific subscriptions - receives only messages for subscribed project
    
    Usage:
        manager = ConnectionManager()
        
        # Global subscription
        await manager.connect(websocket)
        await manager.disconnect(websocket)
        
        # Project-specific subscription
        await manager.connect_project(websocket, "project_123")
        await manager.disconnect_project(websocket, "project_123")
        
        # Broadcast to all
        await manager.broadcast({"type": "agent_status", ...})
        
        # Broadcast to specific project
        await manager.broadcast_project("project_123", {"type": "workflow_progress", ...})
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_connections: set[WebSocket] = set()
        self._project_subscriptions: dict[str, ProjectSubscription] = {}
        self._connection_projects: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a global WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to register
        """
        await websocket.accept()
        self._active_connections.add(websocket)
        self._connection_projects[websocket] = set()
        logger.info(f"WebSocket connected (global). Total connections: {len(self._active_connections)}")

    async def connect_project(self, websocket: WebSocket, project_id: str) -> None:
        """Register a WebSocket connection for a specific project.
        
        Args:
            websocket: The WebSocket connection to register
            project_id: The project ID to subscribe to
        """
        await websocket.accept()
        
        # Initialize connection tracking if needed
        if websocket not in self._connection_projects:
            self._connection_projects[websocket] = set()
        
        self._active_connections.add(websocket)
        
        if project_id not in self._project_subscriptions:
            self._project_subscriptions[project_id] = ProjectSubscription(project_id=project_id)
        
        self._project_subscriptions[project_id].add_connection(websocket)
        self._connection_projects[websocket].add(project_id)
        
        logger.info(f"WebSocket connected to project {project_id}. "
                   f"Project has {self._project_subscriptions[project_id].count()} connections")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket from all subscriptions.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        # Remove from global connections
        if websocket in self._active_connections:
            self._active_connections.discard(websocket)
        
        # Remove from all project subscriptions
        if websocket in self._connection_projects:
            for project_id in self._connection_projects[websocket]:
                if project_id in self._project_subscriptions:
                    self._project_subscriptions[project_id].remove_connection(websocket)
            del self._connection_projects[websocket]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self._active_connections)}")

    def disconnect_project(self, websocket: WebSocket, project_id: str) -> None:
        """Remove a WebSocket from a specific project subscription.
        
        Args:
            websocket: The WebSocket connection to remove
            project_id: The project ID to unsubscribe from
        """
        if project_id in self._project_subscriptions:
            self._project_subscriptions[project_id].remove_connection(websocket)
            
        if websocket in self._connection_projects:
            self._connection_projects[websocket].discard(project_id)
            
        logger.info(f"WebSocket disconnected from project {project_id}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message dictionary to broadcast
        """
        if not self._active_connections:
            return

        message_json = json.dumps(message)
        disconnected: set[WebSocket] = set()

        for connection in self._active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_project(self, project_id: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all subscribers of a specific project.
        
        Args:
            project_id: The project ID to broadcast to
            message: The message dictionary to broadcast
        """
        if project_id not in self._project_subscriptions:
            return

        subscription = self._project_subscriptions[project_id]
        if not subscription.connections:
            return

        message_json = json.dumps(message)
        disconnected: set[WebSocket] = set()

        for connection in subscription.connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to project {project_id} WebSocket: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect_project(conn, project_id)

    async def broadcast_global_and_project(
        self, 
        project_id: str | None, 
        message: dict[str, Any]
    ) -> None:
        """Broadcast to both global and optionally project-specific subscribers.
        
        Args:
            project_id: Optional project ID to also broadcast to
            message: The message dictionary to broadcast
        """
        await self.broadcast(message)
        
        if project_id:
            await self.broadcast_project(project_id, message)

    def get_connection_count(self) -> int:
        """Return total number of active connections."""
        return len(self._active_connections)

    def get_project_connection_count(self, project_id: str) -> int:
        """Return number of connections for a project."""
        if project_id not in self._project_subscriptions:
            return 0
        return self._project_subscriptions[project_id].count()

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific client.
        
        Args:
            message: The message dictionary to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


# =============================================================================
# Progress Broadcast Functions
# =============================================================================

async def broadcast_progress(
    task_id: str,
    progress: int,
    current_step: str,
    project_id: str | None = None,
    additional_data: dict[str, Any] | None = None
) -> None:
    """Broadcast workflow progress update to connected clients.
    
    Args:
        task_id: Unique task identifier
        progress: Progress percentage (0-100)
        current_step: Current step description
        project_id: Optional project ID for targeted broadcast
        additional_data: Optional additional metadata
    """
    message: dict[str, Any] = {
        "type": "workflow_progress",
        "data": {
            "task_id": task_id,
            "progress": progress,
            "current_step": current_step
        }
    }
    
    if additional_data:
        message["data"].update(additional_data)
    
    await manager.broadcast_global_and_project(project_id, message)


async def broadcast_workflow_start(
    task_id: str,
    project_id: str,
    workflow_type: str = "chapter_generation",
    total_steps: int = 10
) -> None:
    """Broadcast workflow start notification.
    
    Args:
        task_id: Unique task identifier
        project_id: Project ID
        workflow_type: Type of workflow (e.g., "chapter_generation", "outline_generation")
        total_steps: Estimated total steps
    """
    await broadcast_progress(
        task_id=task_id,
        progress=0,
        current_step=f"Starting {workflow_type}",
        project_id=project_id,
        additional_data={
            "workflow_type": workflow_type,
            "total_steps": total_steps
        }
    )


async def broadcast_workflow_complete(
    task_id: str,
    project_id: str,
    results: dict[str, Any] | None = None
) -> None:
    """Broadcast workflow completion notification.
    
    Args:
        task_id: Unique task identifier
        project_id: Project ID
        results: Optional workflow results
    """
    await broadcast_progress(
        task_id=task_id,
        progress=100,
        current_step="Workflow completed",
        project_id=project_id,
        additional_data={"completed": True, "results": results or {}}
    )


async def broadcast_workflow_error(
    task_id: str,
    project_id: str,
    error_message: str,
    step: str | None = None
) -> None:
    """Broadcast workflow error notification.
    
    Args:
        task_id: Unique task identifier
        project_id: Project ID
        error_message: Error description
        step: Step where error occurred
    """
    await broadcast_progress(
        task_id=task_id,
        progress=0,
        current_step=step or "Error occurred",
        project_id=project_id,
        additional_data={
            "error": True,
            "error_message": error_message
        }
    )


async def broadcast_workflow_step_complete(
    task_id: str,
    project_id: str,
    step_name: str,
    progress: int
) -> None:
    """Broadcast individual workflow step completion.
    
    Args:
        task_id: Unique task identifier
        project_id: Project ID
        step_name: Name of completed step
        progress: Current progress percentage
    """
    await broadcast_progress(
        task_id=task_id,
        progress=progress,
        current_step=f"Completed: {step_name}",
        project_id=project_id
    )


# =============================================================================
# Query helpers
# =============================================================================

def extract_project_id_from_query(query_params: str) -> str | None:
    """Extract project_id from WebSocket query parameters.
    
    Args:
        query_params: Query string (e.g., "project_id=abc123")
        
    Returns:
        Project ID if found, None otherwise
    """
    if not query_params:
        return None
    
    try:
        params = query_params.split("&")
        for param in params:
            if param.startswith("project_id="):
                return param.split("=", 1)[1]
    except Exception:
        pass
    
    return None


async def subscribe_to_project_from_query(
    websocket: WebSocket,
    query_params: str
) -> str | None:
    """Connect WebSocket and subscribe to project from query params.
    
    Args:
        websocket: The WebSocket connection
        query_params: Query string with project_id
        
    Returns:
        Project ID if subscription successful, None otherwise
    """
    project_id = extract_project_id_from_query(query_params)
    
    if project_id:
        await manager.connect_project(websocket, project_id)
        return project_id
    
    await manager.connect(websocket)
    return None


__all__ = [
    "ConnectionManager",
    "manager",
    "broadcast_progress",
    "broadcast_workflow_start",
    "broadcast_workflow_complete",
    "broadcast_workflow_error",
    "broadcast_workflow_step_complete",
    "extract_project_id_from_query",
    "subscribe_to_project_from_query",
]
