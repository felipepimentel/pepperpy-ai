"""Módulo de composição universal.

Este módulo fornece uma API para composição universal, permitindo
a composição de componentes de diferentes domínios em pipelines de processamento.

Example:
    >>> from pepperpy.core.composition import compose, Sources, Processors, Outputs
    >>>
    >>> # Criar um pipeline para gerar um podcast a partir de um feed RSS
    >>> pipeline = (
    ...     compose("podcast_pipeline")
    ...     .source(Sources.rss("https://news.google.com/rss", max_items=3))
    ...     .process(Processors.summarize(max_length=150))
    ...     .output(Outputs.podcast("podcast.mp3", voice="pt"))
    ... )
    >>>
    >>> # Executar o pipeline
    >>> podcast_path = await pipeline.execute()
"""

from pepperpy.core.composition.components import Outputs, Processors, Sources
from pepperpy.core.composition.public import compose, compose_parallel

__all__ = ["compose", "compose_parallel", "Sources", "Processors", "Outputs"]
