"""Base interfaces for workflows
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from ..core.base.common import BaseComponent

Define the base interfaces and classes for the workflow system,
including definition, execution and management of workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID, uuid4

from pepperpy.core.base import (
    ComponentCallback,
    ComponentConfig,
    ComponentState,
)

# Removido: Redefinition of unused `ComponentState` from line 21
from pepperpy.core.errors import StateError, WorkflowError
from pepperpy.core.types import WorkflowID

# Removido: Redefinition of unused `ComponentState` from line 23
from pepperpy.observability.metrics.collector import (
    Counter,
    Histogram,
    MetricsCollector,
)
from pepperpy.observability.metrics.manager import MetricsRegistry as MetricsManager


class WorkflowState(str, Enum):
    """Workflow execution states."""

    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class WorkflowStepConfig:
    """Workflow step definition."""

    name: str
    description: str
    action: str
    agent: Optional[str] = None
    timeout: float = 60.0
    retry: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    id: str
    name: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dependency(self, step_id: str) -> None:
        """Add a dependency on another step.

        Args:
            step_id: ID of the step this step depends on

        """
        if step_id not in self.dependencies:
            self.dependencies.append(step_id)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the step.

        Args:
            key: Metadata key
            value: Metadata value

        """
        self.metadata[key] = value


@dataclass
class WorkflowConfig(ComponentConfig):
    """Workflow configuration."""

    steps: List[WorkflowStep] = field(default_factory=list)
    parallel: bool = False
    timeout: float = 3600.0
    retry: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """Workflow execution context."""

    workflow_id: WorkflowID
    state: WorkflowState = WorkflowState.INITIALIZING
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowCallback(ComponentCallback, Protocol):
    """Workflow callback interface."""

    async def on_state_change(self, workflow_id: str, state: ComponentState) -> None:
        """Called when workflow state changes."""

    async def on_step_start(self, workflow_id: str, step: str) -> None:
        """Called when workflow step starts."""

    async def on_step_complete(self, workflow_id: str, step: str, result: Any) -> None:
        """Called when workflow step completes."""

    async def on_error(self, workflow_id: str, error: Exception) -> None:
        """Called when workflow encounters an error."""

    async def on_progress(self, workflow_id: str, progress: float) -> None:
        """Called when workflow progress changes."""


class AbstractWorkflowStep(ABC):
    """Abstract base class for workflow steps."""

    def __init__(self, name: str) -> None:
        """Initialize step."""
        self.name = name

    @abstractmethod
    async def execute(self) -> Any:
        """Execute step."""
        ...


class AbstractWorkflowDefinition(ABC):
    """Abstract base class for workflow definitions."""

    def __init__(self, name: str) -> None:
        """Initialize workflow definition."""
        self.name = name
        self._steps: List[AbstractWorkflowStep] = []

    def add_step(self, step: AbstractWorkflowStep) -> None:
        """Add step to workflow."""
        self._steps.append(step)

    def get_steps(self) -> List[AbstractWorkflowStep]:
        """Get workflow steps."""
        return self._steps.copy()


