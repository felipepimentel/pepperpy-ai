"""Implementações de pipelines para o módulo de composição universal.

Este módulo fornece implementações concretas de pipelines para o módulo
de composição universal, incluindo pipelines sequenciais e paralelos.
"""

import asyncio
import logging
from typing import Any, Generic, List, TypeVar, cast

from pepperpy.core.composition.types import (
    OutputComponent,
    Pipeline,
    PipelineExecutionError,
    ProcessingError,
    ProcessorComponent,
    SourceComponent,
    SourceReadError,
)

# Tipos genéricos para entrada e saída
T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída

# Logger para o módulo
logger = logging.getLogger(__name__)


class StandardPipeline(Pipeline[T, U], Generic[T, U]):
    """Pipeline padrão que executa processadores sequencialmente.

    Esta implementação de pipeline executa os processadores em sequência,
    passando a saída de um processador para a entrada do próximo.
    """

    def __init__(
        self,
        name: str,
        source: SourceComponent[T],
        processors: List[ProcessorComponent[Any, Any]],
        output: OutputComponent[U],
    ) -> None:
        """Inicializa um pipeline padrão.

        Args:
            name: O nome do pipeline.
            source: O componente de fonte.
            processors: Os componentes de processamento.
            output: O componente de saída.
        """
        self.name = name
        self.source = source
        self.processors = processors
        self.output = output
        logger.info(f"Pipeline '{name}' criado com {len(processors)} processadores")

    async def execute(self) -> str:
        """Executa o pipeline.

        Returns:
            O resultado da execução do pipeline.

        Raises:
            PipelineExecutionError: Se ocorrer um erro durante a execução do pipeline.
        """
        logger.info(f"Executando pipeline '{self.name}'")

        try:
            # Ler dados da fonte
            logger.debug(f"Pipeline '{self.name}': lendo dados da fonte")
            data = await self.source.read()

            # Processar dados
            current_data: Any = data
            for i, processor in enumerate(self.processors):
                logger.debug(
                    f"Pipeline '{self.name}': executando processador {i + 1}/{len(self.processors)}"
                )
                current_data = await processor.process(current_data)

            # Escrever dados na saída
            logger.debug(f"Pipeline '{self.name}': escrevendo dados na saída")
            result = await self.output.write(cast(U, current_data))

            logger.info(f"Pipeline '{self.name}' executado com sucesso")
            return result

        except SourceReadError as e:
            logger.error(f"Erro ao ler dados da fonte: {e}")
            raise PipelineExecutionError(f"Erro ao ler dados da fonte: {e}") from e
        except ProcessingError as e:
            logger.error(f"Erro ao processar dados: {e}")
            raise PipelineExecutionError(f"Erro ao processar dados: {e}") from e
        except Exception as e:
            logger.error(f"Erro inesperado ao executar pipeline: {e}")
            raise PipelineExecutionError(
                f"Erro inesperado ao executar pipeline: {e}"
            ) from e


class ParallelPipeline(Pipeline[T, U], Generic[T, U]):
    """Pipeline paralelo que executa processadores em paralelo.

    Esta implementação de pipeline executa os processadores em paralelo,
    aplicando todos eles aos mesmos dados de entrada e combinando os resultados.
    """

    def __init__(
        self,
        name: str,
        source: SourceComponent[T],
        processors: List[ProcessorComponent[Any, Any]],
        output: OutputComponent[U],
    ) -> None:
        """Inicializa um pipeline paralelo.

        Args:
            name: O nome do pipeline.
            source: O componente de fonte.
            processors: Os componentes de processamento.
            output: O componente de saída.
        """
        self.name = name
        self.source = source
        self.processors = processors
        self.output = output
        logger.info(
            f"Pipeline paralelo '{name}' criado com {len(processors)} processadores"
        )

    async def execute(self) -> str:
        """Executa o pipeline.

        Returns:
            O resultado da execução do pipeline.

        Raises:
            PipelineExecutionError: Se ocorrer um erro durante a execução do pipeline.
        """
        logger.info(f"Executando pipeline paralelo '{self.name}'")

        try:
            # Ler dados da fonte
            logger.debug(f"Pipeline '{self.name}': lendo dados da fonte")
            data = await self.source.read()

            # Processar dados em paralelo
            logger.debug(
                f"Pipeline '{self.name}': executando {len(self.processors)} processadores em paralelo"
            )
            tasks = [processor.process(data) for processor in self.processors]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verificar se houve erros
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                error_msg = (
                    f"Erros em {len(errors)}/{len(results)} processadores: {errors[0]}"
                )
                logger.error(error_msg)
                raise PipelineExecutionError(error_msg) from errors[0]

            # Combinar resultados (neste exemplo, usamos o último resultado)
            # Em uma implementação real, você pode querer uma estratégia mais sofisticada
            combined_result = results[-1] if results else data

            # Escrever dados na saída
            logger.debug(f"Pipeline '{self.name}': escrevendo dados na saída")
            result = await self.output.write(cast(U, combined_result))

            logger.info(f"Pipeline paralelo '{self.name}' executado com sucesso")
            return result

        except SourceReadError as e:
            logger.error(f"Erro ao ler dados da fonte: {e}")
            raise PipelineExecutionError(f"Erro ao ler dados da fonte: {e}") from e
        except Exception as e:
            logger.error(f"Erro inesperado ao executar pipeline: {e}")
            raise PipelineExecutionError(
                f"Erro inesperado ao executar pipeline: {e}"
            ) from e
