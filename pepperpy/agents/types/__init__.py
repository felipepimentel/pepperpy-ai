"""Specific agent types implemented by the framework

Este módulo define os diferentes tipos de agentes suportados pelo framework,
incluindo:

- Agentes autônomos para execução independente
- Agentes interativos para colaboração com humanos
- Agentes assistentes para tarefas específicas
- Agentes especialistas em domínios particulares
- Agentes de coordenação para orquestração
- Agentes de aprendizado para adaptação contínua
"""

from typing import Dict, List, Optional, Union

from .autonomous import AutonomousAgent
from .interactive import InteractiveAgent
from .task import TaskAssistant

__version__ = "0.1.0"
__all__ = ["AutonomousAgent", "InteractiveAgent", "TaskAssistant"]
