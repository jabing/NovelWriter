"""
Tests for NovelWriter LSP Validator Agent.

This module tests the ValidatorAgent class defined in novelwriter_lsp.agents.validator.
"""

import pytest
from novelwriter_lsp.agents import ValidatorAgent, AgentResult


class TestValidatorAgent:
    """Tests for ValidatorAgent class."""

    def test_validator_agent_initialization(self):
        """Test creating a ValidatorAgent instance."""
        agent = ValidatorAgent()
        assert agent.name == "ValidatorAgent"
        assert agent.state == "idle"
        assert agent.execution_count == 0

    @pytest.mark.asyncio
    async def test_validate_no_issues(self):
        """Test validating content with no issues."""
        agent = ValidatorAgent()
        content = """
# Novel: Test

@Character: Alice { status: "alive", age: 30 }
@Location: The Park { city: "Testville" }

## Chapter 1

Alice walked into The Park.
"""
        result = await agent.validate("test.md", content)
        assert result.success is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_dead_character_alive(self):
        """Test detecting a dead character appearing alive."""
        agent = ValidatorAgent()
        content = """
@Character: Bob { status: "dead" }

Bob was alive and talking.
"""
        result = await agent.validate("test.md", content)
        assert result.success is False
        assert any("Dead character appears alive" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_validate_timeline_inconsistency(self):
        """Test detecting timeline inconsistencies (multiple events at same time)."""
        agent = ValidatorAgent()
        content = """
@Event: Party { time: "2024-01-01" }
@Event: Meeting { time: "2024-01-01" }
"""
        result = await agent.validate("test.md", content)
        assert result.success is False
        assert any("Multiple events at the same time" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_validate_missing_event_details(self):
        """Test detecting events missing details."""
        agent = ValidatorAgent()
        content = """
@Event: Birthday { }
"""
        result = await agent.validate("test.md", content)
        assert result.success is True  # warnings don't fail validation
        assert len(result.warnings) > 0
        assert any("missing details" in warn for warn in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_age_inconsistency(self):
        """Test detecting character age inconsistencies."""
        agent = ValidatorAgent()
        content = """
@Character: Charlie { age: 25 }
@Character: Charlie { age: 30 }
"""
        result = await agent.validate("test.md", content)
        assert result.success is False
        assert any("conflicting ages" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_execute_method(self):
        """Test the execute method (entry point)."""
        agent = ValidatorAgent()
        input_data = {"uri": "test.md", "content": "@Character: Dave { status: 'alive' }"}
        result = await agent.execute(input_data)
        assert isinstance(result, AgentResult)
        assert result.data.get("uri") == "test.md"
