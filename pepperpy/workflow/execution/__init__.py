"""Execução e controle de workflows.

Este módulo implementa o sistema de execução de workflows,
fornecendo:

- Execução
  - Execução síncrona e assíncrona
  - Paralelismo e concorrência
  - Controle de fluxo
  - Tratamento de erros

- Monitoramento
  - Estado de execução
  - Progresso
  - Métricas
  - Logs

- Controle
  - Início e parada
  - Pausa e retomada
  - Cancelamento
  - Timeout

O módulo de execução é responsável por:
- Gerenciar ciclo de vida
- Garantir confiabilidade
- Otimizar performance
- Prover observabilidade
"""

from typing import Dict, List, Optional, Union

from .executor import WorkflowExecutor
from .pipeline import Pipeline

__version__ = "0.1.0"
__all__ = [
    "WorkflowExecutor",
    "Pipeline",
]
