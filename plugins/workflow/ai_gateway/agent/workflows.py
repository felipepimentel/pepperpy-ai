"""Agent workflow management and orchestration.

This module provides the infrastructure to define and execute workflows
that involve multiple agents working together on complex tasks.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum, auto
from typing import Any

from .base import AgentCapability, AgentContext, BaseAgent, Task

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of workflows supported by the system."""

    SEQUENTIAL = auto()
    PARALLEL = auto()
    CONDITIONAL = auto()
    ITERATIVE = auto()
    DYNAMIC = auto()


class WorkflowStatus(Enum):
    """Status of a workflow."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(
        self,
        agent: BaseAgent,
        task: Task,
        name: str,
        depends_on: list[str] | None = None,
        condition: Callable[[dict[str, Any]], bool] | None = None,
        retry_policy: dict[str, Any] | None = None,
    ):
        """Initialize workflow step.

        Args:
            agent: Agent to execute the task
            task: Task to execute
            name: Unique name for the step
            depends_on: Names of steps this step depends on
            condition: Function that determines if this step should run
            retry_policy: Policy for retrying the step on failure
        """
        self.agent = agent
        self.task = task
        self.name = name
        self.depends_on = depends_on or []
        self.condition = condition
        self.retry_policy = retry_policy or {
            "max_attempts": 3,
            "delay_seconds": 1,
            "backoff_factor": 2,
        }
        self.result: Any = None
        self.status = WorkflowStatus.PENDING
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.attempts = 0
        self.error: Exception | None = None

    async def execute(
        self, context: AgentContext, workflow_memory: dict[str, Any]
    ) -> Any:
        """Execute this workflow step.

        Args:
            context: Agent context to use
            workflow_memory: Shared memory for the workflow

        Returns:
            Result of the task execution
        """
        self.start_time = datetime.now()
        self.status = WorkflowStatus.RUNNING
        self.attempts += 1

        # Check condition if provided
        if self.condition and not self.condition(workflow_memory):
            logger.info(f"Skipping step {self.name} due to condition")
            self.status = WorkflowStatus.COMPLETED
            self.end_time = datetime.now()
            return None

        try:
            # Provide workflow memory to task
            self.task.parameters = self.task.parameters or {}
            self.task.parameters["workflow_memory"] = workflow_memory
            self.task.parameters["step_name"] = self.name

            # Execute task with agent
            self.result = await self.agent.execute(self.task, context)
            self.status = WorkflowStatus.COMPLETED

            # Store result in workflow memory
            workflow_memory[self.name] = self.result

            logger.info(f"Step {self.name} completed successfully")
            return self.result

        except Exception as e:
            logger.error(f"Step {self.name} failed: {e}")
            self.error = e

            # Check if we should retry
            max_attempts = self.retry_policy["max_attempts"]
            if self.attempts < max_attempts:
                delay = self.retry_policy["delay_seconds"]
                backoff = self.retry_policy["backoff_factor"]

                # Calculate backoff delay
                retry_delay = delay * (backoff ** (self.attempts - 1))
                logger.info(
                    f"Retrying step {self.name} in {retry_delay} seconds (attempt {self.attempts + 1}/{max_attempts})"
                )

                # Wait before retry
                await asyncio.sleep(retry_delay)

                # Recursive retry
                return await self.execute(context, workflow_memory)
            else:
                self.status = WorkflowStatus.FAILED
                raise e
        finally:
            self.end_time = datetime.now()


class Workflow:
    """A workflow that orchestrates multiple agents working on complex tasks."""

    def __init__(
        self,
        name: str,
        description: str,
        workflow_type: WorkflowType,
        steps: list[WorkflowStep],
        context: AgentContext,
        max_concurrency: int = 5,
        timeout_seconds: int | None = None,
    ):
        """Initialize workflow.

        Args:
            name: Name of the workflow
            description: Description of the workflow
            workflow_type: Type of workflow
            steps: List of workflow steps
            context: Agent context to use
            max_concurrency: Maximum number of steps to run concurrently
            timeout_seconds: Maximum time in seconds to run the workflow
        """
        self.name = name
        self.description = description
        self.workflow_type = workflow_type
        self.steps = {step.name: step for step in steps}
        self.context = context
        self.max_concurrency = max_concurrency
        self.timeout_seconds = timeout_seconds
        self.status = WorkflowStatus.PENDING
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.memory: dict[str, Any] = {}

        # Validate step dependencies
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Validate that all step dependencies exist."""
        for step_name, step in self.steps.items():
            for dep in step.depends_on:
                if dep not in self.steps:
                    raise ValueError(
                        f"Step {step_name} depends on non-existent step {dep}"
                    )

    async def execute(self) -> dict[str, Any]:
        """Execute the workflow.

        Returns:
            Dictionary of step results
        """
        self.start_time = datetime.now()
        self.status = WorkflowStatus.RUNNING
        logger.info(f"Starting workflow: {self.name}")

        try:
            if self.workflow_type == WorkflowType.SEQUENTIAL:
                await self._execute_sequential()
            elif self.workflow_type == WorkflowType.PARALLEL:
                await self._execute_parallel()
            elif self.workflow_type == WorkflowType.CONDITIONAL:
                await self._execute_conditional()
            elif self.workflow_type == WorkflowType.ITERATIVE:
                await self._execute_iterative()
            elif self.workflow_type == WorkflowType.DYNAMIC:
                await self._execute_dynamic()
            else:
                raise ValueError(f"Unsupported workflow type: {self.workflow_type}")

            self.status = WorkflowStatus.COMPLETED
            logger.info(f"Workflow {self.name} completed successfully")

        except Exception as e:
            logger.error(f"Workflow {self.name} failed: {e}")
            self.status = WorkflowStatus.FAILED
            raise

        finally:
            self.end_time = datetime.now()

        return self.memory

    async def _execute_sequential(self) -> None:
        """Execute steps sequentially in dependency order."""
        # Determine execution order based on dependencies
        executed_steps: set[str] = set()
        pending_steps = list(self.steps.keys())

        while pending_steps:
            # Find steps that can be executed now
            executable_steps = [
                step_name
                for step_name in pending_steps
                if all(
                    dep in executed_steps for dep in self.steps[step_name].depends_on
                )
            ]

            if not executable_steps:
                remaining = ", ".join(pending_steps)
                raise RuntimeError(
                    f"Circular dependency detected in workflow steps: {remaining}"
                )

            # Execute the first available step
            step_name = executable_steps[0]
            step = self.steps[step_name]

            logger.info(f"Executing step: {step_name}")
            await step.execute(self.context, self.memory)

            executed_steps.add(step_name)
            pending_steps.remove(step_name)

    async def _execute_parallel(self) -> None:
        """Execute steps in parallel, respecting dependencies."""
        # Track completed steps
        completed_steps: set[str] = set()

        # Keep going until all steps are completed
        while len(completed_steps) < len(self.steps):
            # Find steps that can be executed now
            executable_steps = [
                step_name
                for step_name in self.steps.keys()
                if (
                    step_name not in completed_steps
                    and all(
                        dep in completed_steps
                        for dep in self.steps[step_name].depends_on
                    )
                )
            ]

            if not executable_steps and len(completed_steps) < len(self.steps):
                remaining = set(self.steps.keys()) - completed_steps
                raise RuntimeError(
                    f"Circular dependency detected in workflow steps: {remaining}"
                )

            # Limit concurrency
            executable_steps = executable_steps[: self.max_concurrency]

            if not executable_steps:
                # Wait for next event loop iteration if nothing to execute now
                await asyncio.sleep(0)
                continue

            # Execute steps in parallel
            logger.info(f"Executing steps in parallel: {', '.join(executable_steps)}")
            tasks = [
                self.steps[name].execute(self.context, self.memory)
                for name in executable_steps
            ]
            await asyncio.gather(*tasks)

            # Mark completed
            completed_steps.update(executable_steps)

    async def _execute_conditional(self) -> None:
        """Execute steps conditionally based on their condition functions."""
        # Similar to sequential but respects conditions
        executed_steps: set[str] = set()
        pending_steps = list(self.steps.keys())

        while pending_steps:
            # Find steps that can be executed now
            executable_steps = [
                step_name
                for step_name in pending_steps
                if all(
                    dep in executed_steps for dep in self.steps[step_name].depends_on
                )
            ]

            if not executable_steps:
                remaining = ", ".join(pending_steps)
                raise RuntimeError(
                    f"Circular dependency detected in workflow steps: {remaining}"
                )

            # Execute the first available step
            step_name = executable_steps[0]
            step = self.steps[step_name]

            logger.info(f"Evaluating step: {step_name}")
            await step.execute(self.context, self.memory)

            executed_steps.add(step_name)
            pending_steps.remove(step_name)

    async def _execute_iterative(self) -> None:
        """Execute steps iteratively with potential for loops."""
        # Implementation of iterative workflow
        # This would allow for loops in the workflow
        executed_steps: set[str] = set()
        iteration = 0
        max_iterations = 10  # Prevent infinite loops

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Starting iteration {iteration}")

            # Reset execution status for this iteration
            newly_executed = False

            for step_name, step in self.steps.items():
                # Skip if dependencies not met
                if not all(dep in executed_steps for dep in step.depends_on):
                    continue

                # Execute step
                logger.info(f"Executing step: {step_name}")
                await step.execute(self.context, self.memory)

                # Check if this is the first time we've executed this step
                if step_name not in executed_steps:
                    executed_steps.add(step_name)
                    newly_executed = True

            # If no new steps were executed in this iteration, we're done
            if not newly_executed:
                break

        # Check if we hit the iteration limit
        if iteration >= max_iterations:
            logger.warning(f"Workflow {self.name} reached maximum iterations")

    async def _execute_dynamic(self) -> None:
        """Dynamically determine next steps based on previous results."""
        # In a dynamic workflow, the next steps are determined at runtime
        # based on the results of previous steps
        executed_steps: set[str] = set()
        available_steps = set(self.steps.keys())

        while executed_steps != available_steps:
            # Find the next step to execute
            next_step = await self._determine_next_step(executed_steps)

            if next_step is None:
                # No more steps to execute
                break

            # Execute the step
            logger.info(f"Dynamically executing step: {next_step}")
            step = self.steps[next_step]
            await step.execute(self.context, self.memory)

            executed_steps.add(next_step)

    async def _determine_next_step(self, executed_steps: set[str]) -> str | None:
        """Determine the next step to execute in a dynamic workflow.

        Args:
            executed_steps: Set of steps already executed

        Returns:
            Name of the next step to execute, or None if no more steps
        """
        # Find unexecuted steps with all dependencies satisfied
        candidates = [
            step_name
            for step_name in self.steps.keys()
            if (
                step_name not in executed_steps
                and all(
                    dep in executed_steps for dep in self.steps[step_name].depends_on
                )
            )
        ]

        if not candidates:
            return None

        # If there are multiple candidates, we could use a heuristic
        # or let a decision agent choose the next step
        # For simplicity, we'll just take the first one
        return candidates[0]


