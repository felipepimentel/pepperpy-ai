"""Error classes for PepperPy.

This module defines the error hierarchy for the PepperPy framework.
All errors in the framework should inherit from PepperPyError.

Example:
    ```python
    from pepperpy.core.errors import PepperPyError

    class MyCustomError(PepperPyError):
        \"\"\"Error raised for custom issues.\"\"\"
        pass

    try:
        # Some operation that might fail
        pass
    except Exception as e:
        raise MyCustomError(f"Operation failed: {e}")
    ```
"""

from typing import Any, Dict, Optional, Type, cast


class PepperPyError(Exception):
    """Base class for all errors in the PepperPy framework."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new PepperPy error.

        Args:
            message: The error message
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """Get the string representation of the error.

        Returns:
            The error message, optionally with the error code
        """
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary.

        Returns:
            Dictionary representation of the error
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


# ---- Core Errors ----


class ConfigError(PepperPyError):
    """Error raised for configuration issues."""

    pass


class ValidationError(PepperPyError):
    """Error raised for validation issues."""

    pass


class NotFoundError(PepperPyError):
    """Error raised when a resource is not found."""

    pass


class DuplicateError(PepperPyError):
    """Error raised when a duplicate resource is detected."""

    pass


class PermissionError(PepperPyError):
    """Error raised for permission issues."""

    pass


class TimeoutError(PepperPyError):
    """Error raised when an operation times out."""

    pass


class NetworkError(PepperPyError):
    """Error raised for network issues."""

    pass


class AuthenticationError(PepperPyError):
    """Error raised for authentication issues."""

    pass


class AuthorizationError(PepperPyError):
    """Error raised for authorization issues."""

    pass


class RateLimitError(PepperPyError):
    """Error raised when a rate limit is exceeded."""

    pass


class ServerError(PepperPyError):
    """Error raised for server issues."""

    pass


class ClientError(PepperPyError):
    """Error raised for client issues."""

    pass


class NotImplementedError(PepperPyError):
    """Error raised when a feature is not implemented."""

    pass


class DeprecatedError(PepperPyError):
    """Error raised when a deprecated feature is used."""

    pass


class SerializationError(PepperPyError):
    """Error raised when serialization or deserialization fails."""

    pass


class ImportError(PepperPyError):
    """Error raised when a required dependency is not installed.

    This is different from Python's built-in ImportError and is used
    specifically for missing optional dependencies in PepperPy.
    """

    def __init__(
        self,
        message: str,
        package: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new import error.

        Args:
            message: The error message
            package: The name of the package that could not be imported
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.package = package
        if package:
            self.details["package"] = package


# ---- Provider Errors ----


class ProviderError(PepperPyError):
    """Error raised for provider-related issues."""

    pass


class ProviderNotFoundError(ProviderError):
    """Error raised when a provider is not found."""

    pass


class ProviderConfigError(ProviderError):
    """Error raised for provider configuration issues."""

    pass


class ProviderAuthenticationError(ProviderError):
    """Error raised when provider authentication fails."""

    pass


class ProviderRateLimitError(ProviderError):
    """Error raised when a provider rate limit is exceeded."""

    pass


class ProviderTimeoutError(ProviderError):
    """Error raised when a provider operation times out."""

    pass


class ProviderNetworkError(ProviderError):
    """Error raised for provider network issues."""

    pass


class ProviderServerError(ProviderError):
    """Error raised for provider server issues."""

    pass


# ---- Registry Errors ----


class RegistryError(PepperPyError):
    """Error raised for registry-related issues."""

    pass


class ItemNotFoundError(RegistryError):
    """Error raised when an item is not found in a registry."""

    pass


class ItemAlreadyExistsError(RegistryError):
    """Error raised when an item already exists in a registry."""

    pass


# ---- Storage Errors ----


class StorageError(PepperPyError):
    """Error raised for storage-related issues."""

    pass


class StorageNotFoundError(StorageError):
    """Error raised when a storage item is not found."""

    pass


class StorageWriteError(StorageError):
    """Error raised when writing to storage fails."""

    pass


class StorageReadError(StorageError):
    """Error raised when reading from storage fails."""

    pass


class StorageDeleteError(StorageError):
    """Error raised when deleting from storage fails."""

    pass


# ---- Data Errors ----


class SchemaError(PepperPyError):
    """Error raised for schema-related issues."""

    pass


class TransformError(PepperPyError):
    """Error raised for data transformation issues."""

    pass


class QueryError(PepperPyError):
    """Error raised for query-related issues."""

    pass


# ---- LLM Errors ----


class LLMError(PepperPyError):
    """Error raised for LLM-related issues."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new LLM error.

        Args:
            message: The error message
            provider: The name of the LLM provider
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.provider = provider

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.provider:
            result["provider"] = self.provider
        return result


