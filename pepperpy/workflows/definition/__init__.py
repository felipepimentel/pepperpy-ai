"""Definição e construção de workflows.

Este módulo fornece as ferramentas para definir e construir workflows,
incluindo:

- Definição de Workflows
  - Estrutura do workflow
  - Configuração de passos
  - Dependências
  - Validações

- Construção de Workflows
  - Padrões de construção
  - Templates
  - Composição
  - Reutilização

- Validação
  - Verificação de estrutura
  - Validação de dependências
  - Checagem de tipos
  - Consistência

O módulo é responsável por:
- Definir interfaces claras
- Garantir consistência
- Facilitar manutenção
- Promover reusabilidade
"""

from typing import Dict, List, Optional, Union

from .builder import WorkflowBuilder
from .factory import WorkflowFactory
from .validator import WorkflowValidator

__version__ = "0.1.0"
__all__ = [
    "WorkflowBuilder",
    "WorkflowFactory",
    "WorkflowValidator",
]
