"""
A2A (Agent-to-Agent) module provides implementation of the A2A protocol for agent-to-agent communication.

This module enables agents to discover each other, exchange messages, and collaborate on tasks.
"""

import importlib
import os
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Dict, Optional, Type, cast

from pepperpy.a2a.base import (
    A2AError,
    A2AProvider,
    AgentCard,
    Artifact,
    DataPart,
    FilePart,
    Message,
    Part,
    PartType,
    Task,
    TaskState,
    TextPart,
)
from pepperpy.a2a.providers import (
    create_data_message,
    create_empty_task,
    create_file_message,
    create_function_call_message,
    create_mixed_message,
    create_text_message,
    extract_text_from_message,
)
from pepperpy.a2a.simulation import (
    SimulatedAgent,
    SimulationEnvironment,
    SimulationError,
    StatefulResponseHandler,
    create_simulation,
    delayed_response_handler,
    simple_echo_handler,
)
from pepperpy.a2a.testing import (
    TestAgentCard,
    TestTask,
    test_provider_lifecycle,
)
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type for provider factory functions
TProvider = Callable[..., Awaitable[A2AProvider]]

# Registry for provider factories
_provider_factories: dict[str, TProvider] = {}


def register_provider(provider_type: str) -> Callable[[TProvider], TProvider]:
    """Register an A2A provider factory function.

    Args:
        provider_type: Provider type identifier

    Returns:
        Decorator function that registers the factory
    """

    def decorator(factory_func: TProvider) -> TProvider:
        @wraps(factory_func)
        async def wrapped_factory(**kwargs: Any) -> A2AProvider:
            return await factory_func(**kwargs)

        _provider_factories[provider_type] = wrapped_factory
        logger.debug(f"Registered A2A provider: {provider_type}")
        return wrapped_factory

    return decorator


async def create_provider(provider_type: str = "default", **kwargs: Any) -> A2AProvider:
    """Create an A2A provider instance.

    This factory function creates an A2A provider of the specified type.
    It will first attempt to find a registered provider factory, then
    look for plugins, and finally try to load built-in providers.

    Args:
        provider_type: Type of provider to create (e.g., "rest", "mock")
        **kwargs: Provider configuration options

    Returns:
        Initialized provider instance

    Raises:
        A2AError: If the provider type is not supported
    """
    # Normalize provider type
    provider_type = provider_type.lower()

    # Default to environment variable if set
    if provider_type == "default":
        provider_type = os.environ.get("PEPPERPY_A2A_PROVIDER", "mock")

    # Check if provider is registered directly
    if provider_type in _provider_factories:
        factory = _provider_factories[provider_type]
        logger.debug(f"Creating A2A provider from registry: {provider_type}")
        return await factory(**kwargs)

    # Try to load from plugins
    try:
        from pepperpy.plugin import create_provider_instance

        logger.debug(f"Attempting to create A2A provider from plugins: {provider_type}")
        return cast(
            A2AProvider, await create_provider_instance("a2a", provider_type, **kwargs)
        )
    except (ImportError, ValueError) as e:
        logger.debug(f"Plugin provider not found: {e}, trying built-in providers")

    # Try to load built-in provider
    try:
        # Import provider module
        module_path = f".providers.{provider_type}.provider"
        provider_module = importlib.import_module(module_path, package="pepperpy.a2a")

        # Get class name using provider type
        class_name = f"{provider_type.capitalize()}A2AProvider"
        provider_class = getattr(provider_module, class_name)

        # Create and initialize provider
        provider = provider_class(**kwargs)
        await provider.initialize()

        logger.debug(f"Created built-in A2A provider: {provider_type}")
        return provider
    except (ImportError, AttributeError) as e:
        error_msg = f"Unsupported A2A provider type: {provider_type} - {e}"
        logger.error(error_msg)
        raise A2AError(error_msg) from e


__all__ = [
    # Base types
    "A2AError",
    "A2AProvider",
    "AgentCard",
    "Artifact",
    "DataPart",
    "FilePart",
    "Message",
    "Part",
    "PartType",
    "Task",
    "TaskState",
    "TextPart",
    # Factory functions
    "create_provider",
    "register_provider",
    # Message utilities
    "create_data_message",
    "create_empty_task",
    "create_file_message",
    "create_function_call_message",
    "create_mixed_message",
    "create_text_message",
    "extract_text_from_message",
    # Testing utilities
    "TestAgentCard",
    "TestTask",
    "test_provider_lifecycle",
    # Simulation
    "SimulatedAgent",
    "SimulationEnvironment",
    "SimulationError",
    "create_simulation",
    "delayed_response_handler",
    "simple_echo_handler",
    "StatefulResponseHandler",
]
