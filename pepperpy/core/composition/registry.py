"""Registro de componentes para o módulo de composição universal.

Este módulo fornece funções para registrar e recuperar componentes de fonte,
processamento e saída.
"""

from typing import Dict, Type

from pepperpy.core.composition.types import (
    OutputComponent,
    OutputComponentRegistry,
    ProcessorComponent,
    ProcessorComponentRegistry,
    SourceComponent,
    SourceComponentRegistry,
)

# Registros de componentes
_source_components: SourceComponentRegistry = {}
_processor_components: ProcessorComponentRegistry = {}
_output_components: OutputComponentRegistry = {}


def register_source_component(
    component_type: str, component_class: Type[SourceComponent]
) -> None:
    """Registra um componente de fonte.

    Args:
        component_type: O tipo do componente.
        component_class: A classe do componente.
    """
    _source_components[component_type] = component_class


def register_processor_component(
    component_type: str, component_class: Type[ProcessorComponent]
) -> None:
    """Registra um componente de processamento.

    Args:
        component_type: O tipo do componente.
        component_class: A classe do componente.
    """
    _processor_components[component_type] = component_class


def register_output_component(
    component_type: str, component_class: Type[OutputComponent]
) -> None:
    """Registra um componente de saída.

    Args:
        component_type: O tipo do componente.
        component_class: A classe do componente.
    """
    _output_components[component_type] = component_class


def get_source_component_class(component_type: str) -> Type[SourceComponent]:
    """Obtém a classe de um componente de fonte.

    Args:
        component_type: O tipo do componente.

    Returns:
        A classe do componente.

    Raises:
        KeyError: Se o componente não estiver registrado.
    """
    return _source_components[component_type]


def get_processor_component_class(component_type: str) -> Type[ProcessorComponent]:
    """Obtém a classe de um componente de processamento.

    Args:
        component_type: O tipo do componente.

    Returns:
        A classe do componente.

    Raises:
        KeyError: Se o componente não estiver registrado.
    """
    return _processor_components[component_type]


def get_output_component_class(component_type: str) -> Type[OutputComponent]:
    """Obtém a classe de um componente de saída.

    Args:
        component_type: O tipo do componente.

    Returns:
        A classe do componente.

    Raises:
        KeyError: Se o componente não estiver registrado.
    """
    return _output_components[component_type]


def list_source_components() -> Dict[str, Type[SourceComponent]]:
    """Lista todos os componentes de fonte registrados.

    Returns:
        Um dicionário com os componentes de fonte registrados.
    """
    return _source_components.copy()


def list_processor_components() -> Dict[str, Type[ProcessorComponent]]:
    """Lista todos os componentes de processamento registrados.

    Returns:
        Um dicionário com os componentes de processamento registrados.
    """
    return _processor_components.copy()


def list_output_components() -> Dict[str, Type[OutputComponent]]:
    """Lista todos os componentes de saída registrados.

    Returns:
        Um dicionário com os componentes de saída registrados.
    """
    return _output_components.copy()


def clear_registries() -> None:
    """Limpa todos os registros de componentes."""
    _source_components.clear()
    _processor_components.clear()
    _output_components.clear()
