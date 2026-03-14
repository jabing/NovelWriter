"""Test data generators for QA testing.

This module provides utilities to generate test data for:
- Novels with multiple chapters
- Character profiles
- Plot outlines
- Knowledge graph data
"""

import random
import string
from datetime import datetime
from typing import Any

from src.novel_agent.novel.schemas import (
    ChapterWritingInput,
    Genre,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    Language,
    PlotGenerationInput,
    WorldbuildingInput,
)

# ============================================================================
# Novel Generators
# ============================================================================


def generate_test_novel(
    chapters: int = 10,
    genre: Genre = Genre.SCI_FI,
    title: str = "测试小说",
) -> dict[str, Any]:
    """Generate test novel data.

    Args:
        chapters: Number of chapters to generate
        genre: Novel genre
        title: Novel title

    Returns:
        Dictionary with complete novel data structure.
    """
    novel_id = f"test_novel_{''.join(random.choices(string.ascii_lowercase, k=6))}"

    characters = [
        generate_test_character(name="主角", role="protagonist", status="alive"),
        generate_test_character(name="配角A", role="supporting", status="alive"),
        generate_test_character(name="配角B", role="supporting", status="alive"),
    ]

    chapter_list = []
    for i in range(1, chapters + 1):
        chapter_list.append(
            {
                "number": i,
                "title": f"第{i}章",
                "summary": f"第{i}章的情节摘要",
                "key_characters": [c["id"] for c in characters[: random.randint(1, 3)]],
                "plot_points": [f"事件{i}_1", f"事件{i}_2"],
                "content": generate_test_chapter_content(i, characters),
            }
        )

    return {
        "novel_id": novel_id,
        "title": title,
        "genre": genre.value,
        "total_chapters": chapters,
        "characters": characters,
        "chapters": chapter_list,
        "world_context": {
            "setting": "测试世界",
            "technology_level": "modern",
        },
        "created_at": datetime.now().isoformat(),
    }


def generate_test_novel_with_inconsistencies(
    inconsistency_type: str = "dead_character",
) -> dict[str, Any]:
    """Generate test novel with intentional inconsistencies for QA testing.

    Args:
        inconsistency_type: Type of inconsistency to introduce
            - "dead_character": Deceased character appears in later chapters
            - "timeline": Timeline ordering issues
            - "location": Location continuity issues

    Returns:
        Dictionary with novel data containing intentional issues.
    """
    base_novel = generate_test_novel(chapters=20)

    if inconsistency_type == "dead_character":
        # Add a character who dies in chapter 10 but appears in chapter 15
        dead_char = generate_test_character(
            name="已故角色", role="supporting", status="deceased"
        )
        dead_char["death_chapter"] = 10
        base_novel["characters"].append(dead_char)

        # Add this character to a later chapter
        base_novel["chapters"][14]["key_characters"].append(dead_char["id"])
        base_novel["chapters"][14]["content"] += "\n\n已故角色突然出现了。"

    elif inconsistency_type == "timeline":
        # Create timeline inconsistency
        base_novel["chapters"][5]["timeline"] = {
            "day": 30,
            "month": 1,
        }
        base_novel["chapters"][6]["timeline"] = {
            "day": 15,
            "month": 1,
        }  # Earlier than chapter 5!

    elif inconsistency_type == "location":
        # Character in two places at once
        base_novel["characters"][0]["id"]
        base_novel["chapters"][3]["locations"] = ["北京", "上海"]

    return base_novel


# ============================================================================
# Character Generators
# ============================================================================


def generate_test_character(
    name: str | None = None,
    role: str = "supporting",
    status: str = "alive",
    genre: Genre = Genre.SCI_FI,
) -> dict[str, Any]:
    """Generate test character profile.

    Args:
        name: Character name (auto-generated if None)
        role: Character role (protagonist, supporting, antagonist)
        status: Character status (alive, deceased, missing)
        genre: Genre for archetype selection

    Returns:
        Dictionary with character profile data.
    """
    if name is None:
        name = f"测试角色_{''.join(random.choices(string.ascii_lowercase, k=4))}"

    char_id = f"char_{name}_{''.join(random.choices(string.digits, k=3))}"

    archetypes = {
        Genre.SCI_FI: ["科学家", "宇航员", "工程师", "探险家"],
        Genre.FANTASY: ["法师", "战士", "精灵", "矮人"],
        Genre.ROMANCE: ["总裁", "明星", "作家", "医生"],
        Genre.HISTORY: ["将军", "谋士", "公主", "商人"],
        Genre.MILITARY: ["指挥官", "狙击手", "飞行员", "特工"],
    }

    archetype = random.choice(archetypes.get(genre, ["普通人"]))

    traits_map = {
        "alive": ["勇敢", "聪明", "善良"],
        "deceased": ["睿智", "慈祥"],
        "missing": ["神秘", "不可捉摸"],
    }

    return {
        "id": char_id,
        "name": name,
        "role": role,
        "status": status,
        "archetype": archetype,
        "age": random.randint(18, 65),
        "personality": {
            "traits": traits_map.get(status, ["普通"]),
            "fears": [f"恐惧{i}" for i in range(random.randint(1, 3))],
            "goals": [f"目标{i}" for i in range(random.randint(1, 3))],
        },
        "background": f"{name}的背景故事",
        "first_appearance": 1,
        "relationships": [],
    }


