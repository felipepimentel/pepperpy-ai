#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo simplificado de processamento paralelo.

Purpose:
    Demonstrar como usar o PepperPy para processar múltiplas fontes
    em paralelo, combinando os resultados em um único output.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/workflow_automation/parallel_processing.py
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar diretório de saída
output_dir = Path("example_output")
output_dir.mkdir(exist_ok=True)

# Lista de URLs para processar
urls = [
    "https://news.google.com/rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]


async def process_parallel_custom():
    """Processa múltiplas fontes em paralelo usando funções personalizadas."""
    logger.info("Processando fontes em paralelo usando funções personalizadas")

    async def fetch_url(url: str) -> Dict[str, Any]:
        """Simula a obtenção de dados de uma URL.

        Args:
            url: URL para obter dados

        Returns:
            Dados obtidos da URL
        """
        logger.info(f"Obtendo dados de {url}")
        await asyncio.sleep(1)  # Simular latência de rede
        return {
            "url": url,
            "title": f"Conteúdo de {url}",
            "items": [
                {"id": 1, "title": "Item 1", "content": "Conteúdo do item 1"},
                {"id": 2, "title": "Item 2", "content": "Conteúdo do item 2"},
                {"id": 3, "title": "Item 3", "content": "Conteúdo do item 3"},
            ],
        }

    async def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula o processamento de dados.

        Args:
            data: Dados a serem processados

        Returns:
            Dados processados
        """
        logger.info(f"Processando dados de {data['url']}")
        await asyncio.sleep(0.5)  # Simular processamento

        # Processar cada item
        processed_items = []
        for item in data["items"]:
            processed_item = item.copy()
            processed_item["processed"] = True
            processed_item["summary"] = (
                f"Resumo de {item['title']}: {item['content'][:30]}..."
            )
            processed_items.append(processed_item)

        result = data.copy()
        result["items"] = processed_items
        result["processed"] = True
        return result

    async def save_result(data: Dict[str, Any], path: Path) -> str:
        """Simula o salvamento de resultados.

        Args:
            data: Dados a serem salvos
            path: Caminho para salvar os dados

        Returns:
            Caminho do arquivo salvo
        """
        logger.info(f"Salvando resultado em {path}")

        # Criar conteúdo formatado
        content = f"# {data['title']}\n\n"
        content += f"URL: {data['url']}\n\n"
        content += "## Itens processados\n\n"

        for item in data["items"]:
            content += f"### {item['title']}\n"
            content += f"ID: {item['id']}\n"
            content += f"Resumo: {item['summary']}\n\n"

        # Salvar no arquivo
        with open(path, "w") as f:
            f.write(content)

        return str(path)

    # Criar tarefas para cada URL
    tasks = []
    for i, url in enumerate(urls):
        output_path = output_dir / f"processed_{i}.txt"

        # Criar pipeline de processamento
        async def process_pipeline(url=url, output_path=output_path):
            """Pipeline de processamento para uma URL.

            Args:
                url: URL para processar
                output_path: Caminho para salvar o resultado

            Returns:
                Caminho do arquivo salvo
            """
            data = await fetch_url(url)
            processed = await process_data(data)
            return await save_result(processed, output_path)

        tasks.append(process_pipeline())

    # Executar tarefas em paralelo
    results = await asyncio.gather(*tasks)

    # Combinar resultados
    combined_path = output_dir / "combined_results.txt"
    with open(combined_path, "w") as f:
        f.write("# Resultados Combinados\n\n")
        for i, result_path in enumerate(results):
            f.write(f"## Resultado {i + 1}: {urls[i]}\n")
            with open(result_path, "r") as result_file:
                f.write(result_file.read())
            f.write("\n---\n\n")

    logger.info(f"Resultados combinados salvos em {combined_path}")
    return results


async def process_parallel_tasks():
    """Demonstra o processamento paralelo usando tarefas assíncronas."""
    logger.info("Processando tarefas em paralelo")

    # Simular tarefas de processamento
    async def task1():
        logger.info("Iniciando tarefa 1")
        await asyncio.sleep(2)
        logger.info("Tarefa 1 concluída")
        return "Resultado da tarefa 1"

    async def task2():
        logger.info("Iniciando tarefa 2")
        await asyncio.sleep(1.5)
        logger.info("Tarefa 2 concluída")
        return "Resultado da tarefa 2"

    async def task3():
        logger.info("Iniciando tarefa 3")
        await asyncio.sleep(1)
        logger.info("Tarefa 3 concluída")
        return "Resultado da tarefa 3"

    # Executar tarefas em paralelo
    results = await asyncio.gather(task1(), task2(), task3())

    # Salvar resultados
    result_path = output_dir / "task_results.txt"
    with open(result_path, "w") as f:
        f.write("# Resultados das Tarefas\n\n")
        for i, result in enumerate(results):
            f.write(f"## Tarefa {i + 1}\n")
            f.write(f"{result}\n\n")

    logger.info(f"Resultados das tarefas salvos em {result_path}")
    return results


async def main():
    """Função principal."""
    logger.info("Iniciando exemplos de processamento paralelo")

    # Exemplo 1: Processamento paralelo usando funções personalizadas
    await process_parallel_custom()

    # Exemplo 2: Processamento paralelo usando tarefas assíncronas
    await process_parallel_tasks()

    logger.info("Exemplos concluídos")


if __name__ == "__main__":
    asyncio.run(main())
