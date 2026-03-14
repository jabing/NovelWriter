# tests/test_agents/test_character.py
"""Tests for Character Agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.agents.character import CharacterAgent


class TestCharacterAgent:
    """Tests for Character Agent."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def agent(self, mock_llm: MagicMock) -> CharacterAgent:
        """Create Character Agent with mock LLM."""
        return CharacterAgent(name="Test Character Agent", llm=mock_llm)

    def test_initialization(self, agent: CharacterAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "Test Character Agent"
        assert "scifi" in agent.ARCHETYPES
        assert "fantasy" in agent.ARCHETYPES

    def test_archetypes_by_genre(self, agent: CharacterAgent) -> None:
        """Test archetypes are defined for each genre."""
        for genre in ["scifi", "fantasy", "romance", "history", "military"]:
            assert genre in agent.ARCHETYPES
            assert len(agent.ARCHETYPES[genre]) > 0

    @pytest.mark.asyncio
    async def test_execute_basic(self, agent: CharacterAgent, mock_llm: MagicMock) -> None:
        """Test basic execution."""
        # Mock responses for character creation and relationships
        mock_llm.generate_with_system.side_effect = [
            # Main characters (3)
            MagicMock(content='{"id": "char_001", "name": "Alice", "role": "protagonist"}'),
            MagicMock(content='{"id": "char_002", "name": "Bob", "role": "antagonist"}'),
            MagicMock(content='{"id": "char_003", "name": "Carol", "role": "main"}'),
            # Supporting characters (2 for this test)
            MagicMock(content='{"id": "char_004", "name": "Dave", "role": "supporting"}'),
            MagicMock(content='{"id": "char_005", "name": "Eve", "role": "supporting"}'),
            # Relationships
            MagicMock(content='[]'),
        ]

        result = await agent.execute({
            "genre": "fantasy",
            "outline": {"main_arc": {"title": "Test"}},
            "num_main_characters": 3,
            "num_supporting": 2,
        })

        assert result.success is True
        assert "characters" in result.data
        assert len(result.data["characters"]) == 5
        assert len(result.data["main_characters"]) == 3
        assert len(result.data["supporting_characters"]) == 2

    @pytest.mark.asyncio
    async def test_create_character(self, agent: CharacterAgent, mock_llm: MagicMock) -> None:
        """Test single character creation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='{"id": "char_test", "name": "Test Hero", "role": "protagonist", "age": 25}'
        )

        char = await agent.create_character("protagonist", "fantasy", {})

        assert char["name"] == "Test Hero"
        assert char["role"] == "protagonist"

    @pytest.mark.asyncio
    async def test_create_character_with_markdown(
        self, agent: CharacterAgent, mock_llm: MagicMock
    ) -> None:
        """Test character creation with markdown-wrapped JSON."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='```json\n{"name": "Hero", "role": "protagonist"}\n```'
        )

        char = await agent.create_character("protagonist", "fantasy", {})

        assert char["name"] == "Hero"

    @pytest.mark.asyncio
    async def test_generate_relationships(self, agent: CharacterAgent, mock_llm: MagicMock) -> None:
        """Test relationship generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='[{"character1": "Alice", "character2": "Bob", "relationship_type": "rivals"}]'
        )

        characters = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]

        relationships = await agent.generate_relationships(characters)

        assert len(relationships) == 1
        assert relationships[0]["relationship_type"] == "rivals"

    @pytest.mark.asyncio
    async def test_generate_relationships_single_char(
        self, agent: CharacterAgent, mock_llm: MagicMock
    ) -> None:
        """Test relationship generation with single character."""
        relationships = await agent.generate_relationships([{"name": "Solo"}])

        assert relationships == []


class TestCharacterAgentErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def agent(self) -> CharacterAgent:
        """Create agent with mock LLM that returns invalid JSON."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="invalid json"))
        return CharacterAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, agent: CharacterAgent) -> None:
        """Test that invalid JSON is handled gracefully."""
        char = await agent.create_character("protagonist", "fantasy", {})

        # Should return a fallback structure
        assert "id" in char
        assert "role" in char
