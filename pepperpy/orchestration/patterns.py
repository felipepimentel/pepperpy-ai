"""
PepperPy Orchestration Patterns Module.

This module defines orchestration patterns for composing workflows and agents.
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, Generic, TypeVar, cast

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.core.context import execution_context
from pepperpy.core.errors import PepperpyError

T = TypeVar("T")
R = TypeVar("R")


class OrchestrationError(PepperpyError):
    """Error raised by orchestration patterns."""

    pass


class FlowStatus(str, Enum):
    """Status of a flow execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Flow(Generic[T, R], ABC):
    """Base class for all flow patterns.

    Flows are composable units of orchestration that define how to execute tasks.
    """

    def __init__(self, name: str) -> None:
        """Initialize a flow.

        Args:
            name: Flow name
        """
        self.name = name
        self.status = FlowStatus.PENDING
        self.result: R | None = None
        self.error: Exception | None = None

    @abstractmethod
    async def execute(self, input_data: T) -> R:
        """Execute the flow with the given input data.

        Args:
            input_data: Input data for the flow

        Returns:
            Flow result

        Raises:
            OrchestrationError: If an error occurs during execution
        """
        pass


class SequentialFlow(Flow[T, R]):
    """Flow that executes tasks in sequence.

    Each task takes the output of the previous task as input.
    """

    def __init__(
        self,
        name: str,
        tasks: list[Callable[[Any], Any]],
    ) -> None:
        """Initialize a sequential flow.

        Args:
            name: Flow name
            tasks: List of tasks to execute in sequence
        """
        super().__init__(name)
        self.tasks = tasks

    async def execute(self, input_data: T) -> R:
        """Execute tasks in sequence.

        Args:
            input_data: Input data for the first task

        Returns:
            Result of the last task

        Raises:
            OrchestrationError: If a task fails
        """
        self.status = FlowStatus.RUNNING
        data = input_data

        try:
            for i, task in enumerate(self.tasks):
                async with execution_context(parent_id=self.name) as context:
                    context.add_metadata("flow_name", self.name)
                    context.add_metadata("task_index", i)
                    context.add_metadata("task_count", len(self.tasks))

                    # Execute the task with current data
                    if asyncio.iscoroutinefunction(task):
                        data = await task(data)
                    else:
                        data = task(data)

            self.status = FlowStatus.SUCCEEDED
            self.result = cast(R, data)
            return self.result

        except Exception as e:
            self.status = FlowStatus.FAILED
            self.error = e
            raise OrchestrationError(
                f"Error in sequential flow '{self.name}': {e!s}"
            ) from e


class ParallelFlow(Flow[list[T], list[R]]):
    """Flow that executes tasks in parallel.

    All tasks are executed simultaneously and their results are collected.
    """

    def __init__(
        self,
        name: str,
        tasks: list[Callable[[T], R]],
        max_concurrency: int | None = None,
    ) -> None:
        """Initialize a parallel flow.

        Args:
            name: Flow name
            tasks: List of tasks to execute in parallel
            max_concurrency: Maximum number of tasks to run concurrently (None for unlimited)
        """
        super().__init__(name)
        self.tasks = tasks
        self.max_concurrency = max_concurrency

    async def execute(self, input_data: list[T]) -> list[R]:
        """Execute tasks in parallel.

        Args:
            input_data: List of input data for each task

        Returns:
            List of task results

        Raises:
            OrchestrationError: If any task fails
            ValueError: If the number of inputs doesn't match the number of tasks
        """
        self.status = FlowStatus.RUNNING

        # Check that input data matches the number of tasks
        if len(input_data) != len(self.tasks):
            self.status = FlowStatus.FAILED
            raise ValueError(
                f"Number of inputs ({len(input_data)}) doesn't match number of tasks ({len(self.tasks)})"
            )

        try:
            # Create task executions
            async def execute_task(task: Callable[[T], R], data: T, index: int) -> R:
                async with execution_context(parent_id=self.name) as context:
                    context.add_metadata("flow_name", self.name)
                    context.add_metadata("task_index", index)
                    context.add_metadata("task_count", len(self.tasks))

                    if asyncio.iscoroutinefunction(task):
                        return await task(data)
                    else:
                        return task(data)

            tasks = [
                execute_task(task, data, i)
                for i, (task, data) in enumerate(
                    zip(self.tasks, input_data, strict=False)
                )
            ]

            # Execute all tasks with optional concurrency limit
            if self.max_concurrency:
                # Limit concurrency using semaphore
                sem = asyncio.Semaphore(self.max_concurrency)

                async def with_semaphore(coro):
                    async with sem:
                        return await coro

                tasks = [with_semaphore(task) for task in tasks]

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)

            self.status = FlowStatus.SUCCEEDED
            self.result = results
            return results

        except Exception as e:
            self.status = FlowStatus.FAILED
            self.error = e
            raise OrchestrationError(
                f"Error in parallel flow '{self.name}': {e!s}"
            ) from e


