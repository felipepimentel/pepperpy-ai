#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assistente virtual usando PepperPy.

Purpose:
    Demonstrar como criar um assistente virtual que pode processar comandos,
    responder perguntas e gerenciar contexto de conversação, utilizando o
    framework PepperPy para orquestrar o fluxo de trabalho.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/assistants/virtual_assistant_example.py
"""

import asyncio
import os
from datetime import datetime

from pepperpy.core.assistant.implementations import ResearchAssistant

# Configuração do assistente
RESEARCH_TOPICS = [
    {
        "topic": "Robótica e Automação Industrial",
        "depth": "basic",
        "max_sources": 3,
    },
    {
        "topic": "Neurociência e Interfaces Cérebro-Computador",
        "depth": "medium",
        "max_sources": 3,
    },
    {
        "topic": "Nanotecnologia e Materiais Avançados",
        "depth": "comprehensive",
        "max_sources": 2,
    },
]

# Diretório para salvar os resultados
OUTPUT_DIR = "examples/outputs/research"


async def perform_research(
    assistant: ResearchAssistant, topic: str, depth: str, max_sources: int
) -> str:
    """Realiza pesquisa sobre um tópico.

    Args:
        assistant: Assistente de pesquisa
        topic: Tópico a ser pesquisado
        depth: Profundidade da pesquisa (basic, medium, comprehensive)
        max_sources: Número máximo de fontes

    Returns:
        Caminho do arquivo de saída
    """
    print(f"\n=== Realizando pesquisa: {topic} (Profundidade: {depth}) ===")

    # Criar nome de arquivo baseado no tópico
    safe_topic = (
        topic.lower()
        .replace(" ", "_")
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("é", "e")
    )
    output_file = f"{safe_topic}_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path = os.path.join(OUTPUT_DIR, output_file)

    # Garantir que o diretório de saída existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Configurar parâmetros da pesquisa
    research_params = {
        "topic": topic,
        "depth": depth,
        "output_format": "markdown",
        "include_citations": True,
        "max_sources": max_sources,
        "verify_facts": True,
    }

    # Realizar pesquisa
    result = await assistant.process_message(f"Pesquise sobre {topic}")

    # Salvar resultado
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.get("content", "Sem conteúdo disponível"))

    print(f"Pesquisa concluída. Relatório salvo em: {output_path}")
    return output_path


async def main():
    """Função principal."""
    print("=== Assistente Virtual PepperPy ===")
    print("Este exemplo demonstra como usar o assistente virtual do PepperPy.")

    # Criar assistente de pesquisa
    assistant = ResearchAssistant(
        name="virtual_assistant",
        config={
            "depth": "medium",
            "output_format": "markdown",
            "include_citations": True,
            "max_sources": 3,
            "verify_facts": True,
        },
        sources=["https://example.com/source1", "https://example.com/source2"],
    )

    # Inicializar assistente
    await assistant.initialize()

    try:
        # Realizar pesquisas sobre diferentes tópicos
        for i, research_config in enumerate(RESEARCH_TOPICS, 1):
            topic = research_config["topic"]
            depth = research_config["depth"]
            max_sources = research_config["max_sources"]

            output_file = f"{topic.lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a').replace('é', 'e')}_research_{i}.md"
            output_path = os.path.join(OUTPUT_DIR, output_file)

            # Garantir que o diretório de saída existe
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            print(f"\n=== Pesquisa {i}: {topic} (Profundidade: {depth}) ===")

            # Realizar pesquisa
            await perform_research(assistant, topic, depth, max_sources)

    finally:
        # Limpar recursos
        await assistant.cleanup()

    print("\n=== Demonstração concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
