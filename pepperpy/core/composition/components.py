"""Componentes para o módulo de composição universal.

Este módulo fornece componentes para uso em pipelines de composição,
incluindo fontes, processadores e saídas.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from pepperpy.core.composition.types import (
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)


class SourceReadError(Exception):
    """Erro ao ler de uma fonte."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProcessingError(Exception):
    """Erro ao processar dados."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class OutputWriteError(Exception):
    """Erro ao escrever em uma saída."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class Sources:
    """Fábrica de componentes de fonte.

    Esta classe fornece métodos estáticos para criar componentes de fonte
    para uso em pipelines de composição.
    """

    @staticmethod
    def rss(url: str, max_items: int = 10) -> SourceComponent[List[Dict[str, Any]]]:
        """Cria uma fonte de dados RSS.

        Args:
            url: URL do feed RSS.
            max_items: Número máximo de itens a serem obtidos.

        Returns:
            Um componente de fonte RSS.
        """

        class RSSSource(SourceComponent[List[Dict[str, Any]]]):
            """Fonte de dados RSS."""

            def __init__(self, url: str, max_items: int = 10) -> None:
                self.url = url
                self.max_items = max_items

            async def read(self) -> List[Dict[str, Any]]:
                """Lê os itens do feed RSS.

                Returns:
                    Lista de itens do feed.

                Raises:
                    SourceReadError: Se ocorrer um erro ao ler o feed.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos feedparser
                    print(f"Lendo feed RSS de {self.url}")
                    items = [
                        {
                            "title": f"Item {i}",
                            "description": f"Descrição do item {i}",
                            "link": f"{self.url}/item{i}",
                            "published": "2023-01-01",
                        }
                        for i in range(1, self.max_items + 1)
                    ]
                    return items
                except Exception as e:
                    raise SourceReadError(f"Erro ao ler feed RSS: {e}")

            async def fetch(self) -> List[Dict[str, Any]]:
                """Obtém os itens do feed RSS.

                Returns:
                    Lista de itens do feed.

                Raises:
                    SourceReadError: Se ocorrer um erro ao obter o feed.
                """
                return await self.read()

        return RSSSource(url, max_items)

    @staticmethod
    def file(path: str) -> SourceComponent[str]:
        """Cria uma fonte de dados de arquivo.

        Args:
            path: Caminho do arquivo.

        Returns:
            Um componente de fonte de arquivo.
        """

        class FileSource(SourceComponent[str]):
            """Fonte de dados de arquivo."""

            def __init__(self, path: str) -> None:
                self.path = path

            async def read(self) -> str:
                """Lê o conteúdo do arquivo.

                Returns:
                    Conteúdo do arquivo.

                Raises:
                    SourceReadError: Se ocorrer um erro ao ler o arquivo.
                """
                try:
                    # Simulação - em uma implementação real, leríamos o arquivo
                    print(f"Lendo arquivo {self.path}")
                    return f"Conteúdo simulado do arquivo {self.path}"
                except Exception as e:
                    raise SourceReadError(f"Erro ao ler arquivo: {e}")

            async def fetch(self) -> str:
                """Obtém o conteúdo do arquivo.

                Returns:
                    Conteúdo do arquivo.

                Raises:
                    SourceReadError: Se ocorrer um erro ao obter o arquivo.
                """
                return await self.read()

        return FileSource(path)

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

            async def fetch(self) -> str:
                """Obtém o texto.

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
    def transform(transform_func: callable) -> ProcessorComponent[Any, Any]:
        """Cria um processador de transformação personalizado.

        Args:
            transform_func: Função de transformação a ser aplicada aos dados.

        Returns:
            Um componente de processamento de transformação.
        """

        class TransformProcessor(ProcessorComponent[Any, Any]):
            """Processador de transformação personalizado."""

            def __init__(self, transform_func: callable) -> None:
                self.transform_func = transform_func

            async def process(self, data: Any) -> Any:
                """Processa os dados aplicando a função de transformação.

                Args:
                    data: Dados a serem transformados.

                Returns:
                    Dados transformados.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a transformação.
                """
                try:
                    # Aplicar a função de transformação
                    if asyncio.iscoroutinefunction(self.transform_func):
                        return await self.transform_func(data)
                    else:
                        return self.transform_func(data)
                except Exception as e:
                    raise ProcessingError(f"Erro ao transformar dados: {e}")

            async def transform(self, data: Any) -> Any:
                """Transforma os dados aplicando a função de transformação.

                Args:
                    data: Dados a serem transformados.

                Returns:
                    Dados transformados.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a transformação.
                """
                return await self.process(data)

        return TransformProcessor(transform_func)

    @staticmethod
    def summarize(
        max_length: int = 150, model: str = "default"
    ) -> ProcessorComponent[Any, str]:
        """Cria um processador de sumarização.

        Args:
            max_length: Tamanho máximo do resumo.
            model: Modelo a ser usado para sumarização.

        Returns:
            Um componente de processamento de sumarização.
        """

        class SummarizationProcessor(ProcessorComponent[str, str]):
            """Processador de sumarização."""

            def __init__(self, max_length: int = 150, model: str = "default") -> None:
                self.max_length = max_length
                self.model = model

            async def process(self, data: str) -> str:
                """Processa os dados para gerar um resumo.

                Args:
                    data: Texto a ser resumido.

                Returns:
                    Texto resumido.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a sumarização.
                """
                try:
                    # Simulação - em uma implementação real, usaríamos um modelo de NLP
                    print(
                        f"Resumindo texto com modelo {self.model} "
                        f"(max_length={self.max_length})"
                    )
                    if len(data) <= self.max_length:
                        return data
                    return data[: self.max_length] + "..."
                except Exception as e:
                    raise ProcessingError(f"Erro ao resumir texto: {e}")

            async def transform(self, data: str) -> str:
                """Transforma os dados para gerar um resumo.

                Args:
                    data: Texto a ser resumido.

                Returns:
                    Texto resumido.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a sumarização.
                """
                return await self.process(data)

        return SummarizationProcessor(max_length, model)

    @staticmethod
    def translate(
        target_language: str = "en", source_language: str = "auto"
    ) -> ProcessorComponent[str, str]:
        """Cria um processador de tradução.

        Args:
            target_language: Idioma de destino.
            source_language: Idioma de origem (auto para detecção automática).

        Returns:
            Um componente de processamento de tradução.
        """

        class TranslationProcessor(ProcessorComponent[str, str]):
            """Processador de tradução."""

            def __init__(
                self, target_language: str = "en", source_language: str = "auto"
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
                    print(
                        f"Traduzindo texto de {self.source_language} "
                        f"para {self.target_language}"
                    )
                    return f"[Tradução para {self.target_language}] {data}"
                except Exception as e:
                    raise ProcessingError(f"Erro ao traduzir texto: {e}")

            async def transform(self, data: str) -> str:
                """Transforma os dados para traduzir o texto.

                Args:
                    data: Texto a ser traduzido.

                Returns:
                    Texto traduzido.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a tradução.
                """
                return await self.process(data)

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

            async def transform(self, data: str) -> List[str]:
                """Transforma os dados para extrair palavras-chave.

                Args:
                    data: Texto do qual extrair palavras-chave.

                Returns:
                    Lista de palavras-chave.

                Raises:
                    ProcessingError: Se ocorrer um erro durante a extração.
                """
                return await self.process(data)

        return KeywordExtractor(max_keywords)


class Outputs:
    """Fábrica de componentes de saída.

    Esta classe fornece métodos estáticos para criar componentes de saída
    para uso em pipelines de composição.
    """

    @staticmethod
    def console(prefix: str = "") -> OutputComponent[Any]:
        """Cria uma saída de console.

        Args:
            prefix: Prefixo a ser adicionado à saída.

        Returns:
            Um componente de saída de console.
        """

        class ConsoleOutput(OutputComponent[Any]):
            """Saída de console."""

            def __init__(self, prefix: str = "") -> None:
                self.prefix = prefix

            async def write(self, data: Any) -> str:
                """Escreve os dados no console.

                Args:
                    data: Dados a serem escritos.

                Returns:
                    Mensagem de confirmação.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao escrever no console.
                """
                try:
                    # Formatar a saída
                    if isinstance(data, dict):
                        output = json.dumps(data, ensure_ascii=False, indent=2)
                    elif isinstance(data, list):
                        output = "\n".join(str(item) for item in data)
                    else:
                        output = str(data)

                    # Adicionar prefixo se fornecido
                    if self.prefix:
                        output = f"{self.prefix}{output}"

                    # Imprimir no console
                    print("\n=== Saída do Pipeline ===")
                    print(output)
                    print("=========================\n")

                    return "Dados exibidos no console"
                except Exception as e:
                    raise OutputWriteError(f"Erro ao escrever no console: {e}")

            async def output(self, data: Any) -> str:
                """Envia os dados para o console.

                Args:
                    data: Dados a serem enviados.

                Returns:
                    Mensagem de confirmação.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao enviar os dados.
                """
                return await self.write(data)

        return ConsoleOutput(prefix)

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

            async def output(self, data: Any) -> str:
                """Envia os dados para o arquivo.

                Args:
                    data: Dados a serem enviados.

                Returns:
                    Caminho do arquivo.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao enviar os dados.
                """
                return await self.write(data)

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

            async def output(self, data: str) -> str:
                """Envia os dados para o podcast.

                Args:
                    data: Dados a serem enviados.

                Returns:
                    Caminho do arquivo de podcast.

                Raises:
                    OutputWriteError: Se ocorrer um erro ao enviar os dados.
                """
                return await self.write(data)

        return PodcastOutput(path, voice)
