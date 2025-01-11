"""PepperPy AI capabilities module."""

from pepperpy_ai.capabilities.base import BaseCapability, CapabilityConfig
from pepperpy_ai.capabilities.chat.base import BaseChat, ChatConfig
from pepperpy_ai.capabilities.chat.simple import SimpleChat
from pepperpy_ai.capabilities.rag.base import BaseRAG, Document, RAGConfig

__all__ = [
    # Base classes
    "BaseCapability",
    "BaseChat",
    "BaseRAG",
    # Configuration classes
    "CapabilityConfig",
    "ChatConfig",
    "RAGConfig",
    # Data classes
    "Document",
    # Implementations
    "SimpleChat",
]

# Optional implementations
try:
    from pepperpy_ai.capabilities.embeddings.base import BaseEmbedding, EmbeddingConfig
    from pepperpy_ai.capabilities.embeddings.simple import SimpleEmbedding
    from pepperpy_ai.capabilities.rag.simple import SimpleRAG
    __all__.extend([
        "BaseEmbedding",
        "EmbeddingConfig",
        "SimpleEmbedding",
        "SimpleRAG",
    ])
except ImportError:
    pass 