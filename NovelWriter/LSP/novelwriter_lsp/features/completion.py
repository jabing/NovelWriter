"""
NovelWriter LSP - Completion Handler

This module provides the completion LSP feature handler to suggest symbols
when typing trigger characters like @, #, or [.
"""

import logging

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    BaseSymbol,
    SymbolType,
)

logger = logging.getLogger(__name__)


def register_completion(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the completion handler with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index for looking up symbols
    """

    @server.feature(
        types.TEXT_DOCUMENT_COMPLETION,
        types.CompletionOptions(
            trigger_characters=["@", "#", "["],
            resolve_provider=False,
        ),
    )
    def completion(
        params: types.CompletionParams,
    ) -> types.CompletionList | list[types.CompletionItem]:
        """
        Handle completion requests.

        When a user types a trigger character (@, #, or [), this handler
        returns relevant symbol suggestions from the index.

        Args:
            params: Completion parameters including position and document URI

        Returns:
            Completion list with symbol suggestions
        """
        uri = params.text_document.uri
        position = params.position

        logger.debug(f"Completion request: {uri} at {position}")

        # Get the current line to determine trigger and query
        try:
            document = server.workspace.get_text_document(uri)
            lines = document.source.split("\n")
            if position.line >= len(lines):
                return types.CompletionList(is_incomplete=False, items=[])

            line = lines[position.line]
            char_before = line[position.character - 1] if position.character > 0 else ""

            # Extract query (text after trigger but before cursor)
            query = ""
            if char_before in ["@", "#", "["]:
                # Start from trigger character and go to cursor
                start = position.character - 1
                while start > 0 and line[start - 1] not in [" ", "\t", "\n"]:
                    start -= 1
                # Query is everything from start+1 to current character
                if start + 1 <= position.character:
                    query = line[start + 1 : position.character]
        except Exception as e:
            logger.error(f"Error extracting query for completion: {e}")
            return types.CompletionList(is_incomplete=False, items=[])

        # Determine which symbol types to search for
        symbols: list[BaseSymbol] = []
        if char_before == "@":
            # Search all @-prefixed symbols: character, location, item, lore, plotpoint
            symbols.extend(index.search(query, symbol_type=SymbolType.CHARACTER))
            symbols.extend(index.search(query, symbol_type=SymbolType.LOCATION))
            symbols.extend(index.search(query, symbol_type=SymbolType.ITEM))
            symbols.extend(index.search(query, symbol_type=SymbolType.LORE))
            symbols.extend(index.search(query, symbol_type=SymbolType.PLOTPOINT))
        elif char_before == "#":
            # Search chapter and outline symbols
            symbols.extend(index.search(query, symbol_type=SymbolType.CHAPTER))
            symbols.extend(index.search(query, symbol_type=SymbolType.OUTLINE))
        elif char_before == "[":
            # Search plot point and event symbols
            symbols.extend(index.search(query, symbol_type=SymbolType.PLOTPOINT))
            symbols.extend(index.search(query, symbol_type=SymbolType.EVENT))
        else:
            return types.CompletionList(is_incomplete=False, items=[])

        # Build completion items
        items: list[types.CompletionItem] = []
        for symbol in symbols[:20]:  # Limit to 20 results
            kind = _get_completion_item_kind(symbol.type)
            items.append(
                types.CompletionItem(
                    label=symbol.name,
                    kind=kind,
                    insert_text=symbol.name,
                    data={"symbol_id": symbol.id},
                )
            )

        logger.debug(f"Returning {len(items)} completion items")
        return types.CompletionList(is_incomplete=False, items=items)


def _get_completion_item_kind(symbol_type: SymbolType) -> types.CompletionItemKind:
    """
    Map SymbolType to CompletionItemKind.

    Args:
        symbol_type: The type of the symbol

    Returns:
        Corresponding CompletionItemKind
    """
    mapping = {
        SymbolType.CHARACTER: types.CompletionItemKind.Class,
        SymbolType.LOCATION: types.CompletionItemKind.Struct,
        SymbolType.ITEM: types.CompletionItemKind.Variable,
        SymbolType.LORE: types.CompletionItemKind.Interface,
        SymbolType.PLOTPOINT: types.CompletionItemKind.Event,
        SymbolType.OUTLINE: types.CompletionItemKind.Module,
        SymbolType.EVENT: types.CompletionItemKind.Event,
        SymbolType.RELATIONSHIP: types.CompletionItemKind.Reference,
        SymbolType.CHAPTER: types.CompletionItemKind.File,
    }
    return mapping.get(symbol_type, types.CompletionItemKind.Text)