class LLMConfigError(LLMError):
    """Error raised when there is a configuration issue with an LLM provider."""

    pass


class LLMAuthenticationError(LLMError):
    """Error raised when authentication with an LLM provider fails."""

    pass


class LLMRateLimitError(LLMError):
    """Error raised when an LLM provider's rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new rate limit error.

        Args:
            message: The error message
            provider: The name of the LLM provider
            retry_after: The number of seconds to wait before retrying
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, provider, code, details)
        self.retry_after = retry_after

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.retry_after is not None:
            result["retry_after"] = self.retry_after
        return result


class LLMContextLengthError(LLMError):
    """Error raised when the input context length exceeds the model's limit."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None,
        current_tokens: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new context length error.

        Args:
            message: The error message
            provider: The name of the LLM provider
            max_tokens: The maximum number of tokens allowed
            current_tokens: The current number of tokens
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, provider, code, details)
        self.max_tokens = max_tokens
        self.current_tokens = current_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.current_tokens is not None:
            result["current_tokens"] = self.current_tokens
        return result


class LLMInvalidRequestError(LLMError):
    """Error raised when an invalid request is made to an LLM provider."""

    pass


class LLMAPIError(LLMError):
    """Error raised when there is an API error from an LLM provider."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new API error.

        Args:
            message: The error message
            provider: The name of the LLM provider
            status_code: The HTTP status code
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, provider, code, details)
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.status_code is not None:
            result["status_code"] = self.status_code
        return result


class LLMTimeoutError(LLMError):
    """Error raised when a request to an LLM provider times out."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        timeout: Optional[float] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new timeout error.

        Args:
            message: The error message
            provider: The name of the LLM provider
            timeout: The timeout value in seconds
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, provider, code, details)
        self.timeout = timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.timeout is not None:
            result["timeout"] = self.timeout
        return result


class LLMProviderError(LLMError):
    """Error raised when there is an issue with an LLM provider."""

    pass


class LLMGenerationError(LLMError):
    """Error raised when text generation fails."""

    pass


class LLMEmbeddingError(LLMError):
    """Error raised when embedding generation fails."""

    pass


class LLMTokenizationError(LLMError):
    """Error raised when tokenization fails."""

    pass


class LLMModelNotFoundError(LLMError):
    """Error raised when a model is not found."""

    pass


# ---- RAG Errors ----


class RAGError(PepperPyError):
    """Error raised for RAG-related issues."""

    pass


class DocumentError(RAGError):
    """Error raised when there is an issue with a document."""

    pass


class DocumentLoadError(DocumentError):
    """Error raised when there is an issue loading a document."""

    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new document load error.

        Args:
            message: The error message
            source: The source of the document
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.source:
            result["source"] = self.source
        return result


class DocumentProcessError(DocumentError):
    """Error raised when there is an issue processing a document."""

    pass


class VectorStoreError(StorageError):
    """Error raised when there is an issue with a vector store."""

    def __init__(
        self,
        message: str,
        store_type: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new vector store error.

        Args:
            message: The error message
            store_type: The type of vector store
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.store_type = store_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.store_type:
            result["store_type"] = self.store_type
        return result


class EmbeddingError(RAGError):
    """Error raised when there is an issue with embeddings."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new embedding error.

        Args:
            message: The error message
            model: The embedding model
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.model = model

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.model:
            result["model"] = self.model
        return result


class PipelineError(RAGError):
    """Error raised when there is an issue with a pipeline."""

    pass


class PipelineStageError(PipelineError):
    """Error raised when there is an issue with a pipeline stage."""

    def __init__(
        self,
        message: str,
        stage_name: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new pipeline stage error.

        Args:
            message: The error message
            stage_name: The name of the pipeline stage
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.stage_name = stage_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.stage_name:
            result["stage_name"] = self.stage_name
        return result


class RAGQueryError(RAGError):
    """Error raised when there is an issue with a RAG query."""

    pass


class RetrievalError(RAGError):
    """Error raised when there is an issue with retrieval."""

    pass


class RerankingError(RAGError):
    """Error raised when there is an issue with reranking."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a new reranking error.

        Args:
            message: The error message
            model: The reranking model
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message, code, details)
        self.model = model

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.

        Returns:
            A dictionary containing the error details
        """
        result = super().to_dict()
        if self.model:
            result["model"] = self.model
        return result


class GenerationError(RAGError):
    """Error raised when there is an issue with generation."""

    pass


class RAGRetrievalError(RAGError):
    """Error raised when retrieval fails in a RAG pipeline."""

    pass


class RAGGenerationError(RAGError):
    """Error raised when generation fails in a RAG pipeline."""

    pass


class RAGIndexError(RAGError):
    """Error raised when there is an issue with a RAG index."""

    pass


# ---- Workflow Errors ----


class WorkflowError(PepperPyError):
    """Error raised for workflow-related issues."""

    pass


class WorkflowStepError(WorkflowError):
    """Error raised when a workflow step fails."""

    pass


class WorkflowValidationError(WorkflowError):
    """Error raised when workflow validation fails."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Error raised when workflow execution fails."""

    pass


