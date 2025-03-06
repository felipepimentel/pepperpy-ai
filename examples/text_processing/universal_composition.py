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

# Configurar diretório de saída
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)


async def example_universal_composition():
    """Demonstra o uso da API de Composição Universal."""
    from pepperpy.core.composition import Outputs, Processors, Sources, compose

    logger.info("=== Exemplo de Composição Universal ===")

    # Criar um podcast a partir de um feed RSS
    podcast_path = await (
        compose("podcast_pipeline")
        .source(Sources.rss("https://news.google.com/rss", max_items=5))
        .process(Processors.summarize(max_length=150))
        .output(Outputs.podcast(str(output_dir / "universal_podcast.mp3"), voice="en"))
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_intent_abstraction():
    """Demonstra o uso da API de Abstração por Intenção."""
    # Simulação de abstração por intenção
    from pepperpy.core.composition import Outputs, Processors, Sources, compose

    logger.info("=== Exemplo de Abstração por Intenção ===")

    # Texto de exemplo
    text = """
    O PepperPy é um framework de composição universal para Python que permite
    a criação de pipelines de processamento flexíveis e reutilizáveis.
    """

    # Criar um pipeline para processar o texto (simulando abstração por intenção)
    podcast_path = await (
        compose("intent_podcast")
        .source(Sources.text(text))
        .process(Processors.summarize(max_length=150))
        .output(Outputs.podcast(str(output_dir / "intent_podcast.mp3"), voice="en"))
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_template():
    """Demonstra o uso de Templates Pré-configurados."""
    # Simulação de template
    from pepperpy.core.composition import Outputs, Processors, Sources, compose

    logger.info("=== Exemplo de Template ===")

    # Criar um podcast a partir de um feed RSS (simulando um template)
    podcast_path = await (
        compose("podcast_template")
        .source(Sources.rss("https://news.google.com/rss", max_items=5))
        .process(Processors.summarize(max_length=150))
        .output(Outputs.podcast(str(output_dir / "template_podcast.mp3"), voice="en"))
        .execute()
    )

    logger.info(f"Podcast gerado em: {podcast_path}")
    return podcast_path


async def example_document_summary():
    """Demonstra a sumarização de documentos."""
    from pepperpy.core.composition import Outputs, Processors, Sources, compose

    logger.info("=== Exemplo de Sumarização de Documentos ===")

    # Texto de exemplo
    document_text = """
    O PepperPy é um framework de composição universal para Python que permite
    a criação de pipelines de processamento flexíveis e reutilizáveis. Ele
    fornece uma API fluente para compor componentes de diferentes domínios,
    como processamento de texto, geração de conteúdo, e automação de fluxos
    de trabalho.

    A arquitetura do PepperPy é baseada em três tipos principais de componentes:
    1. Fontes (Sources): Componentes que fornecem dados para o pipeline.
    2. Processadores (Processors): Componentes que transformam os dados.
    3. Saídas (Outputs): Componentes que escrevem os dados processados.

    Esses componentes são combinados em pipelines que podem ser executados
    para processar dados de forma sequencial ou paralela. A API fluente
    permite a criação de pipelines de forma intuitiva e encadeada.

    O PepperPy também fornece abstrações de alto nível, como intenções e
    templates, que simplificam ainda mais o uso do framework para casos
    comuns. Isso permite que os usuários escolham o nível de abstração
    mais adequado para suas necessidades.
    """

    # Criar um pipeline para sumarizar o documento
    summary_path = await (
        compose("document_summarizer")
        .source(Sources.text(document_text))
        .process(Processors.summarize(max_length=100))
        .output(Outputs.file(str(output_dir / "document_summary.txt")))
        .execute()
    )

    logger.info(f"Resumo salvo em: {summary_path}")

    # Ler o resumo
    with open(summary_path, "r") as f:
        summary = f.read()

    logger.info(f"Resumo: {summary[:100]}...")
    return summary_path


async def example_content_translation():
    """Demonstra a tradução de conteúdo."""
    from pepperpy.core.composition import Outputs, Processors, Sources, compose

    logger.info("=== Exemplo de Tradução de Conteúdo ===")

    # Texto de exemplo
    text = """
    O PepperPy é um framework de composição universal para Python que permite
    a criação de pipelines de processamento flexíveis e reutilizáveis.
    """

    # Criar um pipeline para traduzir o texto
    translation_path = await (
        compose("content_translator")
        .source(Sources.text(text))
        .process(Processors.translate(target_language="en"))
        .output(Outputs.file(str(output_dir / "translated_content.txt")))
        .execute()
    )

    logger.info(f"Tradução salva em: {translation_path}")

    # Ler a tradução
    with open(translation_path, "r") as f:
        translation = f.read()

    logger.info(f"Tradução: {translation[:100]}...")
    return translation_path


async def example_parallel_pipeline():
    """Demonstra o uso de pipelines paralelos."""
    from pepperpy.core.composition import Outputs, Processors, Sources, compose_parallel

    logger.info("=== Exemplo de Pipeline Paralelo ===")

    # Texto de exemplo
    text = """
    O PepperPy é um framework de composição universal para Python que permite
    a criação de pipelines de processamento flexíveis e reutilizáveis.
    """

    # Criar um pipeline paralelo para processar o texto
    result_path = await (
        compose_parallel("parallel_pipeline")
        .source(Sources.text(text))
        .process(Processors.summarize(max_length=50))
        .process(Processors.translate(target_language="en"))
        .process(Processors.extract_keywords(max_keywords=5))
        .output(Outputs.file(str(output_dir / "parallel_result.txt")))
        .execute()
    )

    logger.info(f"Resultado salvo em: {result_path}")

    # Ler o resultado
    with open(result_path, "r") as f:
        result = f.read()

    logger.info(f"Resultado: {result[:100]}...")
    return result_path


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
