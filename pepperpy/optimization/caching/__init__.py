"""Cache geral para otimização de performance.

Este módulo implementa um sistema de cache para otimização geral de performance,
focando em:

- Cache de Dados
  - Resultados de computação
  - Dados frequentes
  - Recursos externos
  - Consultas comuns

- Características Gerais
  - Política de expiração
  - Limite de tamanho
  - Persistência
  - Distribuição

Este cache é diferente do cache de agentes (pepperpy/memory/cache.py)
pois é focado em:
- Otimizar performance geral
- Reduzir carga em recursos
- Minimizar latência
- Economizar banda

O módulo fornece:
- Cache local
- Cache distribuído
- Políticas configuráveis
- Métricas de performance
"""

from typing import Dict, List, Optional, Union

from .distributed import DistributedCache
from .local import LocalCache
from .policy import CachePolicy

__version__ = "0.1.0"
__all__ = [
    "LocalCache",
    "DistributedCache",
    "CachePolicy",
]
