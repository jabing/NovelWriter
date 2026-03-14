"""Shared fixtures for API tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import NovelProject, StudioState


@pytest.fixture
def mock_studio_state():
    """Create a mock StudioState with in-memory storage."""
    from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, StudioState

    with tempfile.TemporaryDirectory() as tmpdir:
        state = StudioState(data_dir=Path(tmpdir))
        yield state


@pytest.fixture
def sample_project(mock_studio_state: "StudioState") -> "NovelProject":
    """Create a sample project for testing."""
    from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

    project = NovelProject(
        id="test-project-001",
        title="Test Novel",
        genre="Fantasy",
        language="en",
        status=ProjectStatus.PLANNING,
        user_id="test-user",
        premise="A hero's journey through a magical world",
        themes=["adventure", "friendship"],
        pov="third",
        tone="balanced",
        target_audience="young_adult",
        story_structure="three_act",
        content_rating="teen",
        target_chapters=50,
        completed_chapters=10,
        total_words=25000,
        target_words=150000,
        platforms=["wattpad", "royalroad"],
    )
    mock_studio_state.add_project(project)
    return project


@pytest.fixture
def sample_project_2(mock_studio_state: "StudioState") -> "NovelProject":
    """Create a second sample project for testing list operations."""
    from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

    project = NovelProject(
        id="test-project-002",
        title="Another Novel",
        genre="Sci-Fi",
        language="en",
        status=ProjectStatus.WRITING,
        user_id="test-user",
        premise="Space exploration gone wrong",
        themes=["survival", "discovery"],
        pov="first",
        tone="dark",
        target_audience="adult",
        story_structure="heros_journey",
        content_rating="mature",
        target_chapters=100,
        completed_chapters=25,
        total_words=75000,
        target_words=300000,
        platforms=["kindle"],
    )
    mock_studio_state.add_project(project)
    return project


@pytest.fixture
def client(mock_studio_state: "StudioState"):
    """Create a test client with mocked state dependency."""
    from src.novel_agent.api.main import app
    from src.novel_agent.api.dependencies import get_state, get_current_user_id

    app.dependency_overrides[get_state] = lambda: mock_studio_state
    app.dependency_overrides[get_current_user_id] = lambda: "test-user"

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_orchestrator():
    """Create a mock AgentOrchestrator."""
    mock = MagicMock()
    mock.get_agent_types.return_value = ["plot", "character", "worldbuilding", "editor", "publisher"]
    mock.get_status.return_value = {"agent_type": "plot", "status": "idle"}
    mock.execute.return_value = {"success": True, "result": "test output"}
    return mock



