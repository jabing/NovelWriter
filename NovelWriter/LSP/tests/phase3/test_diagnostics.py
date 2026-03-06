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
        """Test registering the diagnostics feature."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        register_diagnostics(server, index)

        assert server.feature.called
        args, kwargs = server.feature.call_args
        assert args[0] == types.TEXT_DOCUMENT_DID_CHANGE

    @pytest.mark.asyncio
    async def test_on_document_change_publishes_diagnostics(self):
        """Test that document change triggers diagnostic publishing."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        # Create mock document
        mock_document = MagicMock()
        mock_document.source = """
@Character: Test { age: 25 }
@Character: Test { age: 30 }
"""
        server.workspace.get_text_document.return_value = mock_document

        # We'll use a class to capture the registered handler
        registered_handlers = []

        def capture_decorator(*args, **kwargs):
            def decorator(func):
                registered_handlers.append(func)
                return func

            return decorator

        server.feature.side_effect = capture_decorator

        # Register the diagnostics feature
        register_diagnostics(server, index)

        # Get the registered handler
        assert len(registered_handlers) == 1
        handler = registered_handlers[0]

        # Call the handler
        params = types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                uri="file:///test.md",
                version=1,
            ),
            content_changes=[],
        )

        await handler(params)

        # Verify diagnostics were published
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"
        assert len(publish_args[0][1]) > 0

    @pytest.mark.asyncio
    async def test_on_document_change_no_issues(self):
        """Test document change with no validation issues."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        # Create mock document with no issues
        mock_document = MagicMock()
        mock_document.source = """
@Character: Alice { age: 25 }
"""
        server.workspace.get_text_document.return_value = mock_document

        # Capture registered handler
        registered_handlers = []

        def capture_decorator(*args, **kwargs):
            def decorator(func):
                registered_handlers.append(func)
                return func

            return decorator

        server.feature.side_effect = capture_decorator

        # Register the diagnostics feature
        register_diagnostics(server, index)

        # Get the registered handler
        assert len(registered_handlers) == 1
        handler = registered_handlers[0]

        # Call the handler
        params = types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                uri="file:///test.md",
                version=1,
            ),
            content_changes=[],
        )

        await handler(params)

        # Verify diagnostics were published
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"

    @pytest.mark.asyncio
    async def test_on_document_change_error_handling(self):
        """Test error handling in document change handler."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        # Make get_text_document raise an exception
        server.workspace.get_text_document.side_effect = Exception("Test error")

        # Capture registered handler
        registered_handlers = []

        def capture_decorator(*args, **kwargs):
            def decorator(func):
                registered_handlers.append(func)
                return func

            return decorator

        server.feature.side_effect = capture_decorator

        # Register the diagnostics feature
        register_diagnostics(server, index)

        # Get the registered handler
        assert len(registered_handlers) == 1
        handler = registered_handlers[0]

        # Call the handler
        params = types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(
                uri="file:///test.md",
                version=1,
            ),
            content_changes=[],
        )

        await handler(params)

        # Verify diagnostics were cleared on error
        assert server.publish_diagnostics.called
        publish_args = server.publish_diagnostics.call_args
        assert publish_args[0][0] == "file:///test.md"
        assert len(publish_args[0][1]) == 0
