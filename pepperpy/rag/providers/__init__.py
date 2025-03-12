"""RAG Providers for PepperPy.

This module provides implementations of various RAG providers for the PepperPy framework,
including embedding, reranking, and generation providers.
"""

from __future__ import annotations

from pepperpy.rag.providers.base import (
    BaseEmbeddingProvider,
    BaseGenerationProvider,
    BaseProvider,
    BaseRerankingProvider,
)

# Import REST-based providers
from pepperpy.rag.providers.rest import (
    RESTEmbeddingProvider,
    RESTGenerationProvider,
    RESTRerankingProvider,
)

# Try to import providers that depend on optional libraries
try:
    from pepperpy.rag.providers.embedding import (
        MockEmbeddingProvider,
        OpenAIEmbeddingProvider,
    )
except ImportError:
    # If the optional dependencies are not installed, these providers won't be available
    pass

try:
    from pepperpy.rag.providers.generation import (
        MockGenerationProvider,
        OpenAIGenerationProvider,
    )
except ImportError:
    pass

try:
    from pepperpy.rag.providers.reranking import (
        MockRerankingProvider,
    )
except ImportError:
    pass

# Tenta importar provedores que dependem de bibliotecas opcionais
try:
    from pepperpy.rag.providers.reranking import CrossEncoderProvider

    _has_cross_encoder = True
except ImportError:
    _has_cross_encoder = False

# Exportação pública
__all__ = [
    # Base providers
    "BaseProvider",
    "BaseEmbeddingProvider",
    "BaseGenerationProvider",
    "BaseRerankingProvider",
    # Embedding providers
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    # Generation providers
    "MockGenerationProvider",
    "OpenAIGenerationProvider",
    # Reranking providers
    "MockRerankingProvider",
    # REST-based providers
    "RESTEmbeddingProvider",
    "RESTGenerationProvider",
    "RESTRerankingProvider",
]

# Adiciona provedores opcionais ao __all__ se disponíveis
if _has_cross_encoder:
    __all__.append("CrossEncoderProvider")
