"""PepperPy AI - A Python library for building AI-powered applications."""

from .core import (
    AIClient,
    AIResponse,
    Cache,
    CacheEntry,
    Function,
    FunctionCall,
    ResponseMetadata,
    Role,
    Template,
    TemplateContext,
)
from .exceptions import (
    CapabilityError,
    ConfigurationError,
    DependencyError,
    PepperPyAIError,
    ProviderError,
    ValidationError,
)
from .types import JsonDict, JsonValue, Message, MessageRole

__version__ = "0.1.0"

__all__ = [
    "AIClient",
    "AIResponse",
    "Cache",
    "CacheEntry",
    "CapabilityError",
    "ConfigurationError",
    "DependencyError",
    "Function",
    "FunctionCall",
    "JsonDict",
    "JsonValue",
    "Message",
    "MessageRole",
    "PepperPyAIError",
    "ProviderError",
    "ResponseMetadata",
    "Role",
    "Template",
    "TemplateContext",
    "ValidationError",
]
