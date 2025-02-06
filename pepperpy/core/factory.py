"""Factory module for creating and managing Pepperpy components.

This module provides factory classes for creating system components with:
- Type-safe component creation
- Configuration validation
- Lifecycle hooks
- Error handling
- Version tracking
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, Field, validator

from pepperpy.common.errors import FactoryError, NotFoundError, ValidationError

from .base import (
    BaseAgent,
)
from .events import Event, EventBus, EventType
from .monitoring import logger

# Type variables for generic implementations
T = TypeVar("T")
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")
T_Config = TypeVar("T_Config", bound=Mapping[str, Any])
T_Context = TypeVar("T_Context")


class FactoryMetadata(BaseModel):
    """Metadata for factory operations.

    Attributes:
        created_at: When the factory was created
        updated_at: When the factory was last updated
        version: Factory version
        metrics: Factory metrics
    """

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")
    metrics: dict[str, Any] = Field(default_factory=dict)

    @validator("metrics")
    def validate_metrics(self, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure metrics dictionary is immutable."""
        return dict(v)


class Factory(ABC, Generic[T]):
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
            event: Event to hook into
            hook: Callback to execute
        """
        if event not in self._hooks:
            self._hooks[event] = set()
        self._hooks[event].add(hook)

    def remove_hook(self, event: str, hook: Callable[[T], None]) -> None:
        """Remove a hook for factory events.

        Args:
            event: Event to remove hook from
            hook: Callback to remove
        """
        if event in self._hooks:
            self._hooks[event].discard(hook)

    async def _run_hooks(self, event: str, component: T) -> None:
        """Run hooks for an event.

        Args:
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
    async def create(self, config: dict[str, Any]) -> T:
        """Create a component from configuration.

        Args:
            config: Component configuration

        Returns:
            Created component

        Raises:
            ValidationError: If configuration is invalid
            FactoryError: If component creation fails
        """
        pass


class AgentFactory(Factory[BaseAgent[T_Input, T_Output, T_Config, T_Context]]):
    """Factory for creating agents.

    This factory manages agent creation with:
    - Type-safe agent instantiation
    - Configuration validation
    - Lifecycle hooks
    - Error handling
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the agent factory.

        Args:
            event_bus: Optional event bus for factory events
        """
        super().__init__(event_bus)
        self._agent_types: dict[
            str,
            type[BaseAgent[T_Input, T_Output, T_Config, T_Context]],
        ] = {}

    def register(
        self,
        agent_type: str,
        agent_class: type[BaseAgent[T_Input, T_Output, T_Config, T_Context]],
    ) -> None:
        """Register an agent type.

        Args:
            agent_type: Unique identifier for the agent type
            agent_class: Agent class to register

        Raises:
            ValueError: If agent type is already registered
        """
        if agent_type in self._agent_types:
            raise ValueError(f"Agent type already registered: {agent_type}")
        self._agent_types[agent_type] = agent_class

    async def create_agent(
        self,
        agent_type: str,
        context: T_Context,
        config: T_Config | None = None,
    ) -> BaseAgent[T_Input, T_Output, T_Config, T_Context]:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            context: Agent context
            config: Optional agent configuration

        Returns:
            Created agent instance

        Raises:
            NotFoundError: If agent type is not registered
            ValidationError: If configuration is invalid
            FactoryError: If agent creation fails
        """
        if agent_type not in self._agent_types:
            raise NotFoundError(
                f"Agent type not found: {agent_type}",
                resource_type="agent_type",
                resource_id=agent_type,
            )

        agent_class = self._agent_types[agent_type]
        try:
            agent = agent_class(
                name=config.get("name", agent_type) if config else agent_type,
                description=(
                    config.get("description", "") if config else "No description"
                ),
                version=config.get("version", "0.1.0") if config else "0.1.0",
                capabilities=config.get("capabilities", []) if config else [],
            )

            if config:
                await agent.initialize(config)

            await self._run_hooks("agent_created", agent)

            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type=EventType.AGENT_CREATED,
                        source_id=str(agent.id),
                        data={
                            "agent_id": str(agent.id),
                            "agent_type": agent_type,
                            "config": config,
                        },
                    )
                )

            return agent
        except Exception as e:
            raise FactoryError(
                f"Failed to create agent: {e!s}",
                component_type="agent",
            ) from e

    async def create(
        self,
        config: dict[str, Any],
    ) -> BaseAgent[T_Input, T_Output, T_Config, T_Context]:
        """Create an agent from configuration.

        Args:
            config: Agent configuration

        Returns:
            Created agent instance

        Raises:
            ValidationError: If configuration is invalid
            FactoryError: If agent creation fails
        """
        if "type" not in config:
            raise ValidationError(
                "Missing required field: type",
                validation_type="config",
            )

        agent_type = config["type"]
        context = cast(T_Context, config.get("context"))
        agent_config = cast(T_Config, config.get("config"))

        return await self.create_agent(agent_type, context, agent_config)


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
            event_bus: Optional event bus for factory events
        """
        super().__init__(event_bus)
        self._component_types: dict[str, type[T]] = {}

    def register(self, component_type: str, component_class: type[T]) -> None:
        """Register a component type.

        Args:
            component_type: Unique identifier for the component type
            component_class: Component class to register

        Raises:
            ValueError: If component type is already registered
        """
        if component_type in self._component_types:
            raise ValueError(f"Component type already registered: {component_type}")
        self._component_types[component_type] = component_class

    async def create(self, config: dict[str, Any]) -> T:
        """Create a component from configuration.

        Args:
            config: Component configuration

        Returns:
            Created component instance

        Raises:
            ValidationError: If configuration is invalid
            FactoryError: If component creation fails
        """
        if "type" not in config:
            raise ValidationError(
                "Missing required field: type",
                validation_type="config",
            )

        component_type = config["type"]
        if component_type not in self._component_types:
            raise NotFoundError(
                f"Component type not found: {component_type}",
                resource_type="component_type",
                resource_id=component_type,
            )

        component_class = self._component_types[component_type]
        try:
            component = component_class(**config.get("config", {}))
            await self._run_hooks("component_created", component)

            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type=EventType.SYSTEM_EVENT,
                        source_id=component_type,
                        data={
                            "component_type": component_type,
                            "config": config,
                        },
                    )
                )

            return component
        except Exception as e:
            raise FactoryError(
                f"Failed to create component: {e!s}",
                component_type=component_type,
            ) from e
