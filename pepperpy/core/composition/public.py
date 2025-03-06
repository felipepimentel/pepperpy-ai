"""API pública para composição universal.

Este módulo fornece uma API pública para composição universal, permitindo
a composição de componentes de diferentes domínios em pipelines de processamento.
"""

from typing import Any, List, Optional

from pepperpy.core.composition.factory import PipelineFactory
from pepperpy.core.composition.types import (
    OutputComponent,
    Pipeline,
    ProcessorComponent,
    SourceComponent,
)


def compose(name: str) -> "PipelineBuilder":
    """Cria um construtor de pipeline com o nome especificado.

    Args:
        name: O nome do pipeline.

    Returns:
        Um construtor de pipeline.

    Example:
        >>> pipeline = (
        ...     compose("podcast_pipeline")
        ...     .source(Sources.rss("https://news.google.com/rss", max_items=3))
        ...     .process(Processors.summarize(max_length=150))
        ...     .output(Outputs.podcast("podcast.mp3", voice="pt"))
        ... )
        >>> podcast_path = await pipeline.execute()
    """
    builder = PipelineBuilder(name)
    return builder


def compose_parallel(name: str) -> "PipelineBuilder":
    """Cria um construtor de pipeline paralelo com o nome especificado.

    Args:
        name: O nome do pipeline.

    Returns:
        Um construtor de pipeline paralelo.

    Example:
        >>> pipeline = (
        ...     compose_parallel("parallel_rss_pipeline")
        ...     .source(Sources.rss("https://news.google.com/rss", max_items=3))
        ...     .process(Processors.summarize(max_length=150))
        ...     .process(Processors.extract_keywords(max_keywords=5))
        ...     .output(Outputs.file("result.txt"))
        ... )
        >>> result_path = await pipeline.execute()
    """
    builder = PipelineBuilder(name)
    builder._use_parallel = True
    return builder


class PipelineBuilder:
    """Construtor de pipeline.

    Esta classe permite a construção fluente de pipelines, definindo
    a fonte, os processadores e a saída.
    """

    def __init__(self, name: str) -> None:
        """Inicializa um construtor de pipeline.

        Args:
            name: O nome do pipeline.
        """
        self.name = name
        self._source: Optional[SourceComponent] = None
        self._processors: List[ProcessorComponent] = []
        self._output: Optional[OutputComponent] = None
        self._use_parallel = False

    def source(self, source_component: SourceComponent) -> "PipelineBuilder":
        """Define a fonte do pipeline.

        Args:
            source_component: O componente de fonte.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self._source = source_component
        return self

    def process(self, processor_component: ProcessorComponent) -> "PipelineBuilder":
        """Adiciona um processador ao pipeline.

        Args:
            processor_component: O componente de processamento.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self._processors.append(processor_component)
        return self

    def output(self, output_component: OutputComponent) -> "PipelineBuilder":
        """Define a saída do pipeline.

        Args:
            output_component: O componente de saída.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self._output = output_component
        return self

    def build(self) -> Pipeline:
        """Constrói o pipeline.

        Returns:
            O pipeline construído.

        Raises:
            ValueError: Se a fonte, os processadores ou a saída não foram definidos.
        """
        if self._source is None:
            raise ValueError("A fonte do pipeline não foi definida")

        if not self._processors:
            raise ValueError("Nenhum processador foi adicionado ao pipeline")

        if self._output is None:
            raise ValueError("A saída do pipeline não foi definida")

        if self._use_parallel:
            pipeline = PipelineFactory.create_parallel_pipeline(
                self.name, self._source, self._processors, self._output
            )
        else:
            pipeline = PipelineFactory.create_pipeline(
                self.name, self._source, self._processors, self._output
            )

        return pipeline

    async def execute(self) -> Any:
        """Constrói e executa o pipeline.

        Returns:
            O resultado da execução do pipeline.

        Raises:
            ValueError: Se a fonte, os processadores ou a saída não foram definidos.
        """
        pipeline = self.build()
        return await pipeline.execute()
