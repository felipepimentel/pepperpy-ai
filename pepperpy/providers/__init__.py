"""Unified provider system for PepperPy"""

# Importações para compatibilidade e conveniência
from pepperpy.providers import (
    agent,
    audio,
    cloud,
    config,
    llm,
    storage,
    vision,
)

# Novos módulos a serem adicionados após a migração
# Estes imports serão ativados após a execução do script de migração
# from pepperpy.providers import embedding
# from pepperpy.providers import memory
# from pepperpy.providers import rag

__all__ = [
    "agent",
    "audio",
    "cloud",
    "config",
    "llm",
    "storage",
    "vision",
    # "embedding",  # Será ativado após a migração
    # "memory",     # Será ativado após a migração
    # "rag",        # Será ativado após a migração
]
