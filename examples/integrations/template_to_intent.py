#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre os sistemas de templates e intenção.

Purpose:
    Demonstrar como o sistema de intenção pode utilizar o sistema de templates
    para implementar a funcionalidade associada a uma intenção reconhecida.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/template_to_intent.py
"""

import asyncio
import os
from typing import Any, Dict

from pepperpy.core.intent import (
    process_intent,
    recognize_intent,
    register_intent_handler,
)
from pepperpy.workflows.templates.public import execute_template


# Definir um manipulador de intenção que usa o sistema de templates
async def handle_podcast_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de criar um podcast.

    Este manipulador extrai parâmetros da intenção reconhecida e usa o sistema
    de templates para executar um template pré-configurado que gera um podcast
    de notícias.

    Args:
        intent_data: Dados da intenção reconhecida
            - source_url: URL da fonte de notícias
            - voice: Voz a ser usada (código de idioma)
            - max_items: Número máximo de itens
            - output_path: Caminho para salvar o resultado

    Returns:
        Resultado do processamento da intenção
    """
    # Mapear parâmetros da intenção para parâmetros do template
    template_params = {
        "source_url": intent_data.get("source_url", "https://news.google.com/rss"),
        "output_path": intent_data.get("output_path", "output/podcast.mp3"),
        "voice": intent_data.get("voice", "pt"),
        "max_articles": intent_data.get("max_items", 3),
        "summary_length": intent_data.get("max_length", 150),
    }

    # Criar diretório de saída se não existir
    os.makedirs(os.path.dirname(template_params["output_path"]), exist_ok=True)

    print(
        f"Processando intenção de criar podcast com fonte {template_params['source_url']}"
    )

    # Executar o template
    result = await execute_template("news_podcast", template_params)

    # Converter o resultado do template para o formato esperado pelo sistema de intenção
    return {
        "status": result.status,
        "output_path": result.result.get("output_path"),
        "message": f"Podcast gerado com sucesso em {result.result.get('output_path')}",
    }


async def setup():
    """Configuração inicial do exemplo."""
    # Registrar o manipulador de intenção
    register_intent_handler("create_podcast", handle_podcast_intent)
    print("Manipulador de intenção 'create_podcast' registrado")


async def demo_intent_to_template():
    """Demonstra o fluxo de intenção para template."""
    # Configurar o exemplo
    await setup()

    # Simular um comando do usuário
    user_command = "criar um podcast em inglês com as 5 principais notícias de https://example.com/news"
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
    print("=== Exemplo de Integração: Intenção → Template ===")
    print(
        "Este exemplo demonstra como o sistema de intenção utiliza o sistema de templates."
    )

    await demo_intent_to_template()

    print("\n=== Fluxo de Integração ===")
    print("1. O usuário fornece um comando em linguagem natural")
    print("2. O sistema de intenção reconhece a intenção e extrai parâmetros")
    print("3. O manipulador de intenção executa um template pré-configurado")
    print("4. O template implementa a funcionalidade usando componentes reutilizáveis")
    print("5. O resultado é retornado ao usuário")


if __name__ == "__main__":
    asyncio.run(main())
