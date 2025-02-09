"""Runtime agent factory implementation.

This module provides factory methods for creating and configuring runtime agents
with proper resource initialization and validation.
"""

from typing import Any
from uuid import UUID

from pepperpy.core.errors import FactoryError
from pepperpy.monitoring.logger import get_logger
from pepperpy.runtime.context import ExecutionContext

logger = get_logger(__name__)


class AgentFactory:
    """Factory for creating and configuring runtime agents.

    Handles agent creation, configuration validation, resource initialization,
    and monitoring integration.
    """

    def __init__(self) -> None:
        """Initialize the agent factory."""
        self._contexts: dict[UUID, ExecutionContext] = {}

    def create_agent(
        self, agent_type: type[Any], config: dict[str, Any] | None = None, **kwargs: Any
    ) -> UUID:
        """Create a new agent instance with the given configuration.

        Args:
            agent_type: The type of agent to create
            config: Optional configuration dictionary
            **kwargs: Additional keyword arguments for agent creation

        Returns:
            The UUID of the created agent

        Raises:
            FactoryError: If agent creation or validation fails
        """
        try:
            # Validate configuration
            validated_config = self._validate_config(agent_type, config or {})

            # Create execution context
            context = ExecutionContext()

            # Initialize agent instance
            agent_type(context=context, config=validated_config, **kwargs)

            # Initialize resources
            self._initialize_resources(context, validated_config)

            # Store context
            self._contexts[context.context_id] = context

            logger.info(
                f"Created agent {context.context_id} of type {agent_type.__name__}"
            )
            return context.context_id

        except Exception as e:
            raise FactoryError(
                message=f"Failed to create agent: {e!s}",
                component_type="agent",
            ) from e

    def get_agent(self, agent_id: UUID) -> ExecutionContext:
        """Retrieve an agent's execution context.

        Args:
            agent_id: The UUID of the agent to retrieve

        Returns:
            The agent's execution context

        Raises:
            FactoryError: If the agent is not found
        """
        if agent_id not in self._contexts:
            raise FactoryError(
                message=f"Agent {agent_id} not found",
                component_type="agent",
            )

        return self._contexts[agent_id]

    def _validate_config(
        self, agent_type: type[Any], config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate agent configuration against schema.

        Args:
            agent_type: The agent class type
            config: The configuration to validate

        Returns:
            Validated configuration dictionary

        Raises:
            FactoryError: If validation fails or result is not a dictionary
        """
        try:
            # Get validation schema from agent type
            schema = getattr(agent_type, "config_schema", None)
            if schema is None:
                logger.warning(
                    f"No config schema found for {agent_type.__name__}, "
                    "skipping validation"
                )
                return dict(config)  # Ensure we return a dict[str, Any]

            # Validate against schema
            validated = schema.validate(config)
            if not isinstance(validated, dict):
                raise FactoryError(
                    f"Schema validation returned {type(validated)}, expected dict",
                    component_type="agent",
                )
            return validated

        except Exception as e:
            raise FactoryError(
                f"Configuration validation failed: {e!s}", component_type="agent"
            ) from e

    def _initialize_resources(
        self, context: ExecutionContext, config: dict[str, Any]
    ) -> None:
        """Initialize agent resources based on configuration.

        Args:
            context: The agent's execution context
            config: The validated configuration

        Raises:
            FactoryError: If resource initialization fails
        """
        try:
            # Get resource definitions from config
            resources = config.get("resources", {})

            # Initialize each resource
            for resource_id, resource_config in resources.items():
                handler = self._create_resource(resource_config)
                context.add_resource(resource_id, handler)

            logger.debug(f"Initialized resources for agent {context.context_id}")

        except Exception as e:
            raise FactoryError(
                f"Resource initialization failed: {e!s}", component_type="resource"
            ) from e

    def _create_resource(self, config: dict[str, Any]) -> Any:
        """Create a resource handler from configuration.

        Args:
            config: Resource configuration

        Returns:
            The created resource handler

        Raises:
            FactoryError: If resource creation fails
        """
        try:
            # Get resource type and configuration
            resource_type = config.get("type")
            if resource_type is None:
                raise ValueError("Resource type not specified")

            # Import and instantiate resource class
            module_path, class_name = resource_type.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            resource_class = getattr(module, class_name)

            # Create resource instance
            return resource_class(**config.get("config", {}))

        except Exception as e:
            raise FactoryError(
                f"Failed to create resource: {e!s}", component_type="resource"
            ) from e
