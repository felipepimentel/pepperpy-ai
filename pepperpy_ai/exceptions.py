"""Custom exceptions."""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import uuid

@dataclass
class ErrorContext:
    """Error context information."""
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class PepperpyError(Exception):
    """Base exception for PepperPy errors."""

    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        context: Optional[ErrorContext] = None
    ) -> None:
        """Initialize exception.

        Args:
            message: Error message
            cause: Original exception that caused this error
            context: Error context information
        """
        super().__init__(message)
        self.cause = cause
        self.context = context or ErrorContext()
        self._log_error()

    def with_context(self, **kwargs) -> "PepperpyError":
        """Add context to error.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Self for chaining
        """
        self.context.details.update(kwargs)
        return self

    def _log_error(self) -> None:
        """Log error details."""
        from logging import getLogger
        logger = getLogger(__name__)
        logger.error(
            f"{self.__class__.__name__}: {str(self)}",
            extra={
                "error_type": self.__class__.__name__,
                "trace_id": self.context.trace_id,
                "operation": self.context.operation,
                "details": self.context.details,
                "timestamp": self.context.timestamp.isoformat(),
            }
        )

class AIError(PepperpyError):
    """AI operation error."""
    
    def __init__(
        self,
        message: str,
        model: str = "",
        prompt: str = "",
        **kwargs
    ) -> None:
        """Initialize AI error.
        
        Args:
            message: Error message
            model: AI model name
            prompt: Failed prompt
            **kwargs: Additional context details
        """
        context = ErrorContext(
            operation="ai_operation",
            details={"model": model, "prompt": prompt, **kwargs}
        )
        super().__init__(message, context=context)

class ConfigError(PepperpyError):
    """Configuration error."""
    
    def __init__(
        self,
        message: str,
        config_path: str = "",
        invalid_keys: Optional[list[str]] = None,
        **kwargs
    ) -> None:
        """Initialize config error.
        
        Args:
            message: Error message
            config_path: Path to config file
            invalid_keys: List of invalid configuration keys
            **kwargs: Additional context details
        """
        context = ErrorContext(
            operation="configuration",
            details={
                "config_path": config_path,
                "invalid_keys": invalid_keys or [],
                **kwargs
            }
        )
        super().__init__(message, context=context)

class ProviderError(PepperpyError):
    """Provider error."""
    
    def __init__(
        self,
        message: str,
        provider: str = "",
        operation: str = "",
        response: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Initialize provider error.
        
        Args:
            message: Error message
            provider: Provider name
            operation: Failed operation
            response: Provider response
            **kwargs: Additional context details
        """
        context = ErrorContext(
            operation=f"provider_{operation}",
            details={
                "provider": provider,
                "response": response or {},
                **kwargs
            }
        )
        super().__init__(message, context=context)

class ValidationError(PepperpyError):
    """Validation error."""
    
    def __init__(
        self,
        message: str,
        field: str = "",
        value: Any = None,
        constraints: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Invalid field
            value: Invalid value
            constraints: Validation constraints
            **kwargs: Additional context details
        """
        context = ErrorContext(
            operation="validation",
            details={
                "field": field,
                "value": value,
                "constraints": constraints or {},
                **kwargs
            }
        )
        super().__init__(message, context=context)

class NetworkError(PepperpyError):
    """Network operation error."""
    
    def __init__(
        self,
        message: str,
        url: str = "",
        method: str = "",
        status_code: Optional[int] = None,
        **kwargs
    ) -> None:
        """Initialize network error.
        
        Args:
            message: Error message
            url: Request URL
            method: HTTP method
            status_code: Response status code
            **kwargs: Additional context details
        """
        context = ErrorContext(
            operation="network_request",
            details={
                "url": url,
                "method": method,
                "status_code": status_code,
                **kwargs
            }
        )
        super().__init__(message, context=context)
