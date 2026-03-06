"""
NovelWriter LSP - Document Parser

This module provides parsing functionality for extracting symbols from novel documents.
"""

import re
from typing import Any, cast
from lsprotocol import types

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
    pairs = re.findall(r"(\w+):\s*([^,}]+)", content)
    for key, value in pairs:
        metadata[key.strip()] = value.strip().strip("\"'")

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
        level = (
            OutlineLevel(level_str)
            if level_str in [e.value for e in OutlineLevel]
            else OutlineLevel.MASTER
        )

        return OutlineSymbol(
            id=symbol_id,
            name=name,
            novel_id="",
            definition_uri=uri,
            definition_range=definition_range,
            metadata=metadata,
            level=level,
            volume_number=int(metadata["volume_number"]) if metadata.get("volume_number") else None,
            chapter_number=int(metadata["chapter_number"])
            if metadata.get("chapter_number")
            else None,
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


def parse_incremental(
    old_content: str,
    new_content: str,
    changes: list[types.TextDocumentContentChangeEvent],
    uri: str,
) -> list[BaseSymbol]:
    """
    Parse only the changed portion of a document.

    Args:
        old_content: Previous content of the document
        new_content: Current content of the document
        changes: List of change events
        uri: The URI of the document

    Returns:
        A list of BaseSymbol instances affected by the changes
    """
    affected_lines: set[int] = set()
    new_lines = new_content.splitlines()
    full_parse_needed = False

    for change in changes:
        # Check if this change has a 'range' attribute (incremental change)
        if hasattr(change, "range"):
            change_range = getattr(change, "range", None)
            if change_range is not None:
                start_line = change_range.start.line
                end_line = change_range.end.line
                for line in range(max(0, start_line - 1), min(len(new_lines), end_line + 2)):
                    affected_lines.add(line)
        else:
            # No range means full document change
            full_parse_needed = True
            break

    if full_parse_needed or not affected_lines:
        return parse_document(new_content, uri)

    all_symbols = parse_document(new_content, uri)
    affected_symbols = []

    for symbol in all_symbols:
        def_range = symbol.definition_range
        symbol_line = def_range.get("start_line", 0)
        if symbol_line in affected_lines:
            affected_symbols.append(symbol)

    return affected_symbols


def parse_incremental_with_range(
    content: str,
    uri: str,
    changed_range: dict[str, int] | None = None,
) -> list[BaseSymbol]:
    """
    Parse only the changed portion of a document (backward compatibility).

    Args:
        content: The document content to parse
        uri: The URI of the document
        changed_range: Dictionary with start_line, end_line, start_character, end_character

    Returns:
        A list of BaseSymbol instances found in the changed range
    """
    # Backward compatibility: if called with old signature, fall back to full parsing
    return parse_document(content, uri)
