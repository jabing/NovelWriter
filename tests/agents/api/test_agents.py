"""Tests for agents router."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import StudioState


class TestListAgentTypes:
    """Tests for GET /api/agents endpoint."""

    def test_list_agent_types_with_orchestrator(self, client: TestClient, mock_orchestrator):
        """Test listing agent types when orchestrator is available."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orchestrator
            
            response = client.get("/api/agents/")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    def test_list_agent_types_without_orchestrator(self, client: TestClient):
        """Test listing agent types when orchestrator is not available."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator", None):
            response = client.get("/api/agents/")
            
            assert response.status_code == 500
            assert "unavailable" in response.json()["detail"].lower()

    def test_list_agent_types_fallback(self, client: TestClient):
        """Test fallback agent types when orchestrator doesn't have get_agent_types."""
        mock_orch = MagicMock()
        # No get_agent_types method, but has agent_types attribute
        mock_orch.agent_types = ["custom1", "custom2"]
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.get("/api/agents/")
            
            assert response.status_code == 200
            data = response.json()
            assert "custom1" in data
            assert "custom2" in data


class TestGetAgentStatus:
    """Tests for GET /api/agents/{agent_type}/status endpoint."""

    def test_get_agent_status_success(self, client: TestClient, mock_orchestrator):
        """Test getting agent status successfully."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orchestrator
            
            response = client.get("/api/agents/plot/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "agent_type" in data or "status" in data

    def test_get_agent_status_with_status_of(self, client: TestClient):
        """Test getting agent status using status_of method."""
        mock_orch = MagicMock()
        mock_orch.get_status.side_effect = AttributeError()
        mock_orch.status_of.return_value = {"agent_type": "character", "status": "idle"}
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.get("/api/agents/character/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == "character"

    def test_get_agent_status_fallback(self, client: TestClient):
        """Test fallback status when orchestrator has no status methods."""
        mock_orch = MagicMock()
        del mock_orch.get_status
        del mock_orch.status_of
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.get("/api/agents/unknown/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "unknown"

    def test_get_agent_status_error(self, client: TestClient):
        """Test handling errors when getting agent status."""
        mock_orch = MagicMock()
        mock_orch.get_status.side_effect = Exception("Status error")
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.get("/api/agents/plot/status")
            
            assert response.status_code == 400

    def test_get_agent_status_orchestrator_unavailable(self, client: TestClient):
        """Test status when orchestrator is unavailable."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator", None):
            response = client.get("/api/agents/plot/status")
            
            assert response.status_code == 500


class TestExecuteAgent:
    """Tests for POST /api/agents/{agent_type}/execute endpoint."""

    def test_execute_agent_success(self, client: TestClient, mock_orchestrator):
        """Test executing agent successfully."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orchestrator
            
            response = client.post(
                "/api/agents/plot/execute",
                json={"prompt": "Test prompt", "params": {"length": "short"}}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_execute_agent_with_payload(self, client: TestClient):
        """Test executing agent with payload."""
        mock_orch = MagicMock()
        mock_orch.execute.return_value = {
            "success": True,
            "result": "Generated content",
            "tokens_used": 150
        }
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.post(
                "/api/agents/writer/execute",
                json={"prompt": "Write a scene", "params": {"genre": "fantasy"}}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_execute_agent_no_execute_method(self, client: TestClient):
        """Test executing agent when orchestrator doesn't have execute method."""
        mock_orch = MagicMock()
        del mock_orch.execute
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.post(
                "/api/agents/plot/execute",
                json={"prompt": "Test"}
            )
            
            assert response.status_code == 501

    def test_execute_agent_error(self, client: TestClient):
        """Test handling errors during agent execution."""
        mock_orch = MagicMock()
        mock_orch.execute.side_effect = Exception("Execution failed")
        
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator") as mock_orch_class:
            mock_orch_class.return_value = mock_orch
            
            response = client.post(
                "/api/agents/plot/execute",
                json={"prompt": "Test"}
            )
            
            assert response.status_code == 500

    def test_execute_agent_orchestrator_unavailable(self, client: TestClient):
        """Test execution when orchestrator is unavailable."""
        with patch("src.novel_agent.api.routers.agents.AgentOrchestrator", None):
            response = client.post(
                "/api/agents/plot/execute",
                json={"prompt": "Test"}
            )
            
            assert response.status_code == 500
