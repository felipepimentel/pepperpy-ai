"""Classes base para o domínio de composição.

Este módulo define as classes base para componentes de composição,
incluindo interfaces e implementações abstratas.
"""

import asyncio
import logging
from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast

from pepperpy.core.base import BaseComponent
from pepperpy.core.composition.types import (
    ComponentType,
    ComposablePipeline,
    CompositionResult,
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)
from pepperpy.core.errors import ExecutionError

T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída
V = TypeVar("V")

logger = logging.getLogger(__name__)


class ComposableComponent(BaseComponent, Generic[T, U]):
    """Componente composável base.

    Esta classe define a interface para componentes que podem ser
    compostos em pipelines de processamento.
    """

    def __init__(self, component_type: ComponentType, config: Dict[str, Any]):
        """Inicializa o componente composável.

        Args:
            component_type: Tipo do componente.
            config: Configuração do componente.
        """
        super().__init__()
        self.component_type = component_type
        self.config = config

    @abstractmethod
    async def process(self, input_data: T) -> U:
        """Processa os dados de entrada.

        Args:
            input_data: Dados de entrada.

        Returns:
            Dados processados.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        pass


class SourceComponentBase(ComposableComponent[None, T]):
    """Componente de fonte base.

    Esta classe define a interface para componentes de fonte,
    que são responsáveis por obter dados de fontes externas.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente de fonte.

        Args:
            config: Configuração do componente.
        """
        super().__init__(ComponentType.SOURCE, config)

    @abstractmethod
    async def fetch(self) -> T:
        """Obtém dados da fonte.

        Returns:
            Dados obtidos.

        Raises:
            FetchError: Se ocorrer um erro durante a obtenção dos dados.
        """
        pass

    async def process(self, input_data: None) -> T:
        """Processa os dados de entrada (obtém dados da fonte).

        Args:
            input_data: Não utilizado para componentes de fonte.

        Returns:
            Dados obtidos.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        return await self.fetch()


class ProcessorComponentBase(ComposableComponent[T, U]):
    """Componente de processamento base.

    Esta classe define a interface para componentes de processamento,
    que são responsáveis por transformar dados.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente de processamento.

        Args:
            config: Configuração do componente.
        """
        super().__init__(ComponentType.PROCESSOR, config)

    @abstractmethod
    async def transform(self, data: T) -> U:
        """Transforma os dados.

        Args:
            data: Dados a serem transformados.

        Returns:
            Dados transformados.

        Raises:
            TransformError: Se ocorrer um erro durante a transformação.
        """
        pass

    async def process(self, input_data: T) -> U:
        """Processa os dados de entrada (transforma os dados).

        Args:
            input_data: Dados a serem processados.

        Returns:
            Dados processados.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        return await self.transform(input_data)


class OutputComponentBase(ComposableComponent[T, CompositionResult]):
    """Componente de saída base.

    Esta classe define a interface para componentes de saída,
    que são responsáveis por armazenar ou enviar dados processados.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente de saída.

        Args:
            config: Configuração do componente.
        """
        super().__init__(ComponentType.OUTPUT, config)

    @abstractmethod
    async def output(self, data: T) -> CompositionResult:
        """Envia os dados para o destino.

        Args:
            data: Dados a serem enviados.

        Returns:
            Resultado da operação.

        Raises:
            OutputError: Se ocorrer um erro durante o envio dos dados.
        """
        pass

    async def process(self, input_data: T) -> CompositionResult:
        """Processa os dados de entrada (envia os dados).

        Args:
            input_data: Dados a serem processados.

        Returns:
            Resultado da operação.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        return await self.output(input_data)


