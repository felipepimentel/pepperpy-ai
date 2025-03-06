"""Componentes concretos para o módulo de composição universal.

Este módulo fornece implementações concretas de componentes para o módulo
de composição universal, incluindo fontes, processadores e saídas.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.composition.types import (
    OutputComponent,
    OutputWriteError,
    ProcessingError,
    ProcessorComponent,
    SourceComponent,
    SourceReadError,
)


class Sources:
    """Fábrica de componentes de fonte.

    Esta classe fornece métodos estáticos para criar componentes de fonte
    para uso em pipelines de composição.
    """

    @staticmethod
    def rss(url: str, max_items: int = 5) -> SourceComponent[List[Dict[str, Any]]]:
        """Cria uma fonte de dados RSS.

        Args:
            url: URL do feed RSS.
            max_items: Número máximo de itens a serem obtidos.

        Returns:
            Um componente de fonte RSS.
        """

        class RSSSource(SourceComponent[List[Dict[str, Any]]]):
            """Fonte de dados RSS."""

            def __init__(self, url: str, max_items: int = 5) -> None:
                self.url = url
                self.max_items = max_items

            async def read(self) -> List[Dict[str, Any]]:
                """Lê dados do feed RSS.

                Returns:
                    Lista de itens do feed RSS.

                Raises:
                    SourceReadError: Se ocorrer um erro ao ler o feed.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos uma biblioteca RSS
                    return [
                        {
                            "title": f"Item {i} do feed {self.url}",
                            "description": f"Descrição do item {i}",
                            "link": f"{self.url}/item{i}",
                            "published": "2023-01-01",
                        }
                        for i in range(1, self.max_items + 1)
                    ]
                except Exception as e:
                    raise SourceReadError(f"Erro ao ler feed RSS: {e}")

        return RSSSource(url, max_items)

    @staticmethod
    def file(path: str, format: str = "auto") -> SourceComponent[str]:
        """Cria uma fonte de dados de arquivo.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo (auto, text, json, etc.).

        Returns:
            Um componente de fonte de arquivo.
        """

        class FileSource(SourceComponent[str]):
            """Fonte de dados de arquivo."""

            def __init__(self, path: str, format: str = "auto") -> None:
                self.path = path
                self.format = format

            async def read(self) -> str:
                """Lê dados do arquivo.

                Returns:
                    Conteúdo do arquivo.

                Raises:
                    SourceReadError: Se ocorrer um erro ao ler o arquivo.
                """
                try:
                    with open(self.path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    raise SourceReadError(f"Erro ao ler arquivo: {e}")

        return FileSource(path, format)

    @staticmethod
    def text(content: str) -> SourceComponent[str]:
        """Cria uma fonte de dados de texto.

        Args:
            content: Conteúdo de texto.

        Returns:
            Um componente de fonte de texto.
        """

        class TextSource(SourceComponent[str]):
            """Fonte de dados de texto."""

            def __init__(self, content: str) -> None:
                self.content = content

            async def read(self) -> str:
                """Lê o texto.

                Returns:
                    O texto.
                """
                return self.content

        return TextSource(content)


class Processors:
    """Fábrica de componentes de processamento.

    Esta classe fornece métodos estáticos para criar componentes de processamento
    para uso em pipelines de composição.
    """

    @staticmethod
    def summarize(
        max_length: int = 150, model: str = "default"
    ) -> ProcessorComponent[Any, str]:
        """Cria um processador de sumarização.

        Args:
            max_length: Comprimento máximo do resumo.
            model: Modelo a ser usado para sumarização.

        Returns:
            Um componente de processamento de sumarização.
        """

        class SummarizationProcessor(ProcessorComponent[Any, str]):
            """Processador de sumarização."""

            def __init__(self, max_length: int = 150, model: str = "default") -> None:
                self.max_length = max_length
                self.model = model

            async def process(self, data: Any) -> str:
                """Processa os dados para gerar um resumo.

                Args:
                    data: Dados a serem resumidos.

                Returns:
                    Resumo dos dados.

                Raises:
                    ProcessingError: Se ocorrer um erro durante o processamento.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos um modelo de IA
                    if isinstance(data, list):
                        # Resumir uma lista de itens (como de um feed RSS)
                        items = data[:3]  # Limitar a 3 itens para o resumo
                        titles = [item.get("title", "") for item in items]
                        return f"Resumo dos principais itens: {', '.join(titles)}"
                    elif isinstance(data, str):
                        # Resumir um texto
                        if len(data) > self.max_length:
                            return data[: self.max_length] + "..."
                        return data
                    else:
                        # Tentar converter para string
                        return str(data)[: self.max_length]
                except Exception as e:
                    raise ProcessingError(f"Erro ao sumarizar conteúdo: {e}")

        return SummarizationProcessor(max_length, model)

    @staticmethod
    def translate(
        target_language: str, source_language: Optional[str] = None
    ) -> ProcessorComponent[str, str]:
        """Cria um processador de tradução.

        Args:
            target_language: Idioma de destino.
            source_language: Idioma de origem (opcional, auto-detectado se não fornecido).

        Returns:
            Um componente de processamento de tradução.
        """

        class TranslationProcessor(ProcessorComponent[str, str]):
            """Processador de tradução."""

            def __init__(
                self, target_language: str, source_language: Optional[str] = None
            ) -> None:
                self.target_language = target_language
                self.source_language = source_language

            async def process(self, data: str) -> str:
                """Processa os dados para traduzir o texto.

                Args:
                    data: Texto a ser traduzido.

                Returns:
                    Texto traduzido.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a tradução.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos uma API de tradução
                    if self.target_language == "pt":
                        return f"[Traduzido para Português]: {data}"
                    elif self.target_language == "en":
                        return f"[Translated to English]: {data}"
                    else:
                        return f"[Translated to {self.target_language}]: {data}"
                except Exception as e:
                    raise ProcessingError(f"Erro ao traduzir texto: {e}")

        return TranslationProcessor(target_language, source_language)

    @staticmethod
    def extract_keywords(max_keywords: int = 5) -> ProcessorComponent[str, List[str]]:
        """Cria um processador de extração de palavras-chave.

        Args:
            max_keywords: Número máximo de palavras-chave a serem extraídas.

        Returns:
            Um componente de processamento de extração de palavras-chave.
        """

        class KeywordExtractor(ProcessorComponent[str, List[str]]):
            """Processador de extração de palavras-chave."""

            def __init__(self, max_keywords: int = 5) -> None:
                self.max_keywords = max_keywords

            async def process(self, data: str) -> List[str]:
                """Processa os dados para extrair palavras-chave.

                Args:
                    data: Texto do qual extrair palavras-chave.

                Returns:
                    Lista de palavras-chave.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a extração.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos um algoritmo de NLP
                    words = data.split()
                    # Filtrar palavras com pelo menos 4 caracteres
                    keywords = [w for w in words if len(w) >= 4]
                    # Limitar ao número máximo de palavras-chave
                    return keywords[: self.max_keywords]
                except Exception as e:
                    raise ProcessingError(f"Erro ao extrair palavras-chave: {e}")

        return KeywordExtractor(max_keywords)


class Outputs:
    """Fábrica de componentes de saída.

    Esta classe fornece métodos estáticos para criar componentes de saída
    para uso em pipelines de composição.
    """

    @staticmethod
    def file(path: str, format: str = "auto") -> OutputComponent[Any]:
        """Cria uma saída de arquivo.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo (auto, text, json, etc.).

        Returns:
            Um componente de saída de arquivo.
        """

        class FileOutput(OutputComponent[Any]):
            """Saída de arquivo."""

            def __init__(self, path: str, format: str = "auto") -> None:
                self.path = path
                self.format = format

            async def write(self, data: Any) -> str:
                """Escreve os dados no arquivo.

                Args:
                    data: Dados a serem escritos.

                Returns:
                    Caminho do arquivo.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao escrever no arquivo.
                """
                try:
                    # Criar diretório se não existir
                    os.makedirs(
                        os.path.dirname(os.path.abspath(self.path)), exist_ok=True
                    )

                    # Determinar o formato
                    format_to_use = self.format
                    if format_to_use == "auto":
                        ext = Path(self.path).suffix.lower()
                        if ext == ".json":
                            format_to_use = "json"
                        else:
                            format_to_use = "text"

                    # Escrever dados no formato apropriado
                    if format_to_use == "json":
                        with open(self.path, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        with open(self.path, "w", encoding="utf-8") as f:
                            if isinstance(data, list):
                                f.write("\n".join(str(item) for item in data))
                            else:
                                f.write(str(data))

                    return self.path
                except Exception as e:
                    raise OutputWriteError(f"Erro ao escrever no arquivo: {e}")

        return FileOutput(path, format)

    @staticmethod
    def podcast(path: str, voice: str = "en") -> OutputComponent[str]:
        """Cria uma saída de podcast.

        Args:
            path: Caminho do arquivo de podcast.
            voice: Voz a ser usada (código de idioma).

        Returns:
            Um componente de saída de podcast.
        """

        class PodcastOutput(OutputComponent[str]):
            """Saída de podcast."""

            def __init__(self, path: str, voice: str = "en") -> None:
                self.path = path
                self.voice = voice

            async def write(self, data: str) -> str:
                """Gera um podcast a partir do texto.

                Args:
                    data: Texto a ser convertido em podcast.

                Returns:
                    Caminho do arquivo de podcast.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao gerar o podcast.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos uma API de TTS
                    # Criar diretório se não existir
                    os.makedirs(
                        os.path.dirname(os.path.abspath(self.path)), exist_ok=True
                    )

                    # Simular a geração do podcast escrevendo um arquivo de texto
                    with open(self.path + ".txt", "w", encoding="utf-8") as f:
                        f.write(f"[Podcast com voz {self.voice}]\n\n{data}")

                    return self.path
                except Exception as e:
                    raise OutputWriteError(f"Erro ao gerar podcast: {e}")

        return PodcastOutput(path, voice)
