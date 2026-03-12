"""NovelWriter LSP Server implementation using pygls framework.

This module provides the core Language Server Protocol implementation
for AI writing systems, supporting novel writing features.
"""

import logging
from typing import Any

from pygls.lsp.server import LanguageServer
from lsprotocol import types

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp import parser
from novelwriter_lsp.features import (
    register_goto_definition,
    register_diagnostics,
    register_codelens,
    register_hover,
    register_completion,
    register_rename,
    register_document_symbol,
)

# Configure logging
logger = logging.getLogger(__name__)


class NovelWriterLSP(LanguageServer):
    """NovelWriter Language Server.

    A custom LSP server for AI writing systems, providing features for:
    - Character, Location, Item, Lore, PlotPoint definitions
    - Chapter and section outlines
    - Go to definition
    - Find references
    - Document symbols
    - Rename symbols
    - Diagnostics and validation

    Attributes:
        version: Server version string
        name: Server name
        workspace: Current workspace (provided by pygls)
    """

    def __init__(
        self,
        name: str = "NovelWriter LSP Server",
        version: str = "0.1.0",
        text_document_sync_kind: types.TextDocumentSyncKind = types.TextDocumentSyncKind.Incremental,
        max_workers: int = 4,
    ) -> None:
        """Initialize the NovelWriter LSP server.

        Args:
            name: Server name for identification
            version: Server version string
            text_document_sync_kind: Type of text synchronization (default: Incremental)
            max_workers: Maximum number of worker threads (default: 4)
        """
        super().__init__(
            name=name,
            version=version,
            text_document_sync_kind=text_document_sync_kind,
            max_workers=max_workers,
        )

        # Initialize server state
        self._diagnostics: dict[str, tuple[int, list[types.Diagnostic]]] = {}
        self._custom_state: dict[str, Any] = {}
        self._documents: dict[str, str] = {}

        logger.info("NovelWriter LSP Server initialized")

    def parse_document(self, uri: str, content: str) -> None:
        """Parse a document and extract symbols.

        This method parses the document content, extracts all symbols,
        and updates the symbol index.

        Args:
            uri: Document URI
            content: Document content
        """
        logger.debug(f"Parsing document: {uri}")

        symbols = parser.parse_document(content, uri)

        for symbol in symbols:
            index.update(symbol)
            logger.debug(f"Updated index with symbol: {symbol.type} - {symbol.name}")

        logger.debug(f"Parsed {len(symbols)} symbols from {uri}")

    def get_diagnostics(self, uri: str) -> tuple[int, list[types.Diagnostic]] | None:
        """Get diagnostics for a document.

        Args:
            uri: Document URI

        Returns:
            Tuple of (version, diagnostics) or None if no diagnostics
        """
        return self._diagnostics.get(uri)

    def set_diagnostics(
        self,
        uri: str,
        version: int,
        diagnostics: list[types.Diagnostic],
    ) -> None:
        """Set diagnostics for a document.

        Args:
            uri: Document URI
            version: Document version
            diagnostics: List of diagnostic items
        """
        self._diagnostics[uri] = (version, diagnostics)
        logger.debug(f"Set {len(diagnostics)} diagnostics for {uri}")

    def publish_diagnostics(
        self,
        uri: str,
        diagnostics: list[types.Diagnostic],
        version: int | None = None,
    ) -> None:
        """Publish diagnostics to the client.

        Args:
            uri: Document URI
            diagnostics: List of diagnostic items
            version: Optional document version
        """
        # Store diagnostics locally first
        doc_version = version or 0
        self.set_diagnostics(uri, doc_version, diagnostics)

        # The actual notification sending is handled by pygls's built-in method
        # For now, we just store them locally
        logger.debug(f"Stored {len(diagnostics)} diagnostics for {uri}")


# Create server instance
server = NovelWriterLSP()


# Register basic LSP features
@server.feature(types.INITIALIZED)
def on_initialized(params: types.InitializedParams) -> None:
    """Handle server initialization completion.

    Args:
        params: Initialization parameters
    """
    logger.info("NovelWriter LSP Server initialized and ready")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def on_text_document_did_open(params: types.DidOpenTextDocumentParams) -> None:
    """Handle text document open event.

    Args:
        params: Document open parameters
    """
    uri = params.text_document.uri
    content = params.text_document.text
    version = params.text_document.version

    logger.info(f"Document opened: {uri} (version {version})")
    server._documents[uri] = content
    server.parse_document(uri, content)


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def on_text_document_did_close(params: types.DidCloseTextDocumentParams) -> None:
    """Handle text document close event.

    Args:
        params: Document close parameters
    """
    uri = params.text_document.uri
    logger.info(f"Document closed: {uri}")
    _ = server._documents.pop(uri, None)
    _ = index.remove(uri)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
async def on_text_document_did_change(params: types.DidChangeTextDocumentParams) -> None:
    """Handle text document change event with cache invalidation.

    This implements event-driven cache invalidation:
    1. Remove all symbols for the document from the index (including aliases)
    2. Re-parse the document to extract updated symbols
    3. Update the index with new symbols (including aliases)
    4. Run diagnostics validation

    This ensures that symbol references and aliases stay in sync with
    the document content without requiring TTL or manual invalidation.

    Note: This handler is called for significant document changes (not
    every keystroke) due to pygls's text synchronization settings.

    Args:
        params: Document change parameters
    """
    uri = params.text_document.uri
    version = params.text_document.version

    logger.debug(f"Document changed: {uri} (version {version})")

    # Step 1: Apply content changes to stored document
    if uri not in server._documents:
        logger.warning(f"Document {uri} not found in cache, skipping")
        return

    current_content = server._documents[uri]
    for change in params.content_changes:
        if isinstance(change, types.TextDocumentContentChangeWholeDocument):
            current_content = change.text
        else:
            start_line = change.range.start.line
            start_char = change.range.start.character
            end_line = change.range.end.line
            end_char = change.range.end.character

            lines = current_content.split("\n")
            if start_line >= len(lines):
                lines.append(change.text)
            else:
                start_of_line = lines[start_line][:start_char]
                end_of_line = lines[end_line][end_char:] if end_line < len(lines) else ""
                lines[start_line : end_line + 1] = [start_of_line + change.text + end_of_line]

            current_content = "\n".join(lines)

    server._documents[uri] = current_content

    # Step 2: Invalidate cache - remove old symbols and aliases
    removed_symbols = index.remove(uri)
    if removed_symbols:
        logger.debug(
            f"Cache invalidated for {uri}: removed {len(removed_symbols)} symbols "
            f"(including aliases)"
        )

    # Step 3: Re-parse and update index with new symbols
    server.parse_document(uri, current_content)
    logger.debug(f"Cache rebuilt for {uri}")

    # Step 4: Run diagnostics validation
    validate_func = server._custom_state.get("validate_document")
    if validate_func:
        await validate_func(uri, current_content)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def on_text_document_did_save(params: types.DidSaveTextDocumentParams) -> None:
    """Handle text document save event.

    Args:
        params: Document save parameters
    """
    uri = params.text_document.uri
    logger.info(f"Document saved: {uri}")


# Initialize index and register features
index = SymbolIndex()
register_goto_definition(server, index)
register_diagnostics(server, index)
register_codelens(server, index)
register_hover(server, index)
register_completion(server, index)
register_rename(server, index)
register_document_symbol(server, index)
