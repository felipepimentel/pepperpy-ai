"""Módulo de vetorização e indexação para RAG

Este módulo combina as funcionalidades de embedding e indexação,
fornecendo uma solução integrada para:

- Vetorização
  - Geração de embeddings
  - Normalização
  - Dimensionalidade
  - Pooling

- Indexação
  - Estruturas de dados eficientes
  - Busca por similaridade
  - Clustering
  - Compressão

- Otimização
  - Cache de embeddings
  - Batch processing
  - Quantização
  - Pruning

O módulo é projetado para:
- Maximizar performance
- Minimizar latência
- Otimizar memória
- Facilitar manutenção
"""

from typing import Dict, List, Optional, Union

from .embedding import EmbeddingConfig, EmbeddingModel
from .indexing import IndexConfig, VectorIndex
from .optimization import VectorOptimizer

__version__ = "0.1.0"
__all__ = [
    "EmbeddingModel",
    "EmbeddingConfig",
    "VectorIndex",
    "IndexConfig",
    "VectorOptimizer",
]
