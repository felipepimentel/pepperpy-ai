"""Security manager for the Pepperpy framework.

This module provides the security manager that handles security component
registration, lifecycle management, and security operations.
"""

from typing import Dict, List, Optional, Type, TypeVar

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.monitoring.metrics import MetricsManager
from pepperpy.security.base import (
    AuthenticationComponent,
    AuthorizationComponent,
    DataProtectionComponent,
    SecurityComponent,
    SecurityConfig,
)

# Configure logging
logger = logger.getChild(__name__)

# Type variables
T = TypeVar("T", bound=SecurityComponent)


class SecurityManager(Lifecycle):
    """Manager for security components.

    This class manages security component registration, initialization,
    and operations for the framework.
    """

    def __init__(self) -> None:
        """Initialize security manager."""
        super().__init__()
        self._components: Dict[str, SecurityComponent] = {}
        self._metrics = MetricsManager.get_instance()
        self._audit = AuditLogger()
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize security manager.

        This method initializes the security manager and all registered
        components.

        Raises:
            RuntimeError: If initialization fails
        """
        try:
            # Initialize metrics
            self._operation_counter = await self._metrics.create_counter(
                name="security_manager_operations_total",
                description="Total security manager operations",
            )
            self._error_counter = await self._metrics.create_counter(
                name="security_manager_errors_total",
                description="Total security manager errors",
            )

            # Initialize components
            for component in self._components.values():
                await component.initialize()

            self._state = ComponentState.RUNNING
            await self._audit.log({
                "event_type": "security.manager.initialized",
            })

        except Exception as e:
            self._state = ComponentState.ERROR
            await self._audit.log({
                "event_type": "security.manager.error",
                "error": str(e),
            })
            raise RuntimeError(f"Failed to initialize security manager: {e}")

    async def cleanup(self) -> None:
        """Clean up security manager.

        This method cleans up the security manager and all registered
        components.

        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            # Clean up components
            for component in self._components.values():
                await component.cleanup()

            self._components.clear()
            self._state = ComponentState.UNREGISTERED
            await self._audit.log({
                "event_type": "security.manager.cleaned_up",
            })

        except Exception as e:
            await self._audit.log({
                "event_type": "security.manager.error",
                "error": str(e),
            })
            raise RuntimeError(f"Failed to clean up security manager: {e}")

    def register_component(
        self,
        component: SecurityComponent,
    ) -> None:
        """Register a security component.

        Args:
            component: Component to register

        Raises:
            ValueError: If component is invalid
            RuntimeError: If registration fails
        """
        try:
            if not isinstance(component, SecurityComponent):
                raise ValueError("Invalid component type")

            component_id = str(component.id)
            if component_id in self._components:
                raise ValueError(f"Component {component_id} already registered")

            self._components[component_id] = component
            logger.info(f"Registered security component {component_id}")

        except Exception as e:
            logger.error(f"Failed to register component: {e}")
            raise

    def unregister_component(
        self,
        component_id: str,
    ) -> None:
        """Unregister a security component.

        Args:
            component_id: ID of component to unregister

        Raises:
            ValueError: If component not found
            RuntimeError: If unregistration fails
        """
        try:
            if component_id not in self._components:
                raise ValueError(f"Component {component_id} not found")

            del self._components[component_id]
            logger.info(f"Unregistered security component {component_id}")

        except Exception as e:
            logger.error(f"Failed to unregister component: {e}")
            raise

    def get_component(
        self,
        component_id: str,
        component_type: Optional[Type[T]] = None,
    ) -> T:
        """Get a registered component.

        Args:
            component_id: Component ID
            component_type: Optional component type to validate

        Returns:
            Component instance

        Raises:
            ValueError: If component not found or type mismatch
        """
        try:
            if component_id not in self._components:
                raise ValueError(f"Component {component_id} not found")

            component = self._components[component_id]
            if component_type and not isinstance(component, component_type):
                raise ValueError(
                    f"Component {component_id} is not of type {component_type}"
                )

            return component  # type: ignore

        except Exception as e:
            logger.error(f"Failed to get component: {e}")
            raise

    def list_components(
        self,
        component_type: Optional[Type[SecurityComponent]] = None,
    ) -> List[SecurityComponent]:
        """List registered components.

        Args:
            component_type: Optional type to filter by

        Returns:
            List of registered components
        """
        try:
            if component_type:
                return [
                    c
                    for c in self._components.values()
                    if isinstance(c, component_type)
                ]
            return list(self._components.values())

        except Exception as e:
            logger.error(f"Failed to list components: {e}")
            raise

    def create_auth_component(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> AuthenticationComponent:
        """Create an authentication component.

        Args:
            name: Component name
            config: Optional configuration

        Returns:
            AuthenticationComponent instance

        Raises:
            ValueError: If creation fails
        """
        try:
            component_config = SecurityConfig(
                name=name,
                type="authentication",
                config=config or {},
            )
            component = AuthenticationComponent(config=component_config)
            self.register_component(component)
            return component

        except Exception as e:
            logger.error(f"Failed to create auth component: {e}")
            raise

    def create_authz_component(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> AuthorizationComponent:
        """Create an authorization component.

        Args:
            name: Component name
            config: Optional configuration

        Returns:
            AuthorizationComponent instance

        Raises:
            ValueError: If creation fails
        """
        try:
            component_config = SecurityConfig(
                name=name,
                type="authorization",
                config=config or {},
            )
            component = AuthorizationComponent(config=component_config)
            self.register_component(component)
            return component

        except Exception as e:
            logger.error(f"Failed to create authz component: {e}")
            raise

    def create_data_protection_component(
        self,
        name: str,
        config: Optional[Dict[str, str]] = None,
    ) -> DataProtectionComponent:
        """Create a data protection component.

        Args:
            name: Component name
            config: Optional configuration

        Returns:
            DataProtectionComponent instance

        Raises:
            ValueError: If creation fails
        """
        try:
            component_config = SecurityConfig(
                name=name,
                type="data_protection",
                config=config or {},
            )
            component = DataProtectionComponent(config=component_config)
            self.register_component(component)
            return component

        except Exception as e:
            logger.error(f"Failed to create data protection component: {e}")
            raise


# Export public API
__all__ = [
    "SecurityManager",
]