class WorkflowDefinition:
    """Defines the structure of a workflow."""

    def __init__(self, name: str) -> None:
        """Initialize workflow definition.

        Args:
            name: Workflow name

        """
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow.

        Args:
            step: Step to add

        Raises:
            ValueError: If a step with the same ID already exists

        """
        if step.id in self.steps:
            raise ValueError(f"Step with ID '{step.id}' already exists")
        self.steps[step.id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID.

        Args:
            step_id: Step ID

        Returns:
            Step with the given ID, or None if not found

        """
        return self.steps.get(step_id)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the workflow.

        Args:
            key: Metadata key
            value: Metadata value

        """
        self.metadata[key] = value

    def validate(self) -> List[str]:
        """Validate workflow definition.

        Returns:
            List of validation errors, empty if valid

        """
        errors = []

        # Check for cycles in dependencies
        for step_id in self.steps:
            if self._has_cycle(step_id):
                errors.append(
                    f"Cycle detected in step dependencies for step '{step_id}'"
                )

        def check_cycle(step_id: str) -> bool:
            """Check if there is a cycle in the dependencies.

            Args:
                step_id: Step ID to check

            Returns:
                True if a cycle is detected, False otherwise

            """
            visited = set()
            path = set()

            def dfs(current_id: str) -> bool:
                """Depth-first search to detect cycles.

                Args:
                    current_id: Current step ID

                Returns:
                    True if a cycle is detected, False otherwise

                """
                if current_id in path:
                    return True
                if current_id in visited:
                    return False

                visited.add(current_id)
                path.add(current_id)

                step = self.steps.get(current_id)
                if step:
                    for dep_id in step.dependencies:
                        if dfs(dep_id):
                            return True

                path.remove(current_id)
                return False

            return dfs(step_id)

        return errors


class BaseWorkflow(ABC):
    """Abstract base class for workflows."""

    def __init__(
        self,
        definition: WorkflowDefinition,
        workflow_id: Optional[WorkflowID] = None,
    ) -> None:
        """Initialize workflow.

        Args:
            definition: Workflow definition
            workflow_id: Optional workflow ID

        """
        self._callback = None
        self._metrics = {}
        self._metrics_manager = None  # Will be initialized later
        self.definition = definition
        self.workflow_id = workflow_id or UUID(str(uuid4()))
        self._results: Dict[str, Any] = {}
        self._current_step: Optional[WorkflowStep] = None
        self._context = WorkflowContext(workflow_id=self.workflow_id)
        self._step_metrics: Dict[str, Union[Counter, Histogram]] = {}
        self._metrics_manager = MetricsManager.get_instance()
        self.metrics_collector = MetricsCollector(f"workflow_{self.workflow_id}")

        # Initialize metrics
        self.step_execution_time = self.metrics_collector.create_histogram(
            "step_execution_time", "Time taken to execute each step in seconds"
        )
        self.step_execution_count = self.metrics_collector.create_counter(
            "step_execution_count", "Number of steps executed"
        )
        self.workflow_execution_time = self.metrics_collector.create_histogram(
            "workflow_execution_time", "Time taken to execute the workflow in seconds"
        )
        self.error_count = self.metrics_collector.create_counter(
            "error_count", "Number of errors encountered during workflow execution"
        )
        self.retry_count = self.metrics_collector.create_counter(
            "retry_count", "Number of retries performed during workflow execution"
        )
        self.success_count = self.metrics_collector.create_counter(
            "success_count", "Number of successful workflow executions"
        )

    @property
    def state(self) -> WorkflowState:
        """Get current workflow state."""
        return self._context.state

    @property
    def current_step(self) -> Optional[str]:
        """Get current workflow step."""
        return self._context.current_step

    @property
    def steps(self) -> List[WorkflowStep]:
        """Get workflow steps."""
        if isinstance(self.definition, WorkflowDefinition):
            return (
                list(self.definition.steps.values())
                if hasattr(self.definition, "steps")
                else []
            )
        return []

    async def set_state(self, value: WorkflowState) -> None:
        """Set workflow state and notify callback."""
        if value != self._context.state:
            self._context.state = value
            if self._callback:
                await self._callback.on_state_change(str(self.workflow_id), value)

    async def initialize(self) -> None:
        """Initialize workflow resources."""
        try:
            # Initialize metrics
            self._metrics[
                "execution_count"
            ] = await self._metrics_manager.create_counter(
                name=f"workflow_{self.definition.name}_executions_total",
                description=f"Total number of executions for workflow {self.definition.name}",
                labels={"status": "success"},
            )
            self._metrics[
                "execution_time"
            ] = await self._metrics_manager.create_histogram(
                name=f"workflow_{self.definition.name}_execution_seconds",
                description=f"Execution time in seconds for workflow {self.definition.name}",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
            self._metrics["step_count"] = await self._metrics_manager.create_counter(
                name=f"workflow_{self.definition.name}_steps_total",
                description=f"Total number of steps executed for workflow {self.definition.name}",
                labels={"status": "success"},
            )
            self._metrics["step_time"] = await self._metrics_manager.create_histogram(
                name=f"workflow_{self.definition.name}_step_seconds",
                description=f"Step execution time in seconds for workflow {self.definition.name}",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )

            # Initialize step metrics
            for step in self.steps:
                self._step_metrics[
                    f"{step.name}_count"
                ] = await self._metrics_manager.create_counter(
                    name=f"{self.definition.name}_step_{step.name}_total",
                    description=f"Total number of executions for step {step.name}",
                    labels={"status": "success"},
                )
                self._step_metrics[
                    f"{step.name}_time"
                ] = await self._metrics_manager.create_histogram(
                    name=f"{self.definition.name}_step_{step.name}_seconds",
                    description=f"Execution time in seconds for step {step.name}",
                    labels={"status": "success"},
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
                )

            # Initialize workflow
            await self._initialize()
            await self.set_state(WorkflowState.READY)

        except Exception as e:
            await self.set_state(WorkflowState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self.workflow_id), e)
            raise WorkflowError(f"Failed to initialize workflow: {e}") from e

    async def execute(self, **kwargs: Any) -> Any:
        """Execute workflow's main functionality.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result

        Raises:
            WorkflowError: If execution fails
            StateError: If workflow is not in valid state

        """
        if self.state != WorkflowState.READY:
            raise StateError(f"Workflow not ready (state: {self.state})")

        start_time = datetime.utcnow()
        await self.set_state(WorkflowState.EXECUTING)

        try:
            # Execute workflow
            result = await self._execute(**kwargs)

            # Update metrics
            if isinstance(self._metrics["execution_count"], Counter):
                await self._metrics["execution_count"].inc()
            if isinstance(self._metrics["execution_time"], Histogram):
                await self._metrics["execution_time"].observe(
                    (datetime.utcnow() - start_time).total_seconds(),
                )

            await self.set_state(WorkflowState.READY)
            return result

        except Exception as e:
            # Update metrics with error labels
            error_counter = await self._metrics_manager.create_counter(
                name=f"workflow_{self.definition.name}_executions_total",
                description=f"Total number of executions for workflow {self.definition.name}",
                labels={"status": "error"},
            )
            error_histogram = await self._metrics_manager.create_histogram(
                name=f"workflow_{self.definition.name}_execution_seconds",
                description=f"Execution time in seconds for workflow {self.definition.name}",
                labels={"status": "error"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
            await error_counter.inc(1.0)
            await error_histogram.observe(
                (datetime.utcnow() - start_time).total_seconds(),
            )

            await self.set_state(WorkflowState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self.workflow_id), e)
            raise WorkflowError(f"Failed to execute workflow: {e}") from e

    async def execute_step(self, step: AbstractWorkflowStep, **kwargs: Any) -> Any:
        """Execute a single workflow step.

        Args:
            step: Step to execute
            **kwargs: Step parameters

        Returns:
            Step result

        Raises:
            WorkflowError: If step execution fails

        """
        if self.state != ComponentState.EXECUTING:
            raise StateError(f"Workflow not executing (state: {self.state})")

        start_time = datetime.utcnow()
        self._context.current_step = step.name

        try:
            # Notify step start
            if isinstance(self._callback, WorkflowCallback):
                await self._callback.on_step_start(str(self.workflow_id), step.name)

            # Execute step
            result = await self._execute_step(step, **kwargs)

            # Update metrics
            await self._step_metrics[f"{step.name}_count"].inc()
            await self._step_metrics[f"{step.name}_time"].observe(
                (datetime.utcnow() - start_time).total_seconds(),
            )

            # Notify step complete
            if isinstance(self._callback, WorkflowCallback):
                await self._callback.on_step_complete(
                    str(self.workflow_id),
                    step.name,
                    result,
                )

            return result

        except Exception as e:
            # Update metrics with error labels
            error_counter = await self._metrics_manager.create_counter(
                name=f"{self.definition.name}_step_{step.name}_total",
                description=f"Total number of executions for step {step.name}",
                labels={"status": "error"},
            )
            error_histogram = await self._metrics_manager.create_histogram(
                name=f"{self.definition.name}_step_{step.name}_seconds",
                description=f"Execution time in seconds for step {step.name}",
                labels={"status": "error"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )
            await error_counter.inc()
            await error_histogram.observe(
                (datetime.utcnow() - start_time).total_seconds(),
            )

            raise WorkflowError(f"Failed to execute step {step.name}: {e}") from e

        finally:
            self._context.current_step = None

    async def cleanup(self) -> None:
        """Clean up workflow resources."""
        try:
            await self._cleanup()
            await self.set_state(WorkflowState.TERMINATED)

        except Exception as e:
            await self.set_state(WorkflowState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self.workflow_id), e)
            raise WorkflowError(f"Failed to clean up workflow: {e}") from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize workflow implementation.

        This method should be implemented by subclasses to perform
        workflow-specific initialization.
        """

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Execute workflow implementation.

        This method should be implemented by subclasses to perform
        workflow-specific execution.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result

        """

    @abstractmethod
    async def _execute_step(self, step: AbstractWorkflowStep, **kwargs: Any) -> Any:
        """Execute step implementation.

        This method should be implemented by subclasses to perform
        step-specific execution.

        Args:
            step: Step to execute
            **kwargs: Step parameters

        Returns:
            Step result

        """

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up workflow implementation.

        This method should be implemented by subclasses to perform
        workflow-specific cleanup.
        """

    @abstractmethod
    async def start(self) -> None:
        """Start workflow execution."""
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Pause workflow execution."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Resume workflow execution."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop workflow execution."""
        ...
