"""Tests for characters router."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import NovelProject, StudioState


class TestListCharacters:
    """Tests for GET /api/novels/{novel_id}/characters endpoint."""

    def test_list_characters_empty(self, client: TestClient, sample_project: "NovelProject"):
        """Test listing characters when directory exists but is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.get(f"/api/novels/{sample_project.id}/characters")
            
            assert response.status_code == 200
            data = response.json()
            assert data["characters"] == []
            assert data["total_count"] == 0
            assert data["main_characters"] == 0
            assert data["supporting_characters"] == 0

    def test_list_characters_with_data(self, client: TestClient, sample_project: "NovelProject"):
        """Test listing characters when characters exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            char_data1 = {
                "name": "Alice",
                "aliases": ["Aly"],
                "tier": 1,
                "bio": "The protagonist",
                "current_status": "alive",
            }
            with open(characters_dir / "Alice.json", "w") as f:
                json.dump(char_data1, f)

            char_data2 = {
                "name": "Bob",
                "tier": 2,
                "bio": "The sidekick",
                "current_status": "alive",
            }
            with open(characters_dir / "Bob.json", "w") as f:
                json.dump(char_data2, f)

            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.get(f"/api/novels/{sample_project.id}/characters")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data["characters"]) == 2
                assert data["total_count"] == 2
                assert data["main_characters"] == 1
                assert data["supporting_characters"] == 1


class TestGetCharacter:
    """Tests for GET /api/novels/{novel_id}/characters/{name} endpoint."""

    def test_get_character_not_found(self, client: TestClient, sample_project: "NovelProject"):
        """Test getting non-existent character."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.get(f"/api/novels/{sample_project.id}/characters/Unknown")
                
                assert response.status_code == 404

    def test_get_character_from_json(self, client: TestClient, sample_project: "NovelProject"):
        """Test getting character from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            char_data = {
                "name": "Charlie",
                "tier": 1,
                "bio": "The protagonist",
                "current_status": "alive",
            }
            with open(characters_dir / "Charlie.json", "w") as f:
                json.dump(char_data, f)

            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.get(f"/api/novels/{sample_project.id}/characters/Charlie")
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Charlie"
                assert data["tier"] == 1


class TestCreateCharacter:
    """Tests for POST /api/novels/{novel_id}/characters endpoint."""

    def test_create_character_novel_not_found(self, client: TestClient):
        """Test creating character for non-existent novel."""
        response = client.post(
            "/api/novels/nonexistent-novel/characters",
            json={"name": "Test"},
        )
        
        assert response.status_code == 404

    def test_create_character_success(self, client: TestClient, sample_project: "NovelProject"):
        """Test successfully creating a character."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.post(
                    f"/api/novels/{sample_project.id}/characters",
                    json={"name": "NewCharacter", "tier": 3},
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "NewCharacter"
                assert data["tier"] == 3
                assert data["current_status"] == "alive"

    def test_create_character_already_exists(self, client: TestClient, sample_project: "NovelProject"):
        """Test creating character that already exists returns 409."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            with open(characters_dir / "Existing.json", "w") as f:
                json.dump({"name": "Existing"}, f)

            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.post(
                    f"/api/novels/{sample_project.id}/characters",
                    json={"name": "Existing", "tier": 1},
                )
                
                assert response.status_code == 409

    def test_create_character_minimal(self, client: TestClient, sample_project: "NovelProject"):
        """Test creating character with minimal data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            characters_dir = Path(tmpdir) / "characters"
            characters_dir.mkdir(parents=True)
            
            with patch("src.api.routers.characters._get_characters_dir", return_value=characters_dir):
                response = client.post(
                    f"/api/novels/{sample_project.id}/characters",
                    json={"name": "Minimal"},
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "Minimal"
                assert data["tier"] == 1
