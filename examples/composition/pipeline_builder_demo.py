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
import os
from typing import Any, Dict


class PipelineBuilder:
    """Construtor de pipelines para demonstração."""

    @staticmethod
    async def build_text_pipeline(text: str) -> str:
        """Constrói e executa um pipeline de processamento de texto.

        Args:
            text: Texto a ser processado

        Returns:
            Texto processado
        """
        # Processar texto
        text = text.strip()
        text = text.upper()
        text = f"Resultado: {text}"

        return text

    @staticmethod
    async def build_data_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói e executa um pipeline de processamento de dados.

        Args:
            data: Dados a serem processados

        Returns:
            Dados processados
        """
        # Processar dados
        items = data.get("items", [])

        # Filtrar itens
        filtered_items = [item for item in items if item.get("value", 0) > 50]

        # Calcular total
        total = sum(item.get("value", 0) for item in filtered_items)

        # Calcular média
        average = total / len(filtered_items) if filtered_items else 0

        return {
            "filtered_items": filtered_items,
            "total": total,
            "average": average,
            "count": len(filtered_items),
        }

    @staticmethod
    async def build_file_pipeline(input_text: str, output_path: str) -> str:
        """Constrói e executa um pipeline de processamento de arquivo.

        Args:
            input_text: Texto a ser processado
            output_path: Caminho do arquivo de saída

        Returns:
            Caminho do arquivo de saída
        """
        # Processar texto
        processed_text = input_text.upper()

        # Criar diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Salvar em arquivo
        with open(output_path, "w") as f:
            f.write(processed_text)

        return output_path


async def example_text_processing():
    """Exemplo de processamento de texto usando o pipeline builder simplificado."""
    print("\n=== Exemplo de Processamento de Texto ===")

    # Texto de entrada
    input_text = "  Este é um exemplo de processamento de texto com pipeline builder.  "
    print(f"Texto original: '{input_text}'")

    # Criar pipeline builder
    builder = PipelineBuilder()

    # Processar texto
    result = await builder.build_text_pipeline(input_text)
    print(f"Resultado: '{result}'")


async def example_data_processing():
    """Exemplo de processamento de dados usando o pipeline builder simplificado."""
    print("\n=== Exemplo de Processamento de Dados ===")

    # Dados de entrada
    input_data = {
        "customer": "João Silva",
        "items": [
            {"name": "Produto A", "value": 100},
            {"name": "Produto B", "value": 25},
            {"name": "Produto C", "value": 75},
            {"name": "Produto D", "value": 30},
            {"name": "Produto E", "value": 150},
        ],
    }
    print(f"Dados originais: {input_data}")

    # Criar pipeline builder
    builder = PipelineBuilder()

    # Processar dados
    result = await builder.build_data_pipeline(input_data)
    print(f"Resultado: {result}")


async def example_file_processing():
    """Exemplo de processamento de arquivo usando o pipeline builder simplificado."""
    print("\n=== Exemplo de Processamento de Arquivo ===")

    # Texto de entrada
    input_text = "Este é um exemplo de processamento de arquivo com pipeline builder."
    print(f"Texto original: '{input_text}'")

    # Criar diretório de saída
    output_dir = "examples/outputs/composition"
    os.makedirs(output_dir, exist_ok=True)

    # Arquivo de saída
    output_path = os.path.join(output_dir, "pipeline_builder_output.txt")

    # Criar pipeline builder
    builder = PipelineBuilder()

    # Processar arquivo
    result_path = await builder.build_file_pipeline(input_text, output_path)
    print(f"Arquivo gerado: {result_path}")

    # Verificar conteúdo do arquivo
    with open(result_path, "r") as f:
        content = f.read()

    print(f"Conteúdo do arquivo: '{content}'")


async def main():
    """Função principal."""
    print("=== Demonstração de Pipeline Builder Simplificado com PepperPy ===")
    print("Este exemplo demonstra como usar o pipeline builder simplificado")
    print("para criar pipelines de processamento com o mínimo de código.")

    # Executar exemplos
    await example_text_processing()
    await example_data_processing()
    await example_file_processing()

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
