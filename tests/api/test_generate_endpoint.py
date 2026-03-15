"""Tests for generate-chapters endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


class TestGenerateChaptersAccessDenied:
    """Tests for access denied scenarios."""

    def test_generate_chapters_access_denied(
        self,
        client: TestClient,
        sample_project: "NovelProject",
        mock_studio_state: "StudioState",
    ) -> None:
        """Test access denied for project from different user."""
        project_id = sample_project.id

        # Override user_id dependency
        from src.novel_agent.api.dependencies import get_current_user_id
        client.app.dependency_overrides[get_current_user_id] = lambda: "different-user"
        try:
            response = client.post(
                f"/api/projects/{project_id}/generate-chapters",
                params={"start_chapter": 1, "count": 1},
            )
            assert response.status_code == 403
            assert "denied" in response.json()["detail"].lower()
        finally:
            client.app.dependency_overrides[get_current_user_id] = lambda: "test-user"
