"""Core error classes for the Pepperpy framework.

This module provides the base error classes used throughout the framework.
All framework errors should inherit from PepperpyError.
"""

from __future__ import annotations

from typing import Any


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
            recovery_hint: Optional hint for error recovery
        """
        super().__init__(message)
        self.details = details or {}
        self.recovery_hint = recovery_hint


# Core errors
class ConfigError(PepperpyError):
    """Error raised when configuration is invalid."""


class ValidationError(PepperpyError):
    """Error raised when validation fails."""


class StateError(PepperpyError):
    """Error raised when an invalid state transition is attempted."""


class NotFoundError(PepperpyError):
    """Error raised when a resource is not found."""


class DuplicateError(PepperpyError):
    """Error raised when a duplicate operation is attempted."""


# Component errors
class ComponentError(PepperpyError):
    """Base class for component errors."""


class LifecycleError(ComponentError):
    """Error raised when a lifecycle operation fails."""


class ResourceError(ComponentError):
    """Error raised when a resource operation fails."""


class ProviderError(ComponentError):
    """Error raised when a provider operation fails."""


class ExtensionError(ComponentError):
    """Error raised when an extension operation fails."""


class PluginError(ComponentError):
    """Error raised when a plugin operation fails."""


class AdapterError(ComponentError):
    """Error raised when an adapter operation fails."""


class FactoryError(ComponentError):
    """Error raised when a factory operation fails."""


# System errors
class SecurityError(PepperpyError):
    """Error raised when a security operation fails."""


class MonitoringError(PepperpyError):
    """Error raised when a monitoring operation fails."""


class MetricsError(PepperpyError):
    """Error raised when a metrics operation fails."""


class NetworkError(PepperpyError):
    """Error raised when a network operation fails."""


class StorageError(PepperpyError):
    """Error raised when a storage operation fails."""


# Feature errors
class AgentError(PepperpyError):
    """Error raised when an agent operation fails."""


class CapabilityError(PepperpyError):
    """Error raised when a capability operation fails."""


class ContentError(PepperpyError):
    """Error raised when a content operation fails."""


class HubError(PepperpyError):
    """Error raised when a hub operation fails."""


class LLMError(PepperpyError):
    """Error raised when an LLM operation fails."""


class WorkflowError(PepperpyError):
    """Error raised when a workflow operation fails."""


class CLIError(PepperpyError):
    """Error raised when a CLI operation fails."""


# Aliases for backward compatibility
PepperError = PepperpyError  # Legacy name
PepperpyMemoryError = StorageError  # Legacy memory error


class DependencyError(PepperpyError):
    """Error raised when a dependency operation fails."""

    pass


class EventError(PepperpyError):
    """Error raised when an event operation fails."""

    pass


__all__ = [
    "AdapterError",
    "AgentError",
    "CLIError",
    "CapabilityError",
    "ComponentError",
    "ConfigError",
    "ContentError",
    "DependencyError",
    "DuplicateError",
    "EventError",
    "ExtensionError",
    "FactoryError",
    "HubError",
    "LLMError",
    "LifecycleError",
    "MetricsError",
    "MonitoringError",
    "NetworkError",
    "NotFoundError",
    "PepperError",  # Legacy alias
    "PepperpyError",
    "PepperpyMemoryError",  # Legacy alias
    "PluginError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "StateError",
    "StorageError",
    "ValidationError",
    "WorkflowError",
]
