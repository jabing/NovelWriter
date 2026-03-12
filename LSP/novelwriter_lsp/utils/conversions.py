"""Conversion utilities between shared models and LSP types.

This module provides bidirectional conversion between novelwriter_shared
models (CharacterProfile, Fact) and LSP internal types (CharacterSymbol, etc.)
"""

from __future__ import annotations

from typing import Any, cast

from novelwriter_shared.models import (
    CharacterProfile,
    CharacterStatus,
    CharacterTimelineEvent,
    EventImportance,
    EventType,
    Fact,
    TimelineConflict,
)
from novelwriter_lsp.types import (
    BaseSymbol,
    CharacterSymbol,
    SymbolType,
)


def profile_to_symbol(
    profile: CharacterProfile,
    definition_uri: str = "",
    definition_range: dict[str, int] | None = None,
    novel_id: str = "",
) -> CharacterSymbol:
    """Convert a CharacterProfile to a CharacterSymbol.

    Args:
        profile: The CharacterProfile from shared models
        definition_uri: URI where the symbol is defined (LSP-specific)
        definition_range: Line/character range of definition (LSP-specific)
        novel_id: ID of the novel this symbol belongs to

    Returns:
        CharacterSymbol for use in LSP features
    """
    if definition_range is None:
        definition_range = {
            "start_line": 0,
            "end_line": 0,
            "start_character": 0,
            "end_character": len(profile.name),
        }

    timeline: list[dict[str, object]] = [
        {
            "chapter": event.chapter,
            "event_type": event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
            "description": event.description,
            "importance": event.importance.value if isinstance(event.importance, EventImportance) else str(event.importance),
        }
        for event in profile.timeline
    ]

    relationships: list[dict[str, object]] = [
        {"character": char_name, "relation_type": rel_type}
        for char_name, rel_type in profile.relationships.items()
    ]

    status_str = profile.current_status.value if isinstance(profile.current_status, CharacterStatus) else str(profile.current_status)

    return CharacterSymbol(
        id=f"char_{profile.name}_{profile.id or ''}",
        name=profile.name,
        novel_id=novel_id,
        definition_uri=definition_uri,
        definition_range=definition_range,
        aliases=profile.aliases,
        age=None,
        status=status_str,
        description=profile.bio,
        personality=[],
        goals=[],
        timeline=timeline,
        relationships=relationships,
        current_location=None,
        inventory=[],
        metadata={
            "tier": profile.tier,
            "mbti": profile.mbti,
            "profession": profile.profession,
            "persona": profile.persona,
            "interested_topics": profile.interested_topics,
            **profile.metadata,
        },
    )


def symbol_to_profile(symbol: CharacterSymbol) -> CharacterProfile:
    """Convert a CharacterSymbol to a CharacterProfile.

    Args:
        symbol: The CharacterSymbol from LSP types

    Returns:
        CharacterProfile for use with shared models
    """
    timeline: list[CharacterTimelineEvent] = []
    for event_data in symbol.timeline:
        if isinstance(event_data, dict):
            timeline.append(CharacterTimelineEvent(
                chapter=int(event_data.get("chapter", 0)),
                event_type=cast(EventType | str, event_data.get("event_type", EventType.APPEARANCE)),
                description=str(event_data.get("description", "")),
                importance=cast(EventImportance | str, event_data.get("importance", "minor")),
            ))

    relationships: dict[str, str] = {}
    for rel in symbol.relationships:
        if isinstance(rel, dict):
            char_name = str(rel.get("character", ""))
            rel_type = str(rel.get("relation_type", ""))
            if char_name:
                relationships[char_name] = rel_type

    metadata = symbol.metadata if symbol.metadata else {}
    
    return CharacterProfile(
        name=symbol.name,
        aliases=symbol.aliases,
        birth_chapter=int(metadata["birth_chapter"]) if "birth_chapter" in metadata else None,
        death_chapter=int(metadata["death_chapter"]) if "death_chapter" in metadata else None,
        current_status=str(symbol.status),
        timeline=timeline,
        relationships=relationships,
        metadata=dict(metadata),
        bio=symbol.description,
        persona=str(metadata.get("persona", "")),
        mbti=str(metadata.get("mbti", "")),
        profession=str(metadata.get("profession", "")),
        interested_topics=list(cast(list[str], metadata.get("interested_topics", []))),
        tier=int(metadata.get("tier", 1)),
    )


def conflict_to_diagnostics(conflict: TimelineConflict) -> dict[str, Any]:
    """Convert a TimelineConflict to diagnostic info.

    Args:
        conflict: The TimelineConflict from shared models

    Returns:
        Dictionary with diagnostic information
    """
    return {
        "message": conflict.description,
        "severity": conflict.severity,
        "conflict_type": conflict.conflict_type.value,
        "character_name": conflict.character_name,
        "event1_chapter": conflict.event1.chapter,
        "event2_chapter": conflict.event2.chapter,
        "suggested_resolution": conflict.suggested_resolution,
    }


def is_character_symbol(symbol: BaseSymbol) -> bool:
    """Check if a symbol is a CharacterSymbol.

    Args:
        symbol: The symbol to check

    Returns:
        True if the symbol is a CharacterSymbol
    """
    return symbol.type == SymbolType.CHARACTER
