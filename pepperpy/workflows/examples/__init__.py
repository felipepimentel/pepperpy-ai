"""Exemplos de implementação de workflows.

Este módulo fornece exemplos práticos de implementação de workflows,
demonstrando:

- Tipos de Workflows
  - Workflows simples
  - Workflows complexos
  - Workflows paralelos
  - Workflows aninhados

- Padrões de Implementação
  - Definição de passos
  - Configuração de execução
  - Tratamento de erros
  - Callbacks e eventos

- Casos de Uso
  - Processamento de dados
  - Integração de serviços
  - Automação de tarefas
  - Orquestração de agentes

Os exemplos servem para:
- Demonstrar funcionalidades
- Ilustrar boas práticas
- Facilitar aprendizado
- Validar implementações
"""

from typing import Dict, List, Optional, Union

from .hello_world import HelloWorldWorkflow

__version__ = "0.1.0"
__all__ = [
    "HelloWorldWorkflow",
]
