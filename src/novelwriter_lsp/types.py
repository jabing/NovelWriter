"""
NovelWriter LSP - Symbol Type Definitions

This module defines the core symbol types used throughout the LSP server.
Based on the architecture design document (LSP_ARCHITECTURE_REDESIGN.md).
"""

from dataclasses import dataclass, field
from enum import Enum


class SymbolType(Enum):
    """Enum representing all supported symbol types."""

    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    LORE = "lore"
    PLOTPOINT = "plotpoint"
    OUTLINE = "outline"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    CHAPTER = "chapter"


class OutlineLevel(Enum):
    """Enum representing the three-tier outline hierarchy."""

    MASTER = "master"  # 总纲 (Master Outline)
    VOLUME = "volume"  # 卷大纲 (Volume Outline)
    CHAPTER = "chapter"  # 章大纲 (Chapter Outline)


@dataclass
class BaseSymbol:
    """
    Base class for all symbol types.

    Attributes:
        id: Unique identifier for the symbol
        type: The type of symbol
        name: Human-readable name
        novel_id: ID of the novel this symbol belongs to
        definition_uri: URI where the symbol is defined
        definition_range: Line/character range of the definition
        references: List of reference locations
        metadata: Additional metadata as key-value pairs
    """

    id: str
    type: SymbolType
    name: str
    novel_id: str
    definition_uri: str
    definition_range: dict[str, int]
    references: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class CharacterSymbol(BaseSymbol):
    """
    Symbol representing a character in the novel.

    Attributes:
        aliases: Alternative names or aliases for this character
        age: Character's age (if known)
        status: Current status (alive, deceased, missing, etc.)
        occupation: Character's job or role
        description: Physical and personality description
        personality: List of personality traits
        goals: List of character goals/motivations
        timeline: List of significant events in character's timeline
        relationships: List of relationships with other characters
        current_location: Where the character currently is
        inventory: Items the character possesses
    """

    type: SymbolType = field(default=SymbolType.CHARACTER, init=False)
    aliases: list[str] = field(default_factory=list)
    age: int | None = None
    status: str = "alive"
    occupation: str | None = None
    description: str = ""
    personality: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    timeline: list[dict[str, object]] = field(default_factory=list)
    relationships: list[dict[str, object]] = field(default_factory=list)
    current_location: str | None = None
    inventory: list[str] = field(default_factory=list)


@dataclass
class LocationSymbol(BaseSymbol):
    """
    Symbol representing a location in the novel.

    Attributes:
        aliases: Alternative names or aliases for this location
        location_type: Type of location (city, building, room, etc.)
        description: Detailed description of the location
        region: Geographic region or area
        climate: Typical weather/climate
        significance: Why this location is important to the story
        visited_by: List of characters who have visited
        events: List of events that occurred here
    """

    type: SymbolType = field(default=SymbolType.LOCATION, init=False)
    aliases: list[str] = field(default_factory=list)
    location_type: str | None = None
    description: str = ""
    region: str | None = None
    climate: str | None = None
    significance: str = ""
    visited_by: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@dataclass
class ItemSymbol(BaseSymbol):
    """
    Symbol representing a significant item/object.

    Attributes:
        aliases: Alternative names or aliases for this item
        item_type: Category of item (weapon, artifact, tool, etc.)
        description: Physical description
        owner: Current owner of the item
        history: Historical background of the item
        abilities: Special properties or abilities
        significance: Why this item is important
    """

    type: SymbolType = field(default=SymbolType.ITEM, init=False)
    aliases: list[str] = field(default_factory=list)
    item_type: str | None = None
    description: str = ""
    owner: str | None = None
    history: str = ""
    abilities: list[str] = field(default_factory=list)
    significance: str = ""


@dataclass
class LoreSymbol(BaseSymbol):
    """
    Symbol representing world-building lore, rules, or facts.

    Attributes:
        aliases: Alternative names or aliases for this lore entry
        lore_type: Category (magic system, history, culture, etc.)
        description: Detailed explanation of the lore
        category: Broader category this belongs to
        rules: Specific rules or constraints
        related_lore: References to related lore entries
    """

    type: SymbolType = field(default=SymbolType.LORE, init=False)
    aliases: list[str] = field(default_factory=list)
    lore_type: str | None = None
    description: str = ""
    category: str | None = None
    rules: list[str] = field(default_factory=list)
    related_lore: list[str] = field(default_factory=list)


