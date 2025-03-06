#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de composição funcional.

Purpose:
    Demonstrar o conceito de composição funcional,
    mostrando como compor funções em pipelines de processamento.

Requirements:
    - Python 3.9+

Usage:
    1. Run the example:
       python examples/composition/composition_demo.py
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def compose(f: Callable[[T], U], g: Callable[[U], V]) -> Callable[[T], V]:
    """Compõe duas funções.

    Args:
        f: Primeira função a ser aplicada
        g: Segunda função a ser aplicada

    Returns:
        Função composta que aplica f e depois g
    """
    return lambda x: g(f(x))


def pipe(*functions: Callable) -> Callable:
    """Cria um pipeline de funções.

    Args:
        *functions: Funções a serem compostas

    Returns:
        Função composta que aplica todas as funções em sequência
    """

    def inner(x):
        result = x
        for f in functions:
            result = f(result)
        return result

    return inner


async def example_text_processing():
    """Demonstra o processamento de texto usando composição funcional."""
    print("\n=== Processamento de Texto ===")

    # Definir funções de processamento
    def remove_whitespace(text: str) -> str:
        return " ".join(text.split())

    def to_uppercase(text: str) -> str:
        return text.upper()

    def add_prefix(text: str) -> str:
        return f"PROCESSADO: {text}"

    def count_words(text: str) -> str:
        return f"{text} (Palavras: {len(text.split())})"

    # Definir texto de entrada
    input_text = """
    O conceito de composição funcional
    permite combinar    funções simples
    para criar    pipelines de processamento
    mais complexos.
    """

    # Criar pipeline usando compose
    pipeline1 = compose(remove_whitespace, to_uppercase)
    result1 = pipeline1(input_text)

    # Criar pipeline usando pipe
    pipeline2 = pipe(
        remove_whitespace,
        to_uppercase,
        add_prefix,
        count_words
    )
    result2 = pipeline2(input_text)

    # Mostrar resultados
    print("Texto original:")
    print("-" * 50)
    print(input_text)
    print("-" * 50)

    print("\nResultado do pipeline 1 (remove_whitespace + to_uppercase):")
    print("-" * 50)
    print(result1)
    print("-" * 50)

    print("\nResultado do pipeline 2 (remove_whitespace + to_uppercase + add_prefix + count_words):")
    print("-" * 50)
    print(result2)
    print("-" * 50)

    # Salvar resultados
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "pipeline1_result.txt", "w") as f:
        f.write(result1)

    with open(output_dir / "pipeline2_result.txt", "w") as f:
        f.write(result2)

    print(f"\nResultados salvos em {output_dir}")

    return result2


async def example_data_processing():
    """Demonstra o processamento de dados usando composição funcional."""
    print("\n=== Processamento de Dados ===")

    # Definir funções de processamento
    def filter_items(data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra itens com valor maior que 15."""
        filtered_data = data.copy()
        filtered_data["items"] = [item for item in data["items"] if item["value"] > 15]
        filtered_data["metadata"]["filtered"] = True
        filtered_data["metadata"]["original_count"] = len(data["items"])
        filtered_data["metadata"]["filtered_count"] = len(filtered_data["items"])
        return filtered_data

    def calculate_total(data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula o valor total dos itens."""
        result = data.copy()
        result["metadata"]["total_value"] = sum(item["value"] for item in data["items"])
        return result

    def add_average(data: Dict[str, Any]) -> Dict[str, Any]:
        """Adiciona o valor médio dos itens."""
        result = data.copy()
        items = data["items"]
        if items:
            result["metadata"]["average_value"] = result["metadata"]["total_value"] / len(items)
        else:
            result["metadata"]["average_value"] = 0
        return result

    def format_as_text(data: Dict[str, Any]) -> str:
        """Formata os dados como texto."""
        result = f"# {data['title']}\n\n"
        result += f"Fonte: {data['metadata']['source']}\n"
        result += f"Timestamp: {data['metadata']['timestamp']}\n\n"

        if "filtered" in data["metadata"]:
            result += f"Itens filtrados: {data['metadata']['original_count']} -> {data['metadata']['filtered_count']}\n"

        if "total_value" in data["metadata"]:
            result += f"Valor total: {data['metadata']['total_value']}\n"

        if "average_value" in data["metadata"]:
            result += f"Valor médio: {data['metadata']['average_value']:.2f}\n"

        result += "\n## Itens\n\n"
        for item in data["items"]:
            result += f"- {item['name']}: {item['value']}\n"

        return result

    # Definir dados de entrada
    input_data = {
        "title": "Exemplo de Dados",
        "items": [
            {"id": 1, "name": "Item 1", "value": 10},
            {"id": 2, "name": "Item 2", "value": 20},
            {"id": 3, "name": "Item 3", "value": 30},
        ],
        "metadata": {
            "source": "composition_demo.py",
            "timestamp": "2023-01-01T12:00:00Z",
        },
    }

    # Criar pipeline
    pipeline = pipe(
        filter_items,
        calculate_total,
        add_average,
        format_as_text
    )

    # Executar pipeline
    result = pipeline(input_data)

    # Mostrar resultado
    print("Dados originais:")
    print("-" * 50)
    print(input_data)
    print("-" * 50)

    print("\nResultado do pipeline:")
    print("-" * 50)
    print(result)
    print("-" * 50)

    # Salvar resultado
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "data_processing_result.txt", "w") as f:
        f.write(result)

    print(f"\nResultado salvo em {output_dir / 'data_processing_result.txt'}")

    return result


async def main():
    """Função principal."""
    print("=== Exemplo de Composição Funcional ===")
    print("Este exemplo demonstra o conceito de composição funcional.")

    # Executar exemplos
    await example_text_processing()
    await example_data_processing()

    print("\n=== Conceitos Demonstrados ===")
    print("1. Composição de funções (compose)")
    print("2. Criação de pipelines funcionais (pipe)")
    print("3. Processamento de texto usando composição")
    print("4. Processamento de dados usando composição")


if __name__ == "__main__":
    asyncio.run(main())
