"""PepperPy framework."""

# Core components
from pepperpy.core.errors import (
    ConfigurationError,
    PepperpyError,
    ProviderError,
    ValidationError,
)
from pepperpy.core.events import Event, EventBus, EventType, emit_event, event_listener
from pepperpy.core.logging import get_logger
from pepperpy.core.services import ServiceLifetime, get_container

# Domain-specific providers
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.pepperpy import PepperPy
from pepperpy.plugins.plugin import PepperpyPlugin

__version__ = "0.1.0"

__all__ = [
    # Core components
    "PepperPy",
    "PepperpyPlugin",
    "PepperpyError",
    "ValidationError",
    "ConfigurationError",
    "ProviderError",
    # Event system
    "Event",
    "EventBus",
    "EventType",
    "emit_event",
    "event_listener",
    # Service container
    "ServiceLifetime",
    "get_container",
    # LLM components
    "LLMProvider",
    "Message",
    "MessageRole",
    # Utility functions
    "get_logger",
]
