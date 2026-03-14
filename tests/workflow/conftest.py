# tests/workflow/conftest.py
"""Shared fixtures for workflow tests."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.novel_agent.studio.core.state import NovelProject, ProjectStatus


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=MagicMock(content="Test generated content"))
    llm.generate_with_system = AsyncMock(
        return_value=MagicMock(content="Test system-generated content")
    )
    llm.name = "mock_llm"
    return llm


@pytest.fixture
def mock_project(mock_llm):
    return NovelProject(
        id="test_project_001",
        title="Test Novel",
        genre="science_fiction",
        language="en",
        status=ProjectStatus.PLANNING,
        premise="A sci-fi adventure about space exploration.",
        themes=["exploration", "discovery", "humanity"],
        target_chapters=20,
        completed_chapters=0,
        target_words=50000,
    )


@pytest.fixture
def mock_chapter_content():
    return """# Chapter 1: The Beginning

The stars hung in the void like diamonds on black velvet. Captain Alice Chen stood at the edge of the observation deck, gazing out at the infinite expanse.

Her SETI array had picked up an anomaly six months ago - a signal that defied explanation. Not natural, not human. Something else.

"Captain, we're approaching the target sector," Lieutenant Vega's voice broke her concentration.

Alice nodded, her fingers unconsciously tracing the edge of her data pad. This was it. The moment they'd been training for, dreaming of, fighting for.

The signal was calling. And they would answer."""


@pytest.fixture
def sample_outline():
    return {
        "title": "Test Novel Outline",
        "premise": "A sci-fi adventure about space exploration.",
        "acts": [
            {
                "title": "Act 1: Discovery",
                "chapters": [1, 2, 3, 4, 5],
                "plot_points": [
                    "The anomaly is discovered",
                    "Initial investigation",
                    "Commitment to the mission",
                ],
            },
            {
                "title": "Act 2: Exploration",
                "chapters": [6, 7, 8, 9, 10],
                "plot_points": [
                    "Entering uncharted territory",
                    "First contact scenario",
                    "Midpoint revelation",
                ],
            },
            {
                "title": "Act 3: Resolution",
                "chapters": [11, 12, 13, 14, 15],
                "plot_points": [
                    "Climactic confrontation",
                    "Resolution of the mystery",
                    "Return and reflection",
                ],
            },
        ],
        "characters": ["Alice Chen", "Lieutenant Vega"],
        "world_elements": ["Faster-than-light travel", "Advanced AI systems"],
    }


@pytest.fixture
def tmp_project_dir(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir
