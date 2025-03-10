"""Error classes for the LLM module.

This module defines error classes specific to LLM operations.
"""

from typing import Any, Dict, Optional

from pepperpy.errors import PepperPyError


class LLMError(PepperPyError):
    """Base class for LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an LLM error.

        Args:
            message: The error message
            provider: The name of the LLM provider that raised the error
            details: Additional details about the error
        """
        super().__init__(message)
        self.provider = provider
        self.details = details or {}


class LLMConfigError(LLMError):
    """Error raised when there is a configuration issue with an LLM provider."""

    pass


class LLMAuthenticationError(LLMError):
    """Error raised when there is an authentication issue with an LLM provider."""

    pass


class LLMRateLimitError(LLMError):
    """Error raised when an LLM provider's rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a rate limit error.

        Args:
            message: The error message
            provider: The name of the LLM provider that raised the error
            retry_after: The number of seconds to wait before retrying
            details: Additional details about the error
        """
        super().__init__(message, provider, details)
        self.retry_after = retry_after


class LLMContextLengthError(LLMError):
    """Error raised when the input context length exceeds the provider's limit."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None,
        current_tokens: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a context length error.

        Args:
            message: The error message
            provider: The name of the LLM provider that raised the error
            max_tokens: The maximum number of tokens allowed
            current_tokens: The current number of tokens
            details: Additional details about the error
        """
        super().__init__(message, provider, details)
        self.max_tokens = max_tokens
        self.current_tokens = current_tokens


class LLMInvalidRequestError(LLMError):
    """Error raised when an invalid request is made to an LLM provider."""

    pass


class LLMAPIError(LLMError):
    """Error raised when there is an API error with an LLM provider."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an API error.

        Args:
            message: The error message
            provider: The name of the LLM provider that raised the error
            status_code: The HTTP status code of the error
            details: Additional details about the error
        """
        super().__init__(message, provider, details)
        self.status_code = status_code


class LLMTimeoutError(LLMError):
    """Error raised when a request to an LLM provider times out."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        timeout: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a timeout error.

        Args:
            message: The error message
            provider: The name of the LLM provider that raised the error
            timeout: The timeout value in seconds
            details: Additional details about the error
        """
        super().__init__(message, provider, details)
        self.timeout = timeout
