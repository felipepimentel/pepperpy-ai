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
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, Union, cast
from uuid import UUID, uuid4

from pepperpy.core.metrics.base import MetricsManager
from pepperpy.core.metrics.types import (
    MetricCounter,
    MetricHistogram,
    MetricLabels,
    MetricType,
    MetricValue,
)
from pepperpy.core.types import (
    AgentID,
    AgentState,
    CapabilityID,
    ComponentState,
    Lifecycle,
    ProviderID,
    ResourceID,
    WorkflowID,
)
from pepperpy.utils.imports import lazy_import

if TYPE_CHECKING:
    from pepperpy.core.errors import ComponentError, StateError
else:
    ComponentError = lazy_import("pepperpy.core.errors", "ComponentError")
    StateError = lazy_import("pepperpy.core.errors", "StateError")

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
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
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
        self._init_duration = None  # type: Any
        self._cleanup_duration = None  # type: Any
        self._error_count = None  # type: Any

    async def _setup_metrics(self) -> None:
        """Set up metrics for the component."""
        # Create metrics with labels
        labels: MetricLabels = {"component_id": str(self.id), "state": str(self.state)}

        # Create histogram for initialization duration
        self._init_duration = await self.metrics.create_histogram(
            name="init_duration_seconds",
            description="Time taken to initialize the component",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels=labels,
        )

        # Create histogram for cleanup duration
        self._cleanup_duration = await self.metrics.create_histogram(
            name="cleanup_duration_seconds",
            description="Time taken to cleanup the component",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels=labels,
        )

        # Create counter for errors
        self._error_count = await self.metrics.create_counter(
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
            value: New state

        Raises:
            StateError: If the state transition is invalid
        """
        if not self._is_valid_transition(value):
            raise StateError(f"Invalid state transition from {self._state} to {value}")
        self._state = value

    def _is_valid_transition(self, new_state: ComponentState) -> bool:
        """Check if a state transition is valid.

        Args:
            new_state: State to transition to

        Returns:
            True if the transition is valid, False otherwise
        """
        if self._state == ComponentState.CREATED:
            return new_state == ComponentState.INITIALIZING
        elif self._state == ComponentState.INITIALIZING:
            return new_state in (ComponentState.READY, ComponentState.ERROR)
        elif self._state == ComponentState.READY:
            return new_state in (
                ComponentState.CLEANING,
                ComponentState.ERROR,
                ComponentState.EXECUTING,
            )
        elif self._state == ComponentState.ERROR:
            return new_state == ComponentState.CLEANING
        elif self._state == ComponentState.CLEANING:
            return new_state in (ComponentState.CLEANED, ComponentState.ERROR)
        elif self._state == ComponentState.EXECUTING:
            return new_state in (ComponentState.READY, ComponentState.ERROR)
        return False

    async def initialize(self) -> None:
        """Initialize the component.

        This method should be overridden by subclasses to perform any necessary
        initialization. The base implementation handles state transitions and
        metrics.

        Raises:
            ComponentError: If initialization fails
            StateError: If the component is in an invalid state
        """
        if self.state != ComponentState.CREATED:
            raise StateError("Component must be in CREATED state to initialize")

        self.state = ComponentState.INITIALIZING
        try:
            await self._setup_metrics()
            self._observe_metric(self._init_duration, 0.0)  # Start timing
            await self._initialize()
            self._observe_metric(self._init_duration, 1.0)  # End timing
            self.state = ComponentState.READY
        except Exception as e:
            self.state = ComponentState.ERROR
            self._increment_counter(self._error_count)
            raise ComponentError(f"Failed to initialize {self.name}") from e

    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be overridden by subclasses to perform any necessary
        cleanup. The base implementation handles state transitions and metrics.

        Raises:
            ComponentError: If cleanup fails
            StateError: If the component is in an invalid state
        """
        if self.state not in (ComponentState.READY, ComponentState.ERROR):
            raise StateError("Component must be in READY or ERROR state to cleanup")

        self.state = ComponentState.CLEANING
        try:
            self._observe_metric(self._cleanup_duration, 0.0)  # Start timing
            await self._cleanup()
            self._observe_metric(self._cleanup_duration, 1.0)  # End timing
            self.state = ComponentState.CLEANED
        except Exception as e:
            self.state = ComponentState.ERROR
            self._increment_counter(self._error_count)
            raise ComponentError(f"Failed to cleanup {self.name}") from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the component.

        This method must be implemented by subclasses to perform any necessary
        initialization.
        """
        ...

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up the component.

        This method must be implemented by subclasses to perform any necessary
        cleanup.
        """
        ...


class BaseProvider(BaseComponent):
    """Base class for all providers."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the provider."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the provider."""
        ...


class BaseAgent(BaseComponent):
    """Base class for all agents."""

    def __init__(
        self,
        id: UUID,
        metadata: Metadata | None = None,
        callback: AgentCallback | None = None,
    ) -> None:
        """Initialize agent.

        Args:
            id: Agent ID
            metadata: Optional metadata
            callback: Optional callback
        """
        super().__init__(name=str(id))  # Convert UUID to string
        self._callback = callback
        self._context = AgentContext(
            agent_id=id,  # UUID is already AgentID
            state=AgentState.IDLE,
            start_time=datetime.utcnow(),
        )

    @property
    def context(self) -> AgentContext:
        """Get the agent's execution context."""
        return self._context

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the agent's main functionality."""
        ...


class BaseResource(BaseComponent):
    """Base class for all resources."""

    @abstractmethod
    async def load(self) -> Any:
        """Load the resource data."""
        ...

    @abstractmethod
    async def save(self, data: Any) -> None:
        """Save the resource data."""
        ...


class BaseCapability(BaseComponent):
    """Base class for all capabilities."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the capability."""
        ...


class BaseWorkflow(BaseComponent):
    """Base class for all workflows."""

    @abstractmethod
    async def start(self) -> None:
        """Start the workflow."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the workflow."""
        ...


# Generic Types


T = TypeVar("T")


class Registry(Generic[T]):
    """Generic registry for managing framework components."""

    def __init__(self) -> None:
        self._items: dict[UUID, T] = {}

    def register(self, item: T) -> None:
        """Register a new item."""
        if not isinstance(item, BaseComponent):
            raise TypeError("Item must be a BaseComponent")
        self._items[item.id] = item

    def unregister(self, id: UUID) -> None:
        """Unregister an item."""
        if id in self._items:
            del self._items[id]

    def get(self, id: UUID) -> T | None:
        """Get an item by ID."""
        return self._items.get(id)

    def list(self) -> list[T]:
        """List all registered items."""
        return list(self._items.values())


# Expose public interface
__all__ = [
    # Protocols
    "Identifiable",
    "Validatable",
    # Data classes
    "Metadata",
    "AgentContext",
    # Enums
    "AgentState",
    # Base classes
    "BaseComponent",
    "BaseProvider",
    "BaseAgent",
    "BaseResource",
    "BaseCapability",
    "BaseWorkflow",
    # Protocols
    "AgentCallback",
    # Generic types
    "Registry",
    # Type aliases
    "ComponentID",
]


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
        """Called when component makes progress."""
        ...


class ComponentBase(ABC):
    """Base class for all components."""

    def __init__(
        self,
        config: ComponentConfig | None = None,
        callback: ComponentCallback | None = None,
    ) -> None:
        """Initialize component.

        Args:
            config: Component configuration
            callback: Component callback
        """
        self._config = config or ComponentConfig(name=self.__class__.__name__)
        self._callback = callback
        self._state = ComponentState.INITIALIZING
        self._context = ComponentContext(
            component_id=cast(ComponentID, uuid4()),
            state=self._state,
        )
        self._metrics = MetricsManager()

        # Initialize metrics as None
        self._execution_counter: MetricCounter | None = None
        self._execution_duration: MetricHistogram | None = None

    async def _setup_metrics(self) -> None:
        """Set up metrics for the component."""
        # Create metrics
        self._execution_counter = await self._metrics.create_counter(
            name="component_executions_total",
            description="Total number of component executions",
            labels={"component_id": str(id(self))},
        )
        self._execution_duration = await self._metrics.create_histogram(
            name="component_execution_duration_seconds",
            description="Duration of component executions",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels={"component_id": str(id(self))},
        )

    def _update_metrics(self, start_time: datetime, error: bool = False) -> None:
        """Update metrics after execution.

        Args:
            start_time: Start time of execution
            error: Whether an error occurred
        """
        if not self._execution_counter or not self._execution_duration:
            return

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Update metrics
        self._execution_counter.inc()
        self._execution_duration.observe(duration)

    @property
    def state(self) -> ComponentState:
        """Get current component state."""
        return self._state

    async def set_state(self, value: ComponentState) -> None:
        """Set component state and notify callback."""
        if value != self._state:
            self._state = value
            if self._callback:
                await self._callback.on_state_change(
                    str(self._context.component_id), value
                )

    async def initialize(self) -> None:
        """Initialize component resources."""
        try:
            # Initialize component
            await self._initialize()
            await self.set_state(ComponentState.READY)

        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise ComponentError(f"Failed to initialize component: {e}")

    async def execute(self, **kwargs: Any) -> Any:
        """Execute component's main functionality.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result

        Raises:
            ComponentError: If execution fails
            StateError: If component is not in valid state
        """
        if self.state != ComponentState.READY:
            raise StateError(f"Component not ready (state: {self.state})")

        start_time = datetime.utcnow()
        await self.set_state(ComponentState.EXECUTING)

        try:
            # Execute component
            result = await self._execute(**kwargs)

            # Update metrics
            await self._update_metrics(start_time)

            await self.set_state(ComponentState.READY)
            return result

        except Exception as e:
            # Update metrics with error labels
            await self._update_metrics(start_time, error=True)

            await self.set_state(ComponentState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise ComponentError(f"Failed to execute component: {e}")

    async def cleanup(self) -> None:
        """Clean up component resources."""
        try:
            await self._cleanup()
            await self.set_state(ComponentState.CLEANED)

        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            self._context.error = e
            if self._callback:
                await self._callback.on_error(str(self._context.component_id), e)
            raise ComponentError(f"Failed to clean up component: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize component.

        This method should be implemented by subclasses to perform
        component-specific initialization.
        """
        pass

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Execute component implementation.

        This method should be implemented by subclasses to perform
        component-specific execution.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution result
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up component implementation.

        This method should be implemented by subclasses to perform
        component-specific cleanup.
        """
        pass
