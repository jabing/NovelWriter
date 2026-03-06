"""
NovelWriter LSP - Diagnostics Handler

This module provides real-time diagnostics validation using ValidatorAgent.
"""

import logging
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.agents import ValidatorAgent
from novelwriter_lsp.index import SymbolIndex

if TYPE_CHECKING:
    from novelwriter_lsp.server import NovelWriterLSP

logger = logging.getLogger(__name__)


def register_diagnostics(server: "NovelWriterLSP", index: SymbolIndex) -> None:
    """
    Register the diagnostics feature with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index (not used for diagnostics but kept for consistency)
    """
    validator = ValidatorAgent()

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    async def on_document_change(params: types.DidChangeTextDocumentParams) -> None:
        """
        Handle document change events and push diagnostics.

        Args:
            params: Document change parameters
        """
        uri = params.text_document.uri

        try:
            document = server.workspace.get_text_document(uri)
            content = document.source

            result = await validator.validate(uri, content)

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

            server.publish_diagnostics(uri, diagnostics)
            logger.debug(f"Published {len(diagnostics)} diagnostics for {uri}")

        except Exception as e:
            logger.error(f"Error processing diagnostics for {uri}: {e}")
            server.publish_diagnostics(uri, [])
