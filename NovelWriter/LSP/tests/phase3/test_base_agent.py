"""
Tests for NovelWriter LSP Base Agent.

This module tests the base agent class defined in novelwriter_lsp.agents.base.
"""

try:
    from typing import override
except ImportError:
    from typing_extensions import override
import pytest
from novelwriter_lsp.agents import AgentState, AgentResult, BaseAgent


class TestAgentState:
    """Tests for AgentState enum."""

    def test_agent_state_count(self):
        """Test that all 4 agent states are defined."""
        assert len(AgentState) == 4

    def test_agent_state_values(self):
        """Test that all expected agent states exist."""
        expected_states = [
            "IDLE",
            "RUNNING",
            "COMPLETED",
            "FAILED",
        ]
        for state_name in expected_states:
            assert hasattr(AgentState, state_name)

    def test_agent_state_string_values(self):
        """Test that enum string values are correct."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_agent_result_creation(self):
        """Test creating a basic AgentResult instance."""
        result = AgentResult(
            success=True,
            data={"key": "value"},
            errors=["error1"],
            warnings=["warning1"],
        )

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]

    def test_agent_result_defaults(self):
        """Test AgentResult default values."""
        result = AgentResult(success=True)

        assert result.success is True
        assert result.data == {}
        assert result.errors == []
        assert result.warnings == []

    def test_agent_result_failure(self):
        """Test creating a failure AgentResult."""
        result = AgentResult(success=False, errors=["Something went wrong"])

        assert result.success is False
        assert result.errors == ["Something went wrong"]


class TestBaseAgent:
    """Tests for BaseAgent abstract base class."""

    class TestAgent(BaseAgent):
        """Concrete test implementation of BaseAgent."""

        @override
        async def execute(self, input_data: dict[str, object]) -> AgentResult:
            return AgentResult(
                success=True,
                data={"processed": input_data},
            )

    class FailingTestAgent(BaseAgent):
        """Test agent that fails during execution."""

        @override
        async def execute(self, input_data: dict[str, object]) -> AgentResult:
            raise ValueError("Intentional failure")

    def test_base_agent_initialization(self):
        """Test creating a BaseAgent instance."""
        agent = self.TestAgent(name="Test Agent")

        assert agent.name == "Test Agent"
        assert agent.state == AgentState.IDLE
        assert agent.execution_count == 0

    def test_base_agent_repr(self):
        """Test string representation of BaseAgent."""
        agent = self.TestAgent(name="Test Agent")
        repr_str = repr(agent)

        assert "TestAgent" in repr_str
        assert "Test Agent" in repr_str
        assert "idle" in repr_str

    @pytest.mark.asyncio
    async def test_base_agent_run_success(self):
        """Test running an agent successfully."""
        agent = self.TestAgent(name="Test Agent")

        result = await agent.run({"input": "test"})

        assert result.success is True
        assert result.data == {"processed": {"input": "test"}}
        assert agent.state == AgentState.COMPLETED
        assert agent.execution_count == 1

    @pytest.mark.asyncio
    async def test_base_agent_run_failure(self):
        """Test running an agent that fails."""
        agent = self.FailingTestAgent(name="Failing Agent")

        result = await agent.run({"input": "test"})

        assert result.success is False
        assert len(result.errors) == 1
        assert "Intentional failure" in result.errors[0]
        assert agent.state == AgentState.FAILED
        assert agent.execution_count == 1

    def test_base_agent_update_state(self):
        """Test updating agent state."""
        agent = self.TestAgent(name="Test Agent")

        agent.update_state(AgentState.RUNNING)
        assert agent.state == AgentState.RUNNING

        agent.update_state(AgentState.COMPLETED)
        assert agent.state == AgentState.COMPLETED
