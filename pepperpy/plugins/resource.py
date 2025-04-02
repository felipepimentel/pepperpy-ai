"""Resource management utilities for plugins.

This module provides decorators and mixins to help manage resources in plugins.
"""

import functools
import inspect
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from pepperpy.core.errors import ProviderError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class ResourceTracker:
    """Track resources for automatic cleanup.

    This class keeps track of resources that need to be cleaned up when a provider
    is no longer needed. This ensures resources are always properly released.
    """

    def __init__(self):
        """Initialize resource tracker."""
        self._resources: Dict[str, Any] = {}
        self._cleanup_funcs: Dict[str, Callable] = {}

    def register(
        self, name: str, resource: Any, cleanup_func: Optional[Callable] = None
    ) -> Any:
        """Register a resource for tracking.

        Args:
            name: Unique name for the resource
            resource: Resource to track
            cleanup_func: Optional function to call for cleanup

        Returns:
            The registered resource
        """
        self._resources[name] = resource

        if cleanup_func:
            self._cleanup_funcs[name] = cleanup_func

        return resource

    def unregister(self, name: str) -> None:
        """Unregister a resource.

        Args:
            name: Name of resource to unregister
        """
        if name in self._resources:
            del self._resources[name]

        if name in self._cleanup_funcs:
            del self._cleanup_funcs[name]

    def get(self, name: str) -> Optional[Any]:
        """Get a registered resource.

        Args:
            name: Name of resource to get

        Returns:
            Resource object or None if not found
        """
        return self._resources.get(name)

    async def cleanup_all(self) -> None:
        """Clean up all registered resources."""
        errors: List[Exception] = []

        # Get the resources to clean up
        resources = list(self._resources.keys())

        for name in resources:
            resource = self._resources.get(name)
            if resource is None:
                continue

            try:
                # Try custom cleanup function if available
                if name in self._cleanup_funcs:
                    cleanup_func = self._cleanup_funcs[name]

                    if inspect.iscoroutinefunction(cleanup_func):
                        await cleanup_func(resource)
                    else:
                        cleanup_func(resource)

                # Try standard cleanup methods
                elif hasattr(resource, "close") and callable(resource.close):
                    if inspect.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()

                elif hasattr(resource, "cleanup") and callable(resource.cleanup):
                    if inspect.iscoroutinefunction(resource.cleanup):
                        await resource.cleanup()
                    else:
                        resource.cleanup()

                elif hasattr(resource, "__aexit__") and callable(resource.__aexit__):
                    await resource.__aexit__(None, None, None)

                elif hasattr(resource, "__exit__") and callable(resource.__exit__):
                    resource.__exit__(None, None, None)

                # Always unregister after cleanup attempt
                self.unregister(name)

            except Exception as e:
                errors.append(e)
                logger.error(f"Error cleaning up resource {name}: {e}")

                # Unregister even if cleanup failed
                with suppress(Exception):
                    self.unregister(name)

        # Report all errors after cleanup
        if errors:
            error_msg = (
                f"Errors during resource cleanup: {'; '.join(str(e) for e in errors)}"
            )
            logger.error(error_msg)
            raise ProviderError(error_msg)


class ResourceMixin:
    """Mixin providing resource management for plugins.

    This mixin adds methods for tracking and cleaning up resources in a structured way.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the resource mixin."""
        super().__init__(*args, **kwargs)
        self._resource_tracker = ResourceTracker()

    def register_resource(
        self, name: str, resource: T, cleanup_func: Optional[Callable] = None
    ) -> T:
        """Register a resource for automatic cleanup.

        Args:
            name: Unique name for the resource
            resource: Resource to track
            cleanup_func: Optional function to call for cleanup

        Returns:
            The registered resource
        """
        return self._resource_tracker.register(name, resource, cleanup_func)

    def unregister_resource(self, name: str) -> None:
        """Unregister a resource.

        Args:
            name: Name of resource to unregister
        """
        self._resource_tracker.unregister(name)

    def get_resource(self, name: str) -> Optional[Any]:
        """Get a registered resource.

        Args:
            name: Name of resource to get

        Returns:
            Resource object or None if not found
        """
        return self._resource_tracker.get(name)

    async def cleanup_resources(self) -> None:
        """Clean up all registered resources."""
        await self._resource_tracker.cleanup_all()


def managed_resource(name: Optional[str] = None) -> Callable[[F], F]:
    """Decorator for methods that create resources.

    This decorator automatically registers the return value of a method as a resource.
    The resource will be automatically cleaned up when the provider's cleanup method is called.

    Args:
        name: Optional name for the resource. If not provided, the method name is used.

    Returns:
        Decorated method
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get resource name
            resource_name = name or func.__name__

            # Call the original function
            resource = func(self, *args, **kwargs)

            # Register the resource if not None
            if resource is not None and hasattr(self, "register_resource"):
                self.register_resource(resource_name, resource)

            return resource

        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get resource name
            resource_name = name or func.__name__

            # Call the original function
            resource = await func(self, *args, **kwargs)

            # Register the resource if not None
            if resource is not None and hasattr(self, "register_resource"):
                self.register_resource(resource_name, resource)

            return resource

        # Use appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def auto_cleanup(original_cleanup_method: Callable) -> Callable:
    """Decorator for cleanup method to ensure all resources are cleaned up.

    This decorator enhances a cleanup method to call the resource tracker's
    cleanup_all method after the original cleanup method finishes.

    Args:
        original_cleanup_method: The original cleanup method

    Returns:
        Enhanced cleanup method
    """

    @functools.wraps(original_cleanup_method)
    async def wrapped_cleanup(self: Any, *args: Any, **kwargs: Any) -> None:
        """Enhanced cleanup that ensures all resources are cleaned up."""
        try:
            # Call original cleanup method
            if inspect.iscoroutinefunction(original_cleanup_method):
                await original_cleanup_method(self, *args, **kwargs)
            else:
                original_cleanup_method(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in original cleanup method: {e}")

        # Always try to clean up all resources
        if hasattr(self, "cleanup_resources"):
            await self.cleanup_resources()

    return wrapped_cleanup
