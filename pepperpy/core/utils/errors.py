"""
Core error handling and custom exceptions.
"""
from typing import Optional


class PepperpyError(Exception):
    """Base exception class for all Pepperpy errors."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        """Initialize PepperpyError.

        Args:
            message: Error message.
            code: Optional error code.
        """
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigurationError(PepperpyError):
    """Raised when there is a configuration-related error."""
    pass


class ValidationError(PepperpyError):
    """Raised when validation fails."""
    pass


class ProviderError(PepperpyError):
    """Raised when there is an error with a provider."""
    pass


class ResourceNotFoundError(PepperpyError):
    """Raised when a requested resource is not found."""
    pass


class AuthenticationError(PepperpyError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(PepperpyError):
    """Raised when authorization fails."""
    pass


class RateLimitError(PepperpyError):
    """Raised when rate limits are exceeded."""
    pass


class TimeoutError(PepperpyError):
    """Raised when an operation times out."""
    pass


class DependencyError(PepperpyError):
    """Raised when there is an error with a dependency."""
    pass


class ResourceError(PepperpyError):
    """Error raised for resource management issues."""
    pass


class SecurityError(PepperpyError):
    """Error raised for security-related issues."""
    pass


class MiddlewareError(PepperpyError):
    """Error raised for middleware-related issues."""
    pass


class ExtensionError(PepperpyError):
    """Error raised for extension-related issues."""
    pass


class CapabilityError(PepperpyError):
    """Error raised for capability-related issues."""
    pass


class AgentError(PepperpyError):
    """Error raised for agent-related issues."""
    pass


class WorkflowError(PepperpyError):
    """Error raised for workflow-related issues."""
    pass


class PersistenceError(PepperpyError):
    """Error raised for persistence-related issues."""
    pass


class MonitoringError(PepperpyError):
    """Error raised for monitoring-related issues."""
    pass
