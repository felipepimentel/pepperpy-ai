"""Pipeline de composição para o framework PepperPy.

Este módulo implementa um pipeline de composição que permite encadear
componentes de diferentes domínios para criar fluxos de processamento
flexíveis e reutilizáveis.
"""

import asyncio
import logging
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast

from pepperpy.core.protocols.composition import (
    ComposableProtocol,
    OutputProtocol,
    ProcessorProtocol,
    SourceProtocol,
)

T = TypeVar("T")
U = TypeVar("U")

logger = logging.getLogger(__name__)


class ComposablePipeline(Generic[T]):
    """Pipeline composável que permite encadear operações de diferentes domínios.

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

    def source(self, source_component: SourceProtocol) -> "ComposablePipeline[T]":
        """Adiciona uma fonte de dados ao pipeline.

        Args:
            source_component: Componente que implementa o protocolo SourceProtocol.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("source", source_component))
        return self

    def process(
        self, processor_component: ProcessorProtocol
    ) -> "ComposablePipeline[T]":
        """Adiciona um processador ao pipeline.

        Args:
            processor_component: Componente que implementa o protocolo ProcessorProtocol.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("process", processor_component))
        return self

    def output(self, output_component: OutputProtocol) -> "ComposablePipeline[T]":
        """Adiciona uma saída ao pipeline.

        Args:
            output_component: Componente que implementa o protocolo OutputProtocol.

        Returns:
            O próprio pipeline, para permitir encadeamento de métodos.
        """
        self.steps.append(("output", output_component))
        return self

    def with_context(self, **kwargs) -> "ComposablePipeline[T]":
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
                    source = cast(SourceProtocol, component)
                    result = await source.fetch(exec_context)
                elif step_type == "process":
                    processor = cast(ProcessorProtocol, component)
                    result = await processor.process(result, exec_context)
                elif step_type == "output":
                    output = cast(OutputProtocol, component)
                    result = await output.generate(result, exec_context)
                else:
                    logger.warning(f"Tipo de passo desconhecido: {step_type}")
            except Exception as e:
                logger.error(f"Erro ao executar passo {step_type}: {e}")
                raise RuntimeError(f"Erro ao executar passo {step_type}: {e}") from e

        return cast(T, result)


class ParallelPipeline(ComposablePipeline[T]):
    """Pipeline que executa passos em paralelo.

    Esta classe estende ComposablePipeline para permitir a execução
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
                *[
                    cast(SourceProtocol, source).fetch(exec_context)
                    for source in sources
                ],
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
                    cast(ProcessorProtocol, processor).process(result, exec_context)
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
                *[
                    cast(OutputProtocol, output).generate(result, exec_context)
                    for output in outputs
                ],
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


def compose(name: Optional[str] = None) -> ComposablePipeline:
    """Cria um novo pipeline composável.

    Args:
        name: Nome do pipeline. Se não for fornecido, será usado "pipeline".

    Returns:
        Um novo pipeline composável.
    """
    return ComposablePipeline(name)


def compose_parallel(name: Optional[str] = None) -> ParallelPipeline:
    """Cria um novo pipeline paralelo.

    Args:
        name: Nome do pipeline. Se não for fornecido, será usado "pipeline".

    Returns:
        Um novo pipeline paralelo.
    """
    return ParallelPipeline(name)
