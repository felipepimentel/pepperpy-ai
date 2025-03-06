"""Protocolos para composição de componentes.

Este módulo define protocolos comuns para componentes que podem ser compostos
em pipelines, permitindo a criação de fluxos de processamento flexíveis e
reutilizáveis.
"""

from typing import Any, Dict, Generic, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
U = TypeVar("U")


@runtime_checkable
class SourceProtocol(Protocol, Generic[T]):
    """Protocolo para fontes de dados.

    Uma fonte de dados é responsável por buscar dados de uma origem externa
    e fornecê-los para processamento posterior.
    """

    async def fetch(self, context: Dict[str, Any]) -> T:
        """Busca dados da fonte.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Dados obtidos da fonte.
        """
        ...


@runtime_checkable
class ProcessorProtocol(Protocol, Generic[T, U]):
    """Protocolo para processadores.

    Um processador é responsável por transformar dados de um tipo em outro,
    aplicando alguma lógica de processamento.
    """

    async def process(self, content: T, context: Dict[str, Any]) -> U:
        """Processa conteúdo.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo processado.
        """
        ...


@runtime_checkable
class OutputProtocol(Protocol, Generic[T, U]):
    """Protocolo para saídas.

    Uma saída é responsável por gerar um resultado final a partir de dados
    processados, como um arquivo, uma mensagem, ou qualquer outro tipo de saída.
    """

    async def generate(self, content: T, context: Dict[str, Any]) -> U:
        """Gera saída.

        Args:
            content: Conteúdo a ser usado para gerar a saída.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Resultado da geração da saída.
        """
        ...


@runtime_checkable
class ComposableProtocol(Protocol):
    """Protocolo para componentes composáveis.

    Um componente composável pode ser combinado com outros componentes
    para formar um pipeline de processamento.
    """

    def compose(self, next_component: Any) -> "ComposableProtocol":
        """Compõe este componente com o próximo.

        Args:
            next_component: Próximo componente na cadeia de processamento.

        Returns:
            Componente composto.
        """
        ...

    async def execute(
        self, input_data: Any, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Executa o componente com os dados de entrada.

        Args:
            input_data: Dados de entrada para o componente.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Resultado da execução do componente.
        """
        ... 