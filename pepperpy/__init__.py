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
    http: Cliente HTTP e utilitários (agora parte de core.http)
    infra: Infraestrutura e serviços compartilhados
    utils: Funções utilitárias

Exemplo Básico:
    >>> import pepperpy as pp
    >>> app = pp.apps.TextApp("minha_app")
    >>> result = await app.process("Texto para processar")
"""

# Re-export core components
from pepperpy.core import PepperpyError, __version__

# Export to __all__
__all__ = [
    "__version__",
    "PepperpyError",
]
