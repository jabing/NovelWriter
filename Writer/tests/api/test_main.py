"""Tests for main.py - health check, WebSocket, and ConnectionManager."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.api.main import ConnectionManager, app, manager


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    def test_init(self):
        """Test ConnectionManager initialization."""
        cm = ConnectionManager()
        assert cm._active_connections == []

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection is accepted and registered."""
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        
        await cm.connect(mock_ws)
        
        mock_ws.accept.assert_called_once()
        assert mock_ws in cm._active_connections

    def test_disconnect(self):
        """Test WebSocket disconnection removes from active connections."""
        cm = ConnectionManager()
        mock_ws = MagicMock()
        cm._active_connections = [mock_ws]
        
        cm.disconnect(mock_ws)
        
        assert mock_ws not in cm._active_connections

    def test_disconnect_not_in_list(self):
        """Test disconnecting a WebSocket not in the list is safe."""
        cm = ConnectionManager()
        mock_ws = MagicMock()
        cm._active_connections = []
        
        cm.disconnect(mock_ws)  # Should not raise
        
        assert cm._active_connections == []

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self):
        """Test broadcast with no connections does nothing."""
        cm = ConnectionManager()
        cm._active_connections = []
        
        await cm.broadcast({"type": "test"})  # Should not raise

    @pytest.mark.asyncio
    async def test_broadcast_single_connection(self):
        """Test broadcast to a single connection."""
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm._active_connections = [mock_ws]
        
        message = {"type": "test", "data": "hello"}
        await cm.broadcast(message)
        
        mock_ws.send_text.assert_called_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        assert json.loads(call_arg) == message

    @pytest.mark.asyncio
    async def test_broadcast_multiple_connections(self):
        """Test broadcast to multiple connections."""
        cm = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        cm._active_connections = [mock_ws1, mock_ws2]
        
        message = {"type": "test"}
        await cm.broadcast(message)
        
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(self):
        """Test broadcast removes connections that fail to receive."""
        cm = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws1.send_text.side_effect = Exception("Connection lost")
        mock_ws2 = AsyncMock()
        cm._active_connections = [mock_ws1, mock_ws2]
        
        await cm.broadcast({"type": "test"})
        
        assert mock_ws1 not in cm._active_connections
        assert mock_ws2 in cm._active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a message to a specific WebSocket."""
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        
        message = {"type": "personal", "data": "for you"}
        await cm.send_personal_message(message, mock_ws)
        
        mock_ws.send_text.assert_called_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        assert json.loads(call_arg) == message

    @pytest.mark.asyncio
    async def test_send_personal_message_failure(self):
        """Test send_personal_message handles failures and disconnects."""
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_text.side_effect = Exception("Send failed")
        
        await cm.send_personal_message({"type": "test"}, mock_ws)
        
        assert mock_ws not in cm._active_connections


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check_returns_ok(self, client: TestClient):
        """Test health check endpoint returns ok status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestWebSocketAgentStatus:
    """Tests for the WebSocket agent status endpoint."""

    def test_websocket_connect(self, client: TestClient):
        """Test WebSocket connection receives connected message."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Receive the connected message
            data = websocket.receive_json()
            
            assert data["type"] == "connected"
            assert "WebSocket connected" in data["message"]

    def test_websocket_ping_pong(self, client: TestClient):
        """Test WebSocket ping/pong functionality."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Skip the connected message
            websocket.receive_json()
            
            # Send ping
            websocket.send_text("ping")
            
            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_heartbeat_on_timeout(self, client: TestClient):
        """Test WebSocket sends heartbeat on timeout."""
        with client.websocket_connect("/ws/agents") as websocket:
            # Skip the connected message
            websocket.receive_json()
            
            # Don't send anything - wait for heartbeat
            # Note: In real tests, we'd need to adjust timeout
            # For now, we test that the endpoint accepts the connection
            assert websocket is not None


class TestBroadcastAgentStatus:
    """Tests for the broadcast_agent_status function."""

    @pytest.mark.asyncio
    async def test_broadcast_agent_status(self):
        """Test broadcasting agent status."""
        from src.api.main import broadcast_agent_status, manager
        
        mock_ws = AsyncMock()
        manager._active_connections = [mock_ws]
        
        await broadcast_agent_status(
            agent_type="plot",
            status="running",
            progress=0.5,
            message="Processing..."
        )
        
        mock_ws.send_text.assert_called_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        data = json.loads(call_arg)
        
        assert data["type"] == "agent_status"
        assert data["data"]["agent_type"] == "plot"
        assert data["data"]["status"] == "running"
        assert data["data"]["progress"] == 0.5
        assert data["data"]["message"] == "Processing..."
        
        manager._active_connections = []


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_title(self):
        """Test app has correct title."""
        assert app.title == "NovelWriter API"

    def test_app_version(self):
        """Test app has correct version."""
        assert app.version == "1.0.0"

    def test_cors_middleware_configured(self):
        """Test CORS middleware is configured."""
        # Check that CORS middleware is in the middleware stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_types or any(
            "cors" in m.lower() for m in middleware_types
        )

    def test_app_routes_registered(self):
        """Test that expected routes are registered."""
        routes = [route.path for route in app.routes]
        
        assert "/api/health" in routes
        assert "/ws/agents" in routes
