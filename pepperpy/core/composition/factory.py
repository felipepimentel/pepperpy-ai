"""Fábricas para criação de componentes e pipelines.

Este módulo fornece fábricas para criar componentes e pipelines a partir
de configurações.
"""

from typing import Any, List, TypeVar

from pepperpy.core.composition.implementation import ParallelPipeline, StandardPipeline
from pepperpy.core.composition.registry import (
    get_output_component_class,
    get_processor_component_class,
    get_source_component_class,
)
from pepperpy.core.composition.types import (
    ComponentNotFoundError,
    OutputComponent,
    Pipeline,
    ProcessorComponent,
    SourceComponent,
)

# Tipos genéricos para entrada e saída
T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída


class ComponentFactory:
    """Fábrica para criação de componentes.

    Esta classe fornece métodos estáticos para criar componentes a partir
    de configurações.
    """

    @staticmethod
    def create_source_component(
        component_type: str, **kwargs: Any
    ) -> SourceComponent[Any]:
        """Cria um componente de fonte.

        Args:
            component_type: O tipo do componente a ser criado.
            **kwargs: Argumentos adicionais para o construtor do componente.

        Returns:
            Um componente de fonte inicializado.

        Raises:
            ComponentNotFoundError: Se o tipo de componente não for encontrado.
        """
        try:
            component_class = get_source_component_class(component_type)
            return component_class(**kwargs)
        except KeyError:
            raise ComponentNotFoundError(
                f"Componente de fonte '{component_type}' não encontrado"
            )

    @staticmethod
    def create_processor_component(
        component_type: str, **kwargs: Any
    ) -> ProcessorComponent[Any, Any]:
        """Cria um componente de processamento.

        Args:
            component_type: O tipo do componente a ser criado.
            **kwargs: Argumentos adicionais para o construtor do componente.

        Returns:
            Um componente de processamento inicializado.

        Raises:
            ComponentNotFoundError: Se o tipo de componente não for encontrado.
        """
        try:
            component_class = get_processor_component_class(component_type)
            return component_class(**kwargs)
        except KeyError:
            raise ComponentNotFoundError(
                f"Componente de processamento '{component_type}' não encontrado"
            )

    @staticmethod
    def create_output_component(
        component_type: str, **kwargs: Any
    ) -> OutputComponent[Any]:
        """Cria um componente de saída.

        Args:
            component_type: O tipo do componente a ser criado.
            **kwargs: Argumentos adicionais para o construtor do componente.

        Returns:
            Um componente de saída inicializado.

        Raises:
            ComponentNotFoundError: Se o tipo de componente não for encontrado.
        """
        try:
            component_class = get_output_component_class(component_type)
            return component_class(**kwargs)
        except KeyError:
            raise ComponentNotFoundError(
                f"Componente de saída '{component_type}' não encontrado"
            )


class PipelineFactory:
    """Fábrica para criação de pipelines.

    Esta classe fornece métodos estáticos para criar pipelines a partir
    de configurações.
    """

    @staticmethod
    def create_pipeline(
        name: str,
        source: SourceComponent[T],
        processors: List[ProcessorComponent[Any, Any]],
        output: OutputComponent[U],
    ) -> Pipeline[T, U]:
        """Cria um pipeline padrão.

        Args:
            name: O nome do pipeline.
            source: O componente de fonte.
            processors: Os componentes de processamento.
            output: O componente de saída.

        Returns:
            Um pipeline inicializado.
        """
        return StandardPipeline(name, source, processors, output)

    @staticmethod
    def create_parallel_pipeline(
        name: str,
        source: SourceComponent[T],
        processors: List[ProcessorComponent[Any, Any]],
        output: OutputComponent[U],
    ) -> Pipeline[T, U]:
        """Cria um pipeline paralelo.

        Args:
            name: O nome do pipeline.
            source: O componente de fonte.
            processors: Os componentes de processamento.
            output: O componente de saída.

        Returns:
            Um pipeline paralelo inicializado.
        """
        return ParallelPipeline(name, source, processors, output)
