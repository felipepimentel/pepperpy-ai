"""Core error classes for the Pepperpy framework.

This module provides the base error classes used throughout the framework.
"""

from typing import Any, Dict, Optional


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message)
        self.details = details or {}


class ComponentError(PepperpyError):
    """Error raised when a component operation fails."""


class StateError(PepperpyError):
    """Error raised when an invalid state transition is attempted."""


class ValidationError(PepperpyError):
    """Error raised when validation fails."""


class ConfigError(PepperpyError):
    """Error raised when configuration is invalid."""


class LifecycleError(PepperpyError):
    """Error raised when a lifecycle operation fails."""


class ProviderError(PepperpyError):
    """Error raised when a provider operation fails."""


class ResourceError(PepperpyError):
    """Error raised when a resource operation fails."""


class SecurityError(PepperpyError):
    """Error raised when a security operation fails."""


class MonitoringError(PepperpyError):
    """Error raised when a monitoring operation fails."""


class NetworkError(PepperpyError):
    """Error raised when a network operation fails."""


class StorageError(PepperpyError):
    """Error raised when a storage operation fails."""


class PluginError(PepperpyError):
    """Error raised when a plugin operation fails."""


class ExtensionError(PepperpyError):
    """Error raised when an extension operation fails."""


class AdapterError(PepperpyError):
    """Error raised when an adapter operation fails."""


class FactoryError(PepperpyError):
    """Error raised when a factory operation fails."""


class HubError(PepperpyError):
    """Error raised when a hub operation fails."""


class CLIError(PepperpyError):
    """Error raised when a CLI operation fails."""


class ContentError(PepperpyError):
    """Error raised when a content operation fails."""


class LLMError(PepperpyError):
    """Error raised when an LLM operation fails."""


class WorkflowError(PepperpyError):
    """Error raised when a workflow operation fails."""


class AgentError(PepperpyError):
    """Error raised when an agent operation fails."""


class CapabilityError(PepperpyError):
    """Error raised when a capability operation fails."""


class DuplicateError(PepperpyError):
    """Error raised when a duplicate operation is attempted."""


class NotFoundError(PepperpyError):
    """Error raised when a resource is not found."""


class MetricsError(PepperpyError):
    """Error raised when a metrics operation fails."""


# Alias for backward compatibility
PepperpyMemoryError = StorageError

__all__ = [
    "AdapterError",
    "AgentError",
    "CLIError",
    "CapabilityError",
    "ComponentError",
    "ConfigError",
    "ContentError",
    "DuplicateError",
    "ExtensionError",
    "FactoryError",
    "HubError",
    "LLMError",
    "LifecycleError",
    "MetricsError",
    "MonitoringError",
    "NetworkError",
    "NotFoundError",
    "PepperpyError",
    "PepperpyMemoryError",  # Alias
    "PluginError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "StateError",
    "StorageError",
    "ValidationError",
    "WorkflowError",
]
