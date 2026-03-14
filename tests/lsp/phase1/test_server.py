"""Tests for NovelWriter LSP Server.

Phase 1 Task 1: Basic server functionality tests.
"""

import pytest
from novelwriter_lsp import __version__
from novelwriter_lsp.server import NovelWriterLSP


class TestNovelWriterLSP:
    """Test cases for NovelWriterLSP server class."""
    
    def test_server_creation(self) -> None:
        """Test that server can be created with default parameters."""
        server = NovelWriterLSP()
        assert server is not None
        assert server.name == "NovelWriter LSP Server"
        assert server.version == "0.1.0"
    
    def test_server_creation_with_custom_params(self) -> None:
        """Test server creation with custom name and version."""
        server = NovelWriterLSP(name="Test Server", version="1.0.0")
        assert server.name == "Test Server"
        assert server.version == "1.0.0"
    
    def test_server_initial_state(self) -> None:
        """Test that server starts with empty state."""
        server = NovelWriterLSP()
        assert server._diagnostics == {}
        assert server._custom_state == {}
    
    def test_set_and_get_diagnostics(self) -> None:
        """Test setting and retrieving diagnostics."""
        from lsprotocol import types
        
        server = NovelWriterLSP()
        uri = "file:///test.md"
        version = 1
        
        # Create a test diagnostic
        diagnostic = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=0, character=10),
            ),
            message="Test diagnostic message",
            severity=types.DiagnosticSeverity.Warning,
        )
        
        # Set diagnostics
        server.set_diagnostics(uri, version, [diagnostic])
        
        # Get diagnostics
        result = server.get_diagnostics(uri)
        assert result is not None
        assert result[0] == version
        assert len(result[1]) == 1
        assert result[1][0].message == "Test diagnostic message"
    
    def test_get_nonexistent_diagnostics(self) -> None:
        """Test getting diagnostics for nonexistent URI."""
        server = NovelWriterLSP()
        result = server.get_diagnostics("file:///nonexistent.md")
        assert result is None
    
    def test_parse_document(self) -> None:
        """Test document parsing (placeholder for Task 3)."""
        server = NovelWriterLSP()
        uri = "file:///test.md"
        content = "@Character: John Doe { age: 42 }"
        
        # Should not raise
        server.parse_document(uri, content)


class TestServerModule:
    """Test cases for server module-level objects."""
    
    def test_default_server_instance(self) -> None:
        """Test that default server instance exists."""
        from novelwriter_lsp.server import server
        assert server is not None
        assert isinstance(server, NovelWriterLSP)


class TestVersion:
    """Test version information."""
    
    def test_version_format(self) -> None:
        """Test that version follows semantic versioning."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        # Should match pattern like "0.1.0"
        parts = __version__.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts[:2])
