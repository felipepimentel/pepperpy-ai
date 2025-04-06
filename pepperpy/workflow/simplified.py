"""
PepperPy Simplified Workflow API.

This module provides a simplified interface for creating and running
workflows with minimal code, hiding the complexity of the full orchestration system.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from pepperpy.core import get_logger

logger = get_logger(__name__)

# Type definitions
TaskFunction = Callable[..., Any]
T = TypeVar("T")


def workflow_task(name: str | None = None, description: str | None = None):
    """
    Decorator for marking methods as workflow tasks.

    This decorator automatically handles logging, validation, and error handling
    for task methods in SimpleWorkflow subclasses.

    Args:
        name: Optional custom name for the task
        description: Optional description for the task

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            task_name = name or func.__name__

            logger.info(f"Executing task {task_name}")
            try:
                result = await func(self, *args, **kwargs)
                logger.info(f"Task {task_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                raise

        # Store metadata as attributes (ignore linter errors for dynamic attributes)
        wrapper.__workflow_task__ = True
        wrapper.__task_name__ = name or func.__name__
        wrapper.__task_description__ = description or func.__doc__

        return wrapper

    return decorator


class SimpleWorkflow:
    """
    Simplified workflow interface for creating and running workflows with minimal code.

    Example:
        ```python
        # Create a workflow
        workflow = SimpleWorkflow("document_processor")

        # Define tasks with simple decorators
        @workflow.task
        async def fetch_document(url: str) -> dict:
            # Fetch document from URL
            return {"content": "Document content", "metadata": {"url": url}}

        @workflow.task(depends_on=["fetch_document"])
        async def process_document(content: str, metadata: dict) -> dict:
            # Process document content
            return {"processed_content": content.upper(), "metadata": metadata}

        @workflow.task(depends_on=["process_document"])
        async def summarize_document(processed_content: str, metadata: dict) -> dict:
            # Create summary
            return {"summary": f"Summary of {metadata['url']}", "length": len(processed_content)}

        # Run the workflow
        result = await workflow.run(url="https://example.com/doc")
        print(result)  # Output from the last task (summarize_document)
        ```
    """

    def __init__(self, name: str, description: str | None = None):
        """
        Initialize a simple workflow.

        Args:
            name: The name of the workflow
            description: Optional description of the workflow
        """
        self.name = name
        self.description = description or f"Simple workflow: {name}"
        self._tasks: dict[str, TaskFunction] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._orchestrator = None
        self._workflow = None
        self.initialized = False
        self.config = {}

    def task(
        self,
        func: TaskFunction | None = None,
        *,
        name: str | None = None,
        depends_on: list[str] | None = None,
    ) -> Any:
        """
        Decorator to register a task in the workflow.

        Args:
            func: The task function to register
            name: Optional custom name for the task
            depends_on: Optional list of task names this task depends on

        Returns:
            The decorated function
        """

        def decorator(fn: TaskFunction) -> TaskFunction:
            task_name = name or fn.__name__
            self._tasks[task_name] = fn
            if depends_on:
                self._dependencies[task_name] = depends_on

            @wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await fn(*args, **kwargs)

            return cast(TaskFunction, wrapper)

        if func is None:
            return decorator
        return decorator(func)

    async def _build_workflow(self) -> Any:
        """
        Build the actual workflow from registered tasks and dependencies.

        Returns:
            Built workflow
        """
        # Lazy import to avoid circular imports
        from pepperpy.workflow.models import Task, Workflow

        if not self._tasks:
            raise ValueError("No tasks registered in workflow")

        # Create tasks
        workflow_tasks = {
            name: Task.from_function(func) for name, func in self._tasks.items()
        }

        # Create edges from dependencies
        edges = []
        for target, sources in self._dependencies.items():
            for source in sources:
                if source not in workflow_tasks:
                    raise ValueError(
                        f"Dependency '{source}' not found for task '{target}'"
                    )
                edges.append((source, target))

        # Create workflow
        builder = (
            Workflow.builder()
            .with_id(self.name.lower().replace(" ", "_"))
            .with_name(self.name)
            .with_description(self.description)
        )

        # Add tasks
        for task in workflow_tasks.values():
            builder.with_task(task)

        # Add edges
        for source, target in edges:
            builder.with_edge(source_task_id=source, target_task_id=target)

        return builder.build()

    async def run(self, **inputs: Any) -> Any:
        """
        Run the workflow with the provided inputs.

        Args:
            **inputs: Input parameters for the workflow

        Returns:
            Output from the last task in the workflow

        Raises:
            ValueError: If the workflow has no tasks
        """
        # Lazy import to avoid circular imports
        from pepperpy.orchestration.orchestrator import WorkflowOrchestrator

        # Create orchestrator if needed
        if not self._orchestrator:
            self._orchestrator = WorkflowOrchestrator()
            await self._orchestrator.initialize()

        # Build workflow if needed
        if not self._workflow:
            self._workflow = await self._build_workflow()

        # Execute workflow
        execution = await self._orchestrator.execute(
            self._workflow, inputs=inputs, wait=True
        )

        # Check execution status
        if execution is None:
            raise RuntimeError("Workflow execution failed: execution is None")

        if execution.status is None or execution.status.value != "COMPLETED":
            error_msg = (
                execution.error
                if execution and hasattr(execution, "error")
                else "Unknown error"
            )
            logger.error(f"Workflow execution failed: {error_msg}")
            raise RuntimeError(f"Workflow execution failed: {error_msg}")

        # Return results
        if execution and hasattr(execution, "outputs") and execution.outputs:
            return execution.outputs
        return None

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a task based on input data.

        Args:
            input_data: Dictionary containing task name and parameters

        Returns:
            Task execution result

        Raises:
            ValueError: If task name is not provided or not found
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")

        # Get task name
        task_name = input_data.get("task")
        if not task_name:
            raise ValueError("Task name must be provided in the input data")

        # Find task function
        task_func = self._tasks.get(task_name)
        if not task_func:
            available_tasks = list(self._tasks.keys())
            raise ValueError(
                f"Task '{task_name}' not found. Available tasks: {available_tasks}"
            )

        # Extract parameters (removing task name)
        params = {k: v for k, v in input_data.items() if k != "task"}

        # Execute task
        logger.info(f"Executing task '{task_name}' with parameters: {params}")
        result = await task_func(**params)

        # Ensure result is a dictionary
        if result is None:
            result = {"status": "success"}
        elif not isinstance(result, dict):
            result = {"result": result, "status": "success"}

        return result

    def get_available_tasks(self) -> list[dict[str, str]]:
        """
        Get information about available tasks.

        Returns:
            List of task information dictionaries
        """
        tasks = []
        for name, func in self._tasks.items():
            description = getattr(func, "__task_description__", "") or ""
            if description and isinstance(description, str):
                description = description.strip()

            tasks.append({"name": name, "description": description})
        return tasks

    async def initialize(self) -> None:
        """Initialize the workflow. Override in subclasses if needed."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._orchestrator:
            await self._orchestrator.cleanup()
            self._orchestrator = None

    async def __aenter__(self):
        """Async context manager enter."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


class SimpleTask:
    """
    Simple task that can be chained to create workflows.

    Example:
        ```python
        # Define tasks
        @SimpleTask
        async def fetch_document(url: str) -> dict:
            return {"content": "Document content", "metadata": {"url": url}}

        @SimpleTask
        async def process_document(content: str, metadata: dict) -> dict:
            return {"processed_content": content.upper(), "metadata": metadata}

        # Chain tasks and run
        result = await fetch_document.then(process_document).run(url="https://example.com/doc")
        ```
    """

    def __init__(self, func: TaskFunction):
        """
        Initialize a simple task.

        Args:
            func: Task function
        """
        self.func = func
        self.next_task: SimpleTask | None = None

    def then(self, next_task: "SimpleTask") -> "SimpleTask":
        """
        Chain this task with another task.

        Args:
            next_task: The next task to execute

        Returns:
            The next task for further chaining
        """
        self.next_task = next_task
        return next_task

    async def run(self, **inputs: Any) -> Any:
        """
        Run this task and all chained tasks.

        Args:
            **inputs: Input parameters

        Returns:
            Result from the last task in the chain
        """
        result = await self.func(**inputs)

        if not self.next_task:
            return result

        # Convert result to kwargs for next task
        if isinstance(result, dict):
            next_inputs = result
        else:
            next_inputs = {"result": result}

        return await self.next_task.run(**next_inputs)

    def __call__(self, **inputs: Any) -> Any:
        """
        Call operator to run the task chain.

        Args:
            **inputs: Input parameters

        Returns:
            Result from the last task in the chain
        """
        return self.run(**inputs)


class WorkflowAdapter:
    """
    Generic adapter for workflow implementations.

    This class adapts SimpleWorkflow instances to be compatible with
    the plugin system. It handles initialization, execution, and cleanup.

    Example:
        ```python
        class MyWorkflowAdapter(WorkflowAdapter):
            async def initialize(self):
                await super().initialize()
                # Custom initialization

            async def execute(self, input_data):
                # Custom execution logic
                return await self.workflow.execute(input_data)
        ```
    """

    def __init__(self, workflow_class, **config):
        """
        Initialize the adapter with a workflow class.

        Args:
            workflow_class: The SimpleWorkflow subclass to adapt
            **config: Configuration options to pass to the workflow
        """
        self.workflow_class = workflow_class
        self.config = config
        self.workflow = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        # Create workflow instance
        self.workflow = self.workflow_class(**self.config)

        # Initialize workflow
        await self.workflow.initialize()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        if self.workflow:
            await self.workflow.cleanup()
            self.workflow = None

        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a workflow task.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        if not self.initialized:
            await self.initialize()

        if self.workflow is None:
            raise RuntimeError("Workflow was not properly initialized")

        return await self.workflow.execute(input_data)

    async def __aenter__(self):
        """Async context manager enter."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