class ConditionalFlow(Flow[T, R]):
    """Flow that executes tasks based on a condition.

    Executes one flow if the condition is true, and another if false.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[T], bool],
        if_true: Flow[T, R],
        if_false: Flow[T, R] | None = None,
    ) -> None:
        """Initialize a conditional flow.

        Args:
            name: Flow name
            condition: Function that evaluates the condition
            if_true: Flow to execute if the condition is true
            if_false: Flow to execute if the condition is false (optional)
        """
        super().__init__(name)
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    async def execute(self, input_data: T) -> R:
        """Execute the flow based on the condition.

        Args:
            input_data: Input data for the flow

        Returns:
            Result of the executed flow

        Raises:
            OrchestrationError: If the condition or selected flow fails
        """
        self.status = FlowStatus.RUNNING

        try:
            # Evaluate the condition
            condition_result = self.condition(input_data)

            # Execute the appropriate flow
            if condition_result:
                result = await self.if_true.execute(input_data)
            elif self.if_false:
                result = await self.if_false.execute(input_data)
            else:
                # If no else flow and condition is false, return None
                result = cast(R, None)

            self.status = FlowStatus.SUCCEEDED
            self.result = result
            return result

        except Exception as e:
            self.status = FlowStatus.FAILED
            self.error = e
            raise OrchestrationError(
                f"Error in conditional flow '{self.name}': {e!s}"
            ) from e


class AgentOrchestrator:
    """Orchestrator for agent-based workflows.

    Provides patterns for coordinating multiple agents to solve complex tasks.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize an agent orchestrator.

        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.agents: dict[str, BaseAgentProvider] = {}

    async def register_agent(self, name: str, agent: BaseAgentProvider) -> None:
        """Register an agent with the orchestrator.

        Args:
            name: Agent name
            agent: Agent instance
        """
        if not agent.initialized:
            await agent.initialize()
        self.agents[name] = agent

    async def get_agent(self, name: str) -> BaseAgentProvider:
        """Get a registered agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance

        Raises:
            OrchestrationError: If agent not found
        """
        if name not in self.agents:
            raise OrchestrationError(f"Agent '{name}' not found")
        return self.agents[name]

    async def execute_sequential(
        self,
        agent_names: list[str],
        initial_prompt: str,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """Execute agents sequentially, passing the output to each next agent.

        Args:
            agent_names: List of agent names to execute in order
            initial_prompt: Initial prompt to start the workflow
            context: Optional context data for execution

        Returns:
            List of agent responses

        Raises:
            OrchestrationError: If an agent fails or is not found
        """
        results = []
        current_prompt = initial_prompt
        ctx = context or {}

        for agent_name in agent_names:
            try:
                agent = await self.get_agent(agent_name)
                response = await agent.process_message(current_prompt, ctx)
                results.append(response)
                current_prompt = response
            except Exception as e:
                raise OrchestrationError(
                    f"Error executing agent '{agent_name}': {e!s}"
                ) from e

        return results

    async def execute_parallel(
        self,
        agent_names: list[str],
        prompts: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Execute multiple agents in parallel with different prompts.

        Args:
            agent_names: List of agent names to execute
            prompts: List of prompts for each agent
            context: Optional context data for execution

        Returns:
            Dict mapping agent names to their responses

        Raises:
            OrchestrationError: If an agent fails or is not found
            ValueError: If prompts don't match agent_names
        """
        if len(agent_names) != len(prompts):
            raise ValueError(
                f"Number of prompts ({len(prompts)}) doesn't match agents ({len(agent_names)})"
            )

        results: dict[str, str] = {}
        ctx = context or {}
        tasks = []

        for agent_name, prompt in zip(agent_names, prompts, strict=False):

            async def execute_agent(name, prompt):
                agent = await self.get_agent(name)
                return name, await agent.process_message(prompt, ctx)

            tasks.append(execute_agent(agent_name, prompt))

        try:
            agent_results = await asyncio.gather(*tasks)
            for name, response in agent_results:
                results[name] = response
            return results
        except Exception as e:
            raise OrchestrationError(
                f"Error executing agents in parallel: {e!s}"
            ) from e
