"""Model error handling utilities."""

from typing import Any, Dict, Optional

from . import ModelError, OpenAIError, AnthropicError


class ModelRequestError(ModelError):
    """Error raised when model request fails."""
    
    def __init__(
        self,
        message: str,
        model: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            model: Model name.
            provider: Provider name.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.model = model
        self.provider = provider
        self.details = details or {}


class ModelResponseError(ModelError):
    """Error raised when model response is invalid."""
    
    def __init__(
        self,
        message: str,
        model: str,
        provider: str,
        response: Any,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            model: Model name.
            provider: Provider name.
            response: Invalid model response.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.model = model
        self.provider = provider
        self.response = response
        self.details = details or {}


class ModelTimeoutError(ModelError):
    """Error raised when model request times out."""
    
    def __init__(
        self,
        message: str,
        model: str,
        provider: str,
        timeout: float,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            model: Model name.
            provider: Provider name.
            timeout: Timeout duration in seconds.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.model = model
        self.provider = provider
        self.timeout = timeout
        self.details = details or {}


class OpenAIRequestError(OpenAIError, ModelRequestError):
    """Error raised when OpenAI request fails."""
    pass


class OpenAIResponseError(OpenAIError, ModelResponseError):
    """Error raised when OpenAI response is invalid."""
    pass


class OpenAITimeoutError(OpenAIError, ModelTimeoutError):
    """Error raised when OpenAI request times out."""
    pass


class AnthropicRequestError(AnthropicError, ModelRequestError):
    """Error raised when Anthropic request fails."""
    pass


class AnthropicResponseError(AnthropicError, ModelResponseError):
    """Error raised when Anthropic response is invalid."""
    pass


class AnthropicTimeoutError(AnthropicError, ModelTimeoutError):
    """Error raised when Anthropic request times out."""
    pass 