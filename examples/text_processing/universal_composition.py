"""Exemplo completo demonstrando todas as funcionalidades do PepperPy.

Este exemplo demonstra as seguintes funcionalidades:
1. Composição Universal
2. Abstração por Intenção
3. Templates Pré-configurados
4. Sumarização de Documentos
5. Tradução de Conteúdo
6. Pipelines Paralelos

Cada funcionalidade é demonstrada usando as três abordagens disponíveis no PepperPy.
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


async def example_universal_composition():
    """Demonstra o uso da API de Composição Universal."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("=== Exemplo de Composição Universal ===")

    # Criar um podcast a partir de um feed RSS
    podcast_path = await (
        compose("podcast_pipeline")
        .source(sources.rss("https://news.google.com/rss", max_items=5))
        .process(processors.summarize(max_length=150))
        .output(
            outputs.podcast(
                voice="en", output_path=str(output_dir / "universal_podcast.mp3")
            )
        )
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_intent_abstraction():
    """Demonstra o uso da API de Abstração por Intenção."""
    from pepperpy import create

    logger.info("=== Exemplo de Abstração por Intenção ===")

    # Criar um podcast a partir de um feed RSS
    podcast_path = await (
        create("podcast")
        .from_source("https://news.google.com/rss")
        .with_summary(max_length=150)
        .to_audio(str(output_dir / "intent_podcast.mp3"), voice="en")
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_template():
    """Demonstra o uso de Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("=== Exemplo de Templates Pré-configurados ===")

    # Criar um podcast a partir de um feed RSS
    podcast_path = await templates.news_podcast(
        source_url="https://news.google.com/rss",
        output_path=str(output_dir / "template_podcast.mp3"),
        voice="en",
        max_articles=5,
        summary_length=150,
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_document_summary():
    """Demonstra a sumarização de documentos."""
    from pepperpy import compose, create, outputs, processors, sources, templates

    logger.info("=== Exemplo de Sumarização de Documentos ===")

    # Criar um documento de exemplo
    sample_text = """
    O framework PepperPy é uma solução moderna para desenvolvimento de aplicações de IA em Python.
    Ele oferece três níveis de abstração para atender diferentes necessidades:
    1. Composição Universal: API de baixo nível para compor componentes em pipelines
    2. Abstração por Intenção: API de médio nível para expressar intenções de forma natural
    3. Templates: API de alto nível com soluções pré-configuradas
    
    Com o PepperPy, você pode facilmente criar pipelines para processamento de texto,
    geração de conteúdo, tradução, sumarização e muito mais. A arquitetura modular
    permite estender o framework com novos componentes e integrações.
    
    O PepperPy é ideal para desenvolvedores que precisam criar soluções de IA
    rapidamente, sem sacrificar flexibilidade ou controle.
    """

    sample_file = output_dir / "sample_document_summary.txt"
    with open(sample_file, "w") as f:
        f.write(sample_text)

    # Sumarização usando Composição Universal
    summary_path_universal = await (
        compose("summary_pipeline")
        .source(sources.file(str(sample_file)))
        .process(processors.summarize(max_length=100))
        .output(outputs.file(str(output_dir / "document_summary_universal.txt")))
        .execute()
    )

    # Sumarização usando Abstração por Intenção
    summary_path_intent = await (
        create("summarizer")
        .from_source(str(sample_file))
        .with_summary(max_length=100)
        .save_to(str(output_dir / "document_summary_intent.txt"))
        .execute()
    )

    # Sumarização usando Templates
    summary_path_template = await templates.document_summarizer(
        content_path=str(sample_file),
        output_path=str(output_dir / "document_summary_template.txt"),
        max_length=100,
    )

    # Exibir resultados
    with open(summary_path_universal, "r") as f:
        logger.info(f"Sumarização Universal:\n{f.read()}")

    with open(summary_path_intent, "r") as f:
        logger.info(f"Sumarização por Intenção:\n{f.read()}")

    with open(summary_path_template, "r") as f:
        logger.info(f"Sumarização por Template:\n{f.read()}")

    return [summary_path_universal, summary_path_intent, summary_path_template]


async def example_content_translation():
    """Demonstra a tradução de conteúdo."""
    from pepperpy import compose, create, outputs, processors, sources, templates

    logger.info("=== Exemplo de Tradução de Conteúdo ===")

    # Criar um documento de exemplo
    sample_text = """
    The PepperPy framework is a modern solution for AI application development in Python.
    It offers three levels of abstraction to meet different needs:
    1. Universal Composition: Low-level API for composing components into pipelines
    2. Intent Abstraction: Mid-level API for expressing intentions naturally
    3. Templates: High-level API with pre-configured solutions
    """

    sample_file = output_dir / "sample_document_translation.txt"
    with open(sample_file, "w") as f:
        f.write(sample_text)

    # Tradução usando Composição Universal
    translation_path_universal = await (
        compose("translation_pipeline")
        .source(sources.file(str(sample_file)))
        .process(processors.translate(target_language="pt"))
        .output(outputs.file(str(output_dir / "content_translation_universal.txt")))
        .execute()
    )

    # Tradução usando Abstração por Intenção
    translation_path_intent = await (
        create("translator")
        .from_source(str(sample_file))
        .to_target_language("pt")
        .save_to(str(output_dir / "content_translation_intent.txt"))
        .execute()
    )

    # Tradução usando Templates
    translation_path_template = await templates.content_translator(
        content_path=str(sample_file),
        target_language="pt",
        output_path=str(output_dir / "content_translation_template.txt"),
    )

    # Exibir resultados
    with open(translation_path_universal, "r") as f:
        logger.info(f"Tradução Universal:\n{f.read()}")

    with open(translation_path_intent, "r") as f:
        logger.info(f"Tradução por Intenção:\n{f.read()}")

    with open(translation_path_template, "r") as f:
        logger.info(f"Tradução por Template:\n{f.read()}")

    return [
        translation_path_universal,
        translation_path_intent,
        translation_path_template,
    ]


async def example_parallel_pipeline():
    """Demonstra o uso de pipeline paralelo."""
    from pepperpy import compose, create, outputs, processors, sources, templates

    logger.info("=== Exemplo de Pipeline Paralelo ===")

    # Definir fontes RSS
    rss_feeds = [
        "https://news.google.com/rss",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ]

    # Processamento paralelo usando Composição Universal
    tasks_universal = []
    for i, feed_url in enumerate(rss_feeds):
        task = (
            compose(f"feed_pipeline_{i}")
            .source(sources.rss(feed_url, max_items=3))
            .process(processors.summarize(max_length=100))
            .output(
                outputs.file(str(output_dir / f"parallel_summary_universal_{i}.txt"))
            )
            .execute()
        )
        tasks_universal.append(task)

    results_universal = await asyncio.gather(*tasks_universal)
    logger.info(
        f"Resultados do processamento paralelo (Universal): {results_universal}"
    )

    # Processamento paralelo usando Abstração por Intenção
    tasks_intent = []
    for i, feed_url in enumerate(rss_feeds):
        task = (
            create("news_processor")
            .from_source(feed_url)
            .with_summary(max_length=100)
            .save_to(str(output_dir / f"parallel_summary_intent_{i}.txt"))
            .execute()
        )
        tasks_intent.append(task)

    results_intent = await asyncio.gather(*tasks_intent)
    logger.info(f"Resultados do processamento paralelo (Intenção): {results_intent}")

    # Processamento paralelo usando Templates
    tasks_template = []
    for i, feed_url in enumerate(rss_feeds):
        task = templates.news_summarizer(
            source_url=feed_url,
            output_path=str(output_dir / f"parallel_summary_template_{i}.txt"),
            max_items=3,
            summary_length=100,
        )
        tasks_template.append(task)

    results_template = await asyncio.gather(*tasks_template)
    logger.info(f"Resultados do processamento paralelo (Template): {results_template}")

    return {
        "universal": results_universal,
        "intent": results_intent,
        "template": results_template,
    }


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos do PepperPy")

    # Executar exemplos
    await example_universal_composition()
    await example_intent_abstraction()
    await example_template()
    await example_document_summary()
    await example_content_translation()
    await example_parallel_pipeline()

    logger.info("Todos os exemplos foram concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
