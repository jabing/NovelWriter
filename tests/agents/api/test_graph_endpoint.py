"""Tests for graph router - character relationship graph endpoint."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import NovelProject, StudioState
else:
    from src.novel_agent.studio.core.state import NovelProject, StudioState


class TestCharacterGraphEndpoint:
    """Tests for GET /api/projects/{id}/graph/characters endpoint."""

    def test_graph_characters_success(self, client: TestClient, sample_project: "NovelProject"):
        """Test successful character graph retrieval with relationships."""
        # Mock character memory data
        mock_characters = {
            "char1": {
                "name": "Alice",
                "aliases": ["Aly"],
                "tier": 1,
                "bio": "The protagonist",
                "current_status": "alive",
            },
            "char2": {
                "name": "Bob",
                "tier": 2,
                "bio": "The sidekick",
                "current_status": "alive",
            },
        }

        mock_relationships = [
            {
                "character1_id": "char1",
                "character2_id": "char2",
                "relationship_type": "FRIEND",
                "strength": 0.8,
                "description": "Best friends since childhood",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "studio"
            state_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.graph.CharacterMemory") as MockMemory:
                mock_memory_instance = MagicMock()

                async def mock_list_keys():
                    return list(mock_characters.keys())

                async def mock_retrieve_character(char_id):
                    return mock_characters.get(char_id)

                async def mock_get_relationships(char_id):
                    return mock_relationships

                mock_memory_instance.list_keys = mock_list_keys
                mock_memory_instance.retrieve_character = mock_retrieve_character
                mock_memory_instance.get_relationships = mock_get_relationships

                MockMemory.return_value = mock_memory_instance

                with patch("src.novel_agent.studio.core.state.StudioState") as MockState:
                    mock_state = MagicMock(spec=StudioState)
                    mock_state.get_project.return_value = sample_project
                    mock_state.data_dir = state_dir

                    from src.novel_agent.api.dependencies import get_state

                    client.app.dependency_overrides[get_state] = lambda: mock_state

                    try:
                        response = client.get(f"/api/projects/{sample_project.id}/graph/characters")

                        assert response.status_code == 200
                        data = response.json()

                        assert "nodes" in data
                        assert "edges" in data

                        # Check nodes
                        assert len(data["nodes"]) == 2
                        node_ids = [n["data"]["id"] for n in data["nodes"]]
                        assert "char1" in node_ids
                        assert "char2" in node_ids

                        # Check node structure
                        alice_node = next(n for n in data["nodes"] if n["data"]["id"] == "char1")
                        assert alice_node["data"]["label"] == "Alice"
                        assert alice_node["data"]["type"] == "character"
                        assert "properties" in alice_node["data"]
                        assert alice_node["data"]["properties"]["tier"] == 1

                        # Check edges
                        assert len(data["edges"]) == 2
                        edge_rel_types = [e["data"]["relationship"] for e in data["edges"]]
                        assert "FRIEND" in edge_rel_types

                        # Check edge structure
                        first_edge = data["edges"][0]
                        assert "source" in first_edge["data"]
                        assert "target" in first_edge["data"]
                        assert first_edge["data"]["relationship"] == "FRIEND"
                        assert "properties" in first_edge["data"]

                    finally:
                        client.app.dependency_overrides.clear()

    def test_graph_empty_project(self, client: TestClient, sample_project: "NovelProject"):
        """Test graph endpoint returns empty structure when no characters exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "studio"
            state_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.graph.CharacterMemory") as MockMemory:
                mock_memory_instance = MagicMock()

                async def mock_list_keys():
                    return []

                async def mock_retrieve_character(char_id):
                    return None

                async def mock_get_relationships(char_id):
                    return []

                mock_memory_instance.list_keys = mock_list_keys
                mock_memory_instance.retrieve_character = mock_retrieve_character
                mock_memory_instance.get_relationships = mock_get_relationships

                MockMemory.return_value = mock_memory_instance

                with patch("src.novel_agent.studio.core.state.StudioState") as MockState:
                    mock_state = MagicMock(spec=StudioState)
                    mock_state.get_project.return_value = sample_project
                    mock_state.data_dir = state_dir

                    from src.novel_agent.api.dependencies import get_state

                    client.app.dependency_overrides[get_state] = lambda: mock_state

                    try:
                        response = client.get(f"/api/projects/{sample_project.id}/graph/characters")

                        assert response.status_code == 200
                        data = response.json()

                        assert data["nodes"] == []
                        assert data["edges"] == []

                    finally:
                        client.app.dependency_overrides.clear()

    def test_graph_project_not_found(self, client: TestClient):
        """Test graph endpoint returns 404 for non-existent project."""
        response = client.get("/api/projects/nonexistent-project/graph/characters")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_graph_project_access_denied(self, client: TestClient, sample_project: "NovelProject"):
        """Test graph endpoint returns 404 when project belongs to another user."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "studio"
            state_dir.mkdir(parents=True)

            with patch("src.novel_agent.studio.core.state.StudioState") as MockState:
                mock_state = MagicMock(spec=StudioState)
                mock_state.get_project.return_value = None  # Project belongs to different user

                from src.novel_agent.api.dependencies import get_state

                client.app.dependency_overrides[get_state] = lambda: mock_state

                try:
                    response = client.get(f"/api/projects/{sample_project.id}/graph/characters")

                    assert response.status_code == 404

                finally:
                    client.app.dependency_overrides.clear()


class TestGraphResponseFormat:
    """Tests for Cytoscape.js response format."""

    def test_node_format(self, client: TestClient, sample_project: "NovelProject"):
        """Test that nodes have correct Cytoscape.js format."""
        mock_characters = {
            "alice": {
                "name": "Alice",
                "aliases": ["Aly", "Ali"],
                "tier": 1,
                "bio": "The hero",
                "current_status": "alive",
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "studio"
            state_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.graph.CharacterMemory") as MockMemory:
                mock_memory_instance = MagicMock()

                async def mock_list_keys():
                    return ["alice"]

                async def mock_retrieve_character(char_id):
                    return mock_characters.get(char_id)

                async def mock_get_relationships(char_id):
                    return []

                mock_memory_instance.list_keys = mock_list_keys
                mock_memory_instance.retrieve_character = mock_retrieve_character
                mock_memory_instance.get_relationships = mock_get_relationships

                MockMemory.return_value = mock_memory_instance

                with patch("src.novel_agent.studio.core.state.StudioState") as MockState:
                    mock_state = MagicMock(spec=StudioState)
                    mock_state.get_project.return_value = sample_project
                    mock_state.data_dir = state_dir

                    from src.novel_agent.api.dependencies import get_state

                    client.app.dependency_overrides[get_state] = lambda: mock_state

                    try:
                        response = client.get(f"/api/projects/{sample_project.id}/graph/characters")
                        assert response.status_code == 200
                        data = response.json()

                        node = data["nodes"][0]

                        # Verify node data structure
                        assert "data" in node
                        assert "id" in node["data"]
                        assert "label" in node["data"]
                        assert "type" in node["data"]
                        assert "properties" in node["data"]

                        # Verify node data values
                        assert node["data"]["id"] == "alice"
                        assert node["data"]["label"] == "Alice"
                        assert node["data"]["type"] == "character"
                        assert node["data"]["properties"]["tier"] == 1

                    finally:
                        client.app.dependency_overrides.clear()

    def test_edge_format(self, client: TestClient, sample_project: "NovelProject"):
        """Test that edges have correct Cytoscape.js format."""
        mock_characters = {
            "alice": {"name": "Alice", "tier": 1, "current_status": "alive"},
            "bob": {"name": "Bob", "tier": 2, "current_status": "alive"},
        }

        mock_relationships = [
            {
                "character1_id": "alice",
                "character2_id": "bob",
                "relationship_type": "KNOWS",
                "strength": 0.5,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "studio"
            state_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.graph.CharacterMemory") as MockMemory:
                mock_memory_instance = MagicMock()

                async def mock_list_keys():
                    return ["alice", "bob"]

                async def mock_retrieve_character(char_id):
                    return mock_characters.get(char_id)

                async def mock_get_relationships(char_id):
                    return mock_relationships

                mock_memory_instance.list_keys = mock_list_keys
                mock_memory_instance.retrieve_character = mock_retrieve_character
                mock_memory_instance.get_relationships = mock_get_relationships

                MockMemory.return_value = mock_memory_instance

                with patch("src.novel_agent.studio.core.state.StudioState") as MockState:
                    mock_state = MagicMock(spec=StudioState)
                    mock_state.get_project.return_value = sample_project
                    mock_state.data_dir = state_dir

                    from src.novel_agent.api.dependencies import get_state

                    client.app.dependency_overrides[get_state] = lambda: mock_state

                    try:
                        response = client.get(f"/api/projects/{sample_project.id}/graph/characters")
                        assert response.status_code == 200
                        data = response.json()

                        edge = data["edges"][0]

                        # Verify edge data structure
                        assert "data" in edge
                        assert "source" in edge["data"]
                        assert "target" in edge["data"]
                        assert "relationship" in edge["data"]
                        assert "properties" in edge["data"]

                        # Verify edge data values
                        assert edge["data"]["source"] == "alice"
                        assert edge["data"]["target"] == "bob"
                        assert edge["data"]["relationship"] == "KNOWS"
                        assert edge["data"]["properties"]["strength"] == 0.5

                    finally:
                        client.app.dependency_overrides.clear()
