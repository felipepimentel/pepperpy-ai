"""Exemplo de uso da API de composição universal.

Este exemplo demonstra como usar a API de composição universal para criar
pipelines de processamento flexíveis e reutilizáveis.
"""

import asyncio
import os

from pepperpy.core.composition import (
    Outputs,
    Processors,
    Sources,
    compose,
    compose_parallel,
)


async def example_universal_composition():
    """Demonstra o uso da API de composição universal."""
    print("\n=== Exemplo de Composição Universal ===")

    # Criar diretório de saída
    os.makedirs("example_output", exist_ok=True)

    # Criar um pipeline para gerar um podcast a partir de um feed RSS
    print("\n1. Criando podcast a partir de feed RSS...")
    pipeline = (
        compose("podcast_pipeline")
        .source(Sources.rss("https://news.google.com/rss", max_items=3))
        .process(Processors.summarize(max_length=150))
        .output(Outputs.podcast("example_output/podcast.mp3", voice="pt"))
    )

    # Executar o pipeline
    podcast_path = await pipeline.execute()
    print(f"Podcast gerado em: {podcast_path}")

    # Criar um pipeline para resumir um documento
    print("\n2. Resumindo documento...")
    with open("example_output/document.txt", "w") as f:
        f.write(
            "Este é um documento de exemplo para demonstrar a API de composição universal. "
            "A API permite compor componentes de diferentes domínios em pipelines de processamento. "
            "Os componentes podem ser fontes de dados, processadores e saídas. "
            "A API é flexível e permite criar pipelines personalizados para diferentes casos de uso. "
            "Este exemplo demonstra como usar a API para criar um pipeline que resume um documento."
        )

    pipeline = (
        compose("document_summary_pipeline")
        .source(Sources.file("example_output/document.txt"))
        .process(Processors.summarize(max_length=50))
        .output(Outputs.file("example_output/document_summary.txt"))
    )

    # Executar o pipeline
    summary_path = await pipeline.execute()
    print(f"Resumo gerado em: {summary_path}")

    # Criar um pipeline para traduzir conteúdo
    print("\n3. Traduzindo conteúdo...")
    pipeline = (
        compose("content_translation_pipeline")
        .source(
            Sources.text("Hello, world! This is a test of the translation pipeline.")
        )
        .process(Processors.translate(target_language="pt"))
        .output(Outputs.file("example_output/translated.txt"))
    )

    # Executar o pipeline
    translation_path = await pipeline.execute()
    print(f"Tradução gerada em: {translation_path}")


async def example_parallel_pipeline():
    """Demonstra o uso de pipelines paralelos."""
    print("\n=== Exemplo de Pipeline Paralelo ===")

    # Criar diretório de saída
    os.makedirs("example_output", exist_ok=True)

    # Criar um pipeline paralelo para processar um feed RSS
    print("\n1. Processando feed RSS em paralelo...")
    pipeline = (
        compose_parallel("parallel_rss_pipeline")
        .source(Sources.rss("https://news.google.com/rss", max_items=3))
        .process(Processors.summarize(max_length=150))
        .process(Processors.extract_keywords(max_keywords=5))
        .output(Outputs.file("example_output/parallel_rss_result.txt"))
    )

    # Executar o pipeline
    result_path = await pipeline.execute()
    print(f"Resultado gerado em: {result_path}")

    # Criar um pipeline paralelo para traduzir e resumir conteúdo
    print("\n2. Traduzindo e resumindo conteúdo em paralelo...")
    pipeline = (
        compose_parallel("parallel_translation_summary_pipeline")
        .source(Sources.text("Hello, world! This is a test of the parallel pipeline."))
        .process(Processors.translate(target_language="pt"))
        .process(Processors.summarize(max_length=50))
        .output(Outputs.file("example_output/parallel_translation_summary.txt"))
    )

    # Executar o pipeline
    result_path = await pipeline.execute()
    print(f"Resultado gerado em: {result_path}")


async def main():
    """Função principal."""
    print("Demonstração da API de Composição Universal do PepperPy")
    print("------------------------------------------------------")

    await example_universal_composition()
    await example_parallel_pipeline()

    print("\nExemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
