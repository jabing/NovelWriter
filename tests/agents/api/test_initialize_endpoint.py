"""Tests for POST /api/projects/{id}/initialize endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import NovelProject, StudioState


class TestInitializeEndpointSuccess:
    """Tests for successful project initialization."""

    def test_init_endpoint_success(
        self,
        client: TestClient,
        sample_project: "NovelProject",
    ):
        """Test successful project initialization returns correct response."""
        response = client.post(
            f"/api/projects/{sample_project.id}/initialize",
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        assert data["message"] == "Initialization queued successfully"

    def test_init_endpoint_returns_202(
        self,
        client: TestClient,
        sample_project: "NovelProject",
    ):
        """Test that endpoint returns 202 Accepted status."""
        response = client.post(
            f"/api/projects/{sample_project.id}/initialize",
        )
        
        assert response.status_code == 202


class TestInitializeEndpointNotFound:
    """Tests for project not found scenarios."""

    def test_init_endpoint_project_not_found(
        self,
        client: TestClient,
    ):
        """Test initializing non-existent project returns 404."""
        response = client.post(
            "/api/projects/nonexistent-id-12345/initialize",
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestInitializeEndpointAuthentication:
    """Tests for authentication/authorization scenarios."""

    def test_init_endpoint_wrong_user(
        self,
        client: TestClient,
        mock_studio_state: "StudioState",
    ):
        """Test user cannot initialize another user's project."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="project-wrong-user",
            title="Other User's Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
            user_id="other-user",
            premise="Test premise",
        )
        mock_studio_state.add_project(project)

        response = client.post(
            f"/api/projects/{project.id}/initialize",
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "denied" in data["detail"].lower() or "does not belong" in data["detail"].lower()


class TestInitializeEndpointRequest:
    """Tests for request body handling."""

    def test_init_endpoint_empty_request_body(
        self,
        client: TestClient,
        sample_project: "NovelProject",
    ):
        """Test endpoint accepts empty request body."""
        response = client.post(
            f"/api/projects/{sample_project.id}/initialize",
            json={},
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"
