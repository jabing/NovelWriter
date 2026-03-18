"""Tests for EntityExtractor role_id integration with CharacterRegistry.

Tests cover:
- Character extraction with registry returns role_id
- Character extraction without registry has no role_id
- Same name characters get different role_ids
- Performance impact when registry is disabled
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.novel_agent.novel.character_registry import CharacterRegistry
from src.novel_agent.novel.entity_extractor import (
    CharacterEntity,
    EntityExtractor,
    ExtractionStrategy,
    RuleBasedExtractor,
)
from src.novel_agent.novel.knowledge_graph import KnowledgeGraph


@pytest.fixture
def registry() -> CharacterRegistry:
    """Create a fresh CharacterRegistry for testing."""
    return CharacterRegistry()


@pytest.fixture
def knowledge_graph(tmp_path: Path) -> KnowledgeGraph:
    """Create a temporary knowledge graph."""
    storage_path = tmp_path / "kg"
    return KnowledgeGraph("test_graph", storage_path)


@pytest.fixture
def extractor_with_registry(
    knowledge_graph: KnowledgeGraph, registry: CharacterRegistry
) -> EntityExtractor:
    """Create EntityExtractor with CharacterRegistry enabled."""
    knowledge_graph.add_node(
        node_id="char_lx",
        node_type="character",
        properties={"name": "林晓", "aliases": []},
    )
    knowledge_graph.add_node(
        node_id="char_zs",
        node_type="character",
        properties={"name": "张三", "aliases": []},
    )
    return EntityExtractor(
        knowledge_graph=knowledge_graph,
        registry=registry,
        strategy=ExtractionStrategy.RULE_BASED,
    )


@pytest.fixture
def extractor_without_registry(knowledge_graph: KnowledgeGraph) -> EntityExtractor:
    """Create EntityExtractor without CharacterRegistry."""
    knowledge_graph.add_node(
        node_id="char_lx",
        node_type="character",
        properties={"name": "林晓", "aliases": []},
    )
    return EntityExtractor(
        knowledge_graph=knowledge_graph,
        strategy=ExtractionStrategy.RULE_BASED,
    )


@pytest.fixture
def rule_extractor_with_registry(registry: CharacterRegistry) -> RuleBasedExtractor:
    """Create RuleBasedExtractor with registry."""
    known_chars = {"林晓": "char_lx", "张三": "char_zs"}
    return RuleBasedExtractor(known_characters=known_chars, registry=registry)


@pytest.fixture
def rule_extractor_without_registry() -> RuleBasedExtractor:
    """Create RuleBasedExtractor without registry."""
    known_chars = {"林晓": "char_lx"}
    return RuleBasedExtractor(known_characters=known_chars)


class TestRuleBasedExtractorWithRegistry:
    """Tests for RuleBasedExtractor with CharacterRegistry."""

    def test_extract_with_registry_returns_role_id(
        self, rule_extractor_with_registry: RuleBasedExtractor
    ) -> None:
        """Extracted characters have role_id when registry is enabled."""
        content = "林晓走进了房间。张三向他挥手。"
        chars = rule_extractor_with_registry.extract_characters(content, chapter_num=1)

        assert len(chars) == 2
        for char in chars:
            assert isinstance(char, CharacterEntity)
            assert char.role_id is not None
            assert char.role_id.startswith("char_")

    def test_extract_without_registry_no_role_id(
        self, rule_extractor_without_registry: RuleBasedExtractor
    ) -> None:
        """Extracted characters have no role_id when registry is disabled."""
        content = "林晓走进了房间。"
        chars = rule_extractor_without_registry.extract_characters(content, chapter_num=1)

        assert len(chars) == 1
        assert chars[0].role_id is None

    def test_same_name_different_role_ids(self, registry: CharacterRegistry) -> None:
        """Characters with same name should get different role_ids."""
        id1 = registry.register("林晓", chapter=1)
        id2 = registry.register("林晓", chapter=5)

        assert id1 != id2
        assert id1 == "char_林晓_001"
        assert id2 == "char_林晓_002"

    def test_get_or_create_returns_existing(self, registry: CharacterRegistry) -> None:
        """get_or_create returns existing ID when only one exists."""
        id1 = registry.register("林晓", chapter=1)
        id2 = registry.get_or_create("林晓", chapter=5)

        assert id1 == id2

    def test_role_id_in_properties(self, rule_extractor_with_registry: RuleBasedExtractor) -> None:
        """role_id is included in entity properties for KG storage."""
        content = "林晓出现了。"
        chars = rule_extractor_with_registry.extract_characters(content, chapter_num=1)

        assert len(chars) == 1
        assert "role_id" in chars[0].properties
        assert chars[0].properties["role_id"] == chars[0].role_id


class TestEntityExtractorWithRegistry:
    """Tests for EntityExtractor with CharacterRegistry."""

    @pytest.mark.asyncio
    async def test_extract_characters_with_registry(
        self, extractor_with_registry: EntityExtractor
    ) -> None:
        """EntityExtractor.extract_characters populates role_id with registry."""
        content = "林晓和张三在北京见面。"
        chars = extractor_with_registry.extract_characters(content)

        assert len(chars) == 2
        for char in chars:
            assert char.role_id is not None
            assert char.role_id.startswith("char_")

    @pytest.mark.asyncio
    async def test_extract_characters_without_registry(
        self, extractor_without_registry: EntityExtractor
    ) -> None:
        """EntityExtractor.extract_characters has no role_id without registry."""
        content = "林晓出现了。"
        chars = extractor_without_registry.extract_characters(content)

        assert len(chars) == 1
        assert chars[0].role_id is None

    @pytest.mark.asyncio
    async def test_extract_from_chapter_with_registry(
        self, extractor_with_registry: EntityExtractor
    ) -> None:
        """Full chapter extraction populates role_id."""
        content = "林晓来到了北京，遇到了张三。"
        result = await extractor_with_registry.extract_from_chapter(chapter_num=1, content=content)

        chars = result.get_entities_by_type(result.entities[0].type if result.entities else None)
        char_entities = [e for e in result.entities if isinstance(e, CharacterEntity)]

        for char in char_entities:
            assert char.role_id is not None

    @pytest.mark.asyncio
    async def test_registry_persists_across_extractions(
        self,
        knowledge_graph: KnowledgeGraph,
        registry: CharacterRegistry,
    ) -> None:
        """Registry maintains state across multiple extractions."""
        knowledge_graph.add_node(
            node_id="char_lx",
            node_type="character",
            properties={"name": "林晓", "aliases": []},
        )

        extractor = EntityExtractor(
            knowledge_graph=knowledge_graph,
            registry=registry,
            strategy=ExtractionStrategy.RULE_BASED,
        )

        content1 = "林晓出现了。"
        chars1 = extractor.extract_characters(content1)
        assert len(chars1) == 1
        first_role_id = chars1[0].role_id

        content2 = "林晓再次出现。"
        chars2 = extractor.extract_characters(content2)
        assert len(chars2) == 1
        assert chars2[0].role_id == first_role_id

    @pytest.mark.asyncio
    async def test_knowledge_graph_stores_role_id(
        self,
        knowledge_graph: KnowledgeGraph,
        registry: CharacterRegistry,
    ) -> None:
        """role_id is stored in knowledge graph."""
        knowledge_graph.add_node(
            node_id="char_lx",
            node_type="character",
            properties={"name": "林晓", "aliases": []},
        )

        extractor = EntityExtractor(
            knowledge_graph=knowledge_graph,
            registry=registry,
            strategy=ExtractionStrategy.RULE_BASED,
        )

        content = "林晓来到了神秘的城堡。"
        await extractor.extract_from_chapter(chapter_num=1, content=content)

        node = knowledge_graph.get_node("char_lx")
        assert node is not None
        assert "role_id" in node.properties
        assert node.properties["role_id"].startswith("char_")


class TestPerformanceWithRegistry:
    """Tests for performance impact of registry."""

    def test_no_performance_impact_when_disabled(
        self, rule_extractor_without_registry: RuleBasedExtractor
    ) -> None:
        """Ensure no significant performance impact when registry is disabled."""
        import time

        content = "林晓" * 1000

        start = time.time()
        chars = rule_extractor_without_registry.extract_characters(content, chapter_num=1)
        elapsed = time.time() - start

        assert len(chars) == 1
        assert elapsed < 1.0

    def test_performance_with_registry_enabled(
        self, rule_extractor_with_registry: RuleBasedExtractor
    ) -> None:
        """Registry operations should be fast."""
        import time

        content = "林晓和张三" * 100

        start = time.time()
        chars = rule_extractor_with_registry.extract_characters(content, chapter_num=1)
        elapsed = time.time() - start

        assert len(chars) == 2
        assert elapsed < 1.0


class TestBackwardCompatibility:
    """Tests for backward compatibility without registry."""

    @pytest.mark.asyncio
    async def test_existing_tests_still_work(self, knowledge_graph: KnowledgeGraph) -> None:
        """Ensure existing functionality works without registry."""
        knowledge_graph.add_node(
            node_id="char_zs",
            node_type="character",
            properties={"name": "张三", "aliases": []},
        )

        extractor = EntityExtractor(
            knowledge_graph=knowledge_graph,
            strategy=ExtractionStrategy.RULE_BASED,
        )

        content = "张三来到了北京。"
        result = await extractor.extract_from_chapter(chapter_num=1, content=content)

        assert result.entity_count >= 1
        assert result.chapter == 1

    def test_character_entity_creation_backward_compatible(self) -> None:
        """CharacterEntity creation works without role_id."""
        char = CharacterEntity(
            id="char_1",
            name="张三",
            gender="男",
            age=25,
            role="protagonist",
        )

        assert char.id == "char_1"
        assert char.name == "张三"
        assert char.role_id is None

    def test_character_entity_with_role_id(self) -> None:
        """CharacterEntity can be created with role_id."""
        char = CharacterEntity(
            id="char_1",
            name="林晓",
            role_id="char_林晓_001",
        )

        assert char.role_id == "char_林晓_001"
