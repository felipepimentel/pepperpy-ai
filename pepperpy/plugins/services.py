"""Plugin Service System.

This module provides the service system for PepperPy plugins,
allowing plugins to offer APIs/services to other plugins and consume
services offered by other plugins.
"""

import asyncio
import inspect
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar, Union, cast

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type definitions
T = TypeVar("T")
ServiceFunction = Callable[..., Any]
AsyncServiceFunction = Callable[..., asyncio.Future]
ServiceProvider = Union[ServiceFunction, AsyncServiceFunction]


class ServiceScope(Enum):
    """Scope of a service provided by a plugin."""

    # Service is only available within the plugin that offers it
    PRIVATE = "private"

    # Service is available to plugins that have a direct dependency on the provider
    DEPENDENT = "dependent"

    # Service is available to any plugin in the system
    PUBLIC = "public"


class ServiceError(Exception):
    """Base class for service-related errors."""

    pass


class ServiceNotFoundError(ServiceError):
    """Raised when a requested service is not found."""

    def __init__(self, provider_id: str, service_name: str):
        """Initialize a new ServiceNotFoundError.

        Args:
            provider_id: ID of the plugin that was requested
            service_name: Name of the service that was requested
        """
        super().__init__(
            f"Service '{service_name}' not found for plugin '{provider_id}'"
        )
        self.provider_id = provider_id
        self.service_name = service_name


class ServiceAccessError(ServiceError):
    """Raised when a plugin attempts to access a service it doesn't have access to."""

    def __init__(self, consumer_id: str, provider_id: str, service_name: str):
        """Initialize a new ServiceAccessError.

        Args:
            consumer_id: ID of the plugin that attempted to access the service
            provider_id: ID of the plugin that provides the service
            service_name: Name of the service
        """
        super().__init__(
            f"Plugin '{consumer_id}' does not have access to service '{service_name}' "
            f"from plugin '{provider_id}'"
        )
        self.consumer_id = consumer_id
        self.provider_id = provider_id
        self.service_name = service_name


