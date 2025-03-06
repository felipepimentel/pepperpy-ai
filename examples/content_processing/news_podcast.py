#!/usr/bin/env python3
"""News Podcast Generator Example

Purpose:
    Demonstrar como criar um gerador de podcast de notícias usando PepperPy
    com uma API moderna baseada em composição universal.

Requirements:
    - Python 3.10+
    - PepperPy library
    - Internet connection (for RSS feeds)
    - API keys for LLM and TTS services (if using external providers)

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables (optional, defaults provided):
       export NEWS_PODCAST_FEED_URL="https://news.google.com/rss"
       export NEWS_PODCAST_MAX_ARTICLES=5
       export NEWS_PODCAST_VOICE_NAME="en"
       export NEWS_PODCAST_OUTPUT_PATH="example_output/news_podcast.mp3"

    3. Run the example:
       poetry run python examples/news_podcast.py
"""

import asyncio
import logging
import os
from pathlib import Path

# Configuração de logging básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Em um ambiente real, estes imports seriam da biblioteca PepperPy
# from pepperpy import compose, create, templates
# from pepperpy.pipeline.namespaces import Sources, Processors, Outputs


# Como estamos simulando, vamos criar as classes necessárias
class MockComponent:
    """Componente base simulado."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class MockSource(MockComponent):
    """Fonte simulada."""

    async def fetch(self, context):
        logger.info(f"Buscando conteúdo de {self.name}")
        # Simulação de busca de conteúdo
        await asyncio.sleep(0.1)
        return [
            {"title": f"Artigo {i + 1}", "content": f"Conteúdo do artigo {i + 1}"}
            for i in range(5)
        ]


class MockProcessor(MockComponent):
    """Processador simulado."""

    async def process(self, content, context):
        logger.info(f"Processando conteúdo com {self.name}")
        # Simulação de processamento
        await asyncio.sleep(0.1)
        return [
            {
                **item,
                "summary": f"Resumo do {item['title']} com no máximo 150 caracteres.",
            }
            for item in content
        ]


class MockOutput(MockComponent):
    """Saída simulada."""

    def __init__(self, name, output_path):
        super().__init__(name)
        self.output_path = output_path

    async def generate(self, content, context):
        logger.info(f"Gerando saída em {self.output_path}")
        # Simulação de geração de saída
        await asyncio.sleep(0.1)

        # Criar conteúdo do podcast
        podcast_content = "\n\n".join([
            f"# {item['title']}\n\n{item.get('summary', item['content'])}"
            for item in content
        ])

        # Criar arquivo de saída
        output_file = Path(self.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(podcast_content)

        return output_file


class MockPipeline:
    """Pipeline simulado."""

    def __init__(self, name=None):
        self.name = name or "pipeline"
        self.steps = []

    def source(self, source):
        self.steps.append(("source", source))
        return self

    def process(self, processor):
        self.steps.append(("process", processor))
        return self

    def output(self, output):
        self.steps.append(("output", output))
        return self

    async def execute(self, context=None):
        logger.info(f"Executando pipeline: {self.name}")

        result = None
        for step_type, component in self.steps:
            if step_type == "source":
                result = await component.fetch(context or {})
            elif step_type == "process":
                result = await component.process(result, context or {})
            elif step_type == "output":
                result = await component.generate(result, context or {})

        return result


class MockCreator:
    """Criador simulado."""

    def __init__(self, intent):
        self.intent = intent
        self.config = {}

    def from_source(self, source_url):
        self.config["source_url"] = source_url
        return self

    def to_audio(self, output_path):
        self.config["output_path"] = output_path
        return self

    def __call__(self):
        # Retorna self em vez de uma coroutine
        return self

    async def execute(self):
        # Criar pipeline baseado na configuração
        pipeline = compose(self.intent)

        # Adicionar fonte
        pipeline.source(Sources.rss(self.config["source_url"]))

        # Adicionar processador padrão
        pipeline.process(Processors.summarize())

        # Adicionar saída
        pipeline.output(Outputs.podcast(output_path=self.config["output_path"]))

        # Executar pipeline
        return await pipeline.execute()


class MockTemplates:
    """Templates simulados."""

    @staticmethod
    async def news_podcast(source_url, output_path):
        # Criar e executar pipeline
        pipeline = (
            compose("news_podcast")
            .source(Sources.rss(source_url))
            .process(Processors.summarize())
            .output(Outputs.podcast(output_path=output_path))
        )

        return await pipeline.execute()


# Funções e classes simuladas para a API
def compose(name=None):
    return MockPipeline(name)


def create(intent):
    return MockCreator(intent)


templates = MockTemplates()


class Sources:
    @staticmethod
    def rss(url, max_items=5):
        return MockSource(f"RSS({url}, max_items={max_items})")


class Processors:
    @staticmethod
    def summarize(max_length=150):
        return MockProcessor(f"Summarize(max_length={max_length})")


class Outputs:
    @staticmethod
    def podcast(voice="en", output_path="output.mp3"):
        return MockOutput(f"Podcast(voice={voice})", output_path)


# Exemplo 1: Composição Universal (cerca de 10 linhas)
async def generate_podcast_composition():
    """Gera um podcast de notícias usando composição universal."""
    # Criar um pipeline usando composição universal
    pipeline = (
        compose("news_podcast")
        .source(Sources.rss("https://news.google.com/rss", max_items=5))
        .process(Processors.summarize(max_length=150))
        .output(
            Outputs.podcast(voice="en", output_path="example_output/news_podcast.mp3")
        )
    )

    # Executar o pipeline
    return await pipeline.execute()


# Exemplo 2: Abstração por Intenção (apenas 3 linhas)
async def generate_podcast_intent():
    """Gera um podcast de notícias usando abstração por intenção."""
    # Criar e executar um podcast expressando a intenção
    return (
        await create("news_podcast")()
        .from_source("https://news.google.com/rss")
        .to_audio("example_output/news_podcast_intent.mp3")
        .execute()
    )


# Exemplo 3: Template Pré-configurado (apenas 1 linha)
async def generate_podcast_template():
    """Gera um podcast de notícias usando um template pré-configurado."""
    # Usar um template pré-configurado
    return await templates.news_podcast(
        "https://news.google.com/rss", "example_output/news_podcast_template.mp3"
    )


async def main():
    """Executa os exemplos de geração de podcast."""
    try:
        # Exemplo 1: Composição Universal
        print("\n=== Exemplo 1: Composição Universal (cerca de 10 linhas) ===")
        print("""
