"""
NovelWriter LSP - Document Symbol Handler

This module provides the documentSymbol LSP feature handler.
"""

import logging

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import SymbolType

logger = logging.getLogger(__name__)


SYMBOL_KIND_MAP = {
    SymbolType.CHARACTER: types.SymbolKind.Class,
    SymbolType.LOCATION: types.SymbolKind.Struct,
    SymbolType.ITEM: types.SymbolKind.Object,
    SymbolType.LORE: types.SymbolKind.Interface,
    SymbolType.PLOTPOINT: types.SymbolKind.Event,
    SymbolType.OUTLINE: types.SymbolKind.Module,
    SymbolType.EVENT: types.SymbolKind.Event,
    SymbolType.RELATIONSHIP: types.SymbolKind.Variable,
    SymbolType.CHAPTER: types.SymbolKind.Module,
}


def register_document_symbol(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the document_symbol handler with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index for looking up symbols
    """

    @server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbol(params: types.DocumentSymbolParams) -> list[types.DocumentSymbol] | list[types.SymbolInformation] | None:
        """
        Handle document symbol requests.

        Returns a hierarchical outline of all symbols in the document,
        including chapters, characters, locations, and other elements.

        Args:
            params: Document symbol parameters including document URI

        Returns:
            List of document symbols with hierarchical structure
        """
        uri = params.text_document.uri

        logger.debug(f"document_symbol request: {uri}")

        symbols = index.get_symbols_by_uri(uri)
        if not symbols:
            logger.debug(f"No symbols found for {uri}")
            return None

        result: list[types.DocumentSymbol] = []
        chapter_stack: list[types.DocumentSymbol] = []

        for symbol in sorted(symbols, key=lambda s: s.definition_range["start_line"]):
            symbol_kind = SYMBOL_KIND_MAP.get(symbol.type, types.SymbolKind.Variable)

            doc_symbol = types.DocumentSymbol(
                name=symbol.name,
                kind=symbol_kind,
                range=types.Range(
                    start=types.Position(
                        line=symbol.definition_range["start_line"],
                        character=symbol.definition_range["start_character"],
                    ),
                    end=types.Position(
                        line=symbol.definition_range["end_line"],
                        character=symbol.definition_range["end_character"],
                    ),
                ),
                selection_range=types.Range(
                    start=types.Position(
                        line=symbol.definition_range["start_line"],
                        character=symbol.definition_range["start_character"],
                    ),
                    end=types.Position(
                        line=symbol.definition_range["end_line"],
                        character=symbol.definition_range["end_character"],
                    ),
                ),
            )

            if symbol.type == SymbolType.CHAPTER:
                while chapter_stack:
                    chapter_stack.pop()
                chapter_stack.append(doc_symbol)
                result.append(doc_symbol)
            elif chapter_stack and symbol.type in [SymbolType.EVENT, SymbolType.PLOTPOINT]:
                parent = chapter_stack[-1]
                children = list(parent.children) if parent.children else []
                children.append(doc_symbol)
                parent.children = children
                result.append(doc_symbol)
            else:
                result.append(doc_symbol)

        logger.debug(f"Found {len(result)} symbols for {uri}")
        return result if result else None
