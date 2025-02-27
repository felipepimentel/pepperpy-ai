"""Sistema de tratamento de erros do PepperPy

Este módulo define o sistema de tratamento de erros do framework,
fornecendo:

- Hierarquia de Exceções
  - Erros de validação
  - Erros de configuração
  - Erros de execução
  - Erros de sistema

- Tratamento de Erros
  - Captura e propagação
  - Contextualização
  - Logging estruturado
  - Recuperação

- Categorização
  - Por severidade
  - Por origem
  - Por impacto
  - Por ação necessária

O sistema de erros é projetado para:
- Facilitar o diagnóstico
- Permitir recuperação graceful
- Manter rastreabilidade
- Melhorar a experiência do desenvolvedor
"""

from typing import Dict, List, Optional, Union

from .base import (
    ConfigError,
    PepperError,
    RuntimeError,
    SystemError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    "PepperError",
    "ValidationError",
    "ConfigError",
    "RuntimeError",
    "SystemError",
]
