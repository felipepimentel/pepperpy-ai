"""@file: base.py
@purpose: Core base interfaces and classes for the Pepperpy framework
@component: Core
@created: 2024-02-15
@task: TASK-003
@status: active
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, Union
from uuid import UUID, uuid4

from pepperpy.core.errors import ComponentError, StateError
from pepperpy.core.metrics import MetricsManager
from pepperpy.core.metrics.types import (
    MetricCounter,
    MetricHistogram,
    MetricLabels,
    MetricType,
    MetricValue,
)
from pepperpy.core.protocols.lifecycle import Lifecycle
from pepperpy.core.types import (
    AgentID,
    AgentState,
    CapabilityID,
    ComponentState,
    ProviderID,
    ResourceID,
    WorkflowID,
)
from pepperpy.utils.imports import lazy_import

# Import prometheus_client safely
prometheus_client = lazy_import("prometheus_client")

# Type aliases for metrics
if prometheus_client:
    PrometheusCounter = prometheus_client.Counter
    PrometheusHistogram = prometheus_client.Histogram
else:
    # Use core metrics when prometheus_client is not available
    PrometheusCounter = MetricCounter
    PrometheusHistogram = MetricHistogram

# Type aliases for metrics
MetricType = Any  # Base type for all metrics
CounterType = MetricType  # Type for counters
HistogramType = MetricType  # Type for histograms

# Type aliases for metrics
if TYPE_CHECKING:
    # Forward references for type checking
    AnyCounter = "MetricCounter"
    AnyHistogram = "MetricHistogram"
else:
    # Runtime type aliases
    AnyCounter = MetricCounter
    AnyHistogram = MetricHistogram


# Type Aliases
ComponentID = Union[
    AgentID,
    ProviderID,
    ResourceID,
    CapabilityID,
    WorkflowID,
]


class Metadata:
    """Component metadata."""

    def __init__(
        self,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: str | None = None,
        tags: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Initialize metadata.

        Args:
            created_at: Creation timestamp
            updated_at: Last update timestamp
            version: Component version
            tags: Component tags
            properties: Additional properties
        """
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.version = version or "0.1.0"
        self.tags = tags or []
        self.properties = properties or {}


@dataclass
class AgentContext:
    """Context for agent execution."""

    agent_id: AgentID
    state: AgentState
    start_time: datetime
    end_time: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentCallback(Protocol):
    """Protocol for agent execution callbacks."""

    async def on_start(self, context: AgentContext) -> None:
        """Called when agent execution starts.

        Args:
            context: Agent execution context
        """
        ...

    async def on_pause(self, context: AgentContext) -> None:
        """Called when agent execution is paused.

        Args:
            context: Agent execution context
        """
        ...

    async def on_resume(self, context: AgentContext) -> None:
        """Called when agent execution resumes.

        Args:
            context: Agent execution context
        """
        ...

    async def on_complete(self, context: AgentContext) -> None:
        """Called when agent execution completes successfully.

        Args:
            context: Agent execution context
        """
        ...

    async def on_error(self, context: AgentContext) -> None:
        """Called when agent execution fails.

        Args:
            context: Agent execution context
        """
        ...


class MetricsComponent(Protocol):
    """Protocol for components with metrics."""

    metrics: MetricsManager

    def _setup_metrics(self) -> None:
        """Set up metrics for the component."""
        ...

    def _observe_metric(self, metric: Any, value: MetricValue) -> None:
        """Safely observe a metric value.

        Args:
            metric: The metric to observe
            value: The value to record
        """
        if metric and hasattr(metric, "observe"):
            metric.observe(value)

    def _increment_counter(self, counter: Any, amount: MetricValue = 1) -> None:
        """Safely increment a counter.

        Args:
            counter: The counter to increment
            amount: The amount to increment by
        """
        if counter and hasattr(counter, "inc"):
            counter.inc(amount)