class ServiceRegistry:
    """Registry for plugin services.

    This class manages the registration, discovery, and access control
    for services provided by plugins.
    """

    def __init__(self):
        """Initialize a new service registry."""
        self._services: dict[
            str, dict[str, tuple[ServiceProvider, ServiceScope, dict[str, Any]]]
        ] = defaultdict(dict)
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    def register_service(
        self,
        provider_id: str,
        service_name: str,
        service: ServiceProvider,
        scope: ServiceScope = ServiceScope.PUBLIC,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a service provided by a plugin.

        Args:
            provider_id: ID of the plugin providing the service
            service_name: Name of the service
            service: Service implementation (function or method)
            scope: Access scope for the service
            metadata: Optional metadata about the service

        Raises:
            ValueError: If a service with the same name is already registered for the provider
        """
        if metadata is None:
            metadata = {}

        # Add service signature to metadata
        if "signature" not in metadata:
            sig = inspect.signature(service)
            metadata["signature"] = str(sig)

        # Add whether the service is async to metadata
        is_async = asyncio.iscoroutinefunction(service)
        metadata["is_async"] = is_async

        with self._lock:
            if service_name in self._services[provider_id]:
                raise ValueError(
                    f"Service '{service_name}' is already registered for plugin '{provider_id}'"
                )

            self._services[provider_id][service_name] = (service, scope, metadata)
            logger.debug(
                f"Registered service '{service_name}' for plugin '{provider_id}' "
                f"with scope '{scope.value}'"
            )

    def unregister_service(self, provider_id: str, service_name: str) -> None:
        """Unregister a service.

        Args:
            provider_id: ID of the plugin providing the service
            service_name: Name of the service

        Raises:
            ServiceNotFoundError: If the service is not found
        """
        with self._lock:
            if (
                provider_id not in self._services
                or service_name not in self._services[provider_id]
            ):
                raise ServiceNotFoundError(provider_id, service_name)

            del self._services[provider_id][service_name]

            # Remove the provider from _services if it has no services left
            if not self._services[provider_id]:
                del self._services[provider_id]

            logger.debug(
                f"Unregistered service '{service_name}' for plugin '{provider_id}'"
            )

    def unregister_all_services(self, provider_id: str) -> int:
        """Unregister all services provided by a plugin.

        Args:
            provider_id: ID of the plugin

        Returns:
            Number of services unregistered
        """
        with self._lock:
            if provider_id not in self._services:
                return 0

            count = len(self._services[provider_id])
            del self._services[provider_id]
            logger.debug(f"Unregistered {count} services for plugin '{provider_id}'")
            return count

    def get_service(
        self, provider_id: str, service_name: str, consumer_id: str | None = None
    ) -> ServiceProvider:
        """Get a service implementation.

        Args:
            provider_id: ID of the plugin providing the service
            service_name: Name of the service
            consumer_id: ID of the plugin consuming the service (for access control)

        Returns:
            Service implementation

        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceAccessError: If the consumer doesn't have access to the service
        """
        with self._lock:
            if (
                provider_id not in self._services
                or service_name not in self._services[provider_id]
            ):
                raise ServiceNotFoundError(provider_id, service_name)

            service, scope, _ = self._services[provider_id][service_name]

            # Check access control
            if consumer_id is not None and consumer_id != provider_id:
                if scope == ServiceScope.PRIVATE:
                    raise ServiceAccessError(consumer_id, provider_id, service_name)

                if (
                    scope == ServiceScope.DEPENDENT
                    and provider_id not in self._dependencies.get(consumer_id, set())
                ):
                    raise ServiceAccessError(consumer_id, provider_id, service_name)

            return service

    def get_service_metadata(
        self, provider_id: str, service_name: str, consumer_id: str | None = None
    ) -> dict[str, Any]:
        """Get metadata for a service.

        Args:
            provider_id: ID of the plugin providing the service
            service_name: Name of the service
            consumer_id: ID of the plugin consuming the service (for access control)

        Returns:
            Service metadata

        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceAccessError: If the consumer doesn't have access to the service
        """
        with self._lock:
            if (
                provider_id not in self._services
                or service_name not in self._services[provider_id]
            ):
                raise ServiceNotFoundError(provider_id, service_name)

            service, scope, metadata = self._services[provider_id][service_name]

            # Check access control
            if consumer_id is not None and consumer_id != provider_id:
                if scope == ServiceScope.PRIVATE:
                    raise ServiceAccessError(consumer_id, provider_id, service_name)

                if (
                    scope == ServiceScope.DEPENDENT
                    and provider_id not in self._dependencies.get(consumer_id, set())
                ):
                    raise ServiceAccessError(consumer_id, provider_id, service_name)

            return dict(metadata)

    def has_service(
        self, provider_id: str, service_name: str, consumer_id: str | None = None
    ) -> bool:
        """Check if a service exists and is accessible.

        Args:
            provider_id: ID of the plugin providing the service
            service_name: Name of the service
            consumer_id: ID of the plugin consuming the service (for access control)

        Returns:
            True if the service exists and is accessible, False otherwise
        """
        with self._lock:
            if (
                provider_id not in self._services
                or service_name not in self._services[provider_id]
            ):
                return False

            _, scope, _ = self._services[provider_id][service_name]

            # Check access control
            if consumer_id is not None and consumer_id != provider_id:
                if scope == ServiceScope.PRIVATE:
                    return False

                if (
                    scope == ServiceScope.DEPENDENT
                    and provider_id not in self._dependencies.get(consumer_id, set())
                ):
                    return False

            return True

    def list_services(
        self, provider_id: str, consumer_id: str | None = None
    ) -> list[str]:
        """List all services provided by a plugin.

        Args:
            provider_id: ID of the plugin providing the services
            consumer_id: ID of the plugin consuming the services (for access control)

        Returns:
            List of service names
        """
        with self._lock:
            if provider_id not in self._services:
                return []

            if consumer_id is None or consumer_id == provider_id:
                # Return all services if no consumer is specified or consumer is the provider
                return list(self._services[provider_id].keys())

            # Filter services based on access control
            has_dependency = provider_id in self._dependencies.get(consumer_id, set())

            return [
                name
                for name, (_, scope, _) in self._services[provider_id].items()
                if scope == ServiceScope.PUBLIC
                or (scope == ServiceScope.DEPENDENT and has_dependency)
            ]

    def list_providers(self, consumer_id: str | None = None) -> list[str]:
        """List all service providers.

        Args:
            consumer_id: ID of the plugin consuming the services (for access control)

        Returns:
            List of provider IDs
        """
        with self._lock:
            if consumer_id is None:
                # Return all providers if no consumer is specified
                return list(self._services.keys())

            # Filter providers based on access control
            dependencies = self._dependencies.get(consumer_id, set())

            result = []
            for provider_id, services in self._services.items():
                if provider_id == consumer_id:
                    # Always include the consumer itself
                    result.append(provider_id)
                    continue

                # Check if any service is accessible to the consumer
                has_dependency = provider_id in dependencies

                for _, scope, _ in services.values():
                    if scope == ServiceScope.PUBLIC or (
                        scope == ServiceScope.DEPENDENT and has_dependency
                    ):
                        result.append(provider_id)
                        break

            return result

    def register_dependency(self, consumer_id: str, provider_id: str) -> None:
        """Register a dependency between two plugins.

        Args:
            consumer_id: ID of the plugin that depends on the provider
            provider_id: ID of the provider plugin
        """
        with self._lock:
            self._dependencies[consumer_id].add(provider_id)
            logger.debug(
                f"Registered dependency: {consumer_id} -> {provider_id} (for service access)"
            )

    def unregister_dependency(self, consumer_id: str, provider_id: str) -> None:
        """Unregister a dependency between two plugins.

        Args:
            consumer_id: ID of the plugin that depends on the provider
            provider_id: ID of the provider plugin
        """
        with self._lock:
            if consumer_id in self._dependencies:
                self._dependencies[consumer_id].discard(provider_id)

                # Remove the consumer from _dependencies if it has no dependencies left
                if not self._dependencies[consumer_id]:
                    del self._dependencies[consumer_id]

                logger.debug(
                    f"Unregistered dependency: {consumer_id} -> {provider_id} (for service access)"
                )

    def unregister_all_dependencies(self, plugin_id: str) -> None:
        """Unregister all dependencies for a plugin.

        Args:
            plugin_id: ID of the plugin
        """
        with self._lock:
            # Remove plugin as a consumer
            if plugin_id in self._dependencies:
                del self._dependencies[plugin_id]

            # Remove plugin as a provider from all consumers
            for consumer_id in list(self._dependencies.keys()):
                self._dependencies[consumer_id].discard(plugin_id)

                # Remove the consumer if it has no dependencies left
                if not self._dependencies[consumer_id]:
                    del self._dependencies[consumer_id]

            logger.debug(f"Unregistered all dependencies for plugin '{plugin_id}'")


# Singleton instance
_service_registry = ServiceRegistry()


# Public API


def register_service(
    provider_id: str,
    service_name: str,
    service: ServiceProvider,
    scope: ServiceScope = ServiceScope.PUBLIC,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Register a service provided by a plugin.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        service: Service implementation (function or method)
        scope: Access scope for the service
        metadata: Optional metadata about the service

    Raises:
        ValueError: If a service with the same name is already registered for the provider
    """
    _service_registry.register_service(
        provider_id, service_name, service, scope, metadata
    )


def unregister_service(provider_id: str, service_name: str) -> None:
    """Unregister a service.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service

    Raises:
        ServiceNotFoundError: If the service is not found
    """
    _service_registry.unregister_service(provider_id, service_name)


def unregister_all_services(provider_id: str) -> int:
    """Unregister all services provided by a plugin.

    Args:
        provider_id: ID of the plugin

    Returns:
        Number of services unregistered
    """
    return _service_registry.unregister_all_services(provider_id)


def get_service(
    provider_id: str, service_name: str, consumer_id: str | None = None
) -> ServiceProvider:
    """Get a service implementation.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        consumer_id: ID of the plugin consuming the service (for access control)

    Returns:
        Service implementation

    Raises:
        ServiceNotFoundError: If the service is not found
        ServiceAccessError: If the consumer doesn't have access to the service
    """
    return _service_registry.get_service(provider_id, service_name, consumer_id)


def get_service_metadata(
    provider_id: str, service_name: str, consumer_id: str | None = None
) -> dict[str, Any]:
    """Get metadata for a service.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        consumer_id: ID of the plugin consuming the service (for access control)

    Returns:
        Service metadata

    Raises:
        ServiceNotFoundError: If the service is not found
        ServiceAccessError: If the consumer doesn't have access to the service
    """
    return _service_registry.get_service_metadata(
        provider_id, service_name, consumer_id
    )


def has_service(
    provider_id: str, service_name: str, consumer_id: str | None = None
) -> bool:
    """Check if a service exists and is accessible.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        consumer_id: ID of the plugin consuming the service (for access control)

    Returns:
        True if the service exists and is accessible, False otherwise
    """
    return _service_registry.has_service(provider_id, service_name, consumer_id)


def list_services(provider_id: str, consumer_id: str | None = None) -> list[str]:
    """List all services provided by a plugin.

    Args:
        provider_id: ID of the plugin providing the services
        consumer_id: ID of the plugin consuming the services (for access control)

    Returns:
        List of service names
    """
    return _service_registry.list_services(provider_id, consumer_id)


def list_providers(consumer_id: str | None = None) -> list[str]:
    """List all service providers.

    Args:
        consumer_id: ID of the plugin consuming the services (for access control)

    Returns:
        List of provider IDs
    """
    return _service_registry.list_providers(consumer_id)


def register_dependency(consumer_id: str, provider_id: str) -> None:
    """Register a dependency between two plugins.

    Args:
        consumer_id: ID of the plugin that depends on the provider
        provider_id: ID of the provider plugin
    """
    _service_registry.register_dependency(consumer_id, provider_id)


def unregister_dependency(consumer_id: str, provider_id: str) -> None:
    """Unregister a dependency between two plugins.

    Args:
        consumer_id: ID of the plugin that depends on the provider
        provider_id: ID of the provider plugin
    """
    _service_registry.unregister_dependency(consumer_id, provider_id)


def unregister_all_dependencies(plugin_id: str) -> None:
    """Unregister all dependencies for a plugin.

    Args:
        plugin_id: ID of the plugin
    """
    _service_registry.unregister_all_dependencies(plugin_id)


class service:
    """Decorator for registering methods as services.

    This decorator can be used on methods of PepperpyPlugin subclasses
    to register them as services.

    Example:
        @service("my_service", scope=ServiceScope.PUBLIC)
        def my_service_method(self, arg1, arg2):
            return arg1 + arg2
    """

    def __init__(
        self,
        service_name: str,
        scope: ServiceScope = ServiceScope.PUBLIC,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize the decorator.

        Args:
            service_name: Name of the service
            scope: Access scope for the service
            metadata: Optional metadata about the service
        """
        self.service_name = service_name
        self.scope = scope
        self.metadata = metadata or {}

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Apply the decorator.

        Args:
            func: Function or method to decorate

        Returns:
            Decorated function or method
        """
        # Store the service metadata on the function
        func.__service_name__ = self.service_name
        func.__service_scope__ = self.scope
        func.__service_metadata__ = self.metadata

        return func


def call_service(
    provider_id: str, service_name: str, consumer_id: str, *args: Any, **kwargs: Any
) -> Any:
    """Call a service synchronously.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        consumer_id: ID of the plugin consuming the service
        *args: Positional arguments to pass to the service
        **kwargs: Keyword arguments to pass to the service

    Returns:
        Result of the service call

    Raises:
        ServiceNotFoundError: If the service is not found
        ServiceAccessError: If the consumer doesn't have access to the service
        TypeError: If the service is async
    """
    service_fn = get_service(provider_id, service_name, consumer_id)
    metadata = get_service_metadata(provider_id, service_name, consumer_id)

    if metadata.get("is_async", False):
        raise TypeError(
            f"Service '{service_name}' is async and must be called with await_service()"
        )

    return service_fn(*args, **kwargs)


async def await_service(
    provider_id: str, service_name: str, consumer_id: str, *args: Any, **kwargs: Any
) -> Any:
    """Call a service asynchronously.

    Args:
        provider_id: ID of the plugin providing the service
        service_name: Name of the service
        consumer_id: ID of the plugin consuming the service
        *args: Positional arguments to pass to the service
        **kwargs: Keyword arguments to pass to the service

    Returns:
        Result of the service call

    Raises:
        ServiceNotFoundError: If the service is not found
        ServiceAccessError: If the consumer doesn't have access to the service
    """
    service_fn = get_service(provider_id, service_name, consumer_id)
    metadata = get_service_metadata(provider_id, service_name, consumer_id)

    if not metadata.get("is_async", False):
        # Call synchronous service
        return service_fn(*args, **kwargs)

    # Call asynchronous service
    return await cast(AsyncServiceFunction, service_fn)(*args, **kwargs)
