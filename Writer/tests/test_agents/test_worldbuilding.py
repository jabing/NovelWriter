# tests/test_agents/test_worldbuilding.py
"""Tests for Worldbuilding Agent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.worldbuilding import WorldbuildingAgent


class TestWorldbuildingAgent:
    """Tests for Worldbuilding Agent."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM."""
        llm = MagicMock()
        llm.generate_with_system = AsyncMock()
        return llm

    @pytest.fixture
    def agent(self, mock_llm: MagicMock) -> WorldbuildingAgent:
        """Create Worldbuilding Agent with mock LLM."""
        return WorldbuildingAgent(name="Test Worldbuilding Agent", llm=mock_llm)

    def test_initialization(self, agent: WorldbuildingAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "Test Worldbuilding Agent"
        assert "scifi" in agent.WORLD_ELEMENTS
        assert "fantasy" in agent.WORLD_ELEMENTS

    def test_world_elements_by_genre(self, agent: WorldbuildingAgent) -> None:
        """Test world elements are defined for each genre."""
        for genre in ["scifi", "fantasy", "romance", "history", "military"]:
            assert genre in agent.WORLD_ELEMENTS
            assert len(agent.WORLD_ELEMENTS[genre]) > 0

    @pytest.mark.asyncio
    async def test_execute_basic(self, agent: WorldbuildingAgent, mock_llm: MagicMock) -> None:
        """Test basic execution."""
        # Mock responses for worldbuilding components
        mock_llm.generate_with_system.side_effect = [
            # Rules
            MagicMock(content='{"name": "Test World", "core_rules": []}'),
            # Locations
            MagicMock(content='[{"id": "loc_001", "name": "Test City"}]'),
            # Society
            MagicMock(content='{"government": {"type": "monarchy"}}'),
            # History
            MagicMock(content='{"ancient_history": "Long ago..."}'),
        ]

        result = await agent.execute({
            "genre": "fantasy",
            "outline": {"main_arc": {"title": "Test"}},
        })

        assert result.success is True
        assert "world" in result.data
        assert result.data["world"]["genre"] == "fantasy"
        assert "rules" in result.data["world"]
        assert "locations" in result.data["world"]

    @pytest.mark.asyncio
    async def test_create_world_rules(self, agent: WorldbuildingAgent, mock_llm: MagicMock) -> None:
        """Test world rules creation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='{"name": "Magic World", "technology_level": "medieval"}'
        )

        rules = await agent.create_world_rules("fantasy", {})

        assert rules["name"] == "Magic World"

    @pytest.mark.asyncio
    async def test_generate_locations(self, agent: WorldbuildingAgent, mock_llm: MagicMock) -> None:
        """Test location generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='[{"id": "loc_001", "name": "Castle", "type": "fortress"}]'
        )

        locations = await agent.generate_locations("fantasy", {})

        assert len(locations) == 1
        assert locations[0]["name"] == "Castle"

    @pytest.mark.asyncio
    async def test_generate_society(self, agent: WorldbuildingAgent, mock_llm: MagicMock) -> None:
        """Test society generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='{"government": {"type": "democracy"}}'
        )

        society = await agent.generate_society("scifi", {})

        assert society["government"]["type"] == "democracy"

    @pytest.mark.asyncio
    async def test_generate_history(self, agent: WorldbuildingAgent, mock_llm: MagicMock) -> None:
        """Test history generation."""
        mock_llm.generate_with_system.return_value = MagicMock(
            content='{"ancient_history": "The world began..."}'
        )

        history = await agent.generate_history("fantasy", {})

        assert "ancient_history" in history


class TestWorldbuildingAgentErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def agent(self) -> WorldbuildingAgent:
        """Create agent with mock LLM that returns invalid JSON."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="invalid json"))
        return WorldbuildingAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_handles_invalid_json_in_rules(self, agent: WorldbuildingAgent) -> None:
        """Test that invalid JSON in rules is handled."""
        rules = await agent.create_world_rules("fantasy", {})

        # Should return a fallback structure
        assert "name" in rules

    @pytest.mark.asyncio
    async def test_handles_invalid_json_in_locations(self, agent: WorldbuildingAgent) -> None:
        """Test that invalid JSON in locations is handled."""
        locations = await agent.generate_locations("fantasy", {})

        # Should return empty list
        assert locations == []
