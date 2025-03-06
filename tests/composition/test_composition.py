#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de teste para verificar o funcionamento básico do módulo de composição."""

import asyncio
import os
import sys

# Adicionar o diretório raiz ao path para importar o módulo pepperpy
sys.path.insert(0, os.path.abspath("."))

# Importar diretamente os módulos necessários
from pepperpy.core.composition.components import Outputs, Processors, Sources
from pepperpy.core.composition.public import compose, compose_parallel


async def test_basic_composition():
    """Testa a composição básica."""
    print("\n=== Teste de Composição Básica ===")

    # Criar uma fonte de texto simples
    text_source = Sources.text("Este é um texto de exemplo para testar a composição.")
    print(f"Fonte criada: {text_source}")

    # Criar um processador de texto
    text_processor = Processors.summarize(max_length=50)
    print(f"Processador criado: {text_processor}")

    # Criar uma saída de console
    console_output = Outputs.file("output.txt")
    print(f"Saída criada: {console_output}")

    # Criar um pipeline
    pipeline = (
        compose("pipeline_teste")
        .source(text_source)
        .process(text_processor)
        .output(console_output)
    )
    print(f"Pipeline criado: {pipeline}")

    # Executar o pipeline
    try:
        print("\nExecutando o pipeline...")
        result = await pipeline.execute()
        print(f"Resultado: {result}")
        print("Pipeline executado com sucesso!")
    except Exception as e:
        print(f"Erro ao executar o pipeline: {e}")


async def test_parallel_composition():
    """Testa a composição paralela."""
    print("\n=== Teste de Composição Paralela ===")

    # Criar uma fonte de texto simples
    text_source = Sources.text(
        "Este é um texto de exemplo para testar a composição paralela."
    )
    print(f"Fonte criada: {text_source}")

    # Criar processadores
    summarize_processor = Processors.summarize(max_length=30)
    keywords_processor = Processors.extract_keywords(max_keywords=3)
    print(f"Processadores criados: {summarize_processor}, {keywords_processor}")

    # Criar uma saída de console
    console_output = Outputs.file("output_parallel.txt")
    print(f"Saída criada: {console_output}")

    # Criar um pipeline paralelo
    pipeline = (
        compose_parallel("pipeline_paralelo_teste")
        .source(text_source)
        .process(summarize_processor)
        .process(keywords_processor)
        .output(console_output)
    )
    print(f"Pipeline paralelo criado: {pipeline}")

    # Executar o pipeline
    try:
        print("\nExecutando o pipeline paralelo...")
        result = await pipeline.execute()
        print(f"Resultado: {result}")
        print("Pipeline paralelo executado com sucesso!")
    except Exception as e:
        print(f"Erro ao executar o pipeline paralelo: {e}")


async def main():
    """Função principal."""
    print("=== Teste do Módulo de Composição ===")

    # Testar composição básica
    await test_basic_composition()

    # Testar composição paralela
    await test_parallel_composition()


if __name__ == "__main__":
    asyncio.run(main())
