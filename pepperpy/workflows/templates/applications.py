"""Templates de aplicação para workflows.

Este módulo fornece classes de templates para aplicações comuns,
permitindo a reutilização de configurações e padrões.
"""

from typing import Optional

from pepperpy.core.composition import Outputs, Processors, Sources, compose


class PodcastTemplate:
    """Template para criação de podcasts.

    Este template fornece métodos para criar podcasts a partir
    de diferentes fontes, como feeds RSS, arquivos e texto.
    """

    def __init__(
        self,
        voice: str = "en",
        max_length: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> None:
        """Inicializa o template de podcast.

        Args:
            voice: Voz a ser usada para o podcast.
            max_length: Comprimento máximo do resumo.
            max_items: Número máximo de itens a serem recuperados.
        """
        self.voice = voice
        self.max_length = max_length
        self.max_items = max_items

    async def create_podcast(
        self,
        source_url: str,
        output_path: str,
        voice: Optional[str] = None,
        max_length: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> str:
        """Cria um podcast a partir de um feed RSS.

        Args:
            source_url: URL do feed RSS.
            output_path: Caminho para o arquivo de podcast.
            voice: Voz a ser usada para o podcast (sobrescreve o valor padrão).
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).
            max_items: Número máximo de itens a serem recuperados (sobrescreve o valor padrão).

        Returns:
            Caminho para o arquivo de podcast.
        """
        voice = voice or self.voice
        max_length = max_length or self.max_length
        max_items = max_items or self.max_items

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("podcast_pipeline").source(Sources.rss(source_url))

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        # Adicionar saída de podcast
        pipeline = pipeline_builder.output(Outputs.podcast(output_path, voice=voice))

        await pipeline.execute()
        return output_path

    async def create_podcast_from_file(
        self,
        file_path: str,
        output_path: str,
        voice: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> str:
        """Cria um podcast a partir de um arquivo.

        Args:
            file_path: Caminho para o arquivo.
            output_path: Caminho para o arquivo de podcast.
            voice: Voz a ser usada para o podcast (sobrescreve o valor padrão).
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).

        Returns:
            Caminho para o arquivo de podcast.
        """
        voice = voice or self.voice
        max_length = max_length or self.max_length

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("podcast_from_file_pipeline").source(
            Sources.file(file_path)
        )

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        # Adicionar saída de podcast
        pipeline = pipeline_builder.output(Outputs.podcast(output_path, voice=voice))

        await pipeline.execute()
        return output_path

    async def create_podcast_from_text(
        self,
        content: str,
        output_path: str,
        voice: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> str:
        """Cria um podcast a partir de um texto.

        Args:
            content: Conteúdo de texto.
            output_path: Caminho para o arquivo de podcast.
            voice: Voz a ser usada para o podcast (sobrescreve o valor padrão).
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).

        Returns:
            Caminho para o arquivo de podcast.
        """
        voice = voice or self.voice
        max_length = max_length or self.max_length

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("podcast_from_text_pipeline").source(
            Sources.text(content)
        )

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        # Adicionar saída de podcast
        pipeline = pipeline_builder.output(Outputs.podcast(output_path, voice=voice))

        await pipeline.execute()
        return output_path


class SummaryTemplate:
    """Template para criação de resumos.

    Este template fornece métodos para criar resumos a partir
    de diferentes fontes, como arquivos, texto e feeds RSS.
    """

    def __init__(
        self,
        max_length: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> None:
        """Inicializa o template de resumo.

        Args:
            max_length: Comprimento máximo do resumo.
            max_items: Número máximo de itens a serem recuperados.
        """
        self.max_length = max_length
        self.max_items = max_items

    async def summarize(
        self,
        document_path: str,
        output_path: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> str:
        """Cria um resumo a partir de um documento.

        Args:
            document_path: Caminho para o documento.
            output_path: Caminho para o arquivo de saída.
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).

        Returns:
            Resumo do documento ou caminho para o arquivo de saída.
        """
        max_length = max_length or self.max_length

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("summary_pipeline").source(
            Sources.file(document_path)
        )

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        if output_path:
            pipeline = pipeline_builder.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline_builder.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result

    async def summarize_text(
        self,
        text: str,
        output_path: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> str:
        """Cria um resumo a partir de um texto.

        Args:
            text: Texto a ser resumido.
            output_path: Caminho para o arquivo de saída.
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).

        Returns:
            Resumo do texto ou caminho para o arquivo de saída.
        """
        max_length = max_length or self.max_length

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("summary_pipeline").source(Sources.text(text))

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        if output_path:
            pipeline = pipeline_builder.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline_builder.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result

    async def summarize_rss(
        self,
        source_url: str,
        output_path: Optional[str] = None,
        max_length: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> str:
        """Cria um resumo a partir de um feed RSS.

        Args:
            source_url: URL do feed RSS.
            output_path: Caminho para o arquivo de saída.
            max_length: Comprimento máximo do resumo (sobrescreve o valor padrão).
            max_items: Número máximo de itens a serem recuperados (sobrescreve o valor padrão).

        Returns:
            Resumo do feed RSS ou caminho para o arquivo de saída.
        """
        max_length = max_length or self.max_length
        max_items = max_items or self.max_items

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("summary_pipeline")

        # Adicionar fonte RSS com max_items se estiver definido
        if max_items is not None:
            pipeline_builder = pipeline_builder.source(
                Sources.rss(source_url, max_items=max_items)
            )
        else:
            pipeline_builder = pipeline_builder.source(Sources.rss(source_url))

        # Adicionar processador de resumo se max_length estiver definido
        if max_length is not None:
            pipeline_builder = pipeline_builder.process(
                Processors.summarize(max_length=max_length)
            )
        else:
            pipeline_builder = pipeline_builder.process(Processors.summarize())

        if output_path:
            pipeline = pipeline_builder.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline_builder.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result


class TranslationTemplate:
    """Template para tradução de conteúdo.

    Este template fornece métodos para traduzir conteúdo a partir
    de diferentes fontes, como arquivos, texto e feeds RSS.
    """

    def __init__(
        self,
        target_language: str,
        max_items: Optional[int] = None,
    ) -> None:
        """Inicializa o template de tradução.

        Args:
            target_language: Idioma de destino para tradução.
            max_items: Número máximo de itens a serem recuperados.
        """
        self.target_language = target_language
        self.max_items = max_items

    async def translate(
        self,
        content: str,
        target_language: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Traduz um texto.

        Args:
            content: Texto a ser traduzido.
            target_language: Idioma de destino (sobrescreve o valor padrão).
            output_path: Caminho para o arquivo de saída.

        Returns:
            Texto traduzido ou caminho para o arquivo de saída.
        """
        target_language = target_language or self.target_language

        pipeline = (
            compose("text_translation_pipeline")
            .source(Sources.text(content))
            .process(Processors.translate(target_language=target_language))
        )

        if output_path:
            pipeline = pipeline.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result

    async def translate_file(
        self,
        file_path: str,
        target_language: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Traduz um arquivo.

        Args:
            file_path: Caminho para o arquivo.
            target_language: Idioma de destino (sobrescreve o valor padrão).
            output_path: Caminho para o arquivo de saída.

        Returns:
            Conteúdo traduzido ou caminho para o arquivo de saída.
        """
        target_language = target_language or self.target_language

        pipeline = (
            compose("file_translation_pipeline")
            .source(Sources.file(file_path))
            .process(Processors.translate(target_language=target_language))
        )

        if output_path:
            pipeline = pipeline.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result

    async def translate_rss(
        self,
        source_url: str,
        target_language: str,
        output_path: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> str:
        """Traduz um feed RSS.

        Args:
            source_url: URL do feed RSS.
            target_language: Idioma de destino.
            output_path: Caminho para o arquivo de saída.
            max_items: Número máximo de itens a serem recuperados (sobrescreve o valor padrão).

        Returns:
            Feed RSS traduzido ou caminho para o arquivo de saída.
        """
        max_items = max_items or self.max_items

        # Construir o pipeline com os parâmetros disponíveis
        pipeline_builder = compose("translation_pipeline")

        # Adicionar fonte RSS com max_items se estiver definido
        if max_items is not None:
            pipeline_builder = pipeline_builder.source(
                Sources.rss(source_url, max_items=max_items)
            )
        else:
            pipeline_builder = pipeline_builder.source(Sources.rss(source_url))

        # Adicionar processador de tradução
        pipeline_builder = pipeline_builder.process(
            Processors.translate(target_language=target_language)
        )

        if output_path:
            pipeline = pipeline_builder.output(Outputs.file(output_path))
            await pipeline.execute()
            return output_path
        else:
            # Executar o pipeline com saída para arquivo temporário
            import tempfile

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            pipeline = pipeline_builder.output(Outputs.file(temp_file.name))
            await pipeline.execute()

            # Ler o conteúdo do arquivo temporário
            with open(temp_file.name, "r") as f:
                result = f.read()

            # Remover o arquivo temporário
            import os

            os.unlink(temp_file.name)

            return result
