"""Error handling for Pepperpy framework."""

from typing import Any, Dict, Optional
from .constants import ErrorCode

class PepperpyError(Exception):
    """Base exception class for Pepperpy framework."""
    
    def __init__(
        self,
        message: str,
        code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the error.
        
        Args:
            message: Error message
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format.
        
        Returns:
            Dictionary containing error information.
        """
        return {
            "message": self.message,
            "code": self.code.value if self.code else None,
            "details": self.details
        }

class ConfigurationError(PepperpyError):
    """Configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize configuration error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.CONFIGURATION_ERROR,
            details=details
        )

class InitializationError(PepperpyError):
    """Initialization-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize initialization error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.INITIALIZATION_ERROR,
            details=details
        )

class ProviderError(PepperpyError):
    """Provider-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize provider error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.PROVIDER_ERROR,
            details=details
        )

class ValidationError(PepperpyError):
    """Validation-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.VALIDATION_ERROR,
            details=details
        )

class RuntimeError(PepperpyError):
    """Runtime-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize runtime error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.RUNTIME_ERROR,
            details=details
        )

class TimeoutError(PepperpyError):
    """Timeout-related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize timeout error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            code=ErrorCode.TIMEOUT_ERROR,
            details=details
        )
