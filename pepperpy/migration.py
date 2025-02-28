"""
Módulo de migração para o framework PepperPy.

Este módulo contém utilitários para ajudar na migração entre diferentes versões
do framework, incluindo a padronização de providers.
"""

import importlib
import warnings
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, cast

T = TypeVar("T")


def import_from_new_location(
    old_module: str, new_module: str, name: Optional[str] = None
) -> Any:
    """
    Importa um objeto de um novo local, com fallback para o local antigo.

    Args:
        old_module: O caminho do módulo antigo.
        new_module: O caminho do módulo novo.
        name: O nome do objeto a ser importado. Se None, importa o módulo inteiro.

    Returns:
        O objeto importado.

    Raises:
        ImportError: Se o objeto não puder ser importado de nenhum dos locais.
    """
    try:
        if name:
            return getattr(importlib.import_module(new_module), name)
        return importlib.import_module(new_module)
    except ImportError:
        try:
            if name:
                return getattr(importlib.import_module(old_module), name)
            return importlib.import_module(old_module)
        except ImportError:
            raise ImportError(
                f"Não foi possível importar {name or ''} de {new_module} ou {old_module}"
            )


def deprecated_import(old_path: str, new_path: str) -> Callable[[Type[T]], Type[T]]:
    """
    Decorador para marcar uma classe ou função como tendo sido movida para um novo local.

    Args:
        old_path: O caminho antigo do objeto.
        new_path: O novo caminho do objeto.

    Returns:
        O decorador.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        @wraps(cls)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{cls.__name__} foi movido de {old_path} para {new_path}. "
                f"Por favor, atualize suas importações.",
                DeprecationWarning,
                stacklevel=2,
            )
            return cls(*args, **kwargs)

        return cast(Type[T], wrapper)

    return decorator


def provider_migration_warning(source_module: str, target_module: str) -> None:
    """
    Emite um aviso de depreciação para módulos de providers que foram movidos.

    Args:
        source_module: O módulo de origem (ex: "embedding.providers").
        target_module: O módulo de destino (ex: "providers.embedding").
    """
    warnings.warn(
        f"O módulo pepperpy.{source_module} foi movido para pepperpy.{target_module}. "
        f"Por favor, atualize suas importações. Este stub de compatibilidade será removido em uma versão futura.",
        DeprecationWarning,
        stacklevel=2,
    )


# Mapeamento de módulos antigos para novos
PROVIDER_MODULE_MAPPING = {
    "embedding.providers": "providers.embedding",
    "memory.providers": "providers.memory",
    "rag.providers": "providers.rag",
    "cloud.providers": "providers.cloud",
    "llm.providers": "providers.llm",
}


def get_new_provider_module(old_module: str) -> str:
    """
    Retorna o novo caminho de um módulo de provider.

    Args:
        old_module: O caminho antigo do módulo.

    Returns:
        O novo caminho do módulo.
    """
    return PROVIDER_MODULE_MAPPING.get(old_module, old_module)
