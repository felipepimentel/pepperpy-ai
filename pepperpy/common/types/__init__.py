"""Type system for PepperPy.

This module defines the framework's fundamental type system,
providing:

- Base Types
  - Components
  - Identifiers
  - Configurations
  - Metadata

- Tipos Genéricos
  - Eventos
  - Resultados
  - Estados
  - Prioridades

- Tipos Específicos
  - Agentes
  - Recursos
  - Provedores
  - Workflows

O sistema de tipos é projetado para:
- Garantir type safety
- Facilitar refatoração
- Melhorar documentação
- Permitir extensibilidade
"""

from .base import (
    BaseComponent,
    ComponentID,
    Metadata,
)
from .enums import (
    AgentID,
    AgentState,
    CapabilityID,
    ComponentState,
    ErrorCategory,
    IndexType,
    LogLevel,
    ProviderID,
    ProviderType,
    ResourceID,
    ResourceType,
    TaskStatus,
    WorkflowID,
)
from .results import Result

__version__ = "0.1.0"
__all__ = [
    # Base types
    "BaseComponent",
    "ComponentID",
    "Metadata",
    # Enums
    "AgentID",
    "AgentState",
    "CapabilityID",
    "ComponentState",
    "ErrorCategory",
    "IndexType",
    "LogLevel",
    "ProviderID",
    "ProviderType",
    "ResourceID",
    "ResourceType",
    "TaskStatus",
    "WorkflowID",
    # Results
    "Result",
]
