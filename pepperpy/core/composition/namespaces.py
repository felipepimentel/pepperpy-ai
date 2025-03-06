"""Namespaces para componentes de composição.

Este módulo define namespaces para facilitar o acesso aos componentes
de composição, como fontes, processadores e saídas.

Example:
    ```python
    from pepperpy.core.composition import Sources, Processors, Outputs

    # Usar namespaces para criar componentes
    source = Sources.rss("https://news.google.com/rss")
    processor = Processors.summarize(max_length=150)
    output = Outputs.podcast("podcast.mp3", voice="pt")
    ```
"""

from typing import Any, Optional

from pepperpy.core.composition.registry import (
    get_output_component_class,
    get_processor_component_class,
    get_source_component_class,
)
from pepperpy.core.errors import ComponentNotFoundError


class Sources:
    """Namespace para componentes de fonte.

    Este namespace fornece métodos para criar componentes de fonte
    para uso em pipelines de composição.
    """

    @staticmethod
    def rss(url: str, max_items: Optional[int] = None, **kwargs: Any) -> Any:
        """Cria um componente de fonte RSS.

        Args:
            url: URL do feed RSS.
            max_items: Número máximo de itens a serem recuperados.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de fonte RSS configurado.

        Raises:
            ComponentNotFoundError: Se o componente de fonte RSS não estiver registrado.
        """
        source_cls = get_source_component_class("rss")
        if source_cls is None:
            raise ComponentNotFoundError("Componente de fonte RSS não encontrado")
        return source_cls(url=url, max_items=max_items, **kwargs)

    @staticmethod
    def file(path: str, **kwargs: Any) -> Any:
        """Cria um componente de fonte de arquivo.

        Args:
            path: Caminho para o arquivo.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de fonte de arquivo configurado.

        Raises:
            ComponentNotFoundError: Se o componente de fonte de arquivo não estiver registrado.
        """
        source_cls = get_source_component_class("file")
        if source_cls is None:
            raise ComponentNotFoundError(
                "Componente de fonte de arquivo não encontrado"
            )
        return source_cls(path=path, **kwargs)

    @staticmethod
    def web(url: str, **kwargs: Any) -> Any:
        """Cria um componente de fonte web.

        Args:
            url: URL da página web.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de fonte web configurado.

        Raises:
            ComponentNotFoundError: Se o componente de fonte web não estiver registrado.
        """
        source_cls = get_source_component_class("web")
        if source_cls is None:
            raise ComponentNotFoundError("Componente de fonte web não encontrado")
        return source_cls(url=url, **kwargs)

    @staticmethod
    def text(content: str, **kwargs: Any) -> Any:
        """Cria um componente de fonte de texto.

        Args:
            content: Conteúdo de texto.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de fonte de texto configurado.

        Raises:
            ComponentNotFoundError: Se o componente de fonte de texto não estiver registrado.
        """
        source_cls = get_source_component_class("text")
        if source_cls is None:
            raise ComponentNotFoundError("Componente de fonte de texto não encontrado")
        return source_cls(content=content, **kwargs)


