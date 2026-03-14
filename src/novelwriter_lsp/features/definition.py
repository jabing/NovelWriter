"""
NovelWriter LSP - Go to Definition Handler

Provides goto definition functionality with support for:
- Exact symbol name matching (highest priority)
- Alias-based symbol lookup (fallback)
- Conflict handling (returning multiple locations when applicable)
- Integration with WriterAPI for character lookups (optional)

Follows LSP specification: textDocument/definition returns Location | Location[] | null
"""

import logging
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import BaseSymbol

if TYPE_CHECKING:
    from novelwriter_shared.api import WriterAPI
    from novelwriter_shared.models import CharacterProfile

logger = logging.getLogger(__name__)

# Type alias for LSP Definition response (Location | Location[] | null)
DefinitionResult = types.Location | list[types.Location] | None

# Maximum number of locations to return for conflict resolution
MAX_LOCATIONS = 10


def _create_location(symbol: BaseSymbol) -> types.Location:
    """Create a Location object from a symbol.

    Args:
        symbol: The symbol to create a location for

    Returns:
        Location pointing to the symbol's definition
    """
    return types.Location(
        uri=symbol.definition_uri,
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
    )


def _create_location_from_profile(
    profile: CharacterProfile, 
    default_uri: str,
) -> types.Location | None:
    """Create a Location object from a CharacterProfile.

    Args:
        profile: The CharacterProfile to create a location for
        default_uri: Default URI to use if profile doesn't have one

    Returns:
        Location for the character definition, or None if not available
    """
    metadata = profile.metadata or {}
    definition_uri = metadata.get("definition_uri", default_uri)
    
    definition_range = metadata.get("definition_range", {
        "start_line": 0,
        "end_line": 0,
        "start_character": 0,
        "end_character": len(profile.name),
    })
    
    return types.Location(
        uri=definition_uri,
        range=types.Range(
            start=types.Position(
                line=definition_range.get("start_line", 0),
                character=definition_range.get("start_character", 0),
            ),
            end=types.Position(
                line=definition_range.get("end_line", 0),
                character=definition_range.get("end_character", len(profile.name)),
            ),
        ),
    )


def register_goto_definition(
    server: LanguageServer, 
    index: SymbolIndex,
    writer_api: "WriterAPI | None" = None,
) -> None:
    """Register goto definition handler with the LSP server.

    The handler implements a two-phase lookup strategy:
    1. Exact symbol name match (highest priority)
    2. Alias-based lookup (fallback)
    3. WriterAPI character lookup (if available)

    When both exact match and alias match find different symbols,
    all matching locations are returned (conflict handling).

    Args:
        server: The LSP server instance
        index: The symbol index for looking up definitions
        writer_api: Optional WriterAPI for character lookups
    """

    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    async def goto_definition(params: types.DefinitionParams) -> DefinitionResult:
        """Handle textDocument/definition requests.

        Lookup strategy:
        1. Extract the word at cursor position
        2. Try exact symbol name match first
        3. Try alias-based lookup as fallback
        4. Try WriterAPI for character lookups (if available)
        5. Collect all unique matches (conflict handling)
        6. Return Location, Location[], or null per LSP spec

        Args:
            params: DefinitionParams from the LSP client

        Returns:
            Location for single match, Location[] for multiple matches,
            or None if no symbol found
        """
        uri = params.text_document.uri
        position = params.position

        logger.debug(
            f"goto_definition request: {uri} at line {position.line}, char {position.character}"
        )

        document = server.workspace.get_text_document(uri)
        if not document or not document.source:
            return None

        lines = document.source.split("\n")
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        if position.character >= len(line):
            return None

        symbol_name = _extract_word(line, position.character, index)
        logger.debug(f"Extracted word: '{symbol_name}'")

        if not symbol_name:
            logger.debug("No word extracted")
            return None

        locations: list[types.Location] = []
        seen_symbol_ids: set[str] = set()

        # Phase 1: Try exact symbol name match (highest priority)
        exact_symbol = index.get_symbol(symbol_name)
        if exact_symbol:
            logger.debug(f"Found exact match for '{symbol_name}'")
            locations.append(_create_location(exact_symbol))
            seen_symbol_ids.add(exact_symbol.id)

        # Phase 2: Try alias-based lookup (fallback)
        alias_symbol = index.get_symbol_by_alias(symbol_name)
        if alias_symbol:
            if alias_symbol.id not in seen_symbol_ids:
                logger.debug(f"Found alias match for '{symbol_name}' -> '{alias_symbol.name}'")
                locations.append(_create_location(alias_symbol))
                seen_symbol_ids.add(alias_symbol.id)
            else:
                logger.debug(f"Alias match for '{symbol_name}' is same as exact match, skipping")

        # Phase 3: Try WriterAPI for character lookups (if available)
        if writer_api and not locations:
            try:
                character = await writer_api.get_character(symbol_name)
                if character:
                    logger.debug(f"Found character '{symbol_name}' via WriterAPI")
                    char_location = _create_location_from_profile(character, uri)
                    if char_location:
                        locations.append(char_location)
            except Exception as e:
                logger.debug(f"WriterAPI lookup failed for '{symbol_name}': {e}")

        if not locations:
            logger.debug(f"Symbol '{symbol_name}' not found in index (exact or alias)")
            return None

        if len(locations) == 1:
            logger.debug(
                f"Found single definition for '{symbol_name}' at line {locations[0].range.start.line}"
            )
            return locations[0]

        result = locations[:MAX_LOCATIONS]
        logger.debug(
            f"Found {len(locations)} definitions for '{symbol_name}', returning {len(result)}"
        )
        return result


def _extract_word(line: str, position: int, index: SymbolIndex) -> str:
    if not line or position < 0 or position >= len(line):
        return ""

    start = position
    while start > 0 and (
        line[start - 1].isalnum() or line[start - 1] == "_" or line[start - 1] == " "
    ):
        start -= 1

    end = position
    while end < len(line) and (line[end].isalnum() or line[end] == "_" or line[end] == " "):
        end += 1

    word = line[start:end].strip()
    logger.debug(f"_extract_word: position={position}, line='{line}' -> word='{word}'")

    for i in range(len(word), 0, -1):
        substring = word[:i]
        if not substring:
            continue

        symbol = index.get_symbol(substring)
        if symbol:
            logger.debug(f"_extract_word: found symbol '{substring}' in index")
            return substring

    return word
