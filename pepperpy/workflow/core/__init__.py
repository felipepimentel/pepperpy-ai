"""Main components of the workflow system.

Este módulo fornece os componentes fundamentais do sistema de workflows,
incluindo:

- Componentes Base
  - Definições de workflow
  - Passos de execução
  - Estados e transições
  - Callbacks e eventos

- Tipos e Interfaces
  - Tipos de workflow
  - Estados de execução
  - Configurações
  - Protocolos

- Registro e Gerenciamento
  - Registro de workflows
  - Gerenciamento de estado
  - Validação
  - Monitoramento

O módulo core é responsável por:
- Definir a estrutura base
- Garantir consistência
- Facilitar extensibilidade
- Prover abstrações comuns
"""

from .base import BaseWorkflow, WorkflowDefinition, WorkflowStep
from .registry import WorkflowRegistry
from .types import (
    WorkflowCallback,
    WorkflowConfig,
    WorkflowPriority,
    WorkflowStatus,
)

__version__ = "0.1.0"
__all__ = [
    # Base
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    # Registry
    "WorkflowRegistry",
    # Types
    "WorkflowCallback",
    "WorkflowConfig",
    "WorkflowPriority",
    "WorkflowStatus",
]
