"""Base exception classes for the Pepperpy framework."""
from typing import Optional

class PepperpyError(Exception):
    """Base class for all Pepperpy exceptions."""
    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.__doc__)

class ConfigError(PepperpyError):
    """Error raised when there is a configuration issue."""
    pass

class LifecycleError(PepperpyError):
    """Error raised when there is a lifecycle management issue."""
    pass

class ProviderError(PepperpyError):
    """Error raised when there is a provider-related issue."""
    pass

class AgentError(PepperpyError):
    """Error raised when there is an agent-related issue."""
    pass

class MemoryError(PepperpyError):
    """Error raised when there is a memory-related issue."""
    pass

class LLMError(PepperpyError):
    """Error raised when there is an LLM-related issue."""
    pass

class VectorStoreError(PepperpyError):
    """Error raised when there is a vector store-related issue."""
    pass

class DocumentStoreError(PepperpyError):
    """Error raised when there is a document store-related issue."""
    pass

class EmbeddingError(PepperpyError):
    """Error raised when there is an embedding-related issue."""
    pass

class ValidationError(PepperpyError):
    """Error raised when there is a validation issue."""
    pass

class SecurityError(PepperpyError):
    """Error raised when there is a security-related issue."""
    pass

class RateLimitError(PepperpyError):
    """Error raised when rate limits are exceeded."""
    pass

class EventError(PepperpyError):
    """Error raised when there is an event-related issue."""
    pass

class ProfileError(PepperpyError):
    """Error raised when there is a profile-related issue."""
    pass 