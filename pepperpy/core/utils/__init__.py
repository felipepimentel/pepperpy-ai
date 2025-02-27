"""Utilitários e funções auxiliares do core.

Este módulo fornece utilitários e funções auxiliares usados em todo o framework,
incluindo:

- Manipulação de Dados
  - Conversão de tipos
  - Validação de dados
  - Serialização
  - Formatação

- Gerenciamento de Recursos
  - Alocação
  - Limpeza
  - Monitoramento
  - Cache

- Otimizações
  - Performance
  - Memória
  - I/O
  - Concorrência

O módulo é projetado para:
- Centralizar funções comuns
- Evitar duplicação
- Padronizar operações
- Facilitar manutenção
"""

from typing import Dict, List, Optional, Union

from .data import DataUtils
from .io import IOUtils
from .system import SystemUtils
from .validation import ValidationUtils

__version__ = "0.1.0"
__all__ = [
    "DataUtils",
    "IOUtils",
    "SystemUtils",
    "ValidationUtils",
]
