"""Structured input schemas for the novel writing system.

This module provides Pydantic models for all agent inputs, enabling:
- Type validation and auto-completion
- Input transformation and normalization
- Documentation generation
- Backward compatibility with existing dict-based inputs
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    """Types of agents in the system."""

    CHARACTER = "character"
    PLOT = "plot"
    WORLDBUILDING = "worldbuilding"
    WRITER = "writer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    PUBLISHER = "publisher"


class Language(str, Enum):
    """Supported languages for content generation."""

    ENGLISH = "en"
    CHINESE = "zh"
    MULTILINGUAL = "multilingual"


class Genre(str, Enum):
    """Supported genres."""

    SCI_FI = "scifi"
    FANTASY = "fantasy"
    ROMANCE = "romance"
    HISTORY = "history"
    MILITARY = "military"
    GENERAL = "general"


class BaseInput(BaseModel):
    """Base input model for all agents."""

    agent_type: AgentType = Field(..., description="Type of agent processing this input")
    novel_id: str = Field(..., description="Unique identifier for the novel/project")
    request_id: str | None = Field(None, description="Unique request ID for tracking")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When request was created"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        extra = "ignore"  # Ignore extra fields for backward compatibility


class CharacterCreationInput(BaseInput):
    """Input for character creation agent."""

    agent_type: AgentType = Field(AgentType.CHARACTER, description="Character agent")
    genre: Genre = Field(..., description="Genre for character archetypes")
    count: int = Field(1, ge=1, le=10, description="Number of characters to create")
    relationships: list[dict[str, Any]] | None = Field(
        None, description="Existing character relationships to consider"
    )
    existing_characters: list[dict[str, Any]] | None = Field(
        None, description="Existing characters to avoid duplicating"
    )
    main_character: bool = Field(False, description="Whether to create a main character")
    archetype: str | None = Field(None, description="Specific archetype to use")

    @field_validator("count")
    @classmethod
    def validate_count(cls, v, info):
        """Validate character count based on genre."""
        if info.data and "genre" in info.data:
            if info.data["genre"] == Genre.ROMANCE and v < 2:
                raise ValueError("Romance genre requires at least 2 characters")
        return v


class PlotGenerationInput(BaseInput):
    """Input for plot generation agent."""

    agent_type: AgentType = Field(AgentType.PLOT, description="Plot agent")
    genre: Genre = Field(..., description="Genre for plot structure")
    chapter_count: int = Field(30, ge=10, le=300, description="Total chapters in novel")
    characters: list[dict[str, Any]] = Field(..., description="Characters to include in the plot")
    world_context: dict[str, Any] | None = Field(None, description="World context for the plot")
    story_structure: str | None = Field(
        None, description="Specific story structure (hero's journey, three-act, etc.)"
    )
    existing_outline: dict[str, Any] | None = Field(
        None, description="Existing outline to expand or modify"
    )

    @field_validator("chapter_count")
    @classmethod
    def validate_chapter_count(cls, v):
        """Validate chapter count."""
        if v % 5 != 0:
            raise ValueError("Chapter count should be divisible by 5 for pacing")
        return v


class WorldbuildingInput(BaseInput):
    """Input for worldbuilding agent."""

    agent_type: AgentType = Field(AgentType.WORLDBUILDING, description="Worldbuilding agent")
    genre: Genre = Field(..., description="Genre for world elements")
    scale: str = Field("planet", description="Scale of world (city, country, planet, galaxy)")
    magic_system: bool = Field(False, description="Whether to include magic system")
    technology_level: str | None = Field(
        None, description="Technology level (medieval, modern, futuristic, etc.)"
    )
    existing_rules: dict[str, Any] | None = Field(
        None, description="Existing world rules to expand"
    )
    characters: list[dict[str, Any]] | None = Field(
        None, description="Characters that inhabit this world"
    )
    plot_context: dict[str, Any] | None = Field(
        None, description="Plot context for world relevance"
    )


class ChapterWritingInput(BaseInput):
    """Input for chapter writing agents."""

    agent_type: AgentType = Field(AgentType.WRITER, description="Writer agent")
    genre: Genre = Field(..., description="Genre for writing style")
    chapter_number: int = Field(..., ge=1, description="Chapter number being written")
    chapter_outline: str = Field(..., description="Outline for this chapter")
    characters: list[dict[str, Any]] = Field(
        ..., description="Character profiles appearing in this chapter"
    )
    world_context: dict[str, Any] = Field(
        ..., description="World-building context for this chapter"
    )
    style_guide: str | None = Field(None, description="Optional style guidelines")
    learning_hints: list[str] | None = Field(
        None, description="Learned patterns from successful chapters"
    )
    market_keywords: dict[str, Any] | None = Field(None, description="Market research keywords")
    language: Language | None = Field(Language.ENGLISH, description="Language for content")
    story_state: dict[str, Any] | None = Field(
        None, description="Current story state for continuity"
    )
    previous_chapter_summary: str | None = Field(None, description="Summary of previous chapter")

    @field_validator("chapter_number")
    @classmethod
    def validate_chapter_number(cls, v, info):
        """Validate chapter number for golden chapters."""
        if v <= 3:
            # Golden chapters require extra attention
            if (
                info.data
                and "genre" in info.data
                and info.data["genre"] == Genre.ROMANCE
                and v == 1
            ):
                # Romance first chapter needs special handling
                pass
        return v


class ReviewInput(BaseInput):
    """Input for review/editor agent."""

    agent_type: AgentType = Field(AgentType.REVIEWER, description="Review agent")
    content_type: str = Field(..., description="Type of content (chapter, character, plot, world)")
    content: dict[str, Any] = Field(..., description="Content to review")
    original_input: dict[str, Any] | None = Field(
        None, description="Original agent input for context"
    )
    review_criteria: list[str] | None = Field(
        None, description="Specific criteria to review against"
    )
    constitution_rules: list[str] | None = Field(None, description="Constitution rules to apply")
    glossary_terms: list[str] | None = Field(
        None, description="Glossary terms to check consistency"
    )
    severity_level: str = Field("normal", description="Review severity (strict, normal, lenient)")


class VersionMetadata(BaseModel):
    """Metadata for version control."""

    version_id: str = Field(..., description="Unique version identifier")
    parent_version: str | None = Field(None, description="Parent version ID")
    agent_type: AgentType = Field(..., description="Agent that created this version")
    timestamp: datetime = Field(default_factory=datetime.now, description="When created")
    changes: list[str] = Field(..., description="List of changes in this version")
    author: str | None = Field(None, description="Author/agent name")
    tags: list[str] = Field(default_factory=list, description="Version tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class KnowledgeGraphNode(BaseModel):
    """Node in the knowledge graph."""

    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Type of node (character, plot, location, concept)")
    properties: dict[str, Any] = Field(..., description="Node properties")
    embeddings: list[float] | None = Field(None, description="Vector embeddings")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class KnowledgeGraphEdge(BaseModel):
    """Edge in the knowledge graph."""

    edge_id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Type of relationship")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Relationship strength")
    properties: dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")


class KnowledgeGraphQuery(BaseModel):
    """Query for the knowledge graph."""

    node_types: list[str] | None = Field(None, description="Node types to search")
    relationship_types: list[str] | None = Field(None, description="Relationship types to follow")
    property_filters: dict[str, Any] | None = Field(None, description="Property filters for nodes")
    depth: int = Field(2, ge=1, le=5, description="Traversal depth")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")


# Union type for all agent inputs
AgentInput = (
    CharacterCreationInput
    | PlotGenerationInput
    | WorldbuildingInput
    | ChapterWritingInput
    | ReviewInput
)


def normalize_agent_input(input_dict: dict[str, Any]) -> AgentInput:
    """Normalize agent input dictionary to appropriate schema.

    Args:
        input_dict: Raw agent input dictionary

    Returns:
        Appropriate AgentInput instance

    Raises:
        ValueError: If input cannot be normalized
    """
    # Detect agent type from input
    agent_type = input_dict.get("agent_type")
    if not agent_type:
        # Try to infer from content
        if "chapter_number" in input_dict:
            agent_type = AgentType.WRITER
        elif "genre" in input_dict and "count" in input_dict:
            agent_type = AgentType.CHARACTER
        elif "chapter_count" in input_dict:
            agent_type = AgentType.PLOT
        elif "scale" in input_dict:
            agent_type = AgentType.WORLDBUILDING
        elif "content_type" in input_dict:
            agent_type = AgentType.REVIEWER
        else:
            raise ValueError("Cannot infer agent type from input")

    # Create appropriate model
    if agent_type == AgentType.CHARACTER:
        return CharacterCreationInput(**input_dict)
    elif agent_type == AgentType.PLOT:
        return PlotGenerationInput(**input_dict)
    elif agent_type == AgentType.WORLDBUILDING:
        return WorldbuildingInput(**input_dict)
    elif agent_type == AgentType.WRITER:
        return ChapterWritingInput(**input_dict)
    elif agent_type in (AgentType.REVIEWER, AgentType.EDITOR):
        return ReviewInput(**input_dict)
    else:
        raise ValueError(f"Unsupported agent type: {agent_type}")