# ---- Utility Functions ----


def convert_exception(exception: Exception, target_class: Type[Exception]) -> Exception:
    """Convert an exception to a different type.

    Args:
        exception: The exception to convert
        target_class: The target exception class

    Returns:
        The converted exception
    """
    if isinstance(exception, target_class):
        return exception

    # Create a new instance of the target class
    if isinstance(exception, PepperPyError):
        # If the source exception is a PepperPyError, preserve metadata
        message = exception.message
        if issubclass(target_class, PepperPyError):
            # If the target class is a PepperPyError, we can pass code and details
            new_exception = cast(
                PepperPyError,
                target_class(message, code=exception.code, details=exception.details),
            )
        else:
            # Otherwise, just pass the message
            new_exception = cast(PepperPyError, target_class(message))
    else:
        # Otherwise, use the string representation as the message
        message = str(exception)
        new_exception = cast(PepperPyError, target_class(message))

    # Set the cause of the new exception to the original exception
    new_exception.__cause__ = exception

    return new_exception


def wrap_exception(
    exception: Exception, wrapper_class: Type[Exception], message: Optional[str] = None
) -> Exception:
    """Wrap an exception in another exception.

    Args:
        exception: The exception to wrap
        wrapper_class: The wrapper exception class
        message: The message for the wrapper exception, or None to use the original message

    Returns:
        The wrapped exception
    """
    if message is None:
        message = str(exception)

    # Create a new instance of the wrapper class
    new_exception = wrapper_class(message)

    # Set the cause of the new exception to the original exception
    new_exception.__cause__ = exception

    return new_exception


# Export all error classes
__all__ = [
    # Base error
    "PepperPyError",
    # Core errors
    "ConfigError",
    "ValidationError",
    "NotFoundError",
    "DuplicateError",
    "PermissionError",
    "TimeoutError",
    "NetworkError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ServerError",
    "ClientError",
    "NotImplementedError",
    "DeprecatedError",
    "SerializationError",
    "ImportError",
    # Provider errors
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderConfigError",
    "ProviderAuthenticationError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderNetworkError",
    "ProviderServerError",
    # Registry errors
    "RegistryError",
    "ItemNotFoundError",
    "ItemAlreadyExistsError",
    # Storage errors
    "StorageError",
    "StorageNotFoundError",
    "StorageWriteError",
    "StorageReadError",
    "StorageDeleteError",
    # Data errors
    "SchemaError",
    "TransformError",
    "QueryError",
    # LLM errors
    "LLMError",
    "LLMConfigError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMContextLengthError",
    "LLMInvalidRequestError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMProviderError",
    "LLMGenerationError",
    "LLMEmbeddingError",
    "LLMTokenizationError",
    "LLMModelNotFoundError",
    # RAG errors
    "RAGError",
    "DocumentError",
    "DocumentLoadError",
    "DocumentProcessError",
    "VectorStoreError",
    "EmbeddingError",
    "PipelineError",
    "PipelineStageError",
    "RAGQueryError",
    "RetrievalError",
    "RerankingError",
    "GenerationError",
    "RAGRetrievalError",
    "RAGGenerationError",
    "RAGIndexError",
    # Workflow errors
    "WorkflowError",
    "WorkflowStepError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    # Utility functions
    "convert_exception",
    "wrap_exception",
]