class BaseComponent(Lifecycle, MetricsComponent):
    """Base class for all components in the system.

    Attributes:
        name: Name of the component
        state: Current state of the component
        logger: Logger instance for the component
        metrics: Metrics manager for the component
    """

    def __init__(self, name: str, id: UUID | None = None) -> None:
        """Initialize the component.

        Args:
            name: Name of the component
            id: Optional UUID for the component
        """
        self.name = name
        self.id = id or uuid4()
        self._state = ComponentState.CREATED
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")
        self.metrics = MetricsManager()

        # Initialize metrics
        self._execution_counter = None
        self._execution_duration = None

    async def _setup_metrics(self) -> None:
        """Set up metrics for the component."""
        # Create metrics with labels
        labels: MetricLabels = {"component_id": str(self.id), "state": str(self.state)}

        # Create histogram for initialization duration
        self._execution_duration = await self.metrics.create_histogram(
            name="execution_duration_seconds",
            description="Time taken to execute the component",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels=labels,
        )

        # Create counter for errors
        self._execution_counter = await self.metrics.create_counter(
            name="errors_total",
            description="Total number of errors encountered",
            labels=labels,
        )

    @property
    def state(self) -> ComponentState:
        """Get the current state of the component."""
        return self._state

    @state.setter
    def state(self, value: ComponentState) -> None:
        """Set the state of the component.

        Args:
            value: New state value

        Raises:
            StateError: If the state transition is invalid
        """
        if not self._is_valid_transition(value):
            raise StateError(f"Invalid state transition from {self.state} to {value}")
        self._state = value

    def _is_valid_transition(self, new_state: ComponentState) -> bool:
        """Check if a state transition is valid.

        Args:
            new_state: Target state

        Returns:
            bool: True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            ComponentState.CREATED: {ComponentState.INITIALIZING},
            ComponentState.INITIALIZING: {ComponentState.READY, ComponentState.ERROR},
            ComponentState.READY: {ComponentState.EXECUTING, ComponentState.CLEANING},
            ComponentState.EXECUTING: {
                ComponentState.READY,
                ComponentState.ERROR,
                ComponentState.CLEANING,
            },
            ComponentState.ERROR: {ComponentState.CLEANING},
            ComponentState.CLEANING: {ComponentState.CLEANED},
        }

        return new_state in valid_transitions.get(self.state, set())

    async def initialize(self) -> None:
        """Initialize the component.

        This method handles the initialization lifecycle, including:
        1. State transition to INITIALIZING
        2. Setting up metrics
        3. Running component-specific initialization
        4. Transitioning to READY state

        Raises:
            ComponentError: If initialization fails
        """
        try:
            self.state = ComponentState.INITIALIZING
            await self._setup_metrics()
            await self._initialize()
            self.state = ComponentState.READY
        except Exception as e:
            self.state = ComponentState.ERROR
            raise ComponentError(f"Failed to initialize {self.name}: {e}") from e

    async def cleanup(self) -> None:
        """Clean up the component.

        This method handles the cleanup lifecycle, including:
        1. State transition to CLEANING
        2. Running component-specific cleanup
        3. Transitioning to CLEANED state

        Raises:
            ComponentError: If cleanup fails
        """
        try:
            self.state = ComponentState.CLEANING
            await self._cleanup()
            self.state = ComponentState.CLEANED
        except Exception as e:
            self.state = ComponentState.ERROR
            raise ComponentError(f"Failed to clean up {self.name}: {e}") from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Component-specific initialization.

        This method should be implemented by subclasses to perform
        any necessary initialization.
        """
        ...

    @abstractmethod
    async def _cleanup(self) -> None:
        """Component-specific cleanup.

        This method should be implemented by subclasses to perform
        any necessary cleanup.
        """
        ...


class BaseProvider(BaseComponent):
    """Base class for service providers."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the service."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the service."""
        ...


