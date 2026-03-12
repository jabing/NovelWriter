# src/agents/orchestrator.py
"""Agent orchestrator for coordinating multi-agent workflows."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.agents.base import AgentResult, BaseAgent
from src.memory.base import BaseMemory

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """State of a workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    agent_name: str
    input_transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    condition: Callable[[dict[str, Any]], bool] | None = None
    on_failure: str = "stop"  # "stop", "skip", "retry"


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    state: WorkflowState
    steps_completed: int
    steps_total: int
    final_output: dict[str, Any]
    step_results: dict[str, AgentResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class AgentOrchestrator:
    """Orchestrator for coordinating multiple agents in workflows.

    The orchestrator manages:
    - Agent registration and discovery
    - Workflow definition and execution
    - State management and error handling
    - Memory sharing between agents
    """

    def __init__(
        self,
        memory: BaseMemory | None = None,
        max_retries: int = 2,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            memory: Shared memory for agents
            max_retries: Maximum retries for failed steps
        """
        self.agents: dict[str, BaseAgent] = {}
        self.workflows: dict[str, list[WorkflowStep]] = {}
        self.memory = memory
        self.max_retries = max_retries
        self._workflow_states: dict[str, WorkflowState] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator.

        Args:
            agent: Agent to register
        """
        if agent.name in self.agents:
            logger.warning(f"Agent '{agent.name}' already registered, replacing")
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent.

        Args:
            agent_name: Name of agent to unregister

        Returns:
            True if agent was unregistered
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        return False

    def get_agent(self, agent_name: str) -> BaseAgent | None:
        """Get a registered agent by name.

        Args:
            agent_name: Name of agent

        Returns:
            Agent if found, None otherwise
        """
        return self.agents.get(agent_name)

    def define_workflow(
        self,
        workflow_name: str,
        steps: list[WorkflowStep],
    ) -> None:
        """Define a named workflow.

        Args:
            workflow_name: Name for the workflow
            steps: List of workflow steps
        """
        self.workflows[workflow_name] = steps
        logger.info(f"Defined workflow '{workflow_name}' with {len(steps)} steps")

    async def run_workflow(
        self,
        workflow_name: str,
        initial_input: dict[str, Any],
        workflow_id: str | None = None,
    ) -> WorkflowResult:
        """Run a defined workflow.

        Args:
            workflow_name: Name of workflow to run
            initial_input: Initial input data
            workflow_id: Optional ID for tracking

        Returns:
            WorkflowResult with execution results
        """
        if workflow_name not in self.workflows:
            return WorkflowResult(
                success=False,
                state=WorkflowState.FAILED,
                steps_completed=0,
                steps_total=0,
                final_output={},
                errors=[f"Workflow '{workflow_name}' not found"],
            )

        steps = self.workflows[workflow_name]
        workflow_id = workflow_id or workflow_name

        self._workflow_states[workflow_id] = WorkflowState.RUNNING

        current_input = initial_input.copy()
        step_results: dict[str, AgentResult] = {}
        errors: list[str] = []

        for i, step in enumerate(steps):
            step_name = f"step_{i+1}_{step.agent_name}"
            logger.info(f"Workflow '{workflow_name}': Running {step_name}")

            # Check condition
            if step.condition and not step.condition(current_input):
                logger.info(f"Workflow '{workflow_name}': Skipping {step_name} (condition not met)")
                continue

            # Get agent
            agent = self.get_agent(step.agent_name)
            if not agent:
                error_msg = f"Agent '{step.agent_name}' not found"
                errors.append(error_msg)
                logger.error(f"Workflow '{workflow_name}': {error_msg}")

                if step.on_failure == "stop":
                    break
                elif step.on_failure == "skip":
                    continue
                else:  # retry
                    # Simple retry logic
                    continue

            # Transform input if needed
            step_input = current_input
            if step.input_transform:
                try:
                    step_input = step.input_transform(current_input)
                except Exception as e:
                    errors.append(f"Input transform failed: {e}")
                    if step.on_failure == "stop":
                        break
                    continue

            # Execute agent with retries
            result = await self._execute_with_retry(agent, step_input)
            step_results[step_name] = result

            if result.success:
                # Update current input with result
                current_input.update(result.data)
                logger.info(f"Workflow '{workflow_name}': {step_name} completed")
            else:
                errors.extend(result.errors)
                if step.on_failure == "stop":
                    break

        # Determine final state
        steps_completed = len([r for r in step_results.values() if r.success])
        all_success = all(r.success for r in step_results.values())

        final_state = WorkflowState.COMPLETED if all_success else WorkflowState.FAILED
        self._workflow_states[workflow_id] = final_state

        return WorkflowResult(
            success=all_success,
            state=final_state,
            steps_completed=steps_completed,
            steps_total=len(steps),
            final_output=current_input,
            step_results=step_results,
            errors=errors,
        )

    async def _execute_with_retry(
        self,
        agent: BaseAgent,
        input_data: dict[str, Any],
    ) -> AgentResult:
        """Execute agent with retry logic.

        Args:
            agent: Agent to execute
            input_data: Input data

        Returns:
            AgentResult from execution
        """
        last_result: AgentResult | None = None

        for attempt in range(self.max_retries + 1):
            result = await agent.run(input_data)
            last_result = result

            if result.success:
                return result

            if attempt < self.max_retries:
                logger.warning(
                    f"Agent '{agent.name}' failed (attempt {attempt + 1}), "
                    f"retrying... Errors: {result.errors}"
                )
                await asyncio.sleep(1)  # Brief delay before retry

        # Return last result after all retries exhausted
        if last_result:
            return last_result
        return AgentResult(success=False, data={}, errors=["Unknown error"])

    async def run_parallel(
        self,
        agent_names: list[str],
        input_data: dict[str, Any],
    ) -> dict[str, AgentResult]:
        """Run multiple agents in parallel.

        Args:
            agent_names: List of agent names to run
            input_data: Input data for all agents

        Returns:
            Dictionary of agent name to result
        """
        tasks: dict[str, asyncio.Task[AgentResult]] = {}

        for name in agent_names:
            agent = self.get_agent(name)
            if agent:
                tasks[name] = asyncio.create_task(agent.run(input_data))
            else:
                logger.warning(f"Agent '{name}' not found, skipping")

        results: dict[str, AgentResult] = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = AgentResult(
                    success=False,
                    data={},
                    errors=[str(e)],
                )

        return results

    def get_workflow_state(self, workflow_id: str) -> WorkflowState | None:
        """Get the state of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowState if found, None otherwise
        """
        return self._workflow_states.get(workflow_id)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def list_workflows(self) -> list[str]:
        """List all defined workflow names."""
        return list(self.workflows.keys())


# Pre-defined novel writing workflow
NOVEL_WRITING_WORKFLOW = [
    WorkflowStep(agent_name="Plot Agent"),
    WorkflowStep(
        agent_name="Character Agent",
        input_transform=lambda d: {**d, "plot": d.get("outline", {})}
    ),
    WorkflowStep(
        agent_name="Worldbuilding Agent",
        input_transform=lambda d: {**d, "plot": d.get("outline", {})}
    ),
    WorkflowStep(
        agent_name="Writer Agent",
        input_transform=lambda d: {
            **d,
            "chapter_outline": d.get("outline", {}).get("chapters", [])[d.get("chapter_number", 0)],
            "characters": d.get("characters", []),
            "world_context": d.get("world", {}),
        }
    ),
    WorkflowStep(
        agent_name="Editor Agent",
        input_transform=lambda d: {
            **d,
            "content": d.get("content", ""),
            "characters": d.get("characters", []),
        }
    ),
    WorkflowStep(
        agent_name="Publisher Agent",
        input_transform=lambda d: {
            "novel_id": d.get("novel_id"),
            "chapter_number": d.get("chapter_number"),
            "content": d.get("edited_content", d.get("content", "")),
            "platforms": d.get("platforms", ["wattpad"]),
        }
    ),
]
