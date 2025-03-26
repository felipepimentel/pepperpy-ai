"""Workflow orchestrator for simplified workflow usage."""

from typing import Any, Dict, List, Optional, Type, TypeVar

from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.models import Task, Workflow, WorkflowExecution
from pepperpy.workflow.providers.local import LocalWorkflowProvider

T = TypeVar("T", bound=WorkflowProvider)


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
        provider: Optional[WorkflowProvider] = None,
        provider_class: Optional[Type[T]] = None,
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            provider: Optional workflow provider instance
            provider_class: Optional workflow provider class to instantiate
            provider_config: Optional provider configuration
        """
        if provider:
            self._provider = provider
        elif provider_class:
            self._provider = provider_class(**(provider_config or {}))
        else:
            self._provider = LocalWorkflowProvider()

        self._tasks: Dict[str, Task] = {}
        self._workflows: Dict[str, Workflow] = {}

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
        tasks: List[Task],
        edges: List[tuple[str, str]],
        description: Optional[str] = None,
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
        inputs: Optional[Dict[str, Any]] = None,
        wait: bool = True,
    ) -> WorkflowExecution:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            inputs: Optional workflow inputs
            wait: Whether to wait for completion

        Returns:
            Workflow execution
        """
        # Register workflow if needed
        if workflow.id not in self._workflows:
            await self._provider.register_workflow(workflow)
            self._workflows[workflow.id] = workflow

        # Execute workflow
        execution = await self._provider.execute_workflow(
            workflow_id=workflow.id, inputs=inputs or {}
        )

        # Wait for completion if requested
        if wait:
            while not execution.is_terminal():
                execution = await self._provider.get_execution(execution.id)

        return execution

    async def cancel(self, execution_id: str) -> None:
        """Cancel a workflow execution.

        Args:
            execution_id: ID of execution to cancel
        """
        await self._provider.cancel_execution(execution_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a registered task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a registered workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        return self._workflows.get(workflow_id)
