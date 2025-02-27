"""Protocolos e interfaces do PepperPy

Este módulo define os protocolos e interfaces fundamentais do framework,
incluindo:

- Ciclo de Vida
  - Inicialização
  - Execução
  - Finalização
  - Estados

- Capacidades
  - Serialização
  - Validação
  - Observabilidade
  - Configuração

- Comunicação
  - Eventos
  - Mensagens
  - Callbacks
  - Streams

Os protocolos são essenciais para:
- Definir contratos claros
- Garantir extensibilidade
- Permitir polimorfismo
- Facilitar testes
"""

from typing import Dict, List, Optional, Protocol, Union

from .lifecycle import Lifecycle
from .messaging import MessageHandler
from .observable import Observable, Observer
from .serialization import Serializable
from .validation import Validatable

__version__ = "0.1.0"
__all__ = [
    "Lifecycle",
    "MessageHandler",
    "Observable",
    "Observer",
    "Serializable",
    "Validatable",
]
