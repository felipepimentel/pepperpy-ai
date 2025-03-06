#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gerador de podcast de notícias usando PepperPy.

Purpose:
    Demonstrar como criar um gerador de podcast de notícias usando o framework
    PepperPy, que busca notícias de um feed RSS, resume os artigos e converte
    o texto em áudio.

Requirements:
    - Python 3.9+
    - PepperPy library
    - Internet connection (para feeds RSS)
    - API keys para serviços de LLM e TTS (se usar provedores externos)

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Set environment variables (optional):
       export NEWS_PODCAST_FEED_URL="https://news.google.com/rss"
       export NEWS_PODCAST_MAX_ARTICLES=5

    3. Run the example:
       python examples/use_cases/news_podcast_generator.py
"""

import asyncio
import os
from typing import Any, Dict, List

from pepperpy.core.composition import compose


class RSSFeedSource:
    """Componente de fonte para buscar notícias de um feed RSS."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - url: URL do feed RSS
                - max_items: Número máximo de itens a buscar
        """
        self.url = config.get("url", "https://news.google.com/rss")
        self.max_items = config.get("max_items", 5)

    async def fetch(self) -> List[Dict[str, str]]:
        """Busca notícias do feed RSS.

        Returns:
            Lista de artigos com título e conteúdo
        """
        print(f"Buscando até {self.max_items} notícias de {self.url}")

        # Simulação de busca de notícias
        return [
            {
                "title": f"Notícia {i + 1}",
                "content": f"Conteúdo da notícia {i + 1}. Este é um texto simulado para demonstrar o processamento de notícias.",
            }
            for i in range(self.max_items)
        ]


class SummarizationProcessor:
    """Componente de processamento para resumir artigos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - max_length: Tamanho máximo do resumo
        """
        self.max_length = config.get("max_length", 150)

    async def transform(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Resume os artigos.

        Args:
            articles: Lista de artigos a serem resumidos

        Returns:
            Lista de artigos com resumos
        """
        print(f"Resumindo {len(articles)} artigos (máx. {self.max_length} caracteres)")

        # Simulação de resumo
        for article in articles:
            article["summary"] = (
                f"Resumo de '{article['title']}'. {article['content'][: self.max_length]}..."
            )

        return articles


class PodcastOutputComponent:
    """Componente de saída para gerar podcast."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - voice: Voz a ser usada (código de idioma)
                - output_path: Caminho para salvar o arquivo de áudio
        """
        self.voice = config.get("voice", "pt")
        self.output_path = config.get("output_path", "output/news_podcast.mp3")

        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    async def output(self, articles: List[Dict[str, str]]) -> str:
        """Gera o podcast a partir dos artigos resumidos.

        Args:
            articles: Lista de artigos resumidos

        Returns:
            Caminho do arquivo de podcast gerado
        """
        print(f"Gerando podcast com {len(articles)} artigos usando voz '{self.voice}'")

        # Construir script do podcast
        script = "Bem-vindo ao podcast de notícias gerado pelo PepperPy!\n\n"

        for i, article in enumerate(articles):
            script += f"Notícia {i + 1}: {article['title']}\n"
            script += f"{article['summary']}\n\n"

        # Simulação de conversão de texto para fala
        print("Convertendo script para áudio (simulado):")
        print("-" * 40)
        print(script[:200] + "...")
        print("-" * 40)

        # Simular gravação do arquivo
        with open(self.output_path, "w") as f:
            f.write(script)

        print(f"Podcast salvo em: {self.output_path}")
        return self.output_path


async def generate_news_podcast(
    feed_url: str = None,
    max_articles: int = None,
    summary_length: int = None,
    voice: str = None,
    output_path: str = None,
) -> str:
    """Gera um podcast de notícias.

    Args:
        feed_url: URL do feed RSS
        max_articles: Número máximo de artigos
        summary_length: Tamanho máximo do resumo
        voice: Voz a ser usada
        output_path: Caminho para salvar o arquivo

    Returns:
        Caminho do arquivo de podcast gerado
    """
    # Usar valores padrão ou do ambiente para parâmetros não especificados
    feed_url = feed_url or os.environ.get(
        "NEWS_PODCAST_FEED_URL", "https://news.google.com/rss"
    )
    max_articles = max_articles or int(os.environ.get("NEWS_PODCAST_MAX_ARTICLES", "5"))
    summary_length = summary_length or int(
        os.environ.get("NEWS_PODCAST_SUMMARY_LENGTH", "150")
    )
    voice = voice or os.environ.get("NEWS_PODCAST_VOICE", "pt")
    output_path = output_path or os.environ.get(
        "NEWS_PODCAST_OUTPUT_PATH", "output/news_podcast.mp3"
    )

    # Criar pipeline de geração de podcast
    podcast_path = await (
        compose("news_podcast_pipeline")
        .source(RSSFeedSource({"url": feed_url, "max_items": max_articles}))
        .process(SummarizationProcessor({"max_length": summary_length}))
        .output(PodcastOutputComponent({"voice": voice, "output_path": output_path}))
        .execute()
    )

    return podcast_path


async def main():
    """Função principal."""
    print("=== Gerador de Podcast de Notícias ===")

    # Gerar podcast com configuração padrão
    podcast_path = await generate_news_podcast()

    print(f"\nPodcast gerado com sucesso em: {podcast_path}")
    print("\nPara personalizar a geração, você pode:")
    print("1. Definir variáveis de ambiente")
    print("2. Passar parâmetros diretamente para a função generate_news_podcast()")
    print("3. Modificar os componentes do pipeline para comportamentos personalizados")


if __name__ == "__main__":
    asyncio.run(main())
