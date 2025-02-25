"""Core module for Pepperpy.

This module provides core functionality including:
- Security
- Configuration
- Error handling
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
from pepperpy.core.models import BaseModel, ModelT
from pepperpy.security import (
    SecurityContext,
    SecurityLevel,
)
from pepperpy.security.decorators import (
    require_permission,
    require_role,
    require_security_level,
)
from pepperpy.security.providers import (
    EncryptedSecurityProvider,
    SimpleSecurityProvider,
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
    "SecurityError",
    "StateError",
    "LifecycleError",
    # Models
    "BaseModel",
    "ModelT",
    # Security
    "SecurityContext",
    "SecurityLevel",
    "EncryptedSecurityProvider",
    "SimpleSecurityProvider",
    "require_permission",
    "require_role",
    "require_security_level",
]

__version__ = "0.1.0"