pipeline = (
    compose("news_podcast")
    .source(Sources.rss("https://news.google.com/rss", max_items=5))
    .process(Processors.summarize(max_length=150))
    .output(
        Outputs.podcast(voice="en", output_path="example_output/news_podcast.mp3")
    )
)

result = await pipeline.execute()
        """)

        result = await generate_podcast_composition()
        print(f"\nPodcast gerado com sucesso: {result}")

        # Exemplo 2: Abstração por Intenção
        print("\n=== Exemplo 2: Abstração por Intenção (apenas 3 linhas) ===")
        print("""
result = await create("news_podcast")()\\
    .from_source("https://news.google.com/rss")\\
    .to_audio("example_output/news_podcast_intent.mp3")\\
    .execute()
        """)

        result = await generate_podcast_intent()
        print(f"\nPodcast gerado com sucesso: {result}")

        # Exemplo 3: Template Pré-configurado
        print("\n=== Exemplo 3: Template Pré-configurado (apenas 1 linha) ===")
        print("""
result = await templates.news_podcast(
    "https://news.google.com/rss", 
    "example_output/news_podcast_template.mp3"
)
        """)

        result = await generate_podcast_template()
        print(f"\nPodcast gerado com sucesso: {result}")

    except Exception as e:
        logger.error(f"Erro: {e}")
        print(f"\nErro: {e}")


if __name__ == "__main__":
    asyncio.run(main())
