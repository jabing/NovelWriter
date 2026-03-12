"""
NovelWriter LSP - Rename Handler

This module provides the rename LSP feature handler.
"""

import logging
from typing import cast

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex

logger = logging.getLogger(__name__)


def register_rename(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the rename handler with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index for looking up symbols to rename
    """

    @server.feature(types.TEXT_DOCUMENT_RENAME)
    def rename(params: types.RenameParams) -> types.WorkspaceEdit | None:
        """
        Handle rename requests.

        When a user requests to rename a symbol, this handler finds
        all occurrences (definition and references) and returns
        a WorkspaceEdit with all necessary changes.

        Args:
            params: Rename parameters including position, document URI, and new name

        Returns:
            WorkspaceEdit with all text edits, or None if no symbol found
        """
        uri = params.text_document.uri
        position = params.position
        new_name = params.new_name

        logger.debug(f"rename request: {uri} at {position} to '{new_name}'")

        symbol_name = _get_word_at_position(server, uri, position)
        if not symbol_name:
            logger.debug(f"No symbol found at position {position}")
            return None

        symbol = index.get_symbol(symbol_name)
        if not symbol:
            logger.debug(f"Symbol '{symbol_name}' not found in index")
            return None

        old_name = symbol.name
        edits: list[types.TextEdit] = []

        if symbol.definition_range:
            def_range = symbol.definition_range
            edits.append(
                types.TextEdit(
                    range=types.Range(
                        start=types.Position(
                            line=def_range["start_line"],
                            character=def_range["start_character"],
                        ),
                        end=types.Position(
                            line=def_range["end_line"],
                            character=def_range["end_character"],
                        ),
                    ),
                    new_text=new_name,
                )
            )

        for ref in symbol.references:
            try:
                ref_uri = cast(str, ref.get("uri", uri))
                if ref_uri != uri:
                    continue

                start_line = cast(int, ref.get("start_line", 0))
                start_char = cast(int, ref.get("start_character", 0))
                end_line = cast(int, ref.get("end_line", 0))
                end_char = cast(int, ref.get("end_character", 0))

                edits.append(
                    types.TextEdit(
                        range=types.Range(
                            start=types.Position(line=start_line, character=start_char),
                            end=types.Position(line=end_line, character=end_char),
                        ),
                        new_text=new_name,
                    )
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid reference format: {e}")
                continue

        if old_name in index:
            from dataclasses import replace

            new_symbol = replace(symbol, name=new_name)
            index.update(new_symbol)

        document = server.workspace.get_text_document(uri)
        version = getattr(document, "version", None)

        return types.WorkspaceEdit(
            document_changes=[
                types.TextDocumentEdit(
                    text_document=types.OptionalVersionedTextDocumentIdentifier(
                        uri=uri,
                        version=version,
                    ),
                    edits=edits,
                )
            ]
        )


def _get_word_at_position(server: LanguageServer, uri: str, position: types.Position) -> str | None:
    """
    Extract the word at the given position from the document.

    Args:
        server: The LSP server instance
        uri: Document URI
        position: Position to extract word from

    Returns:
        The word at the position, or None if extraction fails
    """
    try:
        document = server.workspace.get_text_document(uri)
        if not document.source:
            return None

        lines = document.source.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        if position.character >= len(line):
            return None

        word = _extract_word(line, position.character)
        return word if word else None
    except Exception as e:
        logger.error(f"Error extracting word at position: {e}")
        return None


def _extract_word(line: str, position: int) -> str:
    """
    Extract a complete word from a line at the given character position.

    Args:
        line: The line of text
        position: Character position within the line

    Returns:
        The complete word containing the position
    """
    if not line or position < 0 or position >= len(line):
        return ""

    start = position
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
        start -= 1

    end = position
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1

    word = line[start:end].strip()
    return word
