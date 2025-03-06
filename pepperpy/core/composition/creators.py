"""Criadores de componentes para pipelines.

Este módulo define classes criadoras para facilitar a construção
de componentes para pipelines de composição universal.
"""

from typing import Any, Dict, List, Union

from pepperpy.core.composition.namespaces import (
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)


class Creator:
    """Classe base para criadores de componentes."""

    def __init__(self):
        """Inicializa o criador."""
        self.config = {}

    def build(self) -> Union[SourceComponent, ProcessorComponent, OutputComponent]:
        """Constrói o componente.

        Returns:
            Componente construído.
        """
        raise NotImplementedError("Método build deve ser implementado por subclasses")


class SourceCreator(Creator):
    """Criador de componentes de fonte."""

    def __init__(self, source_type: str):
        """Inicializa o criador de fonte.

        Args:
            source_type: Tipo de fonte.
        """
        super().__init__()
        self.config["type"] = source_type

    def with_url(self, url: str) -> "SourceCreator":
        """Define a URL da fonte.

        Args:
            url: URL da fonte.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["url"] = url
        return self

    def with_path(self, path: str) -> "SourceCreator":
        """Define o caminho do arquivo da fonte.

        Args:
            path: Caminho do arquivo.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["path"] = path
        return self

    def with_content(self, content: str) -> "SourceCreator":
        """Define o conteúdo da fonte.

        Args:
            content: Conteúdo da fonte.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["content"] = content
        return self

    def with_max_items(self, max_items: int) -> "SourceCreator":
        """Define o número máximo de itens.

        Args:
            max_items: Número máximo de itens.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["max_items"] = max_items
        return self

    def build(self) -> SourceComponent:
        """Constrói o componente de fonte.

        Returns:
            Componente de fonte.
        """
        return SourceComponent(self.config)


class ProcessorCreator(Creator):
    """Criador de componentes de processamento."""

    def __init__(self, processor_type: str):
        """Inicializa o criador de processador.

        Args:
            processor_type: Tipo de processador.
        """
        super().__init__()
        self.config["type"] = processor_type

    def with_max_length(self, max_length: int) -> "ProcessorCreator":
        """Define o tamanho máximo para sumarização.

        Args:
            max_length: Tamanho máximo.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["max_length"] = max_length
        return self

    def with_target_language(self, target_language: str) -> "ProcessorCreator":
        """Define o idioma de destino para tradução.

        Args:
            target_language: Idioma de destino.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["target_language"] = target_language
        return self

    def with_source_language(self, source_language: str) -> "ProcessorCreator":
        """Define o idioma de origem para tradução.

        Args:
            source_language: Idioma de origem.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["source_language"] = source_language
        return self

    def with_fields(self, fields: List[str]) -> "ProcessorCreator":
        """Define os campos para extração.

        Args:
            fields: Lista de campos.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["fields"] = fields
        return self

    def with_format(self, format: str) -> "ProcessorCreator":
        """Define o formato de saída para extração.

        Args:
            format: Formato de saída.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["format"] = format
        return self

    def with_transformation(
        self, transformation: Union[str, Dict[str, Any]]
    ) -> "ProcessorCreator":
        """Define a transformação a ser aplicada.

        Args:
            transformation: Transformação.

        Returns:
            O próprio criador para encadeamento.
        """
        if isinstance(transformation, str):
            self.config["name"] = transformation
        else:
            self.config.update(transformation)
        return self

    def build(self) -> ProcessorComponent:
        """Constrói o componente de processamento.

        Returns:
            Componente de processamento.
        """
        return ProcessorComponent(self.config)


class OutputCreator(Creator):
    """Criador de componentes de saída."""

    def __init__(self, output_type: str):
        """Inicializa o criador de saída.

        Args:
            output_type: Tipo de saída.
        """
        super().__init__()
        self.config["type"] = output_type

    def with_output_path(self, output_path: str) -> "OutputCreator":
        """Define o caminho do arquivo de saída.

        Args:
            output_path: Caminho do arquivo.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["output_path"] = output_path
        return self

    def with_voice(self, voice: str) -> "OutputCreator":
        """Define a voz para podcast.

        Args:
            voice: Código da voz.

        Returns:
            O próprio criador para encadeamento.
        """
        self.config["voice"] = voice
        return self

    def build(self) -> OutputComponent:
        """Constrói o componente de saída.

        Returns:
            Componente de saída.
        """
        return OutputComponent(self.config)


class SourceBuilder:
    """Construtor de componentes de fonte."""

    @staticmethod
    def rss() -> SourceCreator:
        """Cria um construtor para fonte RSS.

        Returns:
            Construtor de fonte RSS.
        """
        return SourceCreator("rss")

    @staticmethod
    def file() -> SourceCreator:
        """Cria um construtor para fonte de arquivo.

        Returns:
            Construtor de fonte de arquivo.
        """
        return SourceCreator("file")

    @staticmethod
    def text() -> SourceCreator:
        """Cria um construtor para fonte de texto.

        Returns:
            Construtor de fonte de texto.
        """
        return SourceCreator("text")

    @staticmethod
    def memory() -> SourceCreator:
        """Cria um construtor para fonte de memória.

        Returns:
            Construtor de fonte de memória.
        """
        return SourceCreator("memory")


class ProcessorBuilder:
    """Construtor de componentes de processamento."""

    @staticmethod
    def summarize() -> ProcessorCreator:
        """Cria um construtor para processador de sumarização.

        Returns:
            Construtor de processador de sumarização.
        """
        return ProcessorCreator("summarize")

    @staticmethod
    def translate() -> ProcessorCreator:
        """Cria um construtor para processador de tradução.

        Returns:
            Construtor de processador de tradução.
        """
        return ProcessorCreator("translate")

    @staticmethod
    def extract() -> ProcessorCreator:
        """Cria um construtor para processador de extração.

        Returns:
            Construtor de processador de extração.
        """
        return ProcessorCreator("extract")

    @staticmethod
    def transform() -> ProcessorCreator:
        """Cria um construtor para processador de transformação.

        Returns:
            Construtor de processador de transformação.
        """
        return ProcessorCreator("transform")


class OutputBuilder:
    """Construtor de componentes de saída."""

    @staticmethod
    def file() -> OutputCreator:
        """Cria um construtor para saída de arquivo.

        Returns:
            Construtor de saída de arquivo.
        """
        return OutputCreator("file")

    @staticmethod
    def podcast() -> OutputCreator:
        """Cria um construtor para saída de podcast.

        Returns:
            Construtor de saída de podcast.
        """
        return OutputCreator("podcast")

    @staticmethod
    def conversation() -> OutputCreator:
        """Cria um construtor para saída de conversa.

        Returns:
            Construtor de saída de conversa.
        """
        return OutputCreator("conversation")
