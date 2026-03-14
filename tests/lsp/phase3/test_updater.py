"""
Tests for NovelWriter LSP Updater Agent.

This module tests the UpdaterAgent class defined in novelwriter_lsp.agents.updater.
"""

import pytest
from novelwriter_lsp.agents import UpdaterAgent, AgentResult


class TestUpdaterAgent:
    """Tests for UpdaterAgent class."""

    def test_updater_agent_initialization(self):
        """Test creating an UpdaterAgent instance."""
        agent = UpdaterAgent()
        assert agent.name == "UpdaterAgent"
        assert agent.state == "idle"
        assert agent.execution_count == 0

    @pytest.mark.asyncio
    async def test_extract_events(self):
        """Test extracting events from content."""
        agent = UpdaterAgent()
        content = """
# Novel: Test

@Event: Party { time: "2024-01-01", location: "The Park", participants: "Alice, Bob" }
@Event: Meeting { time: "2024-01-02", location: "Office" }
        """
        result = await agent.extract_and_update("test.md", content)
        assert result.success is True
        events = result.data["new_events"]
        assert len(events) == 2
        assert events[0]["name"] == "Party"
        assert events[0]["time"] == "2024-01-01"
        assert events[0]["location"] == "The Park"
        assert events[0]["participants"] == "Alice, Bob"
        assert events[1]["name"] == "Meeting"
        assert events[1]["location"] == "Office"

    @pytest.mark.asyncio
    async def test_extract_character_updates(self):
        """Test extracting character updates from content."""
        agent = UpdaterAgent()
        content = """
@Character: Alice { status: "alive", age: "30", mood: "happy" }
@Character: Bob { status: "dead", age: "35" }
        """
        result = await agent.extract_and_update("test.md", content)
        assert result.success is True
        updates = result.data["character_updates"]
        assert len(updates) == 2
        assert updates[0]["character"] == "Alice"
        assert updates[0]["status"] == "alive"
        assert updates[0]["age"] == "30"
        assert updates[0]["mood"] == "happy"
        assert updates[1]["character"] == "Bob"
        assert updates[1]["status"] == "dead"

    @pytest.mark.asyncio
    async def test_extract_relationships(self):
        """Test extracting relationships from content."""
        agent = UpdaterAgent()
        content = """
@Relationship: Alice & Bob { type: "friends", since: "2020" }
@Relationship: Charlie & Dave { type: "enemies" }
        """
        result = await agent.extract_and_update("test.md", content)
        assert result.success is True
        relations = result.data["relationship_changes"]
        assert len(relations) == 2
        assert relations[0]["character1"] == "Alice"
        assert relations[0]["character2"] == "Bob"
        assert relations[0]["type"] == "friends"
        assert relations[0]["since"] == "2020"
        assert relations[1]["character1"] == "Charlie"
        assert relations[1]["character2"] == "Dave"
        assert relations[1]["type"] == "enemies"

    @pytest.mark.asyncio
    async def test_extract_empty_content(self):
        """Test extracting from empty content."""
        agent = UpdaterAgent()
        content = ""
        result = await agent.extract_and_update("test.md", content)
        assert result.success is True
        assert len(result.data["new_events"]) == 0
        assert len(result.data["character_updates"]) == 0
        assert len(result.data["relationship_changes"]) == 0

    @pytest.mark.asyncio
    async def test_execute_method(self):
        """Test the execute method (entry point)."""
        agent = UpdaterAgent()
        input_data = {"uri": "test.md", "content": "@Event: Test { }"}
        result = await agent.execute(input_data)
        assert isinstance(result, AgentResult)
        assert "new_events" in result.data
