#!/usr/bin/env python3
"""Test script for InventoryUpdater functionality."""

import asyncio
import logging

from src.novel.continuity import CharacterState, StoryState
from src.novel.inventory_updater import InventoryUpdater

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("src.novel.inventory_updater").setLevel(logging.DEBUG)


async def test_inventory_updater() -> None:
    """Test basic inventory updating with sample chapter content."""
    print("Testing InventoryUpdater...")

    # Create inventory updater with default components
    updater = InventoryUpdater()

    # Sample chapter content with characters, locations, items, and events
    chapter_content = """
    Sir Kael rode his horse Stormwind through the ancient Forest of Elders.
    He carried the legendary Sword of Dawn, a weapon of immense power.
    At the edge of the forest, he met Lady Elara, who was searching for her lost brother.
    Together they discovered a hidden cave that contained a mysterious glowing crystal.
    Suddenly, a dragon appeared from the sky, breathing fire!
    Kael raised his sword to defend Elara.
    """

    # Create a simple story state with existing characters
    character_state = CharacterState(
        name="Sir Kael",
        status="alive",
        location="Forest of Elders",
        physical_form="human",
        relationships={},
    )

    story_state = StoryState(
        chapter=1,
        location="Forest of Elders",
        active_characters=["Sir Kael"],
        character_states={"Sir Kael": character_state},
        plot_threads=[],
        key_events=[],
    )

    # Update inventory
    stats = await updater.update_inventory(
        chapter_content=chapter_content,
        chapter_number=2,
        story_state=story_state,
    )

    print(f"Update stats: {stats}")

    # Check knowledge graph
    kg = updater.knowledge_graph
    print(f"Knowledge graph nodes: {len(kg._nodes)}")
    for node_id, node in kg._nodes.items():
        print(f"  Node: {node_id} ({node.node_type}) - {node.properties.get('name', '')}")

    print(f"Knowledge graph edges: {len(kg._edges)}")
    for edge_id, edge in kg._edges.items():
        print(f"  Edge: {edge.source_id} -> {edge.target_id} ({edge.relationship_type})")

    # Check timeline
    timeline = updater.timeline_manager
    print(f"Timeline events: {len(timeline._events)}")
    for event_id, event in timeline._events.items():
        print(f"  Event: {event_id} - {event.description[:50]}...")

    # Check glossary (may be empty if glossary manager fails)
    try:
        glossary = updater.glossary_manager
        # We can't easily list terms without async, but we can try
        print("Glossary manager initialized.")
    except Exception as e:
        print(f"Glossary manager error (expected if no Milvus): {e}")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_inventory_updater())
