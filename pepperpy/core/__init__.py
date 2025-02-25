"""Core module for Pepperpy.

This module provides core functionality including:
- Security
- Configuration
- Error handling
- Metrics
- Context management
"""

from pepperpy.core.context import (
    clear_context,
    get_context,
    get_context_value,
    set_context,
    update_context,
)
from pepperpy.core.errors.unified import (
    ConfigError,
    LifecycleError,
    PepperError,
    ProviderError,
    ResourceError,
    SecurityError,
    StateError,
    ValidationError,
)
from pepperpy.core.metrics.unified import MetricsManager
from pepperpy.core.models import BaseModel, Field, ModelT
from pepperpy.core.security import (
    EncryptedSecurityProvider,
    SecurityContext,
    SecurityLevel,
    SecurityManager,
    SimpleSecurityProvider,
    require_permission,
    require_role,
    require_security_level,
)

__all__ = [
    # Context
    "get_context",
    "set_context",
    "update_context",
    "get_context_value",
    "clear_context",
    # Errors
    "PepperError",
    "ValidationError",
    "ConfigError",
    "ProviderError",
    "ResourceError",
    "StateError",
    "LifecycleError",
    "SecurityError",
    # Metrics
    "MetricsManager",
    # Models
    "BaseModel",
    "Field",
    "ModelT",
    # Security
    "SecurityContext",
    "SecurityLevel",
    "SecurityManager",
    "SimpleSecurityProvider",
    "EncryptedSecurityProvider",
    "require_security_level",
    "require_permission",
    "require_role",
]

__version__ = "0.1.0"
