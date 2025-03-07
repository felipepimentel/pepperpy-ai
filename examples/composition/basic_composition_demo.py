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
import os
from typing import Any, Dict, List


class TextProcessor:
    """Processador de texto simples para demonstração."""

    @staticmethod
    async def process_text(text: str) -> str:
        """Processa um texto.

        Args:
            text: Texto a ser processado

        Returns:
            Texto processado
        """
        # Remover espaços em branco
        text = text.strip()

        # Converter para maiúsculas
        text = text.upper()

        # Adicionar prefixo
        text = f"Resultado: {text}"

        return text


class DataProcessor:
    """Processador de dados simples para demonstração."""

    @staticmethod
    async def filter_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra itens com valor maior que 15.

        Args:
            items: Lista de itens

        Returns:
            Lista filtrada
        """
        return [item for item in items if item["value"] > 15]

    @staticmethod
    async def double_values(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Duplica os valores dos itens.

        Args:
            items: Lista de itens

        Returns:
            Lista com valores duplicados
        """
        return [{**item, "value_doubled": item["value"] * 2} for item in items]


async def example_text_processing():
    """Exemplo de processamento de texto."""
    print("\n=== Exemplo de Processamento de Texto ===")

    # Texto de entrada
    input_text = (
        "  Este é um exemplo de processamento de texto com composição funcional.  "
    )
    print(f"Texto original: '{input_text}'")

    # Processar texto
    processor = TextProcessor()
    result = await processor.process_text(input_text)

    # Exibir resultado
    print(f"Resultado: '{result}'")

    # Exemplo com bifurcação
    print("\n=== Exemplo com Bifurcação ===")

    # Texto de entrada
    input_text = "Este texto será processado de duas formas diferentes."
    print(f"Texto original: '{input_text}'")

    # Processar texto de duas formas
    uppercase = input_text.upper()
    lowercase = input_text.lower()

    # Exibir resultados
    print(f"Versão maiúscula: '{uppercase}'")
    print(f"Versão minúscula: '{lowercase}'")


async def example_data_processing():
    """Exemplo de processamento de dados."""
    print("\n=== Exemplo de Processamento de Dados ===")

    # Dados de entrada
    input_data = {
        "items": [
            {"id": 1, "name": "Item 1", "value": 10},
            {"id": 2, "name": "Item 2", "value": 20},
            {"id": 3, "name": "Item 3", "value": 30},
        ]
    }
    print(f"Dados originais: {input_data}")

    # Processar dados
    processor = DataProcessor()
    filtered_items = await processor.filter_items(input_data["items"])
    processed_items = await processor.double_values(filtered_items)

    # Exibir resultado
    print(f"Dados processados: {{'items': {processed_items}}}")


async def example_file_processing():
    """Exemplo de processamento de arquivos."""
    print("\n=== Exemplo de Processamento de Arquivos ===")

    # Criar diretório de saída
    output_dir = "examples/outputs/composition"
    os.makedirs(output_dir, exist_ok=True)

    # Arquivo de saída
    output_file = os.path.join(output_dir, "processed_text.txt")

    # Texto de entrada
    input_text = "Este texto será salvo em um arquivo após processamento."
    print(f"Texto original: '{input_text}'")

    # Processar texto
    processed_text = input_text.upper()

    # Salvar em arquivo
    with open(output_file, "w") as f:
        f.write(processed_text)

    print(f"Texto processado salvo em: {output_file}")

    # Verificar conteúdo do arquivo
    with open(output_file, "r") as f:
        content = f.read()

    print(f"Conteúdo do arquivo: '{content}'")


async def main():
    """Função principal."""
    print("=== Demonstração de Composição Funcional Simplificada com PepperPy ===")
    print("Este exemplo demonstra como usar a composição funcional simplificada")
    print("para criar pipelines de processamento com o mínimo de código.")

    # Executar exemplos
    await example_text_processing()
    await example_data_processing()
    await example_file_processing()

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
