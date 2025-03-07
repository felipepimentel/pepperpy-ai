#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assistente de pesquisa usando PepperPy.

Purpose:
    Demonstrar como criar um assistente de pesquisa que pode buscar informações,
    analisar documentos e gerar relatórios usando o framework PepperPy.

Requirements:
    - Python 3.9+
    - PepperPy library
    - Internet connection

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Set environment variables (optional):
       export PEPPERPY_API_KEY="your_api_key"

    3. Run the example:
       python examples/assistants/research_assistant.py
"""

import asyncio
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.assistant.implementations import ResearchAssistant

# Definir pasta de saída para os artefatos gerados
OUTPUT_DIR = Path("examples/outputs/research")

# Garantir que a pasta de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_fake_topic() -> str:
    """Gera um tópico de pesquisa fake.

    Returns:
        Tópico de pesquisa
    """
    topics = [
        "Inteligência Artificial e Ética",
        "Mudanças Climáticas e Biodiversidade",
        "Economia Circular e Consumo Sustentável",
        "Neurociência e Interfaces Cérebro-Computador",
        "Segurança Cibernética e Privacidade de Dados",
        "Energias Renováveis e Sustentabilidade",
        "Cidades Inteligentes e Urbanismo",
        "Medicina Personalizada e Genômica",
        "Exploração Espacial e Colonização de Marte",
        "Blockchain e Criptomoedas",
        "Realidade Virtual e Aumentada",
        "Robótica e Automação Industrial",
        "Biotecnologia e Edição Genética",
        "Nanotecnologia e Materiais Avançados",
        "Avanços em Medicina Personalizada",
    ]
    return random.choice(topics)


def generate_fake_sources() -> List[str]:
    """Gera uma lista de fontes fake.

    Returns:
        Lista de fontes
    """
    sources = [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3",
        "https://example.com/article4",
        "https://example.com/article5",
        "https://example.com/article6",
        "https://example.com/article7",
        "https://example.com/article8",
        "https://example.com/article9",
        "https://example.com/article10",
    ]
    num_sources = random.randint(2, 5)
    return random.sample(sources, num_sources)


async def run_research_assistant(
    topic: str,
    depth: str = "medium",
    sources: Optional[List[str]] = None,
    output_format: str = "markdown",
    output_path: Optional[str] = None,
    include_citations: bool = True,
) -> Dict[str, Any]:
    """Executa uma pesquisa sobre um tópico.

    Args:
        topic: Tópico a ser pesquisado
        depth: Profundidade da pesquisa (basic, medium, comprehensive)
        sources: Lista de fontes a serem consultadas (URLs, arquivos)
        output_format: Formato do relatório (markdown, html, text)
        output_path: Caminho para salvar o relatório
        include_citations: Incluir citações no relatório

    Returns:
        Resultado da pesquisa com relatório e metadados
    """
    # Criar assistente de pesquisa
    assistant = ResearchAssistant(
        name="research_assistant",
        config={
            "depth": depth,
            "output_format": output_format,
            "include_citations": include_citations,
            "max_sources": 10,
            "verify_facts": True,
        },
    )

    # Inicializar o assistente
    await assistant.initialize()

    # Adicionar fontes se especificadas
    if sources:
        for source in sources:
            assistant.add_source(source)

    # Se um caminho de saída foi especificado, configurar
    if output_path:
        # Garantir que o caminho é relativo à pasta de saída
        full_output_path = OUTPUT_DIR / output_path
        assistant.set_output_path(str(full_output_path))

    # Executar pesquisa com uma única chamada
    result = await assistant.research(topic)

    return result


async def main():
    """Executa o exemplo de assistente de pesquisa."""
    print("=== Assistente de Pesquisa com PepperPy ===")
    print("Este exemplo demonstra como criar um assistente de pesquisa")
    print("que pode buscar informações e gerar relatórios.")

    # Definir configurações para diferentes pesquisas
    configurations = [
        {
            "name": "Pesquisa Básica",
            "config": {
                "depth": "basic",
                "output_format": "markdown",
                "include_citations": True,
            },
        },
        {
            "name": "Pesquisa Média",
            "config": {
                "depth": "medium",
                "output_format": "markdown",
                "include_citations": True,
            },
        },
        {
            "name": "Pesquisa Abrangente",
            "config": {
                "depth": "comprehensive",
                "output_format": "markdown",
                "include_citations": True,
            },
        },
    ]

    # Executar pesquisas com diferentes configurações
    for i, config_item in enumerate(configurations):
        # Gerar tópico e fontes fake
        topic = generate_fake_topic()
        sources = generate_fake_sources()

        # Obter configuração
        config_name = config_item["name"]
        config = config_item["config"]

        print(f"\n--- Executando {config_name} ---")
        print(f"Tópico: {topic}")
        print(f"Fontes: {len(sources)}")
        print(f"Configuração: {config}")

        # Gerar nome de arquivo para o relatório
        output_path = f"{topic.lower().replace(' ', '_')}_research_{i + 1}.md"

        # Executar pesquisa
        result = await run_research_assistant(
            topic=topic, sources=sources, output_path=output_path, **config
        )

        print("\nPesquisa concluída com sucesso!")
        print(f"Relatório salvo em: {result['output_path']}")
        print(f"Fontes consultadas: {len(result['sources'])}")
        print(f"Tempo de pesquisa: {result['research_time']:.2f} segundos")

        # Mostrar primeiras linhas do relatório
        if os.path.exists(result["output_path"]):
            print("\nPrimeiras linhas do relatório:")
            print("-" * 50)
            with open(result["output_path"], "r") as f:
                lines = f.readlines()
                print("".join(lines[:15]))
                print("..." if len(lines) > 15 else "")
            print("-" * 50)

        # Pausa entre pesquisas
        if i < len(configurations) - 1:
            await asyncio.sleep(1)

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
