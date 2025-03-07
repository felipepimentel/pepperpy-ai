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
       export NEWS_PODCAST_MAX_ARTICLES="5"

    3. Run the example:
       python examples/content_generation/news_podcast_generator.py
"""

import asyncio
import os
import random
from datetime import datetime
from typing import Optional

from pepperpy.apps import MediaApp
from pepperpy.sources import RSSSource


def generate_fake_feed_url() -> str:
    """Gera uma URL fake de feed RSS.

    Returns:
        URL fake de feed RSS
    """
    feeds = [
        "https://news.google.com/rss",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.tecmundo.com.br/rss",
        "https://www.wired.com/feed/rss",
        "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
        "https://g1.globo.com/rss/g1/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.engadget.com/rss.xml",
        "https://www.cnet.com/rss/news/",
    ]

    return random.choice(feeds)


def generate_fake_voice() -> str:
    """Gera uma voz fake para o podcast.

    Returns:
        Voz fake
    """
    voices = [
        "pt-BR-Standard-A",
        "pt-BR-Standard-B",
        "pt-BR-Standard-C",
        "pt-BR-Wavenet-A",
        "pt-BR-Wavenet-B",
        "pt-BR-Wavenet-C",
        "en-US-Standard-A",
        "en-US-Standard-B",
        "en-US-Standard-C",
        "en-US-Wavenet-A",
    ]

    return random.choice(voices)


async def generate_news_podcast(
    feed_url: Optional[str] = None,
    max_articles: Optional[int] = None,
    summary_length: Optional[int] = None,
    voice: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Gera um podcast de notícias.

    Args:
        feed_url: URL do feed RSS de notícias
        max_articles: Número máximo de artigos a processar
        summary_length: Comprimento máximo do resumo em palavras
        voice: Voz a ser usada para o podcast
        output_path: Caminho para salvar o podcast

    Returns:
        Caminho do arquivo de podcast gerado
    """
    # Valores padrão
    feed_url = feed_url or os.environ.get(
        "NEWS_PODCAST_FEED_URL", "https://news.google.com/rss"
    )
    max_articles = max_articles or int(os.environ.get("NEWS_PODCAST_MAX_ARTICLES", "5"))
    summary_length = summary_length or int(
        os.environ.get("NEWS_PODCAST_SUMMARY_LENGTH", "100")
    )
    voice = voice or os.environ.get("NEWS_PODCAST_VOICE", "pt-BR-Standard-A")

    # Criar aplicação de mídia com uma única linha
    app = MediaApp(name="news_podcast_generator")

    # Configurar a aplicação com uma API fluente
    app.configure(
        max_articles=max_articles,
        summary_length=summary_length,
        voice=voice,
        intro_text="Bem-vindo ao podcast de notícias gerado pelo PepperPy.",
        outro_text="Obrigado por ouvir. Até a próxima!",
        add_timestamps=True,
    )

    # Adicionar fonte de dados RSS
    app.add_source(RSSSource(feed_url))

    # Se um caminho de saída foi especificado, configurar
    if output_path:
        app.set_output_path(output_path)
    else:
        # Gerar nome de arquivo baseado na data
        date_str = datetime.now().strftime("%Y%m%d")
        app.set_output_path(f"news_podcast_{date_str}.mp3")

    # Gerar podcast com uma única chamada
    result = await app.generate_podcast()

    return result.output_path


async def main():
    """Executa o exemplo de geração de podcast de notícias."""
    print("=== Gerador de Podcast de Notícias com PepperPy ===")
    print("Este exemplo demonstra como gerar um podcast de notícias")
    print("a partir de feeds RSS usando o PepperPy.")

    # Definir configurações para diferentes podcasts
    configurations = [
        {"name": "Podcast Curto", "config": {"max_articles": 3, "summary_length": 50}},
        {
            "name": "Podcast Padrão",
            "config": {"max_articles": 5, "summary_length": 100},
        },
        {
            "name": "Podcast Detalhado",
            "config": {"max_articles": 8, "summary_length": 200},
        },
    ]

    # Gerar podcasts com diferentes configurações
    for i, config_item in enumerate(configurations):
        # Gerar feed e voz fake
        feed_url = generate_fake_feed_url()
        voice = generate_fake_voice()

        # Obter configuração
        config_name = config_item["name"]
        config = config_item["config"]

        print(f"\n--- Gerando Podcast {i + 1}: {config_name} ---")
        print(f"Feed: {feed_url}")
        print(f"Voz: {voice}")
        print(f"Configuração: {config}")

        # Gerar podcast
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = f"news_podcast_{date_str}_{i + 1}.mp3"

        podcast_path = await generate_news_podcast(
            feed_url=feed_url, voice=voice, output_path=output_path, **config
        )

        print("Podcast gerado com sucesso!")
        print(f"Salvo em: {podcast_path}")

        # Mostrar informações do arquivo
        if os.path.exists(podcast_path):
            file_size = os.path.getsize(podcast_path)
            print(f"Tamanho do arquivo: {file_size / 1024:.2f} KB")

        # Pausa entre gerações
        if i < len(configurations) - 1:
            await asyncio.sleep(1)

    print("\n=== Geração de Podcasts Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
