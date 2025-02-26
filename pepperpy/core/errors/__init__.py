"""Unified error handling system for PepperPy.

This module provides a comprehensive error handling system including:
1. Base exceptions and error types
2. Error codes and categories
3. Error handlers and middleware
4. Error reporting and logging
5. Error recovery strategies
6. Error hierarchy management
"""

from .handlers import (
    ChainedErrorHandler,
    DefaultErrorHandler,
    ErrorHandler,
    ErrorMiddleware,
)
from .hierarchy import ErrorHierarchy, ErrorNode
from .recovery import ErrorRecoveryStrategy, FallbackStrategy, RetryStrategy
from .reporting import ErrorFormatter, ErrorReport
from .unified import (
    ConfigError,
    LifecycleError,
    PepperError,
    ProviderError,
    ResourceError,
    SecurityError,
    StateError,
    ValidationError,
)

__all__ = [
    # Base exceptions
    "PepperError",
    "ValidationError",
    "ConfigError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "StateError",
    "LifecycleError",
    # Error handling
    "ErrorHandler",
    "DefaultErrorHandler",
    "ChainedErrorHandler",
    "ErrorMiddleware",
    # Error hierarchy
    "ErrorHierarchy",
    "ErrorNode",
    # Error recovery
    "ErrorRecoveryStrategy",
    "RetryStrategy",
    "FallbackStrategy",
    # Error reporting
    "ErrorFormatter",
    "ErrorReport",
]
