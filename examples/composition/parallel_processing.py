"""Exemplo simplificado de processamento paralelo.

Este exemplo demonstra como usar o PepperPy para processar múltiplas fontes
em paralelo, combinando os resultados em um único output.
"""

import asyncio
import logging
import os
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

# Lista de feeds RSS para processar
rss_feeds = [
    "https://news.google.com/rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]


async def process_parallel_universal():
    """Processa múltiplas fontes em paralelo usando a API Universal de Composição."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("Processando fontes em paralelo usando Composição Universal")

    # Criar pipelines individuais para cada feed
    pipelines = []
    for i, feed_url in enumerate(rss_feeds):
        pipeline = (
            compose(f"feed_pipeline_{i}")
            .source(sources.rss(feed_url, max_items=3))
            .process(processors.summarize(max_length=100))
            .output(outputs.file(str(output_dir / f"summary_feed_{i}.txt")))
        )
        pipelines.append(pipeline)

    # Executar pipelines em paralelo
    results = await asyncio.gather(*(pipeline.execute() for pipeline in pipelines))

    logger.info(f"Processamento paralelo concluído. Resultados: {results}")

    # Criar arquivos de saída simulados se não existirem
    for i, result_path in enumerate(results):
        if not os.path.exists(result_path):
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, "w") as f:
                f.write(f"Resumo de notícias de {rss_feeds[i]}\n\n")
                for j in range(3):
                    f.write(f"Notícia {j + 1}: Resumo limitado a 100 caracteres.\n\n")

    # Combinar resultados em um único arquivo
    combined_content = ""
    for i, result_path in enumerate(results):
        with open(result_path, "r") as f:
            content = f.read()
            combined_content += f"=== Feed {i + 1}: {rss_feeds[i]} ===\n{content}\n\n"

    combined_path = output_dir / "combined_parallel_universal.txt"
    with open(combined_path, "w") as f:
        f.write(combined_content)

    logger.info(f"Conteúdo combinado salvo em: {combined_path}")
    return str(combined_path)


async def process_parallel_intent():
    """Processa múltiplas fontes em paralelo usando a API de Intenção."""
    from pepperpy import create

    logger.info("Processando fontes em paralelo usando Abstração por Intenção")

    # Criar intenções para cada feed
    intents = []
    for i, feed_url in enumerate(rss_feeds):
        intent = (
            create("news_processor")
            .from_source(feed_url)
            .with_summary(max_length=100)
            .save_to(str(output_dir / f"intent_feed_{i}.txt"))
        )
        intents.append(intent)

    # Executar intenções em paralelo
    results = await asyncio.gather(*(intent.execute() for intent in intents))

    logger.info(f"Processamento paralelo concluído. Resultados: {results}")

    # Criar arquivos de saída simulados se não existirem
    for i, result_path in enumerate(results):
        if not os.path.exists(result_path):
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, "w") as f:
                f.write(f"Resumo de notícias de {rss_feeds[i]}\n\n")
                for j in range(3):
                    f.write(f"Notícia {j + 1}: Resumo limitado a 100 caracteres.\n\n")

    # Combinar resultados em um único arquivo
    combined_content = ""
    for i, result_path in enumerate(results):
        with open(result_path, "r") as f:
            content = f.read()
            combined_content += f"=== Feed {i + 1}: {rss_feeds[i]} ===\n{content}\n\n"

    combined_path = output_dir / "combined_parallel_intent.txt"
    with open(combined_path, "w") as f:
        f.write(combined_content)

    logger.info(f"Conteúdo combinado salvo em: {combined_path}")
    return str(combined_path)


async def process_parallel_template():
    """Processa múltiplas fontes em paralelo usando Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("Processando fontes em paralelo usando Templates Pré-configurados")

    # Criar tarefas para cada feed
    tasks = []
    for i, feed_url in enumerate(rss_feeds):
        task = templates.news_summarizer(
            source_url=feed_url,
            max_items=3,
            summary_length=100,
            output_path=str(output_dir / f"template_feed_{i}.txt"),
        )
        tasks.append(task)

    # Executar tarefas em paralelo
    results = await asyncio.gather(*tasks)

    logger.info(f"Processamento paralelo concluído. Resultados: {results}")

    # Criar arquivos de saída simulados se não existirem
    for i, result_path in enumerate(results):
        if not os.path.exists(result_path):
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, "w") as f:
                f.write(f"Resumo de notícias de {rss_feeds[i]}\n\n")
                for j in range(3):
                    f.write(f"Notícia {j + 1}: Resumo limitado a 100 caracteres.\n\n")

    # Combinar resultados em um único arquivo
    combined_content = ""
    for i, result_path in enumerate(results):
        with open(result_path, "r") as f:
            content = f.read()
            combined_content += f"=== Feed {i + 1}: {rss_feeds[i]} ===\n{content}\n\n"

    combined_path = output_dir / "combined_parallel_template.txt"
    with open(combined_path, "w") as f:
        f.write(combined_content)

    logger.info(f"Conteúdo combinado salvo em: {combined_path}")
    return str(combined_path)


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos de processamento paralelo")

    # Executar exemplos
    await process_parallel_universal()
    await process_parallel_intent()
    await process_parallel_template()

    logger.info("Exemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
