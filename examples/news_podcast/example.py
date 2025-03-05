#!/usr/bin/env python3
"""Exemplo de uso do gerador de podcast de notícias.

Este exemplo demonstra como usar o gerador de podcast de notícias
com configurações personalizadas.
"""

import asyncio
from pathlib import Path

from examples.news_podcast.config import load_config
from examples.news_podcast.news_podcast_workflow import NewsPodcastWorkflow


async def main():
    """Função principal do exemplo."""
    # Definir o diretório de saída
    output_dir = Path(__file__).parent / "example_output"
    output_dir.mkdir(exist_ok=True)

    # Carregar configuração com valores personalizados
    config = load_config(
        feed_url="https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        output_path=str(output_dir / "nytimes_podcast.mp3"),
        max_articles=3,
        voice_name="en",
    )

    # Criar e executar o fluxo de trabalho
    workflow = NewsPodcastWorkflow(config)
    podcast_path = await workflow.run()

    if podcast_path:
        print(f"Podcast gerado com sucesso: {podcast_path}")
    else:
        print("Falha ao gerar o podcast")


if __name__ == "__main__":
    asyncio.run(main())
