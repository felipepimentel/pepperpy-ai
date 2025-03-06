"""Factory para componentes do pipeline.

Este módulo fornece factory methods para criar componentes de pipeline,
como fontes, processadores e saídas, seguindo o padrão existente.
"""

import logging
from typing import TypeVar

from pepperpy.core.protocols.composition import (
    OutputProtocol,
    ProcessorProtocol,
    SourceProtocol,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def create_source(source_type: str, **kwargs) -> SourceProtocol:
    """Cria uma fonte de dados com base no tipo especificado.

    Args:
        source_type: Tipo de fonte a ser criada (rss, api, file, etc).
        **kwargs: Parâmetros específicos para o tipo de fonte.

    Returns:
        Uma instância de SourceProtocol.

    Raises:
        ValueError: Se o tipo de fonte não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if source_type == "rss":
        url = kwargs.get("url")
        max_items = kwargs.get("max_items", 5)

        if not url:
            raise ValueError("URL é obrigatório para fontes RSS")

        try:
            from pepperpy.content.sources.rss import RSSSource

            return RSSSource(url=url, max_items=max_items)
        except ImportError:
            logger.warning("Módulo RSSSource não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockRSSSource

            return MockRSSSource(url=url, max_items=max_items)

    elif source_type == "api":
        url = kwargs.get("url")
        method = kwargs.get("method", "GET")
        headers = kwargs.get("headers", {})

        if not url:
            raise ValueError("URL é obrigatório para fontes API")

        try:
            from pepperpy.content.sources.api import APISource

            return APISource(url=url, method=method, headers=headers)
        except ImportError:
            logger.warning("Módulo APISource não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockAPISource

            return MockAPISource(url=url, method=method, headers=headers)

    elif source_type == "file":
        path = kwargs.get("path")
        format = kwargs.get("format", "auto")

        if not path:
            raise ValueError("Path é obrigatório para fontes File")

        try:
            from pepperpy.content.sources.file import FileSource

            return FileSource(path=path, format=format)
        except ImportError:
            logger.warning("Módulo FileSource não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockFileSource

            return MockFileSource(path=path, format=format)

    else:
        raise ValueError(f"Tipo de fonte não suportado: {source_type}")


def create_processor(processor_type: str, **kwargs) -> ProcessorProtocol:
    """Cria um processador com base no tipo especificado.

    Args:
        processor_type: Tipo de processador a ser criado (summarize, translate, classify, etc).
        **kwargs: Parâmetros específicos para o tipo de processador.

    Returns:
        Uma instância de ProcessorProtocol.

    Raises:
        ValueError: Se o tipo de processador não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if processor_type == "summarize":
        max_length = kwargs.get("max_length", 150)
        model = kwargs.get("model", "default")

        try:
            from pepperpy.llm.summarization import SummarizationProcessor

            return SummarizationProcessor(max_length=max_length, model=model)
        except ImportError:
            logger.warning("Módulo SummarizationProcessor não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockSummarizationProcessor

            return MockSummarizationProcessor(max_length=max_length, model=model)

    elif processor_type == "translate":
        target_language = kwargs.get("target_language")
        source_language = kwargs.get("source_language")

        if not target_language:
            raise ValueError(
                "Target language é obrigatório para processadores de tradução"
            )

        try:
            from pepperpy.llm.translation import TranslationProcessor

            return TranslationProcessor(
                target_language=target_language, source_language=source_language
            )
        except ImportError:
            logger.warning("Módulo TranslationProcessor não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockTranslationProcessor

            return MockTranslationProcessor(
                target_language=target_language, source_language=source_language
            )

    elif processor_type == "classify":
        categories = kwargs.get("categories", [])
        model = kwargs.get("model", "default")

        if not categories:
            raise ValueError(
                "Categories é obrigatório para processadores de classificação"
            )

        try:
            from pepperpy.llm.classification import ClassificationProcessor

            return ClassificationProcessor(categories=categories, model=model)
        except ImportError:
            logger.warning(
                "Módulo ClassificationProcessor não encontrado. Usando mock."
            )
            from pepperpy.pipeline.mocks import MockClassificationProcessor

            return MockClassificationProcessor(categories=categories, model=model)

    else:
        raise ValueError(f"Tipo de processador não suportado: {processor_type}")


def create_output(output_type: str, **kwargs) -> OutputProtocol:
    """Cria uma saída com base no tipo especificado.

    Args:
        output_type: Tipo de saída a ser criada (podcast, file, etc).
        **kwargs: Parâmetros específicos para o tipo de saída.

    Returns:
        Uma instância de OutputProtocol.

    Raises:
        ValueError: Se o tipo de saída não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if output_type == "podcast":
        voice = kwargs.get("voice", "en")
        output_path = kwargs.get("output_path", "output.mp3")

        try:
            from pepperpy.multimodal.audio.podcast import PodcastGenerator

            return PodcastGenerator(voice=voice, output_path=output_path)
        except ImportError:
            logger.warning("Módulo PodcastGenerator não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockPodcastGenerator

            return MockPodcastGenerator(voice=voice, output_path=output_path)

    elif output_type == "file":
        path = kwargs.get("path")
        format = kwargs.get("format", "auto")

        if not path:
            raise ValueError("Path é obrigatório para saídas File")

        try:
            from pepperpy.content.outputs.file import FileOutput

            return FileOutput(path=path, format=format)
        except ImportError:
            logger.warning("Módulo FileOutput não encontrado. Usando mock.")
            from pepperpy.pipeline.mocks import MockFileOutput

            return MockFileOutput(path=path, format=format)

    else:
        raise ValueError(f"Tipo de saída não suportado: {output_type}")
