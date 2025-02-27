"""Core workflow components.

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
from .types import WorkflowCallback, WorkflowStatus

__all__ = [
    "BaseWorkflow",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowCallback",
    "WorkflowStatus",
]