class Processors:
    """Namespace para componentes de processamento.

    Este namespace fornece métodos para criar componentes de processamento
    para uso em pipelines de composição.
    """

    @staticmethod
    def summarize(max_length: Optional[int] = None, **kwargs: Any) -> Any:
        """Cria um componente de processamento para resumir conteúdo.

        Args:
            max_length: Comprimento máximo do resumo.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de processamento de resumo configurado.

        Raises:
            ComponentNotFoundError: Se o componente de resumo não estiver registrado.
        """
        processor_cls = get_processor_component_class("summarize")
        if processor_cls is None:
            raise ComponentNotFoundError("Componente de resumo não encontrado")
        return processor_cls(max_length=max_length, **kwargs)

    @staticmethod
    def translate(target_language: str, **kwargs: Any) -> Any:
        """Cria um componente de processamento para traduzir conteúdo.

        Args:
            target_language: Idioma de destino para tradução.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de processamento de tradução configurado.

        Raises:
            ComponentNotFoundError: Se o componente de tradução não estiver registrado.
        """
        processor_cls = get_processor_component_class("translate")
        if processor_cls is None:
            raise ComponentNotFoundError("Componente de tradução não encontrado")
        return processor_cls(target_language=target_language, **kwargs)

    @staticmethod
    def extract_keywords(max_keywords: Optional[int] = None, **kwargs: Any) -> Any:
        """Cria um componente de processamento para extrair palavras-chave.

        Args:
            max_keywords: Número máximo de palavras-chave a serem extraídas.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de processamento de extração de palavras-chave configurado.

        Raises:
            ComponentNotFoundError: Se o componente de extração de palavras-chave não estiver registrado.
        """
        processor_cls = get_processor_component_class("extract_keywords")
        if processor_cls is None:
            raise ComponentNotFoundError(
                "Componente de extração de palavras-chave não encontrado"
            )
        return processor_cls(max_keywords=max_keywords, **kwargs)

    @staticmethod
    def sentiment_analysis(**kwargs: Any) -> Any:
        """Cria um componente de processamento para análise de sentimento.

        Args:
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de processamento de análise de sentimento configurado.

        Raises:
            ComponentNotFoundError: Se o componente de análise de sentimento não estiver registrado.
        """
        processor_cls = get_processor_component_class("sentiment_analysis")
        if processor_cls is None:
            raise ComponentNotFoundError(
                "Componente de análise de sentimento não encontrado"
            )
        return processor_cls(**kwargs)


class Outputs:
    """Namespace para componentes de saída.

    Este namespace fornece métodos para criar componentes de saída
    para uso em pipelines de composição.
    """

    @staticmethod
    def file(path: str, **kwargs: Any) -> Any:
        """Cria um componente de saída para arquivo.

        Args:
            path: Caminho para o arquivo de saída.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de saída de arquivo configurado.

        Raises:
            ComponentNotFoundError: Se o componente de saída para arquivo não estiver registrado.
        """
        output_cls = get_output_component_class("file")
        if output_cls is None:
            raise ComponentNotFoundError(
                "Componente de saída para arquivo não encontrado"
            )
        return output_cls(path=path, **kwargs)

    @staticmethod
    def podcast(path: str, voice: str = "en", **kwargs: Any) -> Any:
        """Cria um componente de saída para podcast.

        Args:
            path: Caminho para o arquivo de podcast.
            voice: Voz a ser usada para o podcast.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de saída de podcast configurado.

        Raises:
            ComponentNotFoundError: Se o componente de saída para podcast não estiver registrado.
        """
        output_cls = get_output_component_class("podcast")
        if output_cls is None:
            raise ComponentNotFoundError(
                "Componente de saída para podcast não encontrado"
            )
        return output_cls(path=path, voice=voice, **kwargs)

    @staticmethod
    def json(path: Optional[str] = None, **kwargs: Any) -> Any:
        """Cria um componente de saída para JSON.

        Args:
            path: Caminho opcional para o arquivo JSON.
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de saída JSON configurado.

        Raises:
            ComponentNotFoundError: Se o componente de saída para JSON não estiver registrado.
        """
        output_cls = get_output_component_class("json")
        if output_cls is None:
            raise ComponentNotFoundError("Componente de saída para JSON não encontrado")
        return output_cls(path=path, **kwargs)

    @staticmethod
    def memory(**kwargs: Any) -> Any:
        """Cria um componente de saída para memória.

        Args:
            **kwargs: Argumentos adicionais para o componente.

        Returns:
            Um componente de saída de memória configurado.

        Raises:
            ComponentNotFoundError: Se o componente de saída para memória não estiver registrado.
        """
        output_cls = get_output_component_class("memory")
        if output_cls is None:
            raise ComponentNotFoundError(
                "Componente de saída para memória não encontrado"
            )
        return output_cls(**kwargs)
