#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de pipeline builder simplificado com PepperPy.

Purpose:
    Demonstrar como usar o pipeline builder simplificado do PepperPy
    para criar pipelines de processamento com o mínimo de código.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/composition/pipeline_builder_demo.py
"""

import asyncio

import pepperpy as pp
from pepperpy.apps import DataApp, TextApp


async def example_text_processing():
    """Exemplo de processamento de texto usando o pipeline builder simplificado."""
    print("\n=== Exemplo de Processamento de Texto ===")

    # Texto de entrada
    input_text = "  Este é um exemplo de processamento de texto com pipeline builder.  "
    print(f"Texto original: '{input_text}'")

    # Criar aplicação de processamento de texto com uma única linha
    text_app = TextApp(name="text_processor")

    # Método 1: Pipeline simples com configuração declarativa
    print("\nPipeline simples:")
    result1 = await text_app.process(
        text=input_text,
        operations=[
            {"name": "clean", "type": "strip"},
            {"name": "transform", "type": "uppercase"},
            {"name": "format", "type": "template", "template": "Resultado: {text}"},
        ],
    )
    print(f"Resultado: '{result1}'")

    # Método 2: Pipeline com bifurcação usando API fluente
    print("\nPipeline com bifurcação:")
    text_app.configure(
        pipeline=pp.TextPipeline()
        .add_step("clean", operation="strip")
        .add_step("transform", operation="uppercase")
        .add_branch(
            pp.TextBranch("format", template="Resultado: {text}"),
            pp.TextBranch(
                "analyze",
                operation="count_words",
                template="{text} (Contém {word_count} palavras)",
            ),
        )
    )

    result2 = await text_app.process_text(input_text)
    print(f"Resultado 1: '{result2.branches[0]}'")
    print(f"Resultado 2: '{result2.branches[1]}'")


async def example_data_processing():
    """Exemplo de processamento de dados usando o pipeline builder simplificado."""
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

    # Criar aplicação de processamento de dados com uma única linha
    data_app = DataApp(name="data_processor")

    # Método 1: Pipeline simples com configuração declarativa
    print("\nPipeline simples:")
    result1 = await data_app.process(
        data=input_data,
        steps=[
            {
                "name": "filter_items",
                "type": "filter",
                "condition": "item.price > 50",
                "target": "items",
            },
            {
                "name": "calculate_total",
                "type": "aggregate",
                "operation": "sum",
                "source": "items.price",
                "target": "total",
            },
            {
                "name": "calculate_average",
                "type": "aggregate",
                "operation": "average",
                "source": "items.price",
                "target": "average",
            },
            {
                "name": "format_report",
                "type": "template",
                "template_file": "report_template.txt",
                "output": "report",
            },
        ],
    )
    print(result1["report"])

    # Método 2: Pipeline com processamento paralelo usando API fluente
    print("\nPipeline com processamento paralelo:")
    data_app.configure(
        pipeline=pp.DataPipeline()
        .add_filter("expensive_items", condition="item.price > 50")
        .add_parallel(
            pp.DataBranch("expensive_analysis")
            .add_filter(condition="item.price > 100")
            .add_aggregate("count", target="count")
            .add_aggregate("sum", source="price", target="total"),
            pp.DataBranch("cheap_analysis")
            .add_filter(condition="item.price <= 100")
            .add_aggregate("count", target="count")
            .add_aggregate("sum", source="price", target="total"),
        )
    )

    result2 = await data_app.process_data(input_data)
    print(f"Análise de itens caros: {result2.parallels[0]}")
    print(f"Análise de itens baratos: {result2.parallels[1]}")


async def main():
    """Executa os exemplos de pipeline builder simplificado."""
    print("=== Demonstração de Pipeline Builder Simplificado do PepperPy ===")
    print(
        "Este exemplo demonstra como usar o pipeline builder simplificado do PepperPy"
    )
    print("para criar pipelines de processamento com o mínimo de código.")

    await example_text_processing()
    await example_data_processing()

    print("\n=== Demonstração Concluída ===")
    print(
        "Para mais informações sobre pipeline builder no PepperPy, consulte a documentação:"
    )
    print("https://docs.pepperpy.ai/concepts/pipeline-builder")


if __name__ == "__main__":
    asyncio.run(main())
