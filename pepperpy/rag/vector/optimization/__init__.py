"""Otimizações para índices vetoriais em RAG.

Este módulo implementa otimizações para melhorar a eficiência e performance
dos índices vetoriais no sistema RAG, incluindo:

- Otimizações de Memória
  - Compressão de vetores
  - Quantização
  - Pruning
  - Caching

- Otimizações de Busca
  - Indexação aproximada
  - Clustering
  - Particionamento
  - Paralelização

- Otimizações de Qualidade
  - Normalização
  - Dimensionalidade
  - Ponderação
  - Filtragem

O módulo fornece:
- Algoritmos eficientes
- Estruturas otimizadas
- Métricas de performance
- Configurações ajustáveis
"""

from typing import Dict, List, Optional, Union

from .caching import VectorCache
from .compression import PCACompressor, QuantizationCompressor, VectorCompressor
from .pruning import ThresholdPruner, TopKPruner, VectorPruner

__version__ = "0.1.0"
__all__ = [
    # Caching
    "VectorCache",
    # Compression
    "VectorCompressor",
    "PCACompressor",
    "QuantizationCompressor",
    # Pruning
    "VectorPruner",
    "ThresholdPruner",
    "TopKPruner",
]