class WorkflowBuilder:
    """Builder for creating workflows."""

    def __init__(self, name: str, description: str, workflow_type: WorkflowType):
        """Initialize builder.

        Args:
            name: Name of the workflow
            description: Description of the workflow
            workflow_type: Type of workflow
        """
        self.name = name
        self.description = description
        self.workflow_type = workflow_type
        self.steps: list[WorkflowStep] = []
        self.max_concurrency = 5
        self.timeout_seconds: int | None = None

    def add_step(
        self,
        agent: BaseAgent,
        task: Task,
        name: str,
        depends_on: list[str] | None = None,
        condition: Callable[[dict[str, Any]], bool] | None = None,
        retry_policy: dict[str, Any] | None = None,
    ) -> "WorkflowBuilder":
        """Add a step to the workflow.

        Args:
            agent: Agent to execute the task
            task: Task to execute
            name: Unique name for the step
            depends_on: Names of steps this step depends on
            condition: Function that determines if this step should run
            retry_policy: Policy for retrying the step on failure

        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            agent=agent,
            task=task,
            name=name,
            depends_on=depends_on,
            condition=condition,
            retry_policy=retry_policy,
        )
        self.steps.append(step)
        return self

    def set_max_concurrency(self, max_concurrency: int) -> "WorkflowBuilder":
        """Set maximum concurrency for parallel execution.

        Args:
            max_concurrency: Maximum number of steps to run concurrently

        Returns:
            Self for chaining
        """
        self.max_concurrency = max_concurrency
        return self

    def set_timeout(self, timeout_seconds: int) -> "WorkflowBuilder":
        """Set timeout for workflow execution.

        Args:
            timeout_seconds: Maximum time in seconds to run the workflow

        Returns:
            Self for chaining
        """
        self.timeout_seconds = timeout_seconds
        return self

    def build(self, context: AgentContext) -> Workflow:
        """Build the workflow.

        Args:
            context: Agent context to use

        Returns:
            Constructed workflow
        """
        return Workflow(
            name=self.name,
            description=self.description,
            workflow_type=self.workflow_type,
            steps=self.steps,
            context=context,
            max_concurrency=self.max_concurrency,
            timeout_seconds=self.timeout_seconds,
        )


# Workflow patterns/templates


async def create_sequential_workflow(
    name: str,
    description: str,
    agent: BaseAgent,
    tasks: list[Task],
    context: AgentContext,
) -> Workflow:
    """Create a simple sequential workflow with a single agent.

    Args:
        name: Name of the workflow
        description: Description of the workflow
        agent: Agent to execute all tasks
        tasks: List of tasks to execute in sequence
        context: Agent context to use

    Returns:
        Constructed workflow
    """
    builder = WorkflowBuilder(name, description, WorkflowType.SEQUENTIAL)

    # Add sequential steps
    prev_step = None
    for i, task in enumerate(tasks):
        step_name = f"step_{i + 1}"
        depends_on = [f"step_{i}"] if i > 0 else []

        builder.add_step(agent=agent, task=task, name=step_name, depends_on=depends_on)

    return builder.build(context)


async def create_parallel_processing_workflow(
    name: str,
    description: str,
    agents: list[BaseAgent],
    tasks: list[Task],
    context: AgentContext,
    max_concurrency: int = 5,
) -> Workflow:
    """Create a workflow for parallel processing of similar tasks.

    Args:
        name: Name of the workflow
        description: Description of the workflow
        agents: List of agents to execute tasks (can be fewer than tasks)
        tasks: List of tasks to execute in parallel
        context: Agent context to use
        max_concurrency: Maximum number of tasks to run concurrently

    Returns:
        Constructed workflow
    """
    builder = WorkflowBuilder(name, description, WorkflowType.PARALLEL)
    builder.set_max_concurrency(max_concurrency)

    # Assign tasks to agents in a round-robin fashion
    for i, task in enumerate(tasks):
        agent = agents[i % len(agents)]
        step_name = f"task_{i + 1}"

        builder.add_step(agent=agent, task=task, name=step_name)

    return builder.build(context)


async def create_specialist_workflow(
    name: str,
    description: str,
    specialist_agents: dict[AgentCapability, BaseAgent],
    coordinator_agent: BaseAgent,
    initial_task: Task,
    context: AgentContext,
) -> Workflow:
    """Create a workflow with specialist agents coordinated by a coordinator.

    Args:
        name: Name of the workflow
        description: Description of the workflow
        specialist_agents: Dictionary mapping capabilities to specialist agents
        coordinator_agent: Agent responsible for coordination
        initial_task: Initial task to start the workflow
        context: Agent context to use

    Returns:
        Constructed workflow
    """
    builder = WorkflowBuilder(name, description, WorkflowType.DYNAMIC)

    # Add coordinator step
    planning_task = Task(
        objective="Plan and coordinate the execution of the overall task",
        parameters={
            "initial_task": initial_task.to_dict(),
            "available_capabilities": list(specialist_agents.keys()),
        },
    )

    builder.add_step(agent=coordinator_agent, task=planning_task, name="planning")

    # Add specialist steps
    for capability, agent in specialist_agents.items():
        specialized_task = Task(
            objective=f"Execute specialized task using {capability} capability",
            parameters={"capability": capability},
        )

        builder.add_step(
            agent=agent,
            task=specialized_task,
            name=f"specialist_{capability}",
            depends_on=["planning"],
            # Only run if the planning step determined this capability is needed
            condition=lambda memory, cap=capability: cap
            in memory.get("planning", {}).get("required_capabilities", []),
        )

    # Add integration step
    integration_task = Task(
        objective="Integrate results from all specialist agents", parameters={}
    )

    builder.add_step(
        agent=coordinator_agent,
        task=integration_task,
        name="integration",
        depends_on=[f"specialist_{cap}" for cap in specialist_agents.keys()],
    )

    return builder.build(context)
