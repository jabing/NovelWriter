"""
NovelWriter LSP - Find References Handler

This module provides the find_references LSP feature handler.
"""

import logging
from typing import cast

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex

logger = logging.getLogger(__name__)


def register_find_references(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the find_references handler with the LSP server.
    
    Args:
        server: The LSP server instance
        index: The symbol index for looking up references
    """
    
    @server.feature(types.TEXT_DOCUMENT_REFERENCES)
    def find_references(params: types.ReferenceParams) -> list[types.Location] | None:
        """
        Handle find references requests.
        
        When a user requests to find all references to a symbol,
        this handler returns all locations where the symbol is referenced.
        
        Args:
            params: Reference parameters including position and document URI
            
        Returns:
            List of locations where the symbol is referenced, or None if not found
        """
        uri = params.text_document.uri
        position = params.position
        
        logger.debug(f"find_references request: {uri} at {position}")
        
        symbol_name = _get_word_at_position(server, uri, position)
        if not symbol_name:
            logger.debug(f"No symbol found at position {position}")
            return None
        
        symbol = index.get_symbol(symbol_name)
        if not symbol:
            logger.debug(f"Symbol '{symbol_name}' not found in index")
            return None
        
        locations = []
        
        if symbol.definition_uri and symbol.definition_range:
            locations.append(
                types.Location(
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
            )
        
        for ref in symbol.references:
            try:
                ref_uri = str(ref.get("uri", uri))  # type: ignore[arg-type]
                start_line = int(ref.get("start_line", 0))  # type: ignore[arg-type]
                start_char = int(ref.get("start_character", 0))  # type: ignore[arg-type]
                end_line = int(ref.get("end_line", 0))  # type: ignore[arg-type]
                end_char = int(ref.get("end_character", 0))  # type: ignore[arg-type]
                
                location = types.Location(
                    uri=ref_uri,
                    range=types.Range(
                        start=types.Position(
                            line=start_line,
                            character=start_char,
                        ),
                        end=types.Position(
                            line=end_line,
                            character=end_char,
                        ),
                    ),
                )
                locations.append(location)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid reference format: {e}")
                continue
        
        logger.debug(f"Found {len(locations)} references for '{symbol_name}'")
        return locations if locations else None


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
