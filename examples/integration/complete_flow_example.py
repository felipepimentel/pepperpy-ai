#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração completa entre os sistemas de composição, intenção e templates.

Este exemplo demonstra como os três sistemas podem ser usados em conjunto para
criar uma solução completa, desde o reconhecimento de intenções até a execução
de templates e pipelines de composição.
"""

import asyncio
import os
from typing import Any, Dict, Optional

from pepperpy.core.composition import Outputs, Processors, Sources, compose
from pepperpy.core.intent import recognize_intent, register_intent_handler
from pepperpy.workflows.templates.public import execute_template


# Definir um template personalizado usando o sistema de composição
async def create_custom_pipeline(
    source_url: str,
    output_format: str = "text",
    max_items: int = 3,
    max_length: int = 150,
    voice: str = "pt",
) -> Dict[str, Any]:
    """Cria um pipeline personalizado com base nos parâmetros.

    Args:
        source_url: URL da fonte de dados.
        output_format: Formato de saída (text, audio, json).
        max_items: Número máximo de itens a processar.
        max_length: Comprimento máximo do resumo.
        voice: Voz a ser usada para saída de áudio.

    Returns:
        Resultado da execução do pipeline.
    """
    # Criar diretório de saída
    os.makedirs("example_output", exist_ok=True)

    # Definir caminho de saída com base no formato
    output_path = f"example_output/result.{output_format}"
    if output_format == "audio":
        output_path = "example_output/result.mp3"

    # Criar pipeline de composição
    pipeline = (
        compose("custom_pipeline")
        .source(Sources.rss(source_url, max_items=max_items))
        .process(Processors.summarize(max_length=max_length))
    )

    # Adicionar saída apropriada com base no formato
    if output_format == "audio":
        pipeline = pipeline.output(Outputs.podcast(output_path, voice=voice))
    elif output_format == "json":
        pipeline = pipeline.output(Outputs.json(output_path))
    else:
        pipeline = pipeline.output(Outputs.file(output_path))

    # Executar o pipeline
    result = await pipeline.execute()

    return {"status": "success", "output_path": result, "format": output_format}


# Definir um manipulador de intenção que usa o sistema de templates
async def handle_news_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de processar notícias.

    Args:
        intent_data: Dados da intenção, incluindo parâmetros.

    Returns:
        Resultado da execução.
    """
    print(f"Processando intenção de notícias com parâmetros: {intent_data}")

    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url")
    output_format = intent_data.get("output_format", "text")
    max_items = intent_data.get("max_items", 3)
    max_length = intent_data.get("max_length", 150)
    voice = intent_data.get("voice", "pt")

    # Determinar qual abordagem usar com base na complexidade
    if output_format == "audio" and max_items > 5:
        # Caso complexo: usar template
        print("Usando template para caso complexo...")
        template_params = {
            "source_url": source_url,
            "output_path": "example_output/news_podcast.mp3",
            "voice": voice,
            "max_articles": max_items,
            "summary_length": max_length,
        }
        result = await execute_template("news_podcast", template_params)
        return {
            "status": result.status,
            "output_path": result.result.get("output_path"),
            "approach": "template",
        }
    else:
        # Caso simples: usar pipeline de composição diretamente
        print("Usando pipeline de composição para caso simples...")
        result = await create_custom_pipeline(
            source_url=source_url,
            output_format=output_format,
            max_items=max_items,
            max_length=max_length,
            voice=voice,
        )
        return {
            "status": "success",
            "output_path": result["output_path"],
            "approach": "composition",
        }


async def process_user_command(command: str) -> Optional[Dict[str, Any]]:
    """Processa um comando do usuário usando o fluxo completo.

    Args:
        command: Comando do usuário em linguagem natural.

    Returns:
        Resultado do processamento, ou None se não for possível processar.
    """
    print(f"\nProcessando comando: '{command}'")

    # 1. Reconhecer a intenção usando o sistema de intenção
    intent = await recognize_intent(command)
    print(f"Intenção reconhecida: {intent['intent']}")
    print(f"Parâmetros: {intent['parameters']}")

    # 2. Processar a intenção
    if intent["intent"] == "process_news":
        # Usar o manipulador de intenção que integra templates e composição
        result = await handle_news_intent(intent["parameters"])
        print(f"Resultado ({result['approach']}): {result}")
        return result
    else:
        print(f"Intenção '{intent['intent']}' não suportada neste exemplo")
        return None


async def main():
    """Função principal."""
    print("Demonstração de Integração Completa: Intenção → Templates → Composição")
    print("---------------------------------------------------------------------")

    # Registrar o manipulador de intenção
    register_intent_handler("process_news", handle_news_intent)

    # Exemplos de comandos do usuário
    user_commands = [
        "Resumir as notícias de https://news.example.com",
        "Criar um podcast com as 10 principais notícias de https://daily.example.com",
        "Gerar um resumo em JSON das notícias de tecnologia de https://tech.example.com",
    ]

    # Processar cada comando
    for command in user_commands:
        await process_user_command(command)

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