def generate_character_cast(
    count: int = 5,
    genre: Genre = Genre.SCI_FI,
) -> list[dict[str, Any]]:
    """Generate a cast of characters with relationships.

    Args:
        count: Number of characters to generate
        genre: Genre for character archetypes

    Returns:
        List of character dictionaries with inter-character relationships.
    """
    characters = []

    # Generate protagonist
    characters.append(
        generate_test_character(name="主角", role="protagonist", genre=genre)
    )

    # Generate supporting characters
    for i in range(count - 1):
        role = "antagonist" if i == count - 2 else "supporting"
        characters.append(
            generate_test_character(
                name=f"配角{chr(65 + i)}", role=role, genre=genre
            )
        )

    # Add relationships
    for i, char in enumerate(characters):
        for j, other in enumerate(characters):
            if i != j:
                relationship_types = ["friend", "enemy", "family", "colleague"]
                char["relationships"].append(
                    {
                        "target_id": other["id"],
                        "type": random.choice(relationship_types),
                        "strength": random.uniform(0.1, 1.0),
                    }
                )

    return characters


# ============================================================================
# Chapter Content Generators
# ============================================================================


def generate_test_chapter_content(
    chapter_number: int,
    characters: list[dict[str, Any]],
    min_paragraphs: int = 3,
    max_paragraphs: int = 6,
) -> str:
    """Generate test chapter content.

    Args:
        chapter_number: Chapter number
        characters: List of characters to include
        min_paragraphs: Minimum number of paragraphs
        max_paragraphs: Maximum number of paragraphs

    Returns:
        Generated chapter content string.
    """
    num_paragraphs = random.randint(min_paragraphs, max_paragraphs)
    paragraphs = [f"第{chapter_number}章\n"]

    # Opening paragraph
    if characters:
        main_char = characters[0]
        paragraphs.append(f"{main_char['name']}站在窗前，思考着接下来的计划。")

    # Middle paragraphs
    for i in range(num_paragraphs - 2):
        if characters:
            char = random.choice(characters)
            actions = ["走动", "思考", "说话", "观察"]
            paragraphs.append(f"{char['name']}{random.choice(actions)}了一会儿。")
        else:
            paragraphs.append(f"这是第{i + 1}段内容。")

    # Closing paragraph
    paragraphs.append("这一天就这样结束了。")

    return "\n\n".join(paragraphs)


def generate_chapter_with_dialogue(
    chapter_number: int,
    characters: list[dict[str, Any]],
) -> str:
    """Generate chapter content with dialogue.

    Args:
        chapter_number: Chapter number
        characters: Characters to include in dialogue

    Returns:
        Chapter content with dialogue exchanges.
    """
    lines = [f"第{chapter_number}章\n"]

    for i, char in enumerate(characters[:2]):
        lines.append(f'{char["name"]}说："这是第{i + 1}句对话。"')

    return "\n\n".join(lines)


# ============================================================================
# Knowledge Graph Data Generators
# ============================================================================


def generate_test_kg_node(
    node_type: str = "character",
    name: str | None = None,
) -> KnowledgeGraphNode:
    """Generate test knowledge graph node.

    Args:
        node_type: Type of node (character, location, concept, event)
        name: Node name (auto-generated if None)

    Returns:
        KnowledgeGraphNode instance.
    """
    if name is None:
        name = f"测试{node_type}_{random.randint(1000, 9999)}"

    node_id = f"kg_{node_type}_{random.randint(1000, 9999)}"

    properties = {"name": name}

    if node_type == "character":
        properties.update(
            {
                "status": random.choice(["alive", "deceased"]),
                "role": random.choice(["protagonist", "supporting", "antagonist"]),
            }
        )
    elif node_type == "location":
        properties.update(
            {
                "type": random.choice(["city", "building", "region"]),
                "country": "测试国",
            }
        )

    return KnowledgeGraphNode(
        node_id=node_id,
        node_type=node_type,
        properties=properties,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def generate_test_kg_edge(
    source_id: str,
    target_id: str,
    relationship_type: str = "related_to",
) -> KnowledgeGraphEdge:
    """Generate test knowledge graph edge.

    Args:
        source_id: Source node ID
        target_id: Target node ID
        relationship_type: Type of relationship

    Returns:
        KnowledgeGraphEdge instance.
    """
    edge_id = f"kg_edge_{random.randint(10000, 99999)}"

    return KnowledgeGraphEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        relationship_type=relationship_type,
        weight=random.uniform(0.5, 1.0),
        properties={},
        created_at=datetime.now(),
    )


