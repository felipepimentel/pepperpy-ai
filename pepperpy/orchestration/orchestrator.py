"""Workflow orchestrator for simplified workflow usage."""

from typing import Any, TypeVar

from pepperpy.orchestration.base import OrchestrationProvider
from pepperpy.orchestration.local import LocalOrchestrationProvider
from pepperpy.workflow.models import Task, Workflow, WorkflowExecution

T = TypeVar("T", bound=OrchestrationProvider)


class WorkflowOrchestrator:
    """Orchestrator for simplified workflow usage.

    This class provides a high-level interface for working with workflows,
    making it easier to define, register, and execute workflows without
    dealing with the low-level details.

    Example:
        ```python
        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Register tasks
        @orchestrator.task
        async def process_text(text: str) -> Dict[str, Any]:
            # Process text...
            return {"result": processed}

        @orchestrator.task
        async def analyze_sentiment(text: str) -> Dict[str, Any]:
            # Analyze sentiment...
            return {"sentiment": sentiment}

        # Create workflow
        workflow = orchestrator.workflow(
            "text_analysis",
            tasks=[process_text, analyze_sentiment],
            edges=[("process_text", "analyze_sentiment")]
        )

        # Execute workflow
        result = await orchestrator.execute(
            workflow,
            inputs={"text": "Sample text"}
        )
        ```
    """

    def __init__(
        self,
        provider: OrchestrationProvider | None = None,
        provider_class: type[T] | None = None,
        provider_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            provider: Optional workflow provider instance
            provider_class: Optional workflow provider class to instantiate
            provider_config: Optional provider configuration
        """
        self._provider: OrchestrationProvider | None = provider
        self._provider_class = provider_class
        self._provider_config = provider_config or {}
        self._initialized = False
        self._tasks: dict[str, Task] = {}
        self._workflows: dict[str, Workflow] = {}

    async def initialize(self) -> None:
        """Initialize the orchestrator.

        This method initializes the orchestration provider if not already done.
        """
        if self._initialized:
            return

        # Create provider if needed
        if not self._provider:
            if self._provider_class:
                self._provider = self._provider_class(**self._provider_config)
            else:
                self._provider = LocalOrchestrationProvider(**self._provider_config)

        # Initialize provider
        await self._provider.initialize()

        # Register existing workflows
        for workflow in self._workflows.values():
            await self._provider.register_workflow(workflow)

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._initialized and self._provider:
            await self._provider.cleanup()
        self._initialized = False

    def task(self, func: Any) -> Task:
        """Decorator to register a task.

        Args:
            func: Task function to register

        Returns:
            Registered task
        """
        task = Task.from_function(func)
        self._tasks[task.id] = task
        return task

    def workflow(
        self,
        name: str,
        tasks: list[Task],
        edges: list[tuple[str, str]],
        description: str | None = None,
        version: str = "1.0.0",
    ) -> Workflow:
        """Create a workflow from tasks and edges.

        Args:
            name: Workflow name
            tasks: List of tasks
            edges: List of (source_task_id, target_task_id) tuples
            description: Optional workflow description
            version: Workflow version

        Returns:
            Created workflow
        """
        workflow = (
            Workflow.builder()
            .with_id(name.lower().replace(" ", "_"))
            .with_name(name)
            .with_description(description or f"Workflow: {name}")
            .with_version(version)
        )

        # Add tasks
        for task in tasks:
            workflow.with_task(task)

        # Add edges
        for source, target in edges:
            workflow.with_edge(source_task_id=source, target_task_id=target)

        workflow = workflow.build()
        self._workflows[workflow.id] = workflow
        return workflow

    async def execute(
        self,
        workflow: Workflow,
        inputs: dict[str, Any] | None = None,
        wait: bool = True,
    ) -> WorkflowExecution | None:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            inputs: Optional workflow inputs
            wait: Whether to wait for completion

        Returns:
            Workflow execution if wait is True, None otherwise
        """
        # Initialize if needed
        await self.initialize()

        # Provider should be initialized at this point
        if not self._provider:
            raise RuntimeError("Provider not initialized")

        # Register workflow if needed
        if workflow.id not in self._workflows:
            self._workflows[workflow.id] = workflow
            await self._provider.register_workflow(workflow)

        # Execute workflow
        execution_id = await self._provider.execute_workflow(
            workflow_id=workflow.id, inputs=inputs or {}
        )

        # Wait for completion if requested
        if wait:
            execution = await self._provider.get_execution(execution_id)
            while execution and not execution.is_terminal():
                import asyncio

                await asyncio.sleep(0.1)
                execution = await self._provider.get_execution(execution_id)
            return execution

        return None

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a workflow execution.

        Args:
            execution_id: ID of execution to cancel

        Returns:
            True if cancelled, False otherwise
        """
        # Initialize if needed
        await self.initialize()

        # Provider should be initialized at this point
        if not self._provider:
            raise RuntimeError("Provider not initialized")

        return await self._provider.cancel_execution(execution_id)

    def get_task(self, task_id: str) -> Task | None:
        """Get a registered task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """Get a registered workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        return self._workflows.get(workflow_id)

    async def list_workflows(self) -> list[Workflow]:
        """List all registered workflows.

        Returns:
            List of workflow objects
        """
        # Initialize if needed
        await self.initialize()

        # Provider should be initialized at this point
        if not self._provider:
            raise RuntimeError("Provider not initialized")

        # Get workflows from provider
        return await self._provider.list_workflows()
