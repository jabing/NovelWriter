"""
Tests for NovelWriter LSP CodeLens Feature.

This module tests the CodeLens feature defined in novelwriter_lsp.features.codelens.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from lsprotocol import types

from novelwriter_lsp.features.codelens import register_codelens
from novelwriter_lsp.index import SymbolIndex


class TestCodeLensFeature:
    """Tests for the CodeLens feature."""

    def test_register_codelens(self):
        """Test registering the codelens feature."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        register_codelens(server, index)

        # Verify feature and commands are registered
        assert server.feature.called
        assert server.command.called

        # Check feature registration
        feature_calls = [call[0][0] for call in server.feature.call_args_list]
        assert types.TEXT_DOCUMENT_CODE_LENS in feature_calls

        # Check command registrations
        command_calls = [call[0][0] for call in server.command.call_args_list]
        assert "novel/validateChapter" in command_calls
        assert "novel/updateMemory" in command_calls
        assert "novel/retryChapter" in command_calls

    def test_code_lens_returns_three_lenses(self):
        """Test that code_lens returns three CodeLens objects."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        registered_handlers = {}

        def capture_decorator(feature_type):
            def decorator(func):
                registered_handlers[feature_type] = func
                return func

            return decorator

        server.feature.side_effect = capture_decorator

        register_codelens(server, index)

        # Get the code_lens handler
        assert types.TEXT_DOCUMENT_CODE_LENS in registered_handlers
        code_lens_handler = registered_handlers[types.TEXT_DOCUMENT_CODE_LENS]

        # Call the handler
        params = types.CodeLensParams(
            text_document=types.TextDocumentIdentifier(uri="file:///test.md")
        )

        lenses = code_lens_handler(params)

        # Verify three lenses are returned
        assert len(lenses) == 3

        # Verify first lens: validateChapter
        assert lenses[0].command is not None
        assert lenses[0].command.title == "✓ 运行一致性检查"
        assert lenses[0].command.command == "novel/validateChapter"
        assert lenses[0].command.arguments == ["file:///test.md"]
        assert lenses[0].range.start.line == 0

        # Verify second lens: updateMemory
        assert lenses[1].command is not None
        assert lenses[1].command.title == "↻ 更新内存系统"
        assert lenses[1].command.command == "novel/updateMemory"
        assert lenses[1].command.arguments == ["file:///test.md"]
        assert lenses[1].range.start.line == 1

        # Verify third lens: retryChapter
        assert lenses[2].command is not None
        assert lenses[2].command.title == "↻ 重试生成"
        assert lenses[2].command.command == "novel/retryChapter"
        assert lenses[2].command.arguments == ["file:///test.md"]
        assert lenses[2].range.start.line == 2

    @pytest.mark.asyncio
    async def test_validate_chapter_command(self):
        """Test the novel/validateChapter command handler."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        # Create mock document
        mock_document = MagicMock()
        mock_document.source = """
@Character: Test { age: 25 }
"""
        server.workspace.get_text_document.return_value = mock_document

        registered_handlers = {}
        registered_commands = {}

        def capture_feature_decorator(feature_type):
            def decorator(func):
                registered_handlers[feature_type] = func
                return func

            return decorator

        def capture_command_decorator(command_name):
            def decorator(func):
                registered_commands[command_name] = func
                return func

            return decorator

        server.feature.side_effect = capture_feature_decorator
        server.command.side_effect = capture_command_decorator

        register_codelens(server, index)

        # Get the validate_chapter command handler
        assert "novel/validateChapter" in registered_commands
        validate_handler = registered_commands["novel/validateChapter"]

        # Call the command handler
        await validate_handler(server, ["file:///test.md"])

        # Verify diagnostics were published
        assert server.publish_diagnostics.called

    @pytest.mark.asyncio
    async def test_update_memory_command(self):
        """Test the novel/updateMemory command handler."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        # Create mock document
        mock_document = MagicMock()
        mock_document.source = """
@Event: Test { time: "2024-01-01" }
"""
        server.workspace.get_text_document.return_value = mock_document

        registered_commands = {}

        def capture_command_decorator(command_name):
            def decorator(func):
                registered_commands[command_name] = func
                return func

            return decorator

        server.command.side_effect = capture_command_decorator
        server.feature.side_effect = lambda *args, **kwargs: lambda f: f

        register_codelens(server, index)

        # Get the update_memory command handler
        assert "novel/updateMemory" in registered_commands
        update_handler = registered_commands["novel/updateMemory"]

        # Call the command handler
        await update_handler(server, ["file:///test.md"])

        # Verify workspace document was accessed
        assert server.workspace.get_text_document.called

    @pytest.mark.asyncio
    async def test_retry_chapter_command(self):
        """Test the novel/retryChapter command handler."""
        server = MagicMock()
        index = MagicMock(spec=SymbolIndex)

        registered_commands = {}

        def capture_command_decorator(command_name):
            def decorator(func):
                registered_commands[command_name] = func
                return func

            return decorator

        server.command.side_effect = capture_command_decorator
        server.feature.side_effect = lambda *args, **kwargs: lambda f: f

        register_codelens(server, index)

        # Get the retry_chapter command handler
        assert "novel/retryChapter" in registered_commands
        retry_handler = registered_commands["novel/retryChapter"]

        # Call the command handler (should not raise)
        await retry_handler(server, ["file:///test.md"])
