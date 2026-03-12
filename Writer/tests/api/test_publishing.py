"""Tests for publishing router."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.studio.core.state import NovelProject, StudioState


class TestListPlatforms:
    """Tests for GET /api/publishing/platforms endpoint."""

    def test_list_platforms(self, client: TestClient):
        """Test listing available platforms."""
        response = client.get("/api/publishing/platforms")
        
        assert response.status_code == 200
        platforms = response.json()
        assert isinstance(platforms, list)
        assert len(platforms) == 4
        
        # Check platform structure
        for platform in platforms:
            assert "id" in platform
            assert "name" in platform
            assert "description" in platform
            assert "enabled" in platform

    def test_list_platforms_includes_expected_platforms(self, client: TestClient):
        """Test that expected platforms are in the list."""
        response = client.get("/api/publishing/platforms")
        
        assert response.status_code == 200
        platforms = response.json()
        platform_ids = [p["id"] for p in platforms]
        
        assert "wattpad" in platform_ids
        assert "royalroad" in platform_ids
        assert "kindle" in platform_ids
        assert "webnovel" in platform_ids

    def test_list_platforms_wattpad_enabled(self, client: TestClient):
        """Test that Wattpad platform is enabled."""
        response = client.get("/api/publishing/platforms")
        
        assert response.status_code == 200
        platforms = response.json()
        wattpad = next(p for p in platforms if p["id"] == "wattpad")
        
        assert wattpad["enabled"] is True
        assert "Wattpad" in wattpad["name"]

    def test_list_platforms_webnovel_disabled(self, client: TestClient):
        """Test that Webnovel platform is disabled."""
        response = client.get("/api/publishing/platforms")
        
        assert response.status_code == 200
        platforms = response.json()
        webnovel = next(p for p in platforms if p["id"] == "webnovel")
        
        assert webnovel["enabled"] is False


class TestPublishNovel:
    """Tests for POST /api/publishing/novels/{novel_id}/publish endpoint."""

    def test_publish_novel_not_found(self, client: TestClient):
        """Test publishing a novel that doesn't exist."""
        response = client.post(
            "/api/publishing/novels/nonexistent-id/publish",
            json={"platform": "wattpad"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_publish_novel_unknown_platform(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test publishing with unknown platform returns 400."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={"platform": "unknown_platform"}
        )
        
        assert response.status_code == 400
        assert "unknown platform" in response.json()["detail"].lower()

    def test_publish_novel_not_configured_for_platform(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test publishing to platform not configured for novel."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={"platform": "webnovel"}  # Not in sample_project.platforms
        )
        
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"].lower()

    def test_publish_novel_success(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test successful publishing to configured platform."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={"platform": "wattpad"}  # In sample_project.platforms
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["platform"] == "wattpad"
        assert "published_chapters" in data
        assert "message" in data

    def test_publish_novel_with_specific_chapters(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test publishing specific chapters."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={
                "platform": "wattpad",
                "chapter_numbers": [1, 2, 3]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["published_chapters"] == [1, 2, 3]

    def test_publish_novel_auto_publish_flag(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test publishing with auto_publish flag."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={
                "platform": "wattpad",
                "auto_publish": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_publish_novel_default_all_chapters(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test that publishing without chapter_numbers defaults to all completed."""
        response = client.post(
            f"/api/publishing/novels/{sample_project.id}/publish",
            json={"platform": "wattpad"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should publish chapters 1 to completed_chapters
        assert len(data["published_chapters"]) > 0


class TestGetComments:
    """Tests for GET /api/publishing/comments/{novel_id} endpoint."""

    def test_get_comments_novel_not_found(self, client: TestClient):
        """Test getting comments for non-existent novel."""
        response = client.get("/api/publishing/comments/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_comments_success(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test getting comments for existing novel."""
        response = client.get(f"/api/publishing/comments/{sample_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["novel_id"] == sample_project.id
        assert "platform" in data
        assert "comments" in data
        assert "total_count" in data

    def test_get_comments_with_platform(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test getting comments for specific platform."""
        response = client.get(
            f"/api/publishing/comments/{sample_project.id}",
            params={"platform": "royalroad"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "royalroad"

    def test_get_comments_with_limit(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test getting comments with limit."""
        response = client.get(
            f"/api/publishing/comments/{sample_project.id}",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"]) <= 10

    def test_get_comments_default_platform(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test that default platform is wattpad."""
        response = client.get(f"/api/publishing/comments/{sample_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "wattpad"

    def test_get_comments_limit_validation(
        self, client: TestClient, sample_project: "NovelProject"
    ):
        """Test limit validation (1-100)."""
        # Test limit below minimum
        response = client.get(
            f"/api/publishing/comments/{sample_project.id}",
            params={"limit": 0}
        )
        assert response.status_code == 422
        
        # Test limit above maximum
        response = client.get(
            f"/api/publishing/comments/{sample_project.id}",
            params={"limit": 101}
        )
        assert response.status_code == 422
