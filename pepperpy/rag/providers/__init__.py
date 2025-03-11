"""
PepperPy RAG Providers Module.

Este módulo contém os provedores para o sistema RAG, incluindo embeddings, geração e reranking.
"""

from __future__ import annotations

# Importa as classes base
from pepperpy.rag.providers.base import (
    BaseEmbeddingProvider,
    BaseGenerationProvider,
    BaseProvider,
    BaseRerankingProvider,
)

# Importa os provedores de embedding
from pepperpy.rag.providers.embedding import (
    MockEmbeddingProvider,
    OpenAIEmbeddingProvider,
)

# Importa os provedores de geração
from pepperpy.rag.providers.generation import (
    MockGenerationProvider,
    OpenAIGenerationProvider,
)

# Importa os provedores de reranking
from pepperpy.rag.providers.reranking import (
    MockRerankingProvider,
)

# Tenta importar provedores que dependem de bibliotecas opcionais
try:
    from pepperpy.rag.providers.reranking import CrossEncoderProvider

    _has_cross_encoder = True
except ImportError:
    _has_cross_encoder = False

# Exportação pública
__all__ = [
    # Classes base
    "BaseProvider",
    "BaseEmbeddingProvider",
    "BaseGenerationProvider",
    "BaseRerankingProvider",
    # Provedores de embedding
    "MockEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    # Provedores de geração
    "MockGenerationProvider",
    "OpenAIGenerationProvider",
    # Provedores de reranking
    "MockRerankingProvider",
]

# Adiciona provedores opcionais ao __all__ se disponíveis
if _has_cross_encoder:
    __all__.append("CrossEncoderProvider")
