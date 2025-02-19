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


class ContentError(PepperpyError):
    """Raised when content processing fails."""

    pass


class LLMError(PepperpyError):
    """Raised when LLM operations fail."""

    pass


class SynthesisError(PepperpyError):
    """Raised when synthesis operations fail."""

    pass


# Expose public interface
__all__ = [
    "AgentError",
    "ConfigurationError",
    "ContentError",
    "LLMError",
    "PepperpyError",
    "ResourceError",
    "SynthesisError",
    "ValidationError",
]
