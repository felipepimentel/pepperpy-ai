"""Exemplo simplificado de geração de podcast de notícias.

Este exemplo demonstra como usar o PepperPy para gerar um podcast de notícias
a partir de um feed RSS, usando as três abordagens diferentes:
1. Composição Universal
2. Abstração por Intenção
3. Templates Pré-configurados
"""

import asyncio
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar diretório de saída
output_dir = Path("example_output")
output_dir.mkdir(exist_ok=True)


async def generate_podcast_universal():
    """Gera um podcast usando a API Universal de Composição."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("Gerando podcast usando Composição Universal")

    podcast_path = await (
        compose("podcast_pipeline")
        .source(sources.rss("https://news.google.com/rss", max_items=5))
        .process(processors.summarize(max_length=150))
        .output(
            outputs.podcast(
                voice="en", output_path=str(output_dir / "news_podcast.mp3")
            )
        )
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def generate_podcast_intent():
    """Gera um podcast usando a API de Intenção."""
    from pepperpy import create

    logger.info("Gerando podcast usando Abstração por Intenção")

    podcast_path = await (
        create("podcast")
        .from_source("https://news.google.com/rss")
        .with_summary(max_length=150)
        .to_audio(str(output_dir / "news_podcast_intent.mp3"), voice="en")
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def generate_podcast_template():
    """Gera um podcast usando Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("Gerando podcast usando Templates Pré-configurados")

    podcast_path = await templates.news_podcast(
        source_url="https://news.google.com/rss",
        output_path=str(output_dir / "news_podcast_template.mp3"),
        voice="en",
        max_articles=5,
        summary_length=150,
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos de geração de podcast de notícias")

    # Executar exemplos
    await generate_podcast_universal()
    await generate_podcast_intent()
    await generate_podcast_template()

    logger.info("Exemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
