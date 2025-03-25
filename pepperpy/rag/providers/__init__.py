"""RAG providers for PepperPy."""

from .base import BaseRAGProvider
from .chroma import ChromaProvider
from .oasys import OasysProvider
from .tiny_vector import TinyVectorProvider
from .vectordb import VectorDBProvider

__all__ = [
    "BaseRAGProvider",
    "ChromaProvider",
    "TinyVectorProvider",
    "VectorDBProvider",
    "OasysProvider",
]

# Set default provider
DEFAULT_PROVIDER = ChromaProvider
