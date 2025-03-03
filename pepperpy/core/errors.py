"""Error handling system for PepperPy.

This module defines the core error types and exceptions used throughout the framework.
"""


class PepperPyError(Exception):
    """Base exception for all PepperPy errors."""



class ConfigError(PepperPyError):
    """Error in configuration."""



class StateError(PepperPyError):
    """Error in component state."""



class WorkflowError(PepperPyError):
    """Error in workflow execution."""



class AgentError(PepperPyError):
    """Error in agent execution."""



class ProviderError(PepperPyError):
    """Error in provider execution."""



class ResourceError(PepperPyError):
    """Error in resource management."""



class ValidationError(PepperPyError):
    """Error in validation."""

