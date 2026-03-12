"""Tests for projects router."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.studio.core.state import NovelProject, StudioState


class TestListProjects:
    """Tests for GET /api/projects endpoint."""

    def test_list_projects_empty(self, client: TestClient):
        """Test listing projects when none exist."""
        response = client.get("/api/projects")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_with_data(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test listing projects when projects exist."""
        response = client.get("/api/projects")
        
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["id"] == sample_project.id
        assert projects[0]["title"] == sample_project.title

    def test_list_projects_multiple(
        self, client: TestClient, mock_studio_state: "StudioState"
    ):
        """Test listing multiple projects."""
        from src.studio.core.state import NovelProject, ProjectStatus

        # Add multiple projects with matching user_id
        for i in range(3):
            project = NovelProject(
                id=f"project-{i}",
                title=f"Project {i}",
                genre="Fantasy",
                status=ProjectStatus.PLANNING,
                user_id="test-user",
            )
            mock_studio_state.add_project(project)

        response = client.get("/api/projects")
        
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 3


class TestCreateProject:
    """Tests for POST /api/projects endpoint."""

    def test_create_project_minimal(self, client: TestClient):
        """Test creating a project with minimal data."""
        response = client.post(
            "/api/projects",
            json={"title": "New Novel"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Novel"
        assert data["genre"] == "General"  # default
        assert data["language"] == "en"  # default
        assert data["status"] == "planning"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_project_full(self, client: TestClient):
        """Test creating a project with all fields."""
        project_data = {
            "title": "Epic Fantasy Novel",
            "genre": "High Fantasy",
            "language": "en",
            "premise": "A young hero discovers magical powers",
            "themes": ["adventure", "magic", "friendship"],
            "pov": "third",
            "tone": "balanced",
            "target_audience": "young_adult",
            "story_structure": "heros_journey",
            "content_rating": "teen",
            "target_chapters": 50,
            "target_words": 150000,
            "platforms": ["kindle", "wattpad"],
        }
        
        response = client.post("/api/projects", json=project_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Epic Fantasy Novel"
        assert data["genre"] == "High Fantasy"
        assert data["premise"] == "A young hero discovers magical powers"
        assert data["themes"] == ["adventure", "magic", "friendship"]
        assert data["platforms"] == ["kindle", "wattpad"]
        assert data["target_chapters"] == 50
        assert data["target_words"] == 150000

    def test_create_project_validation_empty_title(self, client: TestClient):
        """Test validation rejects empty title."""
        response = client.post(
            "/api/projects",
            json={"title": ""},
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_project_validation_long_title(self, client: TestClient):
        """Test validation rejects title over 200 characters."""
        response = client.post(
            "/api/projects",
            json={"title": "x" * 201},
        )
        
        assert response.status_code == 422

    def test_create_project_validation_negative_chapters(self, client: TestClient):
        """Test validation rejects negative chapter count."""
        response = client.post(
            "/api/projects",
            json={"title": "Test", "target_chapters": -1},
        )
        
        assert response.status_code == 422

    def test_create_project_defaults(self, client: TestClient):
        """Test that default values are set correctly."""
        response = client.post(
            "/api/projects",
            json={"title": "Defaults Test"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check defaults
        assert data["pov"] == "first"
        assert data["tone"] == "balanced"
        assert data["target_audience"] == "young_adult"
        assert data["story_structure"] == "three_act"
        assert data["content_rating"] == "teen"
        assert data["target_chapters"] == 100
        assert data["target_words"] == 300000


class TestGetProject:
    """Tests for GET /api/projects/{project_id} endpoint."""

    def test_get_project_exists(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test getting an existing project."""
        response = client.get(f"/api/projects/{sample_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_project.id
        assert data["title"] == sample_project.title

    def test_get_project_not_found(self, client: TestClient):
        """Test getting a non-existent project returns 404."""
        response = client.get("/api/projects/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_project_response_fields(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test that response includes all expected fields."""
        response = client.get(f"/api/projects/{sample_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields are present
        expected_fields = [
            "id", "title", "genre", "language", "status",
            "premise", "themes", "pov", "tone", "target_audience",
            "story_structure", "content_rating", "sensitive_handling",
            "target_chapters", "completed_chapters", "total_words",
            "target_words", "progress_percent", "created_at", "updated_at",
            "platforms", "published_chapters", "total_reads",
            "total_votes", "total_comments", "followers",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestUpdateProject:
    """Tests for PUT /api/projects/{project_id} endpoint."""

    def test_update_project_title(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test updating project title."""
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={"title": "Updated Title"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_project_status(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test updating project status."""
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={"status": "writing"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "writing"

    def test_update_project_multiple_fields(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test updating multiple fields at once."""
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={
                "title": "New Title",
                "genre": "Science Fiction",
                "premise": "New premise",
                "target_chapters": 200,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["genre"] == "Science Fiction"
        assert data["premise"] == "New premise"
        assert data["target_chapters"] == 200

    def test_update_project_not_found(self, client: TestClient):
        """Test updating non-existent project returns 404."""
        response = client.put(
            "/api/projects/nonexistent-id",
            json={"title": "New Title"},
        )
        
        assert response.status_code == 404

    def test_update_project_partial_update(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test partial update only updates provided fields."""
        original_genre = sample_project.genre
        
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={"title": "Only Title Changed"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Only Title Changed"
        assert data["genre"] == original_genre  # Unchanged

    def test_update_project_platforms(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test updating project platforms."""
        response = client.put(
            f"/api/projects/{sample_project.id}",
            json={"platforms": ["wattpad", "royalroad", "webnovel"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["platforms"] == ["wattpad", "royalroad", "webnovel"]


class TestDeleteProject:
    """Tests for DELETE /api/projects/{project_id} endpoint."""

    def test_delete_project_exists(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test deleting an existing project."""
        response = client.delete(f"/api/projects/{sample_project.id}")
        
        assert response.status_code == 204
        
        # Verify project is deleted
        get_response = client.get(f"/api/projects/{sample_project.id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client: TestClient):
        """Test deleting non-existent project returns 404."""
        response = client.delete("/api/projects/nonexistent-id")
        
        assert response.status_code == 404

    def test_delete_project_removes_from_list(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test that deleted project is removed from list."""
        # First verify it exists
        list_response = client.get("/api/projects")
        assert len(list_response.json()) == 1
        
        # Delete
        client.delete(f"/api/projects/{sample_project.id}")
        
        # Verify list is empty
        list_response = client.get("/api/projects")
        assert list_response.json() == []


class TestProjectToResponse:
    """Tests for the _project_to_response helper function."""

    def test_project_to_response_complete(self, client: TestClient):
        """Test that all project fields are correctly mapped."""
        from src.studio.core.state import NovelProject, ProjectStatus
        from src.api.routers.projects import _project_to_response

        project = NovelProject(
            id="test-id",
            title="Test Novel",
            genre="Fantasy",
            language="en",
            status=ProjectStatus.WRITING,
            premise="Test premise",
            themes=["theme1", "theme2"],
            pov="third",
            tone="dark",
            target_audience="adult",
            story_structure="heros_journey",
            content_rating="mature",
            sensitive_handling="direct",
            target_chapters=100,
            completed_chapters=25,
            total_words=50000,
            target_words=200000,
            platforms=["kindle"],
            published_chapters=20,
            total_reads=1000,
            total_votes=500,
            total_comments=200,
            followers=300,
        )

        response = _project_to_response(project)

        assert response.id == "test-id"
        assert response.title == "Test Novel"
        assert response.genre == "Fantasy"
        assert response.language == "en"
        assert response.status == "writing"
        assert response.premise == "Test premise"
        assert response.themes == ["theme1", "theme2"]
        assert response.progress_percent == 25.0
