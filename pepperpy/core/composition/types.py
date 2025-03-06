"""Definições de tipos para o módulo de composição universal.

Este módulo define as interfaces e tipos para os componentes de composição,
incluindo fontes, processadores e saídas.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Generic, Protocol, TypeVar

# Definição de tipos genéricos para entrada e saída de componentes
T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída
V = TypeVar("V")  # Tipo de resultado final

# Definição do tipo de resultado de composição
CompositionResult = str


class ComponentType(Enum):
    """Tipos de componentes de composição."""

    SOURCE = "source"
    PROCESSOR = "processor"
    OUTPUT = "output"


class SourceComponent(Generic[T], ABC):
    """Interface base para componentes de fonte.

    Os componentes de fonte são responsáveis por fornecer dados para o pipeline.
    """

    @abstractmethod
    async def read(self) -> T:
        """Lê dados da fonte.

        Returns:
            T: Os dados lidos da fonte.

        Raises:
            SourceReadError: Se ocorrer um erro ao ler da fonte.
        """
        pass

    @abstractmethod
    async def fetch(self) -> T:
        """Obtém dados da fonte.

        Returns:
            T: Os dados obtidos da fonte.

        Raises:
            SourceReadError: Se ocorrer um erro ao obter dados da fonte.
        """
        pass


class ProcessorComponent(Generic[T, U], ABC):
    """Interface base para componentes de processamento.

    Os componentes de processamento são responsáveis por transformar dados
    de um tipo para outro.
    """

    @abstractmethod
    async def process(self, data: T) -> U:
        """Processa os dados de entrada.

        Args:
            data: Os dados a serem processados.

        Returns:
            U: Os dados processados.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        pass

    @abstractmethod
    async def transform(self, data: T) -> U:
        """Transforma os dados de entrada.

        Args:
            data: Os dados a serem transformados.

        Returns:
            U: Os dados transformados.

        Raises:
            ProcessingError: Se ocorrer um erro durante a transformação.
        """
        pass


class OutputComponent(Generic[T], ABC):
    """Interface base para componentes de saída.

    Os componentes de saída são responsáveis por escrever dados em algum destino.
    """

    @abstractmethod
    async def write(self, data: T) -> str:
        """Escreve os dados no destino.

        Args:
            data: Os dados a serem escritos.

        Returns:
            str: Um identificador ou caminho para o resultado da escrita.

        Raises:
            OutputWriteError: Se ocorrer um erro ao escrever no destino.
        """
        pass

    @abstractmethod
    async def output(self, data: T) -> CompositionResult:
        """Envia os dados para o destino.

        Args:
            data: Os dados a serem enviados.

        Returns:
            CompositionResult: O resultado da operação.

        Raises:
            OutputWriteError: Se ocorrer um erro ao enviar os dados.
        """
        pass


class ComposablePipeline(Generic[T, U, V], Protocol):
    """Interface para pipelines composáveis.

    Os pipelines composáveis são responsáveis por orquestrar a execução de componentes
    de fonte, processamento e saída.
    """

    @abstractmethod
    async def execute(self) -> V:
        """Executa o pipeline.

        Returns:
            V: O resultado da execução do pipeline.

        Raises:
            PipelineExecutionError: Se ocorrer um erro durante a execução do pipeline.
        """
        pass


class Pipeline(Generic[T, U], ABC):
    """Interface base para pipelines.

    Os pipelines são responsáveis por orquestrar a execução de componentes
    de fonte, processamento e saída.
    """

    @abstractmethod
    async def execute(self) -> U:
        """Executa o pipeline.

        Returns:
            U: O resultado da execução do pipeline.

        Raises:
            PipelineExecutionError: Se ocorrer um erro durante a execução do pipeline.
        """
        pass


# Aliases de tipo para facilitar o uso
SourceComponentType = TypeVar("SourceComponentType", bound=SourceComponent)
ProcessorComponentType = TypeVar("ProcessorComponentType", bound=ProcessorComponent)
OutputComponentType = TypeVar("OutputComponentType", bound=OutputComponent)

# Dicionários de componentes
SourceComponentRegistry = Dict[str, type[SourceComponent]]
ProcessorComponentRegistry = Dict[str, type[ProcessorComponent]]
OutputComponentRegistry = Dict[str, type[OutputComponent]]


# Erros específicos
class ComponentNotFoundError(Exception):
    """Erro lançado quando um componente não é encontrado no registro."""

    pass


class SourceReadError(Exception):
    """Erro lançado quando ocorre um problema ao ler de uma fonte."""

    pass


class ProcessingError(Exception):
    """Erro lançado quando ocorre um problema durante o processamento."""

    pass


class OutputWriteError(Exception):
    """Erro lançado quando ocorre um problema ao escrever em um destino."""

    pass


class PipelineExecutionError(Exception):
    """Erro lançado quando ocorre um problema durante a execução do pipeline."""

    pass
