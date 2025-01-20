"""Error handling module for Pepperpy."""

from typing import Optional

# Base errors
class PepperpyError(Exception):
    """Base exception class for all Pepperpy errors."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            cause: Original exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.cause = cause
        
    def __str__(self) -> str:
        """Get string representation of error.
        
        Returns:
            str: Error message with optional cause.
        """
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ValidationError(PepperpyError):
    """Error raised when validation fails."""
    pass


class ConfigError(ValidationError):
    """Error raised for configuration-related issues."""
    pass


class StorageError(PepperpyError):
    """Base class for storage-related errors."""
    pass


class VectorStoreError(StorageError):
    """Error raised for vector store operations."""
    pass


class DocumentStoreError(StorageError):
    """Error raised for document store operations."""
    pass


class MemoryStoreError(StorageError):
    """Error raised for memory store operations."""
    pass


class ModelError(PepperpyError):
    """Base class for model-related errors."""
    pass


class OpenAIError(ModelError):
    """Error raised for OpenAI-specific issues."""
    pass


class AnthropicError(ModelError):
    """Error raised for Anthropic-specific issues."""
    pass


class LearningError(PepperpyError):
    """Base class for learning-related errors."""
    pass


class InContextError(LearningError):
    """Error raised for in-context learning issues."""
    pass


class RetrievalError(LearningError):
    """Error raised for retrieval-related issues."""
    pass


class FineTuningError(LearningError):
    """Error raised for fine-tuning issues."""
    pass


class APIError(PepperpyError):
    """Base class for API-related errors."""
    pass


class ClientError(APIError):
    """Error raised for client-side issues (4xx)."""
    pass


class ServerError(APIError):
    """Error raised for server-side issues (5xx)."""
    pass


# Import specific error classes
from .http import (
    HTTPError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    InternalServerError,
    ServiceUnavailableError,
)

from .model import (
    ModelRequestError,
    ModelResponseError,
    ModelTimeoutError,
    OpenAIRequestError,
    OpenAIResponseError,
    OpenAITimeoutError,
    AnthropicRequestError,
    AnthropicResponseError,
    AnthropicTimeoutError,
)

from .storage import (
    StorageConnectionError,
    StorageOperationError,
    VectorIndexError,
    DocumentNotFoundError,
    DocumentChunkError,
    MemoryExpiredError,
    MemoryCapacityError,
)

from .learning import (
    ExampleMatchError,
    ExampleLimitError,
    RetrievalMatchError,
    ContextLengthError,
    TrainingError,
    ValidationError as LearningValidationError,
)


__all__ = [
    # Base errors
    "PepperpyError",
    "ValidationError",
    "ConfigError",
    "StorageError",
    "VectorStoreError",
    "DocumentStoreError",
    "MemoryStoreError",
    "ModelError",
    "OpenAIError",
    "AnthropicError",
    "LearningError",
    "InContextError",
    "RetrievalError",
    "FineTuningError",
    "APIError",
    "ClientError",
    "ServerError",
    
    # HTTP errors
    "HTTPError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "InternalServerError",
    "ServiceUnavailableError",
    
    # Model errors
    "ModelRequestError",
    "ModelResponseError",
    "ModelTimeoutError",
    "OpenAIRequestError",
    "OpenAIResponseError",
    "OpenAITimeoutError",
    "AnthropicRequestError",
    "AnthropicResponseError",
    "AnthropicTimeoutError",
    
    # Storage errors
    "StorageConnectionError",
    "StorageOperationError",
    "VectorIndexError",
    "DocumentNotFoundError",
    "DocumentChunkError",
    "MemoryExpiredError",
    "MemoryCapacityError",
    
    # Learning errors
    "ExampleMatchError",
    "ExampleLimitError",
    "RetrievalMatchError",
    "ContextLengthError",
    "TrainingError",
    "LearningValidationError",
] 