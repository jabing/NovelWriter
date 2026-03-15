"""Tests for generate-chapters endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import StudioState


class TestGenerateChaptersSuccess:
    """Tests for successful chapter generation requests."""

    def test_generate_chapters_success(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test generating chapters returns 202 with task_id."""
        project_id = sample_project.id

        response = client.post(
            f"/api/projects/{project_id}/generate-chapters",
            params={
                "start_chapter": 1,
                "count": 5,
                "resume": False,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["task_id"]
        assert data["status"] == "queued"

    def test_generate_chapters_with_resume(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test generating chapters with resume parameter."""
        project_id = sample_project.id

        response = client.post(
            f"/api/projects/{project_id}/generate-chapters",
            params={
                "start_chapter": 3,
                "count": 2,
                "resume": True,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"

    def test_generate_chapters_default_params(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test generating chapters with default parameters."""
        project_id = sample_project.id

        response = client.post(
            f"/api/projects/{project_id}/generate-chapters",
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"


class TestGenerateChaptersValidation:
    """Tests for input validation."""

    def test_generate_chapters_invalid_count(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test that count > 100 returns 422."""
        project_id = sample_project.id

        response = client.post(
            f"/api/projects/{project_id}/generate-chapters",
            params={
                "count": 101,
            },
        )

        assert response.status_code == 422

    def test_generate_chapters_invalid_start_chapter(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test that start_chapter < 1 returns 422."""
        project_id = sample_project.id

        response = client.post(
            f"/api/projects/{project_id}/generate-chapters",
            params={
                "start_chapter": 0,
            },
        )

        assert response.status_code == 422


class TestGenerateChaptersProjectNotFound:
    """Tests for project not found scenarios."""

    def test_generate_chapters_project_not_found(
        self,
        client: TestClient,
        mock_studio_state: "StudioState",
    ) -> None:
        """Test that nonexistent project returns 404."""
        response = client.post(
            "/api/projects/nonexistent-project-id/generate-chapters",
            params={"start_chapter": 1, "count": 1},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_chapters_access_denied(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test access denied for project from different user."""
        project_id = sample_project.id

        # Mock get_current_user_id to return different user
        with patch(
            "src.novel_agent.api.routers.projects.get_current_user_id",
            return_value="different-user",
        ):
            response = client.post(
                f"/api/projects/{project_id}/generate-chapters",
                params={"start_chapter": 1, "count": 1},
            )

        assert response.status_code == 403
        assert "denied" in response.json()["detail"].lower()