class UniversalComposablePipeline(Generic[T]):
    """Pipeline composável universal que permite encadear operações de diferentes domínios.

    Esta classe implementa um pipeline que pode ser composto por fontes de dados,
    processadores e saídas, permitindo a criação de fluxos de processamento
    flexíveis e reutilizáveis.

    Attributes:
        name: Nome do pipeline.
        steps: Lista de passos do pipeline.
        context: Contexto de execução do pipeline.
    """

    def __init__(self, name: Optional[str] = None):
        """Inicializa um novo pipeline composável.

        Args:
            name: Nome do pipeline. Se não for fornecido, será usado "pipeline".
        """
        self.name = name or "pipeline"
        self.steps: List[Tuple[str, Any]] = []
        self.context: Dict[str, Any] = {}

    def source(
        self, source_component: SourceComponent
    ) -> "UniversalComposablePipeline[T]":
        """Adiciona uma fonte de dados ao pipeline.

        Args:
            source_component: Componente que implementa a interface SourceComponent.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("source", source_component))
        return self

    def process(
        self, processor_component: ProcessorComponent
    ) -> "UniversalComposablePipeline[T]":
        """Adiciona um processador ao pipeline.

        Args:
            processor_component: Componente que implementa a interface ProcessorComponent.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("process", processor_component))
        return self

    def output(
        self, output_component: OutputComponent
    ) -> "UniversalComposablePipeline[T]":
        """Adiciona uma saída ao pipeline.

        Args:
            output_component: Componente que implementa a interface OutputComponent.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("output", output_component))
        return self

    def with_context(self, **kwargs) -> "UniversalComposablePipeline[T]":
        """Adiciona valores ao contexto do pipeline.

        Args:
            **kwargs: Pares chave-valor a serem adicionados ao contexto.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.context.update(kwargs)
        return self

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> T:
        """Executa o pipeline com o contexto fornecido.

        Args:
            context: Contexto adicional para a execução. Se fornecido,
                será mesclado com o contexto do pipeline.

        Returns:
            O resultado da execução do pipeline.

        Raises:
            ValueError: Se o pipeline não tiver passos.
            RuntimeError: Se ocorrer um erro durante a execução.
        """
        if not self.steps:
            raise ValueError("Pipeline vazio. Adicione pelo menos um passo.")

        # Preparar contexto
        exec_context = self.context.copy()
        if context:
            exec_context.update(context)

        logger.info(f"Executando pipeline: {self.name}")

        # Executar passos
        result: Any = None
        for step_type, component in self.steps:
            logger.info(f"Executando passo {step_type}: {component}")

            try:
                if step_type == "source":
                    source = cast(SourceComponent, component)
                    result = await source.fetch()
                elif step_type == "process":
                    processor = cast(ProcessorComponent, component)
                    result = await processor.transform(result)
                elif step_type == "output":
                    output = cast(OutputComponent, component)
                    result = await output.output(result)
                else:
                    logger.warning(f"Tipo de passo desconhecido: {step_type}")
            except Exception as e:
                logger.error(f"Erro ao executar passo {step_type}: {e}")
                raise RuntimeError(f"Erro ao executar passo {step_type}: {e}") from e

        return cast(T, result)


