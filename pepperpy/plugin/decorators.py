"""
Decoradores para plugins do PepperPy.

Este módulo fornece decoradores para facilitar a criação e descoberta de plugins.
"""

from typing import Any, TypeVar

T = TypeVar("T")

# Registro global de plugins decorados
REGISTERED_PLUGINS: dict[str, dict[str, type[Any]]] = {}


def plugin(
    plugin_type: str,
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador para marcar uma classe como um plugin do PepperPy.

    Args:
        plugin_type: Tipo de plugin (workflow, llm, etc)
        name: Nome opcional do plugin (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do plugin
    """

    def decorator(cls: type[T]) -> type[T]:
        # Define o nome do plugin com base no parâmetro ou nome da classe
        plugin_name = name or cls.__name__

        # Se o nome não incluir o tipo/domínio e não for um workflow, adicionar como prefixo
        if "/" not in plugin_name and plugin_type != "workflow":
            plugin_name = f"{plugin_type}/{plugin_name}"

        # Armazena metadados na própria classe
        cls.__pepperpy_plugin__ = {
            "name": plugin_name,
            "type": plugin_type,
            "description": description or cls.__doc__ or f"{cls.__name__} plugin",
            "version": version,
        }

        # Registra globalmente
        if plugin_type not in REGISTERED_PLUGINS:
            REGISTERED_PLUGINS[plugin_type] = {}

        REGISTERED_PLUGINS[plugin_type][plugin_name] = cls

        return cls

    return decorator


def workflow(
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador específico para plugins de workflow.

    Args:
        name: Nome opcional do workflow (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do workflow
    """

    def decorator(cls: type[T]) -> type[T]:
        # Define o nome do plugin com base no parâmetro ou nome da classe
        plugin_name = name or cls.__name__

        # Remove any workflow prefix if present
        if plugin_name.startswith("workflow/"):
            plugin_name = plugin_name[len("workflow/") :]

        # Armazena metadados na própria classe
        cls.__pepperpy_plugin__ = {
            "name": plugin_name,
            "type": "workflow",
            "description": description or cls.__doc__ or f"{cls.__name__} plugin",
            "version": version,
        }

        # Registra globalmente
        if "workflow" not in REGISTERED_PLUGINS:
            REGISTERED_PLUGINS["workflow"] = {}

        REGISTERED_PLUGINS["workflow"][plugin_name] = cls

        return cls

    return decorator


def llm_provider(
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador específico para plugins de LLM.

    Args:
        name: Nome opcional do provider (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do provider
    """
    return plugin(
        plugin_type="llm",
        name=name,
        description=description,
        version=version,
    )


def tts_provider(
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador específico para plugins de TTS.

    Args:
        name: Nome opcional do provider (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do provider
    """
    return plugin(
        plugin_type="tts",
        name=name,
        description=description,
        version=version,
    )


def content_processor(
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador específico para plugins de processamento de conteúdo.

    Args:
        name: Nome opcional do processor (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do processor
    """
    return plugin(
        plugin_type="content",
        name=name,
        description=description,
        version=version,
    )


def rag_provider(
    name: str | None = None,
    description: str | None = None,
    version: str = "0.1.0",
):
    """Decorador específico para plugins de RAG.

    Args:
        name: Nome opcional do provider (padrão é o nome da classe)
        description: Descrição opcional
        version: Versão do provider
    """
    return plugin(
        plugin_type="rag",
        name=name,
        description=description,
        version=version,
    )


def get_registered_plugins() -> dict[str, dict[str, type[Any]]]:
    """Obtém todos os plugins registrados.

    Returns:
        Dicionário de plugins registrados por tipo
    """
    return REGISTERED_PLUGINS
