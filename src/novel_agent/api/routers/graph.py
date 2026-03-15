"""Graph API router for character relationship graph queries.

Provides endpoints to retrieve character relationships in Cytoscape.js format
for visualization of character relationship networks.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.novel_agent.api.dependencies import get_current_user_id, get_state
from src.novel_agent.api.schemas.graph import (
    GraphEdge,
    GraphNode,
    GraphResponse,
)
from src.novel_agent.memory.character_memory import CharacterMemory
from src.novel_agent.studio.core.state import StudioState

router = APIRouter(
    prefix="/api/projects/{project_id}/graph",
    tags=["graph"],
    redirect_slashes=False,
)


@router.get("/characters", response_model=GraphResponse)
async def get_character_graph(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    state: Annotated[StudioState, Depends(get_state)],
) -> GraphResponse:
    """Get character relationship graph in Cytoscape.js format.

    Retrieves all characters for the project and their relationships,
    transforming them into Cytoscape.js graph format with nodes and edges.

    Args:
        project_id: The project ID to get characters for
        user_id: Current user ID (for access control)
        state: StudioState instance

    Returns:
        GraphResponse with nodes and edges in Cytoscape.js format

    Raises:
        HTTPException: If project not found or access denied
    """
    # Get project
    project = state.get_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    if project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: this project does not belong to you",
        )

    # Get characters and relationships from character memory
    characters, relationships = await _get_project_characters_and_relationships(
        state, project_id
    )

    # Transform to Cytoscape.js format
    nodes, edges = _transform_to_cytoscape(characters, relationships)

    return GraphResponse(nodes=nodes, edges=edges)


async def _get_project_characters_and_relationships(
    state: StudioState, project_id: str
) -> tuple[dict[str, dict], list[dict]]:
    """Get characters and relationships for a project.

    Args:
        state: StudioState instance
        project_id: Project ID

    Returns:
        Tuple of (characters dict, relationships list)
    """
    # Initialize character memory with project-specific namespace
    character_memory = CharacterMemory(
        base_path=state.data_dir,
        namespace=project_id,
        collection=f"character_memory_{project_id}",
    )

    # Get all characters from character memory
    characters: dict[str, dict] = {}

    # Get all character keys first
    char_keys = await character_memory.list_keys()

    # Then retrieve each character
    for char_id in char_keys:
        profile = await character_memory.retrieve_character(char_id)
        if profile:
            characters[char_id] = profile

    # Get relationships
    relationships: list[dict] = []
    for char_id in characters:
        rels = await character_memory.get_relationships(char_id)
        relationships.extend(rels)

    return characters, relationships


def _transform_to_cytoscape(
    characters: dict[str, dict], relationships: list[dict]
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Transform internal data to Cytoscape.js format.

    Args:
        characters: Dict of character_id -> character_profile
        relationships: List of relationship records

    Returns:
        Tuple of (nodes list, edges list) in Cytoscape.js format
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen_nodes: set[str] = set()

    # Add character nodes
    for char_id, profile in characters.items():
        if char_id not in seen_nodes:
            seen_nodes.add(char_id)
            nodes.append(
                GraphNode(
                    data={
                        "id": char_id,
                        "label": profile.get("name", char_id),
                        "type": "character",
                        "properties": {
                            "aliases": profile.get("aliases", []),
                            "tier": profile.get("tier", 1),
                            "bio": profile.get("bio", ""),
                            "status": profile.get("current_status", "unknown"),
                        },
                    }
                )
            )

    # Add relationship edges
    for rel in relationships:
        source = rel.get("character1_id") or rel.get("source")
        target = rel.get("character2_id") or rel.get("target")
        rel_type = rel.get("relationship_type") or rel.get("type", "KNOWS")

        if source and target and source != target:
            edges.append(
                GraphEdge(
                    data={
                        "source": source,
                        "target": target,
                        "relationship": rel_type,
                        "properties": {
                            "strength": rel.get("strength", 0.5),
                            "description": rel.get("description", ""),
                            "start_context": rel.get("start_context", ""),
                        },
                    }
                )
            )

    return nodes, edges
