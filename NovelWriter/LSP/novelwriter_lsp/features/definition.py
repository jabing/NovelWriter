"""
NovelWriter LSP - Go to Definition Handler
"""

import logging

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.index import SymbolIndex

from typing import Optional

logger = logging.getLogger(__name__)


def register_goto_definition(server: LanguageServer, index: SymbolIndex) -> None:
    """Register goto definition handler with the LSP server.
    
    Args:
        server: The LSP server instance
        index: The symbol index for looking up definitions
    """
    @server.feature(types.TEXT_DOCUMENT_DEFINITION)
    def goto_definition(params: types.DefinitionParams) -> Optional[types.Location]:
        uri = params.text_document.uri
        position = params.position
        
        logger.debug(f"goto_definition request: {uri} at line {position.line}, char {position.character}")
        
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
        
        symbol = index.get_symbol(symbol_name)
        if not symbol:
            symbol = index.get_symbol_by_alias(symbol_name)
            if not symbol:
                logger.debug(f"Symbol '{symbol_name}' not found in index (exact or alias)")
                return None
            else:
                logger.debug(f"Found symbol '{symbol_name}' via alias")
        
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
        
        logger.debug(f"Found definition for '{symbol_name}' at line {location.range.start.line}")
        return location

    

def _extract_word(line: str, position: int, index: SymbolIndex) -> str:
    if not line or position < 0 or position >= len(line):
        return ""
    
    start = position
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_" or line[start - 1] == " "):
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
