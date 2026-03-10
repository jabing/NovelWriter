"""
NovelWriter LSP - Completion Handler

This module provides the completion LSP feature handler to suggest symbols
when typing trigger characters like @, #, or [.
Supports integration with WriterAPI for character completions.
"""

import logging
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    BaseSymbol,
    SymbolType,
)
if TYPE_CHECKING:
    from novelwriter_shared.api import WriterAPI
    from novelwriter_shared.models import CharacterStatus

logger = logging.getLogger(__name__)


def register_completion(
    server: LanguageServer, 
    index: SymbolIndex,
    writer_api: "WriterAPI | None" = None,
) -> None:
    """
    Register the completion handler with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index for looking up symbols
        writer_api: Optional WriterAPI for character completions
    """

    @server.feature(
        types.TEXT_DOCUMENT_COMPLETION,
        types.CompletionOptions(
            trigger_characters=["@", "#", "["],
            resolve_provider=False,
        ),
    )
    async def completion(
        params: types.CompletionParams,
    ) -> types.CompletionList | list[types.CompletionItem]:
        """
        Handle completion requests.

        When a user types a trigger character (@, #, or [), this handler
        returns relevant symbol suggestions from the index and WriterAPI.

        Args:
            params: Completion parameters including position and document URI

        Returns:
            Completion list with symbol suggestions
        """
        uri = params.text_document.uri
        position = params.position

        logger.debug(f"Completion request: {uri} at {position}")

        try:
            document = server.workspace.get_text_document(uri)
            lines = document.source.split("\n")
            if position.line >= len(lines):
                return types.CompletionList(is_incomplete=False, items=[])

            line = lines[position.line]
            char_before = line[position.character - 1] if position.character > 0 else ""

            query = ""
            if char_before in ["@", "#", "["]:
                start = position.character - 1
                while start > 0 and line[start - 1] not in [" ", "\t", "\n"]:
                    start -= 1
                if start + 1 <= position.character:
                    query = line[start + 1 : position.character]
        except Exception as e:
            logger.error(f"Error extracting query for completion: {e}")
            return types.CompletionList(is_incomplete=False, items=[])

        items: list[types.CompletionItem] = []
        seen_names: set[str] = set()

        if char_before == "@":
            items.extend(await _get_character_completions(query, index, writer_api, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.LOCATION, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.ITEM, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.LORE, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.PLOTPOINT, seen_names))
        elif char_before == "#":
            items.extend(_get_symbol_completions(query, index, SymbolType.CHAPTER, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.OUTLINE, seen_names))
        elif char_before == "[":
            items.extend(_get_symbol_completions(query, index, SymbolType.PLOTPOINT, seen_names))
            items.extend(_get_symbol_completions(query, index, SymbolType.EVENT, seen_names))
        else:
            return types.CompletionList(is_incomplete=False, items=[])

        logger.debug(f"Returning {len(items)} completion items")
        return types.CompletionList(is_incomplete=False, items=items)


async def _get_character_completions(
    query: str,
    index: SymbolIndex,
    writer_api: "WriterAPI | None",
    seen_names: set[str],
) -> list[types.CompletionItem]:
    """
    Get character completions from both index and WriterAPI.

    Args:
        query: Search query
        index: Symbol index
        writer_api: Optional WriterAPI
        seen_names: Set of names already added

    Returns:
        List of completion items for characters
    """
    items = []
    
    # First, get characters from local index
    for symbol in index.search(query, symbol_type=SymbolType.CHARACTER):
        if symbol.name not in seen_names:
            seen_names.add(symbol.name)
            items.append(types.CompletionItem(
                label=symbol.name,
                kind=types.CompletionItemKind.Class,
                insert_text=symbol.name,
                detail="Character (local)",
                data={"symbol_id": symbol.id},
            ))
    
    # Then, get characters from WriterAPI if available
    if writer_api:
        try:
            characters = await writer_api.list_characters()
            for profile in characters:
                if profile.name not in seen_names:
                    if not query or query.lower() in profile.name.lower():
                        seen_names.add(profile.name)
                        items.append(types.CompletionItem(
                            label=profile.name,
                            kind=types.CompletionItemKind.Class,
                            insert_text=profile.name,
                            detail=f"Character ({profile.current_status.value if isinstance(profile.current_status, CharacterStatus) else profile.current_status})",
                            documentation=profile.bio[:200] if profile.bio else None,
                            data={"character_name": profile.name, "source": "writer_api"},
                        ))
                        for alias in profile.aliases:
                            if alias not in seen_names and (not query or query.lower() in alias.lower()):
                                seen_names.add(alias)
                                items.append(types.CompletionItem(
                                    label=alias,
                                    kind=types.CompletionItemKind.Class,
                                    insert_text=profile.name,
                                    detail=f"Alias for {profile.name}",
                                    data={"character_name": profile.name, "source": "writer_api"},
                                ))
        except Exception as e:
            logger.debug(f"Failed to get characters from WriterAPI: {e}")
    
    return items[:20]


def _get_symbol_completions(
    query: str,
    index: SymbolIndex,
    symbol_type: SymbolType,
    seen_names: set[str],
) -> list[types.CompletionItem]:
    """
    Get symbol completions from the index.

    Args:
        query: Search query
        index: Symbol index
        symbol_type: Type of symbols to search for
        seen_names: Set of names already added

    Returns:
        List of completion items
    """
    items = []
    
    for symbol in index.search(query, symbol_type=symbol_type):
        if symbol.name not in seen_names:
            seen_names.add(symbol.name)
            kind = _get_completion_item_kind(symbol.type)
            items.append(types.CompletionItem(
                label=symbol.name,
                kind=kind,
                insert_text=symbol.name,
                data={"symbol_id": symbol.id},
            ))
    
    return items


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
