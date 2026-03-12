"""
NovelWriter LSP - CodeLens Handler

Provides CodeLens buttons for quick access to common operations:
- ✓ 运行一致性检查 (novel/validateChapter)
- ↻ 更新内存系统 (novel/updateMemory)
- ↻ 重试生成 (novel/retryChapter)
"""

import logging
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.agents import ValidatorAgent, UpdaterAgent
from novelwriter_lsp.index import SymbolIndex

if TYPE_CHECKING:
    from novelwriter_lsp.server import NovelWriterLSP

logger = logging.getLogger(__name__)


def register_codelens(server: "NovelWriterLSP", index: SymbolIndex) -> None:
    """
    Register the CodeLens feature with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index (not used for codelens but kept for consistency)
    """
    validator = ValidatorAgent()
    updater = UpdaterAgent()

    @server.feature(types.TEXT_DOCUMENT_CODE_LENS)
    def code_lens(params: types.CodeLensParams) -> list[types.CodeLens]:
        """
        Handle CodeLens requests.

        Args:
            params: CodeLens parameters

        Returns:
            List of CodeLens objects
        """
        uri = params.text_document.uri
        logger.debug(f"Generating codelens for {uri}")

        return [
            types.CodeLens(
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=0, character=1),
                ),
                command=types.Command(
                    title="✓ 运行一致性检查",
                    command="novel/validateChapter",
                    arguments=[uri],
                ),
            ),
            types.CodeLens(
                range=types.Range(
                    start=types.Position(line=1, character=0),
                    end=types.Position(line=1, character=1),
                ),
                command=types.Command(
                    title="↻ 更新内存系统",
                    command="novel/updateMemory",
                    arguments=[uri],
                ),
            ),
            types.CodeLens(
                range=types.Range(
                    start=types.Position(line=2, character=0),
                    end=types.Position(line=2, character=1),
                ),
                command=types.Command(
                    title="↻ 重试生成",
                    command="novel/retryChapter",
                    arguments=[uri],
                ),
            ),
        ]

    @server.command("novel/validateChapter")
    async def validate_chapter(ls: "NovelWriterLSP", args: list[object]) -> None:
        """
        Handle validateChapter command.

        Args:
            ls: The language server instance
            args: Command arguments (uri)
        """
        uri = str(args[0]) if args else ""
        logger.info(f"Validating chapter: {uri}")

        try:
            document = ls.workspace.get_text_document(uri)
            content = document.source
            result = await validator.validate(uri, content)

            # Publish diagnostics
            diagnostics = []
            for error in result.errors:
                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                    message=error,
                    severity=types.DiagnosticSeverity.Error,
                    source="NovelWriter LSP",
                )
                diagnostics.append(diagnostic)

            for warning in result.warnings:
                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                    message=warning,
                    severity=types.DiagnosticSeverity.Warning,
                    source="NovelWriter LSP",
                )
                diagnostics.append(diagnostic)

            ls.publish_diagnostics(uri, diagnostics)

            if result.success:
                logger.info(f"Validation successful for {uri}")
            else:
                logger.warning(f"Validation completed with errors for {uri}")

        except Exception as e:
            logger.error(f"Error validating chapter {uri}: {e}")
            ls.publish_diagnostics(uri, [])

    @server.command("novel/updateMemory")
    async def update_memory(ls: "NovelWriterLSP", args: list[object]) -> None:
        """
        Handle updateMemory command.

        Args:
            ls: The language server instance
            args: Command arguments (uri)
        """
        uri = str(args[0]) if args else ""
        logger.info(f"Updating memory system for: {uri}")

        try:
            document = ls.workspace.get_text_document(uri)
            content = document.source
            result = await updater.extract_and_update(uri, content)

            if result.success:
                logger.info(f"Memory system updated successfully for {uri}")
                logger.debug(f"Extracted data: {result.data}")
            else:
                logger.warning(f"Memory system update completed with warnings for {uri}")

        except Exception as e:
            logger.error(f"Error updating memory system for {uri}: {e}")

    @server.command("novel/retryChapter")
    async def retry_chapter(ls: "NovelWriterLSP", args: list[object]) -> None:
        """
        Handle retryChapter command.

        Args:
            ls: The language server instance
            args: Command arguments (uri)
        """
        uri = str(args[0]) if args else ""
        logger.info(f"Retrying chapter generation for: {uri}")

        # TODO: Implement actual retry generation logic
        # For now, just log that the command was triggered
        logger.warning("Retry chapter generation not yet implemented")
