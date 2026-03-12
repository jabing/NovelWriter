"""
NovelWriter LSP - Hover Handler

This module provides the hover LSP feature handler to show symbol
information when hovering over a symbol.
"""

import logging

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    BaseSymbol,
    CharacterSymbol,
    LocationSymbol,
    ItemSymbol,
    LoreSymbol,
    PlotPointSymbol,
    OutlineSymbol,
    EventSymbol,
    RelationshipSymbol,
    ChapterSymbol,
)

logger = logging.getLogger(__name__)


def register_hover(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the hover handler with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index for looking up symbols
    """

    @server.feature(types.TEXT_DOCUMENT_HOVER)
    def hover(params: types.HoverParams) -> types.Hover | None:
        """
        Handle hover requests.

        When a user hovers over a symbol, this handler finds
        the symbol and returns formatted information about it.

        Args:
            params: Hover parameters including position and document URI

        Returns:
            Hover information with Markdown content, or None if not found
        """
        uri = params.text_document.uri
        position = params.position

        logger.debug(f"Hover request: {uri} at {position}")

        # Extract word at position and look up symbol
        symbol_name = _get_word_at_position(server, uri, position)
        if not symbol_name:
            logger.debug(f"No symbol found at position {position}")
            return None

        symbol = index.get_symbol(symbol_name)
        if not symbol:
            logger.debug(f"Symbol '{symbol_name}' not found in index")
            return None

        # Build Markdown content
        content = _build_hover_content(symbol)

        # Build range from symbol definition
        def_range = symbol.definition_range
        hover_range = types.Range(
            start=types.Position(
                line=def_range.get("start_line", 0),
                character=def_range.get("start_character", 0),
            ),
            end=types.Position(
                line=def_range.get("end_line", 0),
                character=def_range.get("end_character", 0),
            ),
        )

        logger.debug(f"Returning hover info for '{symbol_name}'")
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=content),
            range=hover_range,
        )


def _build_hover_content(symbol: BaseSymbol) -> str:
    """
    Build Markdown content for hover information based on symbol type.

    Args:
        symbol: The symbol to display information for

    Returns:
        Markdown formatted string with symbol information
    """
    content = f"**{symbol.type.value.capitalize()}**: {symbol.name}\n\n"

    if isinstance(symbol, CharacterSymbol):
        content += _character_info(symbol)
    elif isinstance(symbol, LocationSymbol):
        content += _location_info(symbol)
    elif isinstance(symbol, ItemSymbol):
        content += _item_info(symbol)
    elif isinstance(symbol, LoreSymbol):
        content += _lore_info(symbol)
    elif isinstance(symbol, PlotPointSymbol):
        content += _plotpoint_info(symbol)
    elif isinstance(symbol, OutlineSymbol):
        content += _outline_info(symbol)
    elif isinstance(symbol, EventSymbol):
        content += _event_info(symbol)
    elif isinstance(symbol, RelationshipSymbol):
        content += _relationship_info(symbol)
    elif isinstance(symbol, ChapterSymbol):
        content += _chapter_info(symbol)

    # Add metadata if present
    if symbol.metadata:
        content += "\n---\n"
        for key, value in symbol.metadata.items():
            content += f"- **{key}**: {value}\n"

    return content


def _character_info(symbol: CharacterSymbol) -> str:
    """Build character-specific information."""
    info = ""
    if symbol.age is not None:
        info += f"- **Age**: {symbol.age}\n"
    if symbol.status:
        info += f"- **Status**: {symbol.status}\n"
    if symbol.occupation:
        info += f"- **Occupation**: {symbol.occupation}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    if symbol.personality:
        info += f"- **Traits**: {', '.join(symbol.personality[:3])}\n"
    if symbol.current_location:
        info += f"- **Location**: {symbol.current_location}\n"
    return info


def _location_info(symbol: LocationSymbol) -> str:
    """Build location-specific information."""
    info = ""
    if symbol.location_type:
        info += f"- **Type**: {symbol.location_type}\n"
    if symbol.region:
        info += f"- **Region**: {symbol.region}\n"
    if symbol.climate:
        info += f"- **Climate**: {symbol.climate}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    if symbol.significance:
        sig = symbol.significance[:80] + ("..." if len(symbol.significance) > 80 else "")
        info += f"- **Significance**: {sig}\n"
    return info


def _item_info(symbol: ItemSymbol) -> str:
    """Build item-specific information."""
    info = ""
    if symbol.item_type:
        info += f"- **Type**: {symbol.item_type}\n"
    if symbol.owner:
        info += f"- **Owner**: {symbol.owner}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    if symbol.abilities:
        info += f"- **Abilities**: {', '.join(symbol.abilities[:3])}\n"
    return info


def _lore_info(symbol: LoreSymbol) -> str:
    """Build lore-specific information."""
    info = ""
    if symbol.lore_type:
        info += f"- **Type**: {symbol.lore_type}\n"
    if symbol.category:
        info += f"- **Category**: {symbol.category}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    if symbol.rules:
        info += f"- **Rules**: {', '.join(symbol.rules[:3])}\n"
    return info


def _plotpoint_info(symbol: PlotPointSymbol) -> str:
    """Build plot point-specific information."""
    info = ""
    if symbol.plot_type:
        info += f"- **Type**: {symbol.plot_type}\n"
    if symbol.chapter is not None:
        info += f"- **Chapter**: {symbol.chapter}\n"
    if symbol.volume is not None:
        info += f"- **Volume**: {symbol.volume}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    if symbol.involved_characters:
        info += f"- **Characters**: {', '.join(symbol.involved_characters[:3])}\n"
    return info


def _outline_info(symbol: OutlineSymbol) -> str:
    """Build outline-specific information."""
    info = ""
    info += f"- **Level**: {symbol.level.value}\n"
    if symbol.volume_number is not None:
        info += f"- **Volume**: {symbol.volume_number}\n"
    if symbol.chapter_number is not None:
        info += f"- **Chapter**: {symbol.chapter_number}\n"
    return info


def _event_info(symbol: EventSymbol) -> str:
    """Build event-specific information."""
    info = ""
    info += f"- **Chapter**: {symbol.chapter}\n"
    if symbol.volume is not None:
        info += f"- **Volume**: {symbol.volume}\n"
    if symbol.time:
        info += f"- **Time**: {symbol.time}\n"
    if symbol.location:
        info += f"- **Location**: {symbol.location}\n"
    if symbol.description:
        desc = symbol.description[:100] + ("..." if len(symbol.description) > 100 else "")
        info += f"- **Description**: {desc}\n"
    info += f"- **Importance**: {symbol.importance}\n"
    return info


def _relationship_info(symbol: RelationshipSymbol) -> str:
    """Build relationship-specific information."""
    info = ""
    info += f"- **From**: {symbol.from_character}\n"
    info += f"- **To**: {symbol.to_character}\n"
    info += f"- **Type**: {symbol.relation_type}\n"
    if symbol.since_chapter is not None:
        info += f"- **Since**: Chapter {symbol.since_chapter}"
        if symbol.since_volume is not None:
            info += f" (Vol. {symbol.since_volume})"
        info += "\n"
    return info


def _chapter_info(symbol: ChapterSymbol) -> str:
    """Build chapter-specific information."""
    info = ""
    info += f"- **Number**: {symbol.chapter_number}\n"
    if symbol.volume_number is not None:
        info += f"- **Volume**: {symbol.volume_number}\n"
    if symbol.title:
        info += f"- **Title**: {symbol.title}\n"
    if symbol.word_count > 0:
        info += f"- **Words**: {symbol.word_count:,}\n"
    if symbol.status:
        info += f"- **Status**: {symbol.status}\n"
    if symbol.summary:
        summary = symbol.summary[:100] + ("..." if len(symbol.summary) > 100 else "")
        info += f"- **Summary**: {summary}\n"
    return info


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
