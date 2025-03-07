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
from typing import Any, Dict, List, Optional

from pepperpy.assistants import ResearchAssistant


def generate_fake_topic() -> str:
    """Gera um tópico fake para pesquisa.

    Returns:
        Tópico fake
    """
    topics = [
        "Impacto da Inteligência Artificial na Educação",
        "Energias Renováveis e Sustentabilidade",
        "Avanços em Medicina Personalizada",
        "Cidades Inteligentes e Urbanismo",
        "Blockchain e Transformação Digital",
        "Mudanças Climáticas e Biodiversidade",
        "Exploração Espacial e Colonização de Marte",
        "Neurociência e Interfaces Cérebro-Computador",
        "Segurança Cibernética e Privacidade de Dados",
        "Economia Circular e Consumo Sustentável",
    ]

    return random.choice(topics)


def generate_fake_sources() -> List[str]:
    """Gera fontes fake para pesquisa.

    Returns:
        Lista de fontes fake
    """
    sources = [
        "https://www.nature.com/articles/s41586-021-03380-x",
        "https://www.science.org/doi/10.1126/science.abc1234",
        "https://www.researchgate.net/publication/123456789",
        "https://arxiv.org/abs/2104.12345",
        "https://www.cell.com/cell/fulltext/S0092-8674(21)00123-4",
        "https://www.nejm.org/doi/full/10.1056/NEJMoa2034577",
        "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)00123-4",
        "https://www.pnas.org/content/118/21/e2026322118",
        "https://www.sciencedirect.com/science/article/pii/S0012345678901234",
        "https://onlinelibrary.wiley.com/doi/abs/10.1002/adma.202100123",
    ]

    # Selecionar um número aleatório de fontes (2-5)
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
    # Criar assistente de pesquisa com uma única linha
    assistant = ResearchAssistant()

    # Configurar o assistente com uma API fluente
    assistant.configure(
        depth=depth,
        output_format=output_format,
        include_citations=include_citations,
        max_sources=10,
        verify_facts=True,
    )

    # Adicionar fontes se especificadas
    if sources:
        for source in sources:
            assistant.add_source(source)

    # Se um caminho de saída foi especificado, configurar
    if output_path:
        assistant.set_output_path(output_path)

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
            with open(result["output_path"], "r") as f:
                content = f.read(500)  # Ler primeiros 500 caracteres
            print("\nPrimeiras linhas do relatório:")
            print("-" * 50)
            print(content + "...")
            print("-" * 50)

        # Pausa entre pesquisas
        if i < len(configurations) - 1:
            await asyncio.sleep(1)

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
