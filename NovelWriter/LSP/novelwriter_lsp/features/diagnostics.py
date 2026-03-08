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

    async def validate_document(uri: str, content: str) -> None:
        """
        Validate document and publish diagnostics.

        Args:
            uri: Document URI
            content: Document content
        """
        try:
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

    # Store the validation function for later use
    server._custom_state["validate_document"] = validate_document
