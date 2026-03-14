"""
Tests for NovelWriter LSP Diagnostics Feature.

This module tests the diagnostics feature defined in novelwriter_lsp.features.diagnostics.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.diagnostics import register_diagnostics
from novelwriter_lsp.index import SymbolIndex


class TestDiagnosticsFeature:
    """Tests for the diagnostics feature."""

    def test_register_diagnostics(self):
        """Test registering the diagnostics feature stores validate_document."""
        server = MagicMock()
        server._custom_state = {}
        index = MagicMock(spec=SymbolIndex)

        register_diagnostics(server, index)

        assert "validate_document" in server._custom_state

    @pytest.mark.asyncio
    async def test_validate_document_publishes_diagnostics(self):
        """Test that validation publishes diagnostics."""
        server = MagicMock()
        server._custom_state = {}
        index = MagicMock(spec=SymbolIndex)

        register_diagnostics(server, index)
        
        validate_func = server._custom_state["validate_document"]
        
        content = """
@Character: Test { age: 25 }
@Character: Test { age: 30 }
"""
        
        await validate_func("file:///test.md", content)
        
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"

    @pytest.mark.asyncio
    async def test_validate_document_no_issues(self):
        """Test validation with no issues."""
        server = MagicMock()
        server._custom_state = {}
        index = MagicMock(spec=SymbolIndex)

        register_diagnostics(server, index)
        
        validate_func = server._custom_state["validate_document"]
        
        content = """
@Character: Alice { age: 25 }
"""
        
        await validate_func("file:///test.md", content)
        
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"

    @pytest.mark.asyncio
    async def test_validate_document_error_handling(self):
        """Test error handling in validation."""
        server = MagicMock()
        server._custom_state = {}
        index = MagicMock(spec=SymbolIndex)

        register_diagnostics(server, index)
        
        validate_func = server._custom_state["validate_document"]
        
        await validate_func("file:///test.md", "test content")
        
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"
