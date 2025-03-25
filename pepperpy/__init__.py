"""
PepperPy - A versatile Python library for building AI-powered applications.

PepperPy provides a comprehensive set of tools and capabilities for building
AI-powered applications, leveraging Large Language Models (LLMs),
Retrieval-Augmented Generation (RAG), and other AI technologies.

Various domain-specific modules are available:
- llm: Large Language Model integrations
- rag: Retrieval-Augmented Generation capabilities
- storage: Storage system for vectors and documents
- workflow: Workflow management
- core: Core functionality and utilities
- tools: Integrations with external services and platforms

Módulos Principais:
    core: Funcionalidades centrais e utilitários
    data: Manipulação e persistência de dados
    http: Cliente HTTP e utilitários (agora parte de core.http)
    infra: Infraestrutura e serviços compartilhados
    utils: Funções utilitárias

Exemplo Básico:
    >>> import pepperpy as pp
    >>> app = pp.apps.TextApp("minha_app")
    >>> result = await app.process("Texto para processar")
"""

# Core functionality
from pepperpy.core import (
    PepperpyError,
    VerbosityLevel,
    configure_logging,
    get_logger,
)

# Nota: As importações do módulo analysis foram removidas pois 
# esse módulo foi substituído pelo módulo tools/repository

__version__ = "0.1.0"

__all__ = [
    # Core
    "PepperpyError",
    "VerbosityLevel",
    "configure_logging",
    "get_logger",
]
