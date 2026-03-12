# tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from src.utils.config import Settings
    return Settings(
        deepseek_api_key="test_key",
        log_level="DEBUG",
    )


@pytest.fixture
def sample_chapter_data():
    """Sample chapter data for testing."""
    return {
        "chapter_number": 1,
        "chapter_outline": "Alice discovers an anomaly in her SETI data that defies explanation.",
        "characters": [
            {
                "id": "char_alice_001",
                "name": "Alice Chen",
                "role": "protagonist",
                "personality": {"traits": ["brilliant", "curious", "guarded"]},
            }
        ],
        "world_context": {
            "setting": "Modern day, SETI Institute",
            "technology_level": "Near-future",
        },
    }