class UniversalParallelPipeline(UniversalComposablePipeline[T]):
    """Pipeline universal que executa passos em paralelo.

    Esta classe estende UniversalComposablePipeline para permitir a execução
    de passos em paralelo, quando possível.
    """

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> T:
        """Executa o pipeline com o contexto fornecido, em paralelo quando possível.

        Args:
            context: Contexto adicional para a execução. Se fornecido,
                será mesclado com o contexto do pipeline.

        Returns:
            O resultado da execução do pipeline.

        Raises:
            ValueError: Se o pipeline não tiver passos.
            RuntimeError: Se ocorrer um erro durante a execução.
        """
        if not self.steps:
            raise ValueError("Pipeline vazio. Adicione pelo menos um passo.")

        # Preparar contexto
        exec_context = self.context.copy()
        if context:
            exec_context.update(context)

        logger.info(f"Executando pipeline paralelo: {self.name}")

        # Agrupar passos por tipo
        sources = [
            component for step_type, component in self.steps if step_type == "source"
        ]
        processors = [
            component for step_type, component in self.steps if step_type == "process"
        ]
        outputs = [
            component for step_type, component in self.steps if step_type == "output"
        ]

        # Executar fontes em paralelo
        if sources:
            logger.info(f"Executando {len(sources)} fontes em paralelo")
            source_results = await asyncio.gather(
                *[cast(SourceComponent, source).fetch() for source in sources],
                return_exceptions=True,
            )

            # Verificar erros
            for i, result in enumerate(source_results):
                if isinstance(result, Exception):
                    logger.error(f"Erro ao executar fonte {i}: {result}")
                    raise RuntimeError(
                        f"Erro ao executar fonte {i}: {result}"
                    ) from result

            # Mesclar resultados
            result = source_results
        else:
            result = None

        # Executar processadores em paralelo
        if processors:
            logger.info(f"Executando {len(processors)} processadores em paralelo")
            processor_results = await asyncio.gather(
                *[
                    cast(ProcessorComponent, processor).transform(result)
                    for processor in processors
                ],
                return_exceptions=True,
            )

            # Verificar erros
            for i, proc_result in enumerate(processor_results):
                if isinstance(proc_result, Exception):
                    logger.error(f"Erro ao executar processador {i}: {proc_result}")
                    raise RuntimeError(
                        f"Erro ao executar processador {i}: {proc_result}"
                    ) from proc_result

            # Mesclar resultados
            result = processor_results

        # Executar saídas em paralelo
        if outputs:
            logger.info(f"Executando {len(outputs)} saídas em paralelo")
            output_results = await asyncio.gather(
                *[cast(OutputComponent, output).output(result) for output in outputs],
                return_exceptions=True,
            )

            # Verificar erros
            for i, out_result in enumerate(output_results):
                if isinstance(out_result, Exception):
                    logger.error(f"Erro ao executar saída {i}: {out_result}")
                    raise RuntimeError(
                        f"Erro ao executar saída {i}: {out_result}"
                    ) from out_result

            # Mesclar resultados
            result = output_results

        return cast(T, result)


class BasePipeline(ComposablePipeline[T, U, V]):
    """Implementação base para pipelines de composição.

    Esta classe fornece uma implementação base para pipelines de composição,
    com suporte para inicialização de componentes e execução do pipeline.
    """

    def __init__(self, name: str) -> None:
        """Inicializa o pipeline.

        Args:
            name: Nome do pipeline.
        """
        self.name = name
        self._source: Optional[SourceComponent[T]] = None
        self._processors: List[ProcessorComponent] = []
        self._output: Optional[OutputComponent[U]] = None
        self._initialized = False

    def initialize(
        self,
        source: SourceComponent[T],
        processors: List[ProcessorComponent],
        output: OutputComponent[U],
    ) -> None:
        """Inicializa o pipeline com os componentes.

        Args:
            source: Componente de fonte.
            processors: Lista de componentes de processamento.
            output: Componente de saída.
        """
        self._source = source
        self._processors = processors
        self._output = output
        self._initialized = True

    async def execute(self) -> V:
        """Executa o pipeline.

        Returns:
            Resultado da execução do pipeline.

        Raises:
            ExecutionError: Se o pipeline não foi inicializado ou ocorreu um erro durante a execução.
        """
        if not self._initialized:
            raise ExecutionError(
                f"Pipeline '{self.name}' não foi inicializado com componentes"
            )

        try:
            # Buscar dados da fonte
            if self._source is None:
                raise ExecutionError(f"Pipeline '{self.name}' não tem fonte definida")
            source_data = await self._source.fetch()

            # Processar dados
            processed_data = source_data
            for processor in self._processors:
                processed_data = await processor.transform(processed_data)

            # Gerar saída
            if self._output is None:
                raise ExecutionError(f"Pipeline '{self.name}' não tem saída definida")
            result = await self._output.output(processed_data)

            return cast(V, result)
        except Exception as e:
            logger.error(f"Erro ao executar pipeline '{self.name}': {e}")
            raise ExecutionError(f"Erro ao executar pipeline '{self.name}': {e}") from e
