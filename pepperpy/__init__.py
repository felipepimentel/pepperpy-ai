"""
PepperPy - Um framework moderno e flexível para aplicações de IA em Python.

PepperPy é um framework que oferece componentes modulares para construção
de aplicações baseadas em IA, com foco em:

- Composição: Combinação de diferentes componentes em pipelines
- Reutilização: Componentes encapsulados e interfaces padronizadas
- Extensibilidade: Fácil adição de novos providers e funcionalidades

Módulos Principais:
    llm: Interação com Large Language Models
    rag: Retrieval Augmented Generation
    data: Manipulação e persistência de dados
    apps: Templates de aplicações pré-configuradas
    workflows: Fluxos de trabalho compostos

Exemplo Básico:
    >>> import pepperpy as pp
    >>> app = pp.apps.TextApp("minha_app")
    >>> result = await app.process("Texto para processar")
"""

from pepperpy import apps, cache, data, events, http, llm, rag, utils, workflows
from pepperpy.core import composition
from pepperpy.version import __version__

__all__ = [
    "__version__",
    "apps",
    "cache",
    "composition",
    "data",
    "events",
    "http",
    "llm",
    "rag",
    "utils",
    "workflows",
]