@dataclass
class PlotPointSymbol(BaseSymbol):
    """
    Symbol representing a plot point or story beat.

    Attributes:
        aliases: Alternative names or aliases for this plot point
        plot_type: Type of plot point (inciting incident, climax, etc.)
        description: What happens at this plot point
        chapter: Which chapter this occurs in
        volume: Which volume this occurs in
        involved_characters: Characters involved in this plot point
        foreshadows: List of plot points this foreshadows
        callbacks: List of earlier plot points this references
    """

    type: SymbolType = field(default=SymbolType.PLOTPOINT, init=False)
    aliases: list[str] = field(default_factory=list)
    plot_type: str | None = None
    description: str = ""
    chapter: int | None = None
    volume: int | None = None
    involved_characters: list[str] = field(default_factory=list)
    foreshadows: list[str] = field(default_factory=list)
    callbacks: list[str] = field(default_factory=list)


@dataclass
class OutlineSymbol(BaseSymbol):
    """
    Symbol representing an outline element (master, volume, or chapter).

    Attributes:
        aliases: Alternative names or aliases for this outline
        level: Hierarchy level (master, volume, chapter)
        volume_number: Volume number (for volume/chapter outlines)
        chapter_number: Chapter number (for chapter outlines)
        content: The actual outline content
        parent: Parent outline ID (for hierarchy)
        children: Child outline IDs
    """

    type: SymbolType = field(default=SymbolType.OUTLINE, init=False)
    aliases: list[str] = field(default_factory=list)
    level: OutlineLevel = OutlineLevel.MASTER
    volume_number: int | None = None
    chapter_number: int | None = None
    content: dict[str, object] = field(default_factory=dict)
    parent: str | None = None
    children: list[str] = field(default_factory=list)


@dataclass
class EventSymbol(BaseSymbol):
    """
    Symbol representing a story event (for timeline tracking).

    Attributes:
        aliases: Alternative names or aliases for this event
        event_id: Unique event identifier
        chapter: Chapter where this event occurs
        volume: Volume where this event occurs
        time: When the event happens (in-story time)
        location: Where the event takes place
        participants: Characters involved in the event
        description: What happens in this event
        evidence: Sources/chapters where this event is mentioned
        impact: Consequences of this event
        importance: Event importance (critical, major, minor)
    """

    type: SymbolType = field(default=SymbolType.EVENT, init=False)
    aliases: list[str] = field(default_factory=list)
    event_id: str = ""
    chapter: int = 0
    volume: int | None = None
    time: str = ""
    location: str = ""
    participants: list[str] = field(default_factory=list)
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    impact: list[str] = field(default_factory=list)
    importance: str = "minor"  # critical, major, minor


@dataclass
class RelationshipSymbol(BaseSymbol):
    """
    Symbol representing a relationship between characters.

    Attributes:
        aliases: Alternative names or aliases for this relationship
        from_character: Source character of the relationship
        to_character: Target character of the relationship
        relation_type: Type of relationship (friend, enemy, lover, etc.)
        since_volume: Volume where this relationship started
        since_chapter: Chapter where this relationship started
        history: Evolution of the relationship over time
    """

    type: SymbolType = field(default=SymbolType.RELATIONSHIP, init=False)
    aliases: list[str] = field(default_factory=list)
    from_character: str = ""
    to_character: str = ""
    relation_type: str = ""
    since_volume: int | None = None
    since_chapter: int | None = None
    history: list[dict[str, object]] = field(default_factory=list)


@dataclass
class ChapterSymbol(BaseSymbol):
    """
    Symbol representing a chapter in the novel.

    Attributes:
        aliases: Alternative names or aliases for this chapter
        chapter_number: Sequential chapter number
        volume_number: Volume this chapter belongs to
        title: Chapter title
        word_count: Number of words in the chapter
        summary: Brief summary of chapter content
        outline_id: Reference to the chapter outline
        events: List of events that occur in this chapter
        characters_appearing: Characters that appear in this chapter
        status: Writing status (draft, revised, final)
    """

    type: SymbolType = field(default=SymbolType.CHAPTER, init=False)
    aliases: list[str] = field(default_factory=list)
    chapter_number: int = 0
    volume_number: int | None = None
    title: str = ""
    word_count: int = 0
    summary: str = ""
    outline_id: str | None = None
    events: list[str] = field(default_factory=list)
    characters_appearing: list[str] = field(default_factory=list)
    status: str = "draft"  # draft, revised, final