class BaseAgent(BaseComponent):
    """Base class for agents."""

    def __init__(
        self,
        id: UUID,
        metadata: Metadata | None = None,
        callback: AgentCallback | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            id: Agent UUID
            metadata: Optional agent metadata
            callback: Optional execution callback
        """
        super().__init__(name=str(id), id=id)
        self._metadata = metadata or Metadata()
        self._callback = callback
        self._context = AgentContext(
            agent_id=AgentID(str(id)),
            state=AgentState.CREATED,
            start_time=datetime.utcnow(),
        )

    @property
    def context(self) -> AgentContext:
        """Get the agent context."""
        return self._context

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the agent's task.

        Args:
            **kwargs: Task parameters
        """
        ...


class BaseResource(BaseComponent):
    """Base class for resources."""

    @abstractmethod
    async def load(self) -> Any:
        """Load the resource."""
        ...

    @abstractmethod
    async def save(self, data: Any) -> None:
        """Save the resource.

        Args:
            data: Data to save
        """
        ...


class BaseCapability(BaseComponent):
    """Base class for capabilities."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the capability.

        Args:
            **kwargs: Execution parameters
        """
        ...


class BaseWorkflow(BaseComponent):
    """Base class for workflows."""

    @abstractmethod
    async def start(self) -> None:
        """Start the workflow."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the workflow."""
        ...


T = TypeVar("T", bound=BaseComponent)


class Registry(Generic[T]):
    """Registry for managing components."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._items: dict[UUID, T] = {}

    def register(self, item: T) -> None:
        """Register an item.

        Args:
            item: Item to register
        """
        self._items[item.id] = item

    def unregister(self, id: UUID) -> None:
        """Unregister an item.

        Args:
            id: ID of item to unregister
        """
        self._items.pop(id, None)

    def get(self, id: UUID) -> T | None:
        """Get an item by ID.

        Args:
            id: Item ID

        Returns:
            The item or None if not found
        """
        return self._items.get(id)

    def list(self) -> list[T]:
        """List all registered items.

        Returns:
            List of registered items
        """
        return list(self._items.values())


@dataclass
class ComponentConfig:
    """Base component configuration."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    monitoring: dict[str, Any] = field(default_factory=dict)
    error_handling: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentContext:
    """Component execution context."""

    component_id: ComponentID
    state: ComponentState = ComponentState.INITIALIZING
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ComponentCallback(Protocol):
    """Protocol for component callbacks."""

    async def on_state_change(self, component_id: str, state: ComponentState) -> None:
        """Called when component state changes."""
        ...

    async def on_error(self, component_id: str, error: Exception) -> None:
        """Called when component encounters an error."""
        ...

    async def on_progress(self, component_id: str, progress: float) -> None:
        """Called when component progress updates."""
        ...


class ComponentBase(ABC):
    """Base class for all components."""

    def __init__(
        self,
        config: ComponentConfig | None = None,
        callback: ComponentCallback | None = None,
    ) -> None:
        """Initialize the component.

        Args:
            config: Optional component configuration
            callback: Optional component callback
        """
        self._config = config or ComponentConfig(name=self.__class__.__name__)
        self._callback = callback
        self._state = ComponentState.INITIALIZING
        self._context = ComponentContext(
            component_id=ComponentID(self.__class__.__name__),
            state=self._state,
        )
        self._metrics = MetricsManager()

        # Initialize metrics
        self._execution_counter = None
        self._execution_duration = None

    async def _setup_metrics(self) -> None:
        """Set up component metrics."""
        # Create metrics with labels
        labels = {
            "component_id": str(self._context.component_id),
            "state": str(self._state),
        }

        # Create histogram for execution duration
        self._execution_duration = await self._metrics.create_histogram(
            name="execution_duration_seconds",
            description="Time taken to execute the component",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels=labels,
        )

        # Create counter for errors
        self._execution_counter = await self._metrics.create_counter(
            name="errors_total",
            description="Total number of errors encountered",
            labels=labels,
        )

    async def _update_metrics(self, start_time: datetime, error: bool = False) -> None:
        """Update component metrics.

        Args:
            start_time: Start time of operation
            error: Whether an error occurred
        """
        duration = (datetime.utcnow() - start_time).total_seconds()
        if self._execution_duration:
            self._execution_duration.observe(duration)
        if error and self._execution_counter:
            self._execution_counter.inc()

    @property
    def state(self) -> ComponentState:
        """Get the current state."""
        return self._state

    async def set_state(self, value: ComponentState) -> None:
        """Set the component state.

        Args:
            value: New state value
        """
        self._state = value
        if self._callback:
            await self._callback.on_state_change(str(self._context.component_id), value)

    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            await self.set_state(ComponentState.INITIALIZING)
            await self._setup_metrics()
            await self._initialize()
            await self.set_state(ComponentState.READY)
        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the component.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result
        """
        start_time = datetime.utcnow()
        self._context.start_time = start_time
        error = False

        try:
            await self.set_state(ComponentState.EXECUTING)
            result = await self._execute(**kwargs)
            await self.set_state(ComponentState.READY)
            return result
        except Exception as e:
            error = True
            await self.set_state(ComponentState.ERROR)
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise
        finally:
            self._context.end_time = datetime.utcnow()
            await self._update_metrics(start_time, error)

    async def cleanup(self) -> None:
        """Clean up the component."""
        try:
            await self.set_state(ComponentState.CLEANING)
            await self._cleanup()
            await self.set_state(ComponentState.CLEANED)
        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise

    @abstractmethod
    async def _initialize(self) -> None:
        """Component-specific initialization.

        This method should be implemented by subclasses to perform
        any necessary initialization.
        """
        ...

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Component-specific execution.

        This method should be implemented by subclasses to perform
        the component's main functionality.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result
        """
        ...

    @abstractmethod
    async def _cleanup(self) -> None:
        """Component-specific cleanup.

        This method should be implemented by subclasses to perform
        any necessary cleanup.
        """
        ...


__all__ = [
    "AgentCallback",
    "AgentContext",
    "BaseAgent",
    "BaseCapability",
    "BaseComponent",
    "BaseProvider",
    "BaseResource",
    "BaseWorkflow",
    "ComponentBase",
    "ComponentCallback",
    "ComponentConfig",
    "ComponentContext",
    "ComponentID",
    "Metadata",
    "MetricsComponent",
    "Registry",
]
