"""
PepperPy - Um framework moderno e flexível para aplicações de IA em Python.

PepperPy é um framework que oferece componentes modulares para construção
de aplicações baseadas em IA, com foco em:

- Composição: Combinação de diferentes componentes em pipelines
- Reutilização: Componentes encapsulados e interfaces padronizadas
- Extensibilidade: Fácil adição de novos providers e funcionalidades

Módulos Principais:
    core: Funcionalidades centrais e utilitários
    data: Manipulação e persistência de dados
    http: Cliente HTTP e utilitários
    infra: Infraestrutura e serviços compartilhados
    utils: Funções utilitárias

Exemplo Básico:
    >>> import pepperpy as pp
    >>> app = pp.apps.TextApp("minha_app")
    >>> result = await app.process("Texto para processar")
"""

from pepperpy import (
    core,
    data,
    http,
    infra,
    registry,
    utils,
)
from pepperpy.version import __version__

__all__ = [
    "__version__",
    "core",
    "data",
    "http",
    "infra",
    "registry",
    "utils",
]
