"""
NovelWriter LSP - Document Parser

This module provides parsing functionality for extracting symbols from novel documents.
"""

import re
from typing import Any, cast

from novelwriter_lsp.types import (
    BaseSymbol,
    CharacterSymbol,
    ChapterSymbol,
    EventSymbol,
    ItemSymbol,
    LocationSymbol,
    LoreSymbol,
    OutlineLevel,
    OutlineSymbol,
    PlotPointSymbol,
    RelationshipSymbol,
    SymbolType,
)


# Regex patterns for symbol types
PATTERNS = {
    SymbolType.CHARACTER: re.compile(r"@Character:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.LOCATION: re.compile(r"@Location:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.ITEM: re.compile(r"@Item:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.LORE: re.compile(r"@Lore:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.PLOTPOINT: re.compile(r"@PlotPoint:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.OUTLINE: re.compile(r"@Outline:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.EVENT: re.compile(r"@Event:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.RELATIONSHIP: re.compile(r"@Relationship:\s*([^{]+)\s*(\{[^}]*\})?"),
    SymbolType.CHAPTER: re.compile(r"^#\s+(.*)$", re.MULTILINE),
}


def _generate_symbol_id(symbol_type: SymbolType, name: str, line_number: int) -> str:
    """Generate a unique symbol ID."""
    return f"{symbol_type.value}_{name.lower().replace(' ', '_')}_{line_number}"


def _parse_metadata(metadata_str: str | None) -> dict[str, Any]:
    """Parse metadata from {key: value} format."""
    if not metadata_str:
        return {}
    
    metadata = {}
    # Remove braces and parse key-value pairs
    content = metadata_str.strip()[1:-1]  # Remove { and }
    
    # Simple parsing for key: value pairs
    pairs = re.findall(r'(\w+):\s*([^,}]+)', content)
    for key, value in pairs:
        metadata[key.strip()] = value.strip().strip('"\'')
    
    return metadata


def _create_symbol_from_match(
    match: re.Match[str],
    symbol_type: SymbolType,
    uri: str,
    line_number: int,
) -> BaseSymbol | None:
    """Create a symbol instance from a regex match."""
    name = match.group(1).strip()
    metadata_str = match.group(2) if match.lastindex and match.lastindex >= 2 else None
    metadata = _parse_metadata(metadata_str)
    
    symbol_id = _generate_symbol_id(symbol_type, name, line_number)
    
    definition_range = {
        "start_line": line_number,
        "end_line": line_number,
        "start_character": match.start(),
        "end_character": match.end(),
    }
    
    # Create appropriate symbol type
    if symbol_type == SymbolType.CHARACTER:
        return CharacterSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            age=int(cast(str, metadata.get("age"))) if metadata.get("age") else None,
            status=cast(str, metadata.get("status", "alive")),
            occupation=metadata.get("occupation"),
            description=metadata.get("description", ""),
        )
    elif symbol_type == SymbolType.LOCATION:
        return LocationSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            location_type=metadata.get("location_type"),
            description=metadata.get("description", ""),
            region=metadata.get("region"),
        )
    elif symbol_type == SymbolType.ITEM:
        return ItemSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            item_type=metadata.get("item_type"),
            description=metadata.get("description", ""),
            owner=metadata.get("owner"),
        )
    elif symbol_type == SymbolType.LORE:
        return LoreSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            lore_type=metadata.get("lore_type"),
            description=metadata.get("description", ""),
            category=metadata.get("category"),
        )
    elif symbol_type == SymbolType.PLOTPOINT:
        return PlotPointSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            plot_type=metadata.get("plot_type"),
            description=metadata.get("description", ""),
        )
    elif symbol_type == SymbolType.OUTLINE:
        level_str = metadata.get("level", "master")
        level = OutlineLevel(level_str) if level_str in [e.value for e in OutlineLevel] else OutlineLevel.MASTER
        
        return OutlineSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            level=level,
            volume_number=int(metadata["volume_number"]) if metadata.get("volume_number") else None,
            chapter_number=int(metadata["chapter_number"]) if metadata.get("chapter_number") else None,
        )
    elif symbol_type == SymbolType.EVENT:
        return EventSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            chapter=int(metadata.get("chapter", 0)),
            location=metadata.get("location", ""),
            description=metadata.get("description", ""),
            importance=metadata.get("importance", "minor"),
        )
    elif symbol_type == SymbolType.RELATIONSHIP:
        return RelationshipSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            from_character=metadata.get("from_character", ""),
            to_character=metadata.get("to_character", ""),
            relation_type=metadata.get("relation_type", ""),
        )
    elif symbol_type == SymbolType.CHAPTER:
        return ChapterSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            title=name,
        )
    
    return None


def parse_document(content: str, uri: str) -> list[BaseSymbol]:
    """
    Parse a document and extract all symbols.
    
    Args:
        content: The document content to parse
        uri: The URI of the document
        
    Returns:
        A list of BaseSymbol instances representing all found symbols
    """
    symbols: list[BaseSymbol] = []
    lines = content.split("\n")
    
    for line_number, line in enumerate(lines):
        for symbol_type, pattern in PATTERNS.items():
            # Special handling for chapter pattern (matches from start of line)
            if symbol_type == SymbolType.CHAPTER:
                for match in pattern.finditer(line):
                    symbol = _create_symbol_from_match(match, symbol_type, uri, line_number)
                    if symbol:
                        symbols.append(symbol)
            else:
                match = pattern.search(line)
                if match:
                    symbol = _create_symbol_from_match(match, symbol_type, uri, line_number)
                    if symbol:
                        symbols.append(symbol)
    
    return symbols


def parse_incremental(content: str, uri: str, changed_range: dict[str, int]) -> list[BaseSymbol]:
    """
    Parse only the changed portion of a document.
    
    This is a stub implementation for future incremental parsing optimization.
    
    Args:
        content: The document content to parse
        uri: The URI of the document
        changed_range: Dictionary with start_line, end_line, start_character, end_character
        
    Returns:
        A list of BaseSymbol instances found in the changed range
    """
    # TODO: Implement incremental parsing logic
    # For now, fall back to full parsing
    return parse_document(content, uri)
