"""Error handling system for PepperPy.

This module defines the core error types and exceptions used throughout the framework.
"""

class PepperPyError(Exception):
    """Base exception for all PepperPy errors."""

    pass


class ConfigError(PepperPyError):
    """Error in configuration."""

    pass


class StateError(PepperPyError):
    """Error in component state."""

    pass


class WorkflowError(PepperPyError):
    """Error in workflow execution."""

    pass


class AgentError(PepperPyError):
    """Error in agent execution."""

    pass


class ProviderError(PepperPyError):
    """Error in provider execution."""

    pass


class ResourceError(PepperPyError):
    """Error in resource management."""

    pass


class ValidationError(PepperPyError):
    """Error in validation."""

    pass