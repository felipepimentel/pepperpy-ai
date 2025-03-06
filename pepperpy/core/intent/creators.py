"""Criadores baseados em intenção para o framework PepperPy.

Este módulo implementa criadores baseados em intenção, que permitem
a criação de componentes a partir de descrições de alto nível.
"""

import logging
from typing import Any, Dict, Optional

from pepperpy.core.composition.namespaces import Outputs, Processors, Sources
from pepperpy.core.composition.public import compose

logger = logging.getLogger(__name__)


class Creator:
    """Criador baseado em intenção.

    Esta classe permite criar componentes a partir de descrições de alto nível,
    abstraindo a complexidade da composição de componentes.

    Attributes:
        intent: Intenção do criador.
        config: Configuração do criador.
    """

    def __init__(self, intent: str):
        """Inicializa um novo criador baseado em intenção.

        Args:
            intent: Intenção do criador.
        """
        self.intent = intent
        self.config: Dict[str, Any] = {}

    def from_source(self, source_url: str) -> "Creator":
        """Define a fonte de dados.

        Args:
            source_url: URL da fonte de dados.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        self.config["source_url"] = source_url
        return self

    def with_summary(self, max_length: int = 150) -> "Creator":
        """Adiciona sumarização.

        Args:
            max_length: Tamanho máximo do resumo.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        self.config["summarize"] = True
        self.config["max_length"] = max_length
        return self

    def with_translation(self, target_language: str) -> "Creator":
        """Adiciona tradução.

        Args:
            target_language: Idioma de destino.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        self.config["translate"] = True
        self.config["target_language"] = target_language
        return self

    def to_audio(self, output_path: str, voice: str = "en") -> "Creator":
        """Define saída como áudio.

        Args:
            output_path: Caminho do arquivo de saída.
            voice: Voz a ser usada para síntese de fala.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        self.config["output_type"] = "audio"
        self.config["output_path"] = output_path
        self.config["voice"] = voice
        return self

    def to_file(self, output_path: str) -> "Creator":
        """Define saída como arquivo.

        Args:
            output_path: Caminho do arquivo de saída.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        self.config["output_type"] = "file"
        self.config["output_path"] = output_path
        return self

    def __call__(self) -> "Creator":
        """Retorna self para encadeamento.

        Returns:
            O próprio criador, para permitir encadeamento de métodos.
        """
        return self

    async def execute(self) -> Any:
        """Executa a criação baseada na intenção.

        Returns:
            Resultado da execução.

        Raises:
            ValueError: Se a configuração for inválida.
            RuntimeError: Se ocorrer um erro durante a execução.
        """
        logger.info(f"Executando criador com intenção: {self.intent}")

        # Criar pipeline baseado na intenção e configuração
        pipeline = compose(self.intent)

        # Adicionar fonte
        if "source_url" in self.config:
            if (
                self.config["source_url"].startswith("http")
                and "/rss" in self.config["source_url"]
            ):
                pipeline.source(Sources.rss(self.config["source_url"]))
            else:
                # Tratar como arquivo para qualquer outro caso
                pipeline.source(Sources.file(self.config["source_url"]))

        # Adicionar processadores
        if self.config.get("summarize"):
            pipeline.process(Processors.summarize(self.config.get("max_length", 150)))

        if self.config.get("translate"):
            pipeline.process(
                Processors.translate(self.config.get("target_language", "en"))
            )

        # Adicionar saída
        if self.config.get("output_type") == "audio":
            pipeline.output(
                Outputs.podcast(
                    self.config.get("output_path", "output.mp3"),
                    voice=self.config.get("voice", "en"),
                )
            )
        elif self.config.get("output_type") == "file":
            pipeline.output(Outputs.file(self.config.get("output_path", "output.txt")))

        # Executar pipeline
        return await pipeline.execute()


def create_podcast_from_rss(
    rss_url: str, output_path: str, voice: str = "en"
) -> Creator:
    """Cria um podcast a partir de um feed RSS.

    Args:
        rss_url: URL do feed RSS.
        output_path: Caminho do arquivo de saída.
        voice: Voz a ser usada para síntese de fala.

    Returns:
        Criador configurado para criar um podcast a partir de um feed RSS.
    """
    return (
        Creator("podcast_from_rss")
        .from_source(rss_url)
        .with_summary()
        .to_audio(output_path, voice)
    )


def create_summary_from_document(
    document_path: str, output_path: str, max_length: int = 150
) -> Creator:
    """Cria um resumo a partir de um documento.

    Args:
        document_path: Caminho do documento.
        output_path: Caminho do arquivo de saída.
        max_length: Tamanho máximo do resumo.

    Returns:
        Criador configurado para criar um resumo a partir de um documento.
    """
    return (
        Creator("summary_from_document")
        .from_source(document_path)
        .with_summary(max_length)
        .to_file(output_path)
    )


def translate_document(
    document_path: str, output_path: str, target_language: str
) -> Creator:
    """Traduz um documento.

    Args:
        document_path: Caminho do documento.
        output_path: Caminho do arquivo de saída.
        target_language: Idioma de destino.

    Returns:
        Criador configurado para traduzir um documento.
    """
    return (
        Creator("translate_document")
        .from_source(document_path)
        .with_translation(target_language)
        .to_file(output_path)
    )


async def create_podcast(
    source_url: str,
    output_path: str,
    voice: str = "en",
    max_length: Optional[int] = None,
    max_items: Optional[int] = None,
) -> str:
    """Cria um podcast a partir de um feed RSS.

    Args:
        source_url: URL do feed RSS.
        output_path: Caminho para o arquivo de podcast.
        voice: Voz a ser usada para o podcast.
        max_length: Comprimento máximo do resumo.
        max_items: Número máximo de itens a serem recuperados.

    Returns:
        Caminho para o arquivo de podcast gerado.

    Example:
        ```python
        from pepperpy.core.intent import create_podcast

        # Criar um podcast a partir de um feed RSS
        podcast_path = await create_podcast(
            source_url="https://news.google.com/rss",
            output_path="podcast.mp3",
            voice="pt",
            max_length=150,
        )
        ```
    """
    pipeline = (
        compose("podcast_pipeline")
        .source(Sources.rss(source_url, max_items=max_items))
        .process(Processors.summarize(max_length=max_length))
        .output(Outputs.podcast(output_path, voice=voice))
    )

    result = await pipeline.execute()
    return output_path


async def summarize_document(
    document_path: str,
    max_length: Optional[int] = None,
    output_path: Optional[str] = None,
) -> str:
    """Resumir um documento.

    Args:
        document_path: Caminho para o documento.
        max_length: Comprimento máximo do resumo.
        output_path: Caminho opcional para o arquivo de saída.

    Returns:
        Resumo do documento ou caminho para o arquivo de saída.

    Example:
        ```python
        from pepperpy.core.intent import summarize_document

        # Resumir um documento
        summary = await summarize_document(
            document_path="document.txt",
            max_length=200,
        )
        ```
    """
    pipeline = (
        compose("document_summary_pipeline")
        .source(Sources.file(document_path))
        .process(Processors.summarize(max_length=max_length))
    )

    if output_path:
        pipeline = pipeline.output(Outputs.file(output_path))
        await pipeline.execute()
        return output_path
    else:
        pipeline = pipeline.output(Outputs.memory())
        result = await pipeline.execute()
        return result


async def translate_content(
    content: str,
    target_language: str,
    output_path: Optional[str] = None,
) -> str:
    """Traduzir conteúdo.

    Args:
        content: Conteúdo a ser traduzido.
        target_language: Idioma de destino para tradução.
        output_path: Caminho opcional para o arquivo de saída.

    Returns:
        Conteúdo traduzido ou caminho para o arquivo de saída.

    Example:
        ```python
        from pepperpy.core.intent import translate_content

        # Traduzir conteúdo
        translated = await translate_content(
            content="Hello, world!",
            target_language="pt",
        )
        ```
    """
    pipeline = (
        compose("content_translation_pipeline")
        .source(Sources.text(content))
        .process(Processors.translate(target_language=target_language))
    )

    if output_path:
        pipeline = pipeline.output(Outputs.file(output_path))
        await pipeline.execute()
        return output_path
    else:
        pipeline = pipeline.output(Outputs.memory())
        result = await pipeline.execute()
        return result
