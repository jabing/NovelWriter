"""
NovelWriter LSP - Go to Definition Handler

This module provides the goto_definition LSP feature handler.
"""

import logging

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex

logger = logging.getLogger(__name__)


def register_goto_definition(server: LanguageServer, index: SymbolIndex) -> None:
    """
    Register the goto_definition handler with the LSP server.
    
    Args:
        server: The LSP server instance
        index: The symbol index for looking up definitions
    """
    
    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    def goto_definition(params: types.DefinitionParams) -> types.Location | None:
        """
        Handle goto definition requests.
        
        When a user clicks on a symbol reference, this handler finds
        the definition location and returns it to the LSP client.
        
        Args:
            params: Definition parameters including position and document URI
            
        Returns:
            Location of the symbol definition, or None if not found
        """
        uri = params.text_document.uri
        position = params.position
        
        logger.debug(f"goto_definition request: {uri} at {position}")
        
        symbol_name = _get_word_at_position(server, uri, position)
        if not symbol_name:
            logger.debug(f"No symbol found at position {position}")
            return None
        
        symbol = index.get_symbol(symbol_name)
        if not symbol:
            logger.debug(f"Symbol '{symbol_name}' not found in index")
            return None
        
        location = types.Location(
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
        
        logger.debug(f"Found definition for '{symbol_name}' at {location.uri}")
        return location


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
