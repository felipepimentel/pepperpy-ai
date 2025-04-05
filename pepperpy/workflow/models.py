"""
PepperPy Workflow Models.

Models for workflow definitions, tasks, and executions.
"""

import inspect
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Status of a task execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ExecutionStatus(str, Enum):
    """Status of a workflow execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class Task:
    """Task definition for workflows.

    A task represents a single unit of work in a workflow,
    with defined inputs and outputs.
    """

    def __init__(
        self,
        id: str,
        name: str,
        function: Callable | None = None,
        description: str | None = None,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a task.

        Args:
            id: Task ID (unique within a workflow)
            name: Task name
            function: Optional function implementing the task
            description: Optional task description
            input_schema: Optional input schema
            output_schema: Optional output schema
            metadata: Optional metadata
        """
        self.id = id
        self.name = name
        self.function = function
        self.description = description or f"Task: {name}"
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        self.metadata = metadata or {}

    @classmethod
    def from_function(cls, func: Callable) -> "Task":
        """Create a task from a function.

        Args:
            func: Function to create task from

        Returns:
            Created task
        """
        # Get function name and docstring
        name = func.__name__
        description = func.__doc__ or f"Task: {name}"

        # Get function signature
        sig = inspect.signature(func)
        input_schema = {
            param.name: {
                "type": param.annotation.__name__
                if hasattr(param.annotation, "__name__")
                else "any"
            }
            for param in sig.parameters.values()
            if param.name != "self" and param.name != "cls"
        }

        # Get return type
        output_schema = {}
        if sig.return_annotation != inspect.Signature.empty:
            output_schema = {
                "type": sig.return_annotation.__name__
                if hasattr(sig.return_annotation, "__name__")
                else "any"
            }

        return cls(
            id=name,
            name=name.replace("_", " ").title(),
            function=func,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the task.

        Args:
            inputs: Task inputs

        Returns:
            Task outputs

        Raises:
            ValueError: If function is not set
        """
        if not self.function:
            raise ValueError(f"No function set for task '{self.id}'")

        result = await self.function(**inputs)

        # Convert to dict if not already
        if not isinstance(result, dict):
            result = {"result": result}

        return result


class WorkflowBuilder:
    """Builder for workflows."""

    def __init__(self):
        """Initialize builder."""
        self.id = None
        self.name = None
        self.description = None
        self.version = "1.0.0"
        self.tasks = {}
        self.edges = []
        self.metadata = {}

    def with_id(self, id: str) -> "WorkflowBuilder":
        """Set workflow ID.

        Args:
            id: Workflow ID

        Returns:
            Builder instance
        """
        self.id = id
        return self

    def with_name(self, name: str) -> "WorkflowBuilder":
        """Set workflow name.

        Args:
            name: Workflow name

        Returns:
            Builder instance
        """
        self.name = name
        return self

    def with_description(self, description: str) -> "WorkflowBuilder":
        """Set workflow description.

        Args:
            description: Workflow description

        Returns:
            Builder instance
        """
        self.description = description
        return self

    def with_version(self, version: str) -> "WorkflowBuilder":
        """Set workflow version.

        Args:
            version: Workflow version

        Returns:
            Builder instance
        """
        self.version = version
        return self

    def with_task(self, task: Task) -> "WorkflowBuilder":
        """Add a task to the workflow.

        Args:
            task: Task to add

        Returns:
            Builder instance
        """
        self.tasks[task.id] = task
        return self

    def with_edge(self, source_task_id: str, target_task_id: str) -> "WorkflowBuilder":
        """Add an edge between tasks.

        Args:
            source_task_id: Source task ID
            target_task_id: Target task ID

        Returns:
            Builder instance
        """
        self.edges.append((source_task_id, target_task_id))
        return self

    def with_metadata(self, key: str, value: Any) -> "WorkflowBuilder":
        """Add metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Builder instance
        """
        self.metadata[key] = value
        return self

    def build(self) -> "Workflow":
        """Build workflow.

        Returns:
            Built workflow

        Raises:
            ValueError: If required fields are missing
        """
        if not self.id:
            raise ValueError("Workflow ID is required")
        if not self.name:
            raise ValueError("Workflow name is required")

        return Workflow(
            id=self.id,
            name=self.name,
            description=self.description or f"Workflow: {self.name}",
            version=self.version,
            tasks=self.tasks,
            edges=self.edges,
            metadata=self.metadata,
        )


class Workflow:
    """Workflow definition.

    A workflow represents a directed acyclic graph (DAG) of tasks,
    with defined inputs and outputs.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        version: str,
        tasks: dict[str, Task],
        edges: list[tuple[str, str]],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a workflow.

        Args:
            id: Workflow ID
            name: Workflow name
            description: Workflow description
            version: Workflow version
            tasks: Dict of task ID to task
            edges: List of (source_task_id, target_task_id) tuples
            metadata: Optional metadata
        """
        self.id = id
        self.name = name
        self.description = description
        self.version = version
        self.tasks = tasks
        self.edges = edges
        self.metadata = metadata or {}

        # Compute dependency graph
        self.dependencies = {}
        self.dependents = {}

        for source, target in self.edges:
            if target not in self.dependencies:
                self.dependencies[target] = set()
            self.dependencies[target].add(source)

            if source not in self.dependents:
                self.dependents[source] = set()
            self.dependents[source].add(target)

        # Compute entry and exit tasks
        self.entry_tasks = {
            task_id
            for task_id in self.tasks
            if task_id not in self.dependencies or not self.dependencies[task_id]
        }

        self.exit_tasks = {
            task_id
            for task_id in self.tasks
            if task_id not in self.dependents or not self.dependents[task_id]
        }

    @classmethod
    def builder(cls) -> WorkflowBuilder:
        """Create a workflow builder.

        Returns:
            Workflow builder
        """
        return WorkflowBuilder()

    def get_task_dependencies(self, task_id: str) -> set[str]:
        """Get dependencies of a task.

        Args:
            task_id: Task ID

        Returns:
            Set of dependency task IDs
        """
        return self.dependencies.get(task_id, set())

    def get_task_dependents(self, task_id: str) -> set[str]:
        """Get dependents of a task.

        Args:
            task_id: Task ID

        Returns:
            Set of dependent task IDs
        """
        return self.dependents.get(task_id, set())

    def is_entry_task(self, task_id: str) -> bool:
        """Check if a task is an entry task.

        Args:
            task_id: Task ID

        Returns:
            True if task is an entry task
        """
        return task_id in self.entry_tasks

    def is_exit_task(self, task_id: str) -> bool:
        """Check if a task is an exit task.

        Args:
            task_id: Task ID

        Returns:
            True if task is an exit task
        """
        return task_id in self.exit_tasks


class TaskExecution:
    """Task execution.

    Represents a single execution of a task within a workflow.
    """

    def __init__(
        self,
        id: str,
        task_id: str,
        workflow_execution_id: str,
        status: TaskStatus = TaskStatus.PENDING,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ):
        """Initialize a task execution.

        Args:
            id: Task execution ID
            task_id: Task ID
            workflow_execution_id: Workflow execution ID
            status: Task status
            inputs: Task inputs
            outputs: Task outputs
            error: Error message if failed
            created_at: Creation timestamp
            started_at: Start timestamp
            completed_at: Completion timestamp
        """
        self.id = id
        self.task_id = task_id
        self.workflow_execution_id = workflow_execution_id
        self.status = status
        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.error = error
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at

    def is_terminal(self) -> bool:
        """Check if task is in a terminal state.

        Returns:
            True if task is in a terminal state
        """
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELED,
        )


class WorkflowExecution:
    """Workflow execution.

    Represents a single execution of a workflow.
    """

    def __init__(
        self,
        id: str,
        workflow_id: str,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        task_executions: dict[str, TaskExecution] | None = None,
    ):
        """Initialize a workflow execution.

        Args:
            id: Workflow execution ID
            workflow_id: Workflow ID
            status: Execution status
            inputs: Workflow inputs
            outputs: Workflow outputs
            error: Error message if failed
            created_at: Creation timestamp
            started_at: Start timestamp
            completed_at: Completion timestamp
            task_executions: Dict of task execution ID to task execution
        """
        self.id = id
        self.workflow_id = workflow_id
        self.status = status
        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.error = error
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at
        self.task_executions = task_executions or {}

    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state.

        Returns:
            True if execution is in a terminal state
        """
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELED,
        )

    def get_task_execution(self, task_id: str) -> TaskExecution | None:
        """Get task execution by task ID.

        Args:
            task_id: Task ID

        Returns:
            Task execution if found, None otherwise
        """
        for task_execution in self.task_executions.values():
            if task_execution.task_id == task_id:
                return task_execution
        return None
