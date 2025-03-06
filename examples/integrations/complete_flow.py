#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração completa entre os sistemas de composição, intenção e templates.

Purpose:
    Demonstrar como os três sistemas podem ser usados em conjunto para
    criar uma solução completa, desde o reconhecimento de intenções até a execução
    de templates e pipelines de composição.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/complete_flow.py
"""

import asyncio
import os
from typing import Any, Dict, Optional

from pepperpy.core.composition import Outputs, Processors, Sources, compose
from pepperpy.core.intent import (
    process_intent,
    recognize_intent,
    register_intent_handler,
)
from pepperpy.workflows.templates.public import execute_template


# Definir um pipeline personalizado usando o sistema de composição
async def create_custom_pipeline(
    source_url: str,
    output_format: str = "text",
    max_items: int = 3,
    max_length: int = 150,
    voice: str = "pt",
) -> Dict[str, Any]:
    """Cria um pipeline personalizado para processamento de notícias.

    Args:
        source_url: URL da fonte de notícias
        output_format: Formato de saída (text, audio)
        max_items: Número máximo de itens
        max_length: Tamanho máximo do resumo
        voice: Voz a ser usada (código de idioma)

    Returns:
        Resultado do processamento
    """
    print(f"Criando pipeline personalizado para {source_url}")
    print(
        f"Configuração: formato={output_format}, itens={max_items}, tamanho={max_length}, voz={voice}"
    )

    # Definir componentes do pipeline
    source = Sources.rss(source_url, max_items=max_items)
    processor = Processors.summarize(max_length=max_length)

    # Escolher o componente de saída com base no formato
    if output_format == "audio":
        output_path = f"output/news_{voice}.mp3"
        output = Outputs.audio(output_path, voice=voice)
    else:
        output_path = "output/news_summary.txt"
        output = Outputs.file(output_path)

    # Criar diretório de saída se não existir
    os.makedirs("output", exist_ok=True)

    # Criar e executar o pipeline
    result = await (
        compose("news_pipeline")
        .source(source)
        .process(processor)
        .output(output)
        .execute()
    )

    return {"status": "success", "output_path": result, "format": output_format}


# Definir um manipulador de intenção que usa o sistema de composição
async def handle_news_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de processar notícias.

    Este manipulador decide se deve usar um pipeline personalizado ou um template
    com base nos parâmetros da intenção.

    Args:
        intent_data: Dados da intenção reconhecida
            - source_url: URL da fonte de notícias
            - output_format: Formato de saída
            - max_items: Número máximo de itens
            - max_length: Tamanho máximo do resumo
            - voice: Voz a ser usada
            - use_template: Se deve usar um template

    Returns:
        Resultado do processamento da intenção
    """
    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url", "https://news.google.com/rss")
    output_format = intent_data.get("output_format", "text")
    max_items = intent_data.get("max_items", 3)
    max_length = intent_data.get("max_length", 150)
    voice = intent_data.get("voice", "pt")
    use_template = intent_data.get("use_template", False)

    # Decidir se deve usar um template ou um pipeline personalizado
    if use_template:
        print("Usando template pré-configurado para processar notícias")

        # Mapear parâmetros para o formato esperado pelo template
        template_params = {
            "source_url": source_url,
            "output_path": f"output/news_template_{voice}.mp3"
            if output_format == "audio"
            else "output/news_template.txt",
            "voice": voice,
            "max_articles": max_items,
            "summary_length": max_length,
        }

        # Executar o template
        result = await execute_template("news_processor", template_params)

        return {
            "status": result.status,
            "output_path": result.result.get("output_path"),
            "message": "Notícias processadas com sucesso usando template",
            "method": "template",
        }
    else:
        print("Usando pipeline personalizado para processar notícias")

        # Criar e executar um pipeline personalizado
        result = await create_custom_pipeline(
            source_url=source_url,
            output_format=output_format,
            max_items=max_items,
            max_length=max_length,
            voice=voice,
        )

        return {
            "status": result["status"],
            "output_path": result["output_path"],
            "message": "Notícias processadas com sucesso usando pipeline personalizado",
            "method": "pipeline",
        }


async def setup():
    """Configuração inicial do exemplo."""
    # Registrar o manipulador de intenção
    register_intent_handler("process_news", handle_news_intent)
    print("Manipulador de intenção 'process_news' registrado")


async def process_user_command(command: str) -> Optional[Dict[str, Any]]:
    """Processa um comando do usuário.

    Args:
        command: Comando em linguagem natural

    Returns:
        Resultado do processamento ou None se o comando não for reconhecido
    """
    print(f"\nProcessando comando: '{command}'")

    # Reconhecer a intenção
    print("Reconhecendo intenção...")
    intent = await recognize_intent(command)

    if intent["intent"] == "unknown":
        print("Intenção não reconhecida")
        return None

    print(f"Intenção reconhecida: {intent['intent']}")
    print(f"Parâmetros: {intent['parameters']}")

    # Processar a intenção
    print("Processando intenção...")
    result = await process_intent(intent)

    print(f"Processamento concluído: {result['status']}")
    return result


async def main():
    """Função principal."""
    print("=== Exemplo de Fluxo Completo: Intenção → Template/Composição ===")
    print(
        "Este exemplo demonstra a integração completa entre os três sistemas do PepperPy."
    )

    # Configurar o exemplo
    await setup()

    # Exemplos de comandos
    commands = [
        "processar as últimas 5 notícias de https://example.com/news em formato de texto",
        "criar um podcast com as notícias mais recentes usando o template",
        "resumir as 3 principais notícias de tecnologia em português",
    ]

    # Processar cada comando
    for command in commands:
        result = await process_user_command(command)

        if result:
            print("\nResultado do processamento:")
            print(f"Status: {result['status']}")
            print(f"Mensagem: {result['message']}")
            print(f"Arquivo de saída: {result['output_path']}")
            print(f"Método: {result.get('method', 'desconhecido')}")

        print("-" * 50)

    print("\n=== Fluxo de Integração Completo ===")
    print("1. O usuário fornece um comando em linguagem natural")
    print("2. O sistema de intenção reconhece a intenção e extrai parâmetros")
    print("3. O manipulador de intenção decide se deve usar:")
    print("   a. Um pipeline personalizado (sistema de composição)")
    print("   b. Um template pré-configurado (sistema de templates)")
    print("4. O resultado é processado e retornado ao usuário")


if __name__ == "__main__":
    asyncio.run(main())
