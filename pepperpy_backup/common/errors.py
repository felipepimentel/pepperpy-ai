"""Common error types for the pepperpy library."""

class PepperpyError(Exception):
    """Base class for all pepperpy errors."""
    pass

class ConfigurationError(PepperpyError):
    """Raised when there is an error in configuration."""
    pass

class RAGError(PepperpyError):
    """Raised when there is an error in RAG operations."""
    pass

class ConfigError(PepperpyError):
    """Configuration error."""
    pass

class ValidationError(PepperpyError):
    """Validation error."""
    pass

class AgentError(PepperpyError):
    """Agent error."""
    pass

class MemoryError(PepperpyError):
    """Memory error."""
    pass

class ModelError(PepperpyError):
    """Model error."""
    pass

class ToolError(PepperpyError):
    """Tool error."""
    pass

class RuntimeError(PepperpyError):
    """Runtime error."""
    pass
