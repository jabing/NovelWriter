# tests/test_agents/test_orchestrator.py
"""Tests for agent orchestrator."""

from unittest.mock import MagicMock

import pytest

from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.agents.orchestrator import (
    AgentOrchestrator,
    WorkflowState,
    WorkflowStep,
)


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(
        self,
        name: str,
        return_success: bool = True,
        return_data: dict | None = None,
        raise_error: bool = False,
    ) -> None:
        super().__init__(name=name, llm=MagicMock())
        self.return_success = return_success
        self.return_data = return_data or {}
        self.raise_error = raise_error
        self.call_count = 0
        self.last_input = None

    async def execute(self, input_data: dict) -> AgentResult:
        self.call_count += 1
        self.last_input = input_data

        if self.raise_error:
            raise RuntimeError("Test error")

        return AgentResult(
            success=self.return_success,
            data=self.return_data,
            errors=[] if self.return_success else ["Test failure"],
        )


class TestOrchestratorRegistration:
    """Tests for agent registration."""

    def test_register_agent(self) -> None:
        """Test registering an agent."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent")

        orchestrator.register_agent(agent)

        assert "TestAgent" in orchestrator.list_agents()
        assert orchestrator.get_agent("TestAgent") is agent

    def test_register_same_agent_twice(self) -> None:
        """Test registering same agent twice replaces."""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("TestAgent")
        agent2 = MockAgent("TestAgent")

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        assert len(orchestrator.list_agents()) == 1
        assert orchestrator.get_agent("TestAgent") is agent2

    def test_unregister_agent(self) -> None:
        """Test unregistering an agent."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("TestAgent")
        orchestrator.register_agent(agent)

        result = orchestrator.unregister_agent("TestAgent")

        assert result is True
        assert "TestAgent" not in orchestrator.list_agents()

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering nonexistent agent."""
        orchestrator = AgentOrchestrator()

        result = orchestrator.unregister_agent("Nonexistent")

        assert result is False


class TestWorkflowDefinition:
    """Tests for workflow definition."""

    def test_define_workflow(self) -> None:
        """Test defining a workflow."""
        orchestrator = AgentOrchestrator()
        steps = [
            WorkflowStep(agent_name="Agent1"),
            WorkflowStep(agent_name="Agent2"),
        ]

        orchestrator.define_workflow("test_workflow", steps)

        assert "test_workflow" in orchestrator.list_workflows()

    def test_workflow_not_found(self) -> None:
        """Test running nonexistent workflow."""
        orchestrator = AgentOrchestrator()

        import asyncio
        result = asyncio.run(orchestrator.run_workflow("nonexistent", {}))

        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "not found" in result.errors[0]


class TestWorkflowExecution:
    """Tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_simple_workflow(self) -> None:
        """Test simple sequential workflow."""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", return_data={"step": 1})
        agent2 = MockAgent("Agent2", return_data={"step": 2})

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        orchestrator.define_workflow("simple", [
            WorkflowStep(agent_name="Agent1"),
            WorkflowStep(agent_name="Agent2"),
        ])

        result = await orchestrator.run_workflow("simple", {"input": "test"})

        assert result.success is True
        assert result.state == WorkflowState.COMPLETED
        assert result.steps_completed == 2
        assert agent1.call_count == 1
        assert agent2.call_count == 1

    @pytest.mark.asyncio
    async def test_workflow_with_failure(self) -> None:
        """Test workflow with failing step."""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", return_success=True)
        agent2 = MockAgent("Agent2", return_success=False)
        agent3 = MockAgent("Agent3", return_success=True)

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)

        orchestrator.define_workflow("failing", [
            WorkflowStep(agent_name="Agent1"),
            WorkflowStep(agent_name="Agent2"),
            WorkflowStep(agent_name="Agent3"),
        ])

        result = await orchestrator.run_workflow("failing", {})

        # Agent2 fails, so Agent3 should not run
        assert result.success is False
        assert agent1.call_count == 1
        assert agent2.call_count > 0  # May be retried
        # Agent3 should not be called due to stop on failure

    @pytest.mark.asyncio
    async def test_workflow_input_transform(self) -> None:
        """Test workflow with input transform."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("Agent", return_data={"result": "ok"})
        orchestrator.register_agent(agent)

        orchestrator.define_workflow("transform", [
            WorkflowStep(
                agent_name="Agent",
                input_transform=lambda d: {"transformed": d["original"] * 2}
            ),
        ])

        result = await orchestrator.run_workflow("transform", {"original": 5})

        assert result.success is True
        assert agent.last_input == {"transformed": 10}

    @pytest.mark.asyncio
    async def test_workflow_skip_on_condition(self) -> None:
        """Test workflow skips step when condition not met."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("Agent")
        orchestrator.register_agent(agent)

        orchestrator.define_workflow("conditional", [
            WorkflowStep(
                agent_name="Agent",
                condition=lambda d: d.get("run", False),
            ),
        ])

        result = await orchestrator.run_workflow("conditional", {"run": False})

        assert result.success is True
        assert agent.call_count == 0  # Skipped


class TestParallelExecution:
    """Tests for parallel agent execution."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self) -> None:
        """Test running agents in parallel."""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1", return_data={"id": 1})
        agent2 = MockAgent("Agent2", return_data={"id": 2})

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        results = await orchestrator.run_parallel(
            ["Agent1", "Agent2"],
            {"shared": "input"}
        )

        assert len(results) == 2
        assert results["Agent1"].success is True
        assert results["Agent2"].success is True
        assert results["Agent1"].data["id"] == 1
        assert results["Agent2"].data["id"] == 2

    @pytest.mark.asyncio
    async def test_parallel_missing_agent(self) -> None:
        """Test parallel execution with missing agent."""
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("Agent1")
        orchestrator.register_agent(agent1)

        results = await orchestrator.run_parallel(
            ["Agent1", "Nonexistent"],
            {}
        )

        assert len(results) == 1
        assert "Agent1" in results
        assert "Nonexistent" not in results


class TestRetryLogic:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        """Test that failed steps are retried."""
        orchestrator = AgentOrchestrator(max_retries=2)
        agent = MockAgent("Agent", return_success=False)
        orchestrator.register_agent(agent)

        orchestrator.define_workflow("retry", [
            WorkflowStep(agent_name="Agent"),
        ])

        result = await orchestrator.run_workflow("retry", {})

        assert result.success is False
        # Initial call + 2 retries = 3 calls
        assert agent.call_count == 3


class TestWorkflowState:
    """Tests for workflow state tracking."""

    @pytest.mark.asyncio
    async def test_workflow_state_tracking(self) -> None:
        """Test that workflow state is tracked."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent("Agent")
        orchestrator.register_agent(agent)

        orchestrator.define_workflow("state_test", [
            WorkflowStep(agent_name="Agent"),
        ])

        result = await orchestrator.run_workflow(
            "state_test",
            {},
            workflow_id="custom_id"
        )

        assert result.state == WorkflowState.COMPLETED
        state = orchestrator.get_workflow_state("custom_id")
        assert state == WorkflowState.COMPLETED
