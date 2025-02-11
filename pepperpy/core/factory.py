"""Factory module for creating and managing Pepperpy components.

This module provides factory classes for creating system components with:
- Type-safe component creation
- Configuration validation
- Lifecycle hooks
- Error handling
- Version tracking
"""

from abc import abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, Generic, Type, TypeVar

from pydantic import BaseModel, Field, field_validator

from pepperpy.core.errors import ConfigurationError, FactoryError, ValidationError

from .base import (
    BaseAgent,
)
from .events import Event, EventBus, EventType
from .monitoring import logger

# Type variables for generic implementations
T = TypeVar("T")
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")
T_Config = TypeVar("T_Config", bound=Dict[str, Any])
T_Context = TypeVar("T_Context")


class FactoryMetadata(BaseModel):
    """Metadata for factory operations.

    Attributes
    ----------
        created_at: When the factory was created
        updated_at: When the factory was last updated
        version: Factory version
        metrics: Factory metrics

    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")
    metrics: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    @field_validator("metrics")
    def validate_metrics(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metrics dictionary is immutable."""
        return dict(v)


class Factory(Generic[T]):
    """Base factory class for creating components.

    This class provides common functionality for component factories:
    - Event bus integration
    - Lifecycle hooks
    - Error handling
    - Metrics tracking
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the factory.

        Args:
        ----
            event_bus: Optional event bus for factory events

        """
        self._event_bus = event_bus
        self._hooks: dict[str, set[Callable[[T], None]]] = {}
        self._metadata = FactoryMetadata()

    @property
    def metadata(self) -> FactoryMetadata:
        """Get factory metadata."""
        return self._metadata

    def add_hook(self, event: str, hook: Callable[[T], None]) -> None:
        """Add a hook for factory events.

        Args:
        ----
            event: Event to hook into
            hook: Callback to execute

        """
        if event not in self._hooks:
            self._hooks[event] = set()
        self._hooks[event].add(hook)

    def remove_hook(self, event: str, hook: Callable[[T], None]) -> None:
        """Remove a hook for factory events.

        Args:
        ----
            event: Event to remove hook from
            hook: Callback to remove

        """
        if event in self._hooks:
            self._hooks[event].discard(hook)

    async def _run_hooks(self, event: str, component: T) -> None:
        """Run hooks for an event.

        Args:
        ----
            event: Event that occurred
            component: Component the event is for

        """
        if event in self._hooks:
            for hook in self._hooks[event]:
                try:
                    hook(component)
                except Exception as e:
                    logger.error(
                        "Hook failed",
                        event=event,
                        error=str(e),
                        component=str(component),
                    )

    @abstractmethod
    async def create(self, config: T_Config) -> T:
        """Create a component from configuration.

        Args:
        ----
            config: Component configuration

        Returns:
        -------
            Created component

        Raises:
        ------
            ValidationError: If configuration is invalid
            FactoryError: If component creation fails

        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up factory resources."""
        pass


class AgentFactory(Factory[BaseAgent]):
    """Factory for creating agent instances.

    This factory is responsible for creating and managing agent instances
    based on configuration.
    """

    def __init__(self, client: Any) -> None:
        """Initialize the agent factory.

        Args:
        ----
            client: The Pepperpy client instance

        """
        self.client = client
        self._agent_types: Dict[str, Type[BaseAgent]] = {}

    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type.

        Args:
        ----
            name: Name of the agent type
            agent_class: Agent class to register

        """
        self._agent_types[name] = agent_class
        logger.info(f"Registered agent type: {name}")

    async def create(self, config: T_Config) -> BaseAgent:
        """Create an agent instance.

        Args:
        ----
            config: Agent configuration

        Returns:
        -------
            Created agent instance

        Raises:
        ------
            ConfigurationError: If agent type is not supported

        """
        agent_type = config.get("type")
        if not agent_type:
            raise ConfigurationError("Agent type not specified")

        agent_class = self._agent_types.get(agent_type)
        if not agent_class:
            raise ConfigurationError(f"Unsupported agent type: {agent_type}")

        try:
            agent = agent_class(client=self.client, config=config)
            logger.info(f"Created agent of type: {agent_type}")
            return agent
        except Exception as e:
            logger.error(
                "Failed to create agent",
                error=str(e),
                agent_type=agent_type,
                config=config,
            )
            raise ConfigurationError(f"Failed to create agent: {e}") from e

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        self._agent_types.clear()
        logger.info("Agent factory cleaned up")


class ComponentFactory(Factory[T]):
    """Factory for creating generic components.

    This factory manages component creation with:
    - Type-safe component instantiation
    - Configuration validation
    - Lifecycle hooks
    - Error handling
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the component factory.

        Args:
        ----
            event_bus: Optional event bus for factory events

        """
        super().__init__(event_bus)
        self._component_types: dict[str, type[T]] = {}

    def register(self, component_type: str, component_class: type[T]) -> None:
        """Register a component type.

        Args:
        ----
            component_type: Unique identifier for the component type
            component_class: Component class to register

        Raises:
        ------
            ValueError: If component type is already registered

        """
        if component_type in self._component_types:
            raise ValueError(f"Component type already registered: {component_type}")
        self._component_types[component_type] = component_class

    async def create(self, config: dict[str, Any]) -> T:
        """Create a component from configuration.

        Args:
        ----
            config: Component configuration

        Returns:
        -------
            Created component instance

        Raises:
        ------
            ValidationError: If configuration is invalid
            FactoryError: If component creation fails

        """
        if "type" not in config:
            raise ValidationError(
                "Missing required field: type",
                details={"field": "type"},
            )

        component_type = config["type"]
        if component_type not in self._component_types:
            raise ValidationError(
                f"Component type not found: {component_type}",
                details={"component_type": component_type},
            )

        component_class = self._component_types[component_type]
        try:
            component = component_class(**config)
            await self._run_hooks("component_created", component)

            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type=EventType.COMPONENT_CREATED,
                        source_id=component_type,
                        data={"component_type": component_type, "config": config},
                    )
                )

            return component
        except Exception as e:
            raise FactoryError(
                f"Failed to create component: {e!s}",
                component_type=component_type,
            ) from e

    async def cleanup(self) -> None:
        """Clean up factory resources."""
        self._component_types.clear()
        logger.info("Component factory cleaned up")
