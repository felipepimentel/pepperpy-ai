#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre os sistemas de intenção e composição.

Purpose:
    Demonstrar como o sistema de intenção pode utilizar o sistema de composição
    para implementar a funcionalidade associada a uma intenção reconhecida.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/intent_to_composition.py
"""

import asyncio
import os
from typing import Any, Dict

from pepperpy.core.composition import Outputs, Processors, Sources, compose
from pepperpy.core.intent import (
    process_intent,
    recognize_intent,
    register_intent_handler,
)


# Definir um manipulador de intenção que usa o sistema de composição
async def handle_summarize_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de resumir conteúdo.

    Este manipulador extrai parâmetros da intenção reconhecida e usa o sistema
    de composição para criar um pipeline que busca o conteúdo, o resume e salva
    o resultado em um arquivo.

    Args:
        intent_data: Dados da intenção reconhecida
            - source_url: URL da fonte de conteúdo
            - max_length: Tamanho máximo do resumo
            - output_path: Caminho para salvar o resultado

    Returns:
        Resultado do processamento da intenção
    """
    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url", "https://example.com")
    max_length = intent_data.get("max_length", 150)
    output_path = intent_data.get("output_path", "output/summary.txt")

    # Criar diretório de saída se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Processando intenção de resumir conteúdo de {source_url}")

    # Criar pipeline de composição
    pipeline = (
        compose("summarization_pipeline")
        .source(Sources.web(source_url))
        .process(Processors.summarize(max_length=max_length))
        .output(Outputs.file(output_path))
    )

    # Executar o pipeline
    result = await pipeline.execute()

    return {
        "status": "success",
        "output_path": result,
        "message": f"Resumo gerado com sucesso em {result}",
    }


async def setup():
    """Configuração inicial do exemplo."""
    # Registrar o manipulador de intenção
    register_intent_handler("summarize", handle_summarize_intent)
    print("Manipulador de intenção 'summarize' registrado")


async def demo_intent_to_composition():
    """Demonstra o fluxo de intenção para composição."""
    # Configurar o exemplo
    await setup()

    # Simular um comando do usuário
    user_command = "resumir o artigo em https://example.com/article em 200 palavras"
    print(f"\nComando do usuário: '{user_command}'")

    # Reconhecer a intenção
    print("Reconhecendo intenção...")
    intent = await recognize_intent(user_command)
    print(f"Intenção reconhecida: {intent['intent']}")
    print(f"Parâmetros: {intent['parameters']}")

    # Processar a intenção
    print("\nProcessando intenção...")
    result = await process_intent(intent)

    # Exibir resultado
    print("\nResultado do processamento:")
    print(f"Status: {result['status']}")
    print(f"Mensagem: {result['message']}")
    print(f"Arquivo de saída: {result['output_path']}")


async def main():
    """Função principal."""
    print("=== Exemplo de Integração: Intenção → Composição ===")
    print(
        "Este exemplo demonstra como o sistema de intenção utiliza o sistema de composição."
    )

    await demo_intent_to_composition()

    print("\n=== Fluxo de Integração ===")
    print("1. O usuário fornece um comando em linguagem natural")
    print("2. O sistema de intenção reconhece a intenção e extrai parâmetros")
    print(
        "3. O manipulador de intenção cria um pipeline usando o sistema de composição"
    )
    print("4. O pipeline é executado para implementar a funcionalidade")
    print("5. O resultado é retornado ao usuário")


if __name__ == "__main__":
    asyncio.run(main())
