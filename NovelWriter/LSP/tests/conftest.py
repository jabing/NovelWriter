"""Pytest configuration and fixtures for NovelWriter LSP tests."""

import pytest
from novelwriter_lsp.server import NovelWriterLSP


@pytest.fixture
def server() -> NovelWriterLSP:
    """Create a fresh server instance for each test."""
    return NovelWriterLSP()


@pytest.fixture
def server_with_defaults() -> NovelWriterLSP:
    """Create server with default parameters."""
    return NovelWriterLSP(
        name="NovelWriter LSP Server",
        version="0.1.0",
    )