def generate_test_knowledge_graph(
    num_characters: int = 3,
    num_locations: int = 2,
    num_events: int = 2,
) -> dict[str, Any]:
    """Generate complete test knowledge graph.

    Args:
        num_characters: Number of character nodes
        num_locations: Number of location nodes
        num_events: Number of event nodes

    Returns:
        Dictionary with nodes and edges for a complete graph.
    """
    nodes = []
    edges = []

    # Generate character nodes
    character_nodes = [
        generate_test_kg_node("character") for _ in range(num_characters)
    ]
    nodes.extend(character_nodes)

    # Generate location nodes
    location_nodes = [generate_test_kg_node("location") for _ in range(num_locations)]
    nodes.extend(location_nodes)

    # Generate event nodes
    event_nodes = [generate_test_kg_node("event") for _ in range(num_events)]
    nodes.extend(event_nodes)

    # Generate edges between characters
    relationship_types = ["friend", "enemy", "family", "colleague"]
    for i, char in enumerate(character_nodes):
        for j, other in enumerate(character_nodes):
            if i < j:
                edges.append(
                    generate_test_kg_edge(
                        char.node_id,
                        other.node_id,
                        random.choice(relationship_types),
                    )
                )

    # Generate edges from characters to locations
    for char in character_nodes:
        for loc in location_nodes:
            edges.append(
                generate_test_kg_edge(
                    char.node_id,
                    loc.node_id,
                    random.choice(["lives_at", "works_at", "visits"]),
                )
            )

    # Generate edges from characters to events
    for char in character_nodes:
        for event in event_nodes:
            edges.append(
                generate_test_kg_edge(
                    char.node_id,
                    event.node_id,
                    random.choice(["participates_in", "witnesses", "causes"]),
                )
            )

    return {
        "nodes": nodes,
        "edges": edges,
    }


# ============================================================================
# Schema Input Generators
# ============================================================================


def generate_chapter_writing_input(
    chapter_number: int = 1,
    genre: Genre = Genre.SCI_FI,
    language: Language = Language.CHINESE,
) -> ChapterWritingInput:
    """Generate ChapterWritingInput for testing.

    Args:
        chapter_number: Chapter number
        genre: Novel genre
        language: Content language

    Returns:
        ChapterWritingInput instance.
    """
    characters = generate_character_cast(count=2, genre=genre)

    return ChapterWritingInput(
        novel_id=f"test_novel_{random.randint(1000, 9999)}",
        genre=genre,
        chapter_number=chapter_number,
        chapter_outline=f"第{chapter_number}章的情节大纲",
        characters=characters,
        world_context={
            "setting": "测试世界",
            "technology_level": "modern",
        },
        language=language,
    )


def generate_plot_generation_input(
    genre: Genre = Genre.SCI_FI,
    chapter_count: int = 30,
) -> PlotGenerationInput:
    """Generate PlotGenerationInput for testing.

    Args:
        genre: Novel genre
        chapter_count: Total chapter count

    Returns:
        PlotGenerationInput instance.
    """
    characters = generate_character_cast(count=3, genre=genre)

    return PlotGenerationInput(
        novel_id=f"test_novel_{random.randint(1000, 9999)}",
        genre=genre,
        chapter_count=chapter_count,
        characters=[{"id": c["id"], "name": c["name"], "role": c["role"]} for c in characters],
        story_structure="three_act",
    )


def generate_worldbuilding_input(
    genre: Genre = Genre.SCI_FI,
    scale: str = "planet",
) -> WorldbuildingInput:
    """Generate WorldbuildingInput for testing.

    Args:
        genre: Novel genre
        scale: World scale

    Returns:
        WorldbuildingInput instance.
    """
    return WorldbuildingInput(
        novel_id=f"test_novel_{random.randint(1000, 9999)}",
        genre=genre,
        scale=scale,
        magic_system=genre == Genre.FANTASY,
        technology_level="futuristic" if genre == Genre.SCI_FI else "modern",
    )


# ============================================================================
# Utility Functions
# ============================================================================


def random_chinese_text(min_length: int = 10, max_length: int = 50) -> str:
    """Generate random Chinese text for testing.

    Args:
        min_length: Minimum character count
        max_length: Maximum character count

    Returns:
        Random Chinese text string.
    """
    length = random.randint(min_length, max_length)
    # Use common Chinese characters
    chars = "的是不在有个为这上着能和就出也你要以他会大来说可以要她多得地"
    return "".join(random.choices(chars, k=length))
