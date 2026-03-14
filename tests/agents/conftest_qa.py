"""QA-specific pytest fixtures for testing the QA system.

This module provides shared fixtures for QA testing including:
- Mock database clients (Neo4j, PostgreSQL, Pinecone)
- Sample data fixtures
- Test configuration
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.novel.schemas import (
    ChapterWritingInput,
    CharacterCreationInput,
    Genre,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    Language,
    PlotGenerationInput,
)

# ============================================================================
# Mock Database Clients
# ============================================================================


@pytest.fixture
async def neo4j_client() -> Generator[MagicMock, None, None]:
    """Provide mock Neo4j client for tests.

    Yields:
        Mock Neo4j client with async connect/close methods.
    """
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.execute_query = AsyncMock(return_value=[])
    client.run = AsyncMock(return_value=[])

    await client.connect()
    yield client
    await client.close()


@pytest.fixture
async def postgres_session() -> Generator[MagicMock, None, None]:
    """Provide mock PostgreSQL session for tests.

    Yields:
        Mock PostgreSQL session with async context manager support.
    """
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()

    yield session
    await session.close()


@pytest.fixture
async def pinecone_client() -> Generator[MagicMock, None, None]:
    """Provide mock Pinecone client for tests.

    Yields:
        Mock Pinecone client with vector operations.
    """
    client = MagicMock()
    client.upsert = AsyncMock(return_value={"upserted_count": 1})
    client.query = AsyncMock(return_value={"matches": []})
    client.delete = AsyncMock(return_value=True)
    client.fetch = AsyncMock(return_value={"vectors": {}})

    yield client


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_character_profile() -> dict[str, Any]:
    """Provide sample character data for testing.

    Returns:
        Dictionary with character profile data.
    """
    return {
        "id": "char_test_001",
        "name": "测试角色",
        "role": "protagonist",
        "status": "alive",
        "age": 28,
        "occupation": "科学家",
        "personality": {
            "traits": ["聪明", "好奇", "坚毅"],
            "fears": ["失败", "孤独"],
            "goals": ["解开宇宙奥秘", "保护家人"],
        },
        "background": "来自普通家庭的科研天才",
        "first_appearance": 1,
        "relationships": [],
    }


@pytest.fixture
def sample_character_deceased() -> dict[str, Any]:
    """Provide sample deceased character for continuity testing.

    Returns:
        Dictionary with deceased character data.
    """
    return {
        "id": "char_test_002",
        "name": "已故导师",
        "role": "mentor",
        "status": "deceased",
        "age": 65,
        "occupation": "教授",
        "personality": {"traits": ["睿智", "慈祥"]},
        "death_chapter": 15,
        "death_cause": "疾病",
    }


@pytest.fixture
def sample_chapter_content() -> str:
    """Provide sample chapter text for testing.

    Returns:
        Sample chapter content with characters and plot elements.
    """
    return """第1章 开端

    测试角色站在实验室的窗前，望着远处的星空。她的导师已故导师曾经在这里工作过，那张旧书桌还在原地。

    "这份数据不对，"她喃喃自语，"信号不应该出现在这个频段。"

    她的手指在键盘上飞快地敲击，屏幕上跳动的数字似乎在嘲笑她的困惑。作为一个来自普通家庭的科研天才，她从不轻易放弃。

    夜深了，实验室里只剩下她一个人。她想起导师临终前说的话："真相往往隐藏在最意想不到的地方。"
    """


@pytest.fixture
def sample_chapter_with_inconsistency() -> str:
    """Provide chapter with intentional inconsistency for QA testing.

    Returns:
        Chapter content with a character who should be deceased.
    """
    return """第20章 意外重逢

    测试角色走进咖啡厅，看到了一个熟悉的身影。

    "已故导师？"她惊讶地喊道，"你不是在第15章就去世了吗？"

    已故导师微笑着走向她："那是个误会，我只是假死。"

    这显然是个情节矛盾点——已故导师的状态应该是"deceased"。
    """


@pytest.fixture
def sample_plot_outline() -> dict[str, Any]:
    """Provide sample plot outline for testing.

    Returns:
        Dictionary with plot outline structure.
    """
    return {
        "novel_id": "test_novel_001",
        "title": "测试小说",
        "genre": "scifi",
        "total_chapters": 30,
        "chapters": [
            {
                "number": 1,
                "title": "开端",
                "summary": "主角发现异常信号",
                "key_characters": ["char_test_001"],
                "plot_points": ["发现异常", "决定调查"],
            },
            {
                "number": 2,
                "title": "调查",
                "summary": "深入研究信号来源",
                "key_characters": ["char_test_001", "char_test_002"],
                "plot_points": ["导师提供线索", "获取关键数据"],
            },
        ],
    }


@pytest.fixture
def sample_world_context() -> dict[str, Any]:
    """Provide sample world context for testing.

    Returns:
        Dictionary with worldbuilding context.
    """
    return {
        "setting": "现代地球，近未来科技",
        "time_period": "2035年",
        "technology_level": "near_future",
        "major_locations": [
            {"name": "SETI研究所", "type": "research_facility"},
            {"name": "加州", "type": "region"},
        ],
        "social_structure": "现代社会",
        "magic_system": None,
        "special_rules": ["基于现实物理学", "无超自然元素"],
    }


# ============================================================================
# Knowledge Graph Fixtures
# ============================================================================


@pytest.fixture
def sample_kg_node_character() -> KnowledgeGraphNode:
    """Provide sample character node for knowledge graph testing.

    Returns:
        KnowledgeGraphNode representing a character.
    """
    from datetime import datetime

    return KnowledgeGraphNode(
        node_id="kg_char_001",
        node_type="character",
        properties={
            "name": "测试角色",
            "status": "alive",
            "role": "protagonist",
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_kg_node_location() -> KnowledgeGraphNode:
    """Provide sample location node for knowledge graph testing.

    Returns:
        KnowledgeGraphNode representing a location.
    """
    from datetime import datetime

    return KnowledgeGraphNode(
        node_id="kg_loc_001",
        node_type="location",
        properties={
            "name": "SETI研究所",
            "type": "research_facility",
            "country": "美国",
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_kg_edge() -> KnowledgeGraphEdge:
    """Provide sample edge for knowledge graph testing.

    Returns:
        KnowledgeGraphEdge representing a relationship.
    """
    from datetime import datetime

    return KnowledgeGraphEdge(
        edge_id="kg_edge_001",
        source_id="kg_char_001",
        target_id="kg_loc_001",
        relationship_type="works_at",
        weight=1.0,
        properties={"since": "2020"},
        created_at=datetime.now(),
    )


# ============================================================================
# Schema Input Fixtures
# ============================================================================


@pytest.fixture
def sample_chapter_writing_input() -> ChapterWritingInput:
    """Provide sample chapter writing input for testing.

    Returns:
        ChapterWritingInput instance.
    """
    return ChapterWritingInput(
        novel_id="test_novel_001",
        genre=Genre.SCI_FI,
        chapter_number=1,
        chapter_outline="测试角色在实验室发现异常信号",
        characters=[
            {
                "id": "char_test_001",
                "name": "测试角色",
                "role": "protagonist",
                "status": "alive",
            }
        ],
        world_context={
            "setting": "SETI研究所",
            "technology_level": "near_future",
        },
        language=Language.CHINESE,
    )


@pytest.fixture
def sample_character_creation_input() -> CharacterCreationInput:
    """Provide sample character creation input for testing.

    Returns:
        CharacterCreationInput instance.
    """
    return CharacterCreationInput(
        novel_id="test_novel_001",
        genre=Genre.SCI_FI,
        count=1,
        main_character=True,
        archetype="科学家",
    )


@pytest.fixture
def sample_plot_generation_input() -> PlotGenerationInput:
    """Provide sample plot generation input for testing.

    Returns:
        PlotGenerationInput instance.
    """
    return PlotGenerationInput(
        novel_id="test_novel_001",
        genre=Genre.SCI_FI,
        chapter_count=30,
        characters=[
            {
                "id": "char_test_001",
                "name": "测试角色",
                "role": "protagonist",
            }
        ],
        story_structure="three_act",
    )


# ============================================================================
# QA Validation Result Fixtures
# ============================================================================


@pytest.fixture
def sample_qa_result_valid() -> dict[str, Any]:
    """Provide sample valid QA result.

    Returns:
        Dictionary representing a valid QA check result.
    """
    return {
        "valid": True,
        "issues": [],
        "warnings": [],
        "score": 1.0,
        "details": {"checks_passed": ["character_status", "timeline", "location"]},
    }


@pytest.fixture
def sample_qa_result_invalid() -> dict[str, Any]:
    """Provide sample invalid QA result with issues.

    Returns:
        Dictionary representing an invalid QA check result.
    """
    return {
        "valid": False,
        "issues": [
            {
                "type": "character_status_mismatch",
                "severity": "error",
                "message": "角色'已故导师'状态为'deceased'，但在第20章中出现",
                "chapter": 20,
                "character_id": "char_test_002",
            }
        ],
        "warnings": [
            {
                "type": "minor_inconsistency",
                "severity": "warning",
                "message": "角色服装描述与前文略有不同",
                "chapter": 20,
            }
        ],
        "score": 0.6,
        "details": {
            "checks_passed": ["timeline", "location"],
            "checks_failed": ["character_status"],
        },
    }
