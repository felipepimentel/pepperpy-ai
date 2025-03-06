#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre o sistema de templates e o sistema de intenção.

Este exemplo demonstra como o sistema de templates pode ser usado para
implementar manipuladores de intenção, permitindo que comandos em linguagem
natural sejam convertidos em execuções de templates.
"""

import asyncio
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

    Args:
        intent_data: Dados da intenção, incluindo parâmetros.

    Returns:
        Resultado da execução do template.
    """
    print(f"Processando intenção de podcast com parâmetros: {intent_data}")

    # Mapear parâmetros da intenção para parâmetros do template
    template_params = {
        "source_url": intent_data.get("source_url"),
        "output_path": intent_data.get("output_path", "example_output/podcast.mp3"),
        "voice": intent_data.get("voice", "pt"),
        "max_articles": intent_data.get("max_items", 3),
        "summary_length": intent_data.get("max_length", 150),
    }

    # Executar o template
    result = await execute_template("news_podcast", template_params)

    return {
        "status": result.status,
        "output_path": result.result.get("output_path"),
        "message": f"Podcast gerado com sucesso em {result.result.get('output_path')}",
    }


async def main():
    """Função principal."""
    print("Demonstração de Integração: Sistema de Templates → Sistema de Intenção")
    print("--------------------------------------------------------------------")

    # Registrar o manipulador de intenção
    register_intent_handler("create_podcast", handle_podcast_intent)

    # Exemplos de comandos do usuário
    user_commands = [
        "Criar um podcast com as notícias de https://news.example.com",
        "Gerar um podcast em inglês sobre tecnologia de https://tech.example.com",
        "Fazer um podcast com as 5 principais notícias de https://daily.example.com",
    ]

    for command in user_commands:
        print(f"\nProcessando comando: '{command}'")

        # Reconhecer a intenção do usuário
        intent = await recognize_intent(command)
        print(f"Intenção reconhecida: {intent['intent']}")
        print(f"Parâmetros: {intent['parameters']}")

        # Processar a intenção (isso chamará o manipulador registrado)
        if intent["intent"] == "create_podcast":
            result = await process_intent(intent)
            print(f"Resultado: {result}")
        else:
            print(f"Intenção '{intent['intent']}' não suportada neste exemplo")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
