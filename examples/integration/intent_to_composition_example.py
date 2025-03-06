#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre o sistema de intenção e o sistema de composição.

Este exemplo demonstra como o sistema de intenção pode ser usado para
reconhecer a intenção do usuário e convertê-la em um pipeline de composição.
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

    Args:
        intent_data: Dados da intenção, incluindo parâmetros.

    Returns:
        Resultado da execução do pipeline.
    """
    print(f"Processando intenção de resumo com parâmetros: {intent_data}")

    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url")
    max_length = intent_data.get("max_length", 150)
    output_format = intent_data.get("output_format", "text")

    # Criar diretório de saída
    os.makedirs("example_output", exist_ok=True)
    output_path = f"example_output/summary.{output_format}"

    # Criar pipeline de composição com base nos parâmetros da intenção
    pipeline = (
        compose("summary_pipeline")
        .source(Sources.web(source_url))
        .process(Processors.summarize(max_length=max_length))
    )

    # Adicionar saída apropriada com base no formato solicitado
    if output_format == "audio":
        pipeline = pipeline.output(Outputs.podcast(output_path, voice="pt"))
    else:
        pipeline = pipeline.output(Outputs.file(output_path))

    # Executar o pipeline
    result = await pipeline.execute()

    return {
        "status": "success",
        "output_path": result,
        "message": f"Resumo gerado com sucesso em {result}",
    }


async def main():
    """Função principal."""
    print("Demonstração de Integração: Sistema de Intenção → Sistema de Composição")
    print("--------------------------------------------------------------------")

    # Registrar o manipulador de intenção
    register_intent_handler("summarize", handle_summarize_intent)

    # Exemplos de comandos do usuário
    user_commands = [
        "Resumir o artigo em https://example.com/article em 100 palavras",
        "Gerar um resumo em áudio do site https://news.example.com",
        "Fazer um resumo curto da página https://blog.example.com/post",
    ]

    for command in user_commands:
        print(f"\nProcessando comando: '{command}'")

        # Reconhecer a intenção do usuário
        intent = await recognize_intent(command)
        print(f"Intenção reconhecida: {intent['intent']}")
        print(f"Parâmetros: {intent['parameters']}")

        # Processar a intenção (isso chamará o manipulador registrado)
        if intent["intent"] == "summarize":
            result = await process_intent(intent)
            print(f"Resultado: {result}")
        else:
            print(f"Intenção '{intent['intent']}' não suportada neste exemplo")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
