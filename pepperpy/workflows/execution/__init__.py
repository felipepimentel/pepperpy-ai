"""Componentes de execução de workflows.

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

from .executor import WorkflowExecutor

__all__ = ["WorkflowExecutor"]
