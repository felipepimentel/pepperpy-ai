#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de composição funcional simplificada com PepperPy.

Purpose:
    Demonstrar como usar a composição funcional simplificada do PepperPy
    para criar pipelines de processamento de forma elegante e concisa.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/composition/basic_composition_demo.py
"""

import asyncio

import pepperpy as pp


async def example_text_processing():
    """Exemplo de processamento de texto usando composição funcional simplificada."""
    print("\n=== Exemplo de Processamento de Texto ===")

    # Texto de entrada
    input_text = (
        "  Este é um exemplo de processamento de texto com composição funcional.  "
    )
    print(f"Texto original: '{input_text}'")

    # Definir processadores de texto de forma declarativa
    text_pipeline = pp.TextPipeline(
        steps=[
            pp.TextStep(name="remove_whitespace", operation="strip"),
            pp.TextStep(name="to_uppercase", operation="uppercase"),
            pp.TextStep(name="add_prefix", template="Resultado: {text}"),
        ]
    )

    # Processar texto com uma única linha
    result = await text_pipeline.process(input_text)
    print(f"Resultado: '{result}'")

    # Exemplo com bifurcação usando API fluente
    branched_pipeline = (
        pp.TextPipeline()
        .add_step(pp.TextStep(name="clean", operation="strip"))
        .add_step(pp.TextStep(name="uppercase", operation="uppercase"))
        .add_branch(
            pp.TextStep(name="add_prefix", template="Resultado: {text}"),
            pp.TextStep(
                name="count_words",
                operation="count_words",
                template="{text} (Contém {word_count} palavras)",
            ),
        )
    )

    # Processar texto com bifurcação
    result = await branched_pipeline.process(input_text)
    print(f"Resultado 1: '{result.branches[0]}'")
    print(f"Resultado 2: '{result.branches[1]}'")


async def example_data_processing():
    """Exemplo de processamento de dados usando composição funcional simplificada."""
    print("\n=== Exemplo de Processamento de Dados ===")

    # Dados de entrada
    input_data = {
        "customer": "João Silva",
        "items": [
            {"name": "Produto A", "price": 100},
            {"name": "Produto B", "price": 25},
            {"name": "Produto C", "price": 75},
            {"name": "Produto D", "price": 30},
            {"name": "Produto E", "price": 150},
        ],
    }
    print("Dados originais:")
    print(f"Cliente: {input_data['customer']}")
    print(f"Itens: {len(input_data['items'])} produtos")

    # Definir processadores de dados de forma declarativa
    data_pipeline = pp.DataPipeline(
        steps=[
            pp.DataStep(
                name="filter_items", filter_condition="item.price > 50", target="items"
            ),
            pp.DataStep(
                name="calculate_total",
                operation="sum",
                source="items.price",
                target="total",
            ),
            pp.DataStep(
                name="add_average",
                operation="average",
                source="items.price",
                target="average",
            ),
            pp.DataStep(
                name="format_as_text",
                template="""
                Relatório para {customer}
                Total de itens: {items.length}
                Valor total: R${total:.2f}
                Valor médio: R${average:.2f}
                
                Itens:
                {#each items}
                - {name}: R${price:.2f}
                {/each}
                """,
            ),
        ]
    )

    # Processar dados com uma única linha
    result = await data_pipeline.process(input_data)
    print(result)

    # Exemplo com processamento paralelo usando API fluente
    parallel_pipeline = (
        pp.DataPipeline()
        .add_step(
            pp.DataStep(
                name="filter_items", filter_condition="item.price > 50", target="items"
            )
        )
        .add_parallel(
            pp.DataStep(
                name="analyze_expensive",
                filter_condition="item.price > 100",
                target="expensive_items",
                aggregations=[
                    {"operation": "count", "target": "expensive_count"},
                    {
                        "operation": "sum",
                        "source": "price",
                        "target": "expensive_total",
                    },
                ],
            ),
            pp.DataStep(
                name="analyze_cheap",
                filter_condition="item.price <= 100",
                target="cheap_items",
                aggregations=[
                    {"operation": "count", "target": "cheap_count"},
                    {"operation": "sum", "source": "price", "target": "cheap_total"},
                ],
            ),
        )
    )

    # Processar dados com processamento paralelo
    result = await parallel_pipeline.process(input_data)
    print(f"Análise de itens caros: {result.parallels[0]}")
    print(f"Análise de itens baratos: {result.parallels[1]}")


async def main():
    """Executa os exemplos de composição funcional simplificada."""
    print("=== Demonstração de Composição Funcional Simplificada com PepperPy ===")
    print("Este exemplo demonstra como usar a composição funcional simplificada")
    print("para criar pipelines de processamento com o mínimo de código.")

    await example_text_processing()
    await example_data_processing()

    print("\n=== Demonstração Concluída ===")
    print(
        "Para mais informações sobre composição funcional no PepperPy, consulte a documentação:"
    )
    print("https://docs.pepperpy.ai/concepts/functional-composition")


if __name__ == "__main__":
    asyncio.run(main())
