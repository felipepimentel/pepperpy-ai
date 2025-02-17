"""Core exceptions for the Pepperpy framework."""


class PepperpyError(Exception):
    """Base class for all Pepperpy exceptions."""

    pass


class ValidationError(PepperpyError):
    """Raised when validation fails."""

    pass


class ConfigurationError(PepperpyError):
    """Raised when configuration is invalid."""

    pass


class ResourceError(PepperpyError):
    """Raised when a resource operation fails."""

    pass


class AgentError(PepperpyError):
    """Raised when an agent operation fails."""

    pass
