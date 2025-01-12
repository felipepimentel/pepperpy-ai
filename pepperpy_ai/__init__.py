"""PepperPy AI - A flexible AI library with modular provider support."""

from .capabilities.base import BaseCapability, CapabilityConfig
from .capabilities.chat.base import ChatCapability, ChatConfig
from .capabilities.rag.base import RAGCapability, Document, RAGConfig
from .exceptions import (
    CapabilityError,
    ConfigurationError,
    DependencyError,
    PepperPyAIError,
    ProviderError,
    ValidationError,
)
from .providers.base import BaseProvider
from .responses import AIResponse
from .types import Message, MessageRole
from .utils import (
    check_dependency,
    format_exception,
    get_missing_dependencies,
    merge_configs,
    safe_import,
    verify_dependencies,
)

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseCapability",
    "ChatCapability",
    "BaseProvider",
    "RAGCapability",
    # Configuration classes
    "CapabilityConfig",
    "ChatConfig",
    "RAGConfig",
    # Data classes
    "AIResponse",
    "Document",
    "Message",
    # Enums
    "MessageRole",
    # Exceptions
    "CapabilityError",
    "ConfigurationError",
    "DependencyError",
    "PepperPyAIError",
    "ProviderError",
    "ValidationError",
    # Utilities
    "check_dependency",
    "format_exception",
    "get_missing_dependencies",
    "merge_configs",
    "safe_import",
    "verify_dependencies",
]

# Optional implementations
try:
    from .capabilities.embeddings.base import BaseEmbeddingsCapability
    from .embeddings.base import EmbeddingsConfig
    from .capabilities.embeddings.simple import SimpleEmbeddingsCapability
    from .capabilities.rag.simple import SimpleRAGCapability
    __all__.extend([
        "BaseEmbeddingsCapability",
        "EmbeddingsConfig",
        "SimpleEmbeddingsCapability",
        "SimpleRAGCapability",
    ])
except ImportError:
    pass
