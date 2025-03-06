#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo básico de reconhecimento de intenção no PepperPy.

Purpose:
    Demonstrar o uso básico da API de intenção do PepperPy,
    mostrando como reconhecer e processar intenções a partir de texto.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/workflow_automation/simple_intent.py
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict

# Importando apenas o que está disponível
from pepperpy.core.intent.types import IntentType


# Simulação da função de reconhecimento de intenção
async def custom_recognize_intent(text: str) -> Dict[str, Any]:
    """Simula o reconhecimento de intenção a partir de texto.

    Args:
        text: Texto a ser analisado

    Returns:
        Intenção reconhecida como dicionário
    """
    print(f"Reconhecendo intenção a partir do texto: '{text}'")

    # Simulação simples de reconhecimento baseado em palavras-chave
    if "resumir" in text.lower() or "resumo" in text.lower():
        # Extrair URL se presente
        url = "https://example.com"
        if "http" in text:
            parts = text.split()
            for part in parts:
                if part.startswith("http"):
                    url = part

        # Extrair tamanho máximo se presente
        max_length = 150
        if "palavras" in text:
            parts = text.split()
            for i, part in enumerate(parts):
                if part == "palavras" and i > 0 and parts[i - 1].isdigit():
                    max_length = int(parts[i - 1])

        return {
            "intent": "summarize",
            "type": IntentType.COMMAND.value,
            "confidence": 0.9,
            "parameters": {"source_url": url, "max_length": max_length},
            "text": text,
        }

    elif "traduzir" in text.lower() or "tradução" in text.lower():
        # Extrair idioma de destino se presente
        target_language = "en"
        if "para" in text:
            parts = text.split("para")
            if len(parts) > 1:
                lang_part = parts[1].strip().split()[0]
                if lang_part in ["inglês", "english"]:
                    target_language = "en"
                elif lang_part in ["espanhol", "spanish"]:
                    target_language = "es"
                elif lang_part in ["francês", "french"]:
                    target_language = "fr"

        return {
            "intent": "translate",
            "type": IntentType.COMMAND.value,
            "confidence": 0.85,
            "parameters": {
                "text": text.split("traduzir")[1].strip()
                if "traduzir" in text
                else "Texto de exemplo",
                "target_language": target_language,
            },
            "text": text,
        }

    else:
        return {
            "intent": "unknown",
            "type": IntentType.UNKNOWN.value,
            "confidence": 0.3,
            "parameters": {},
            "text": text,
        }


# Simulação do processador de intenção
async def process_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o processamento de uma intenção.

    Args:
        intent: Intenção a ser processada

    Returns:
        Resultado do processamento
    """
    intent_name = intent["intent"]
    print(f"Processando intenção: {intent_name}")

    # Verificar se há um manipulador registrado para esta intenção
    handler = INTENT_HANDLERS.get(intent_name)

    if handler:
        return await handler(intent["parameters"])
    else:
        return {
            "status": "error",
            "message": f"Intenção '{intent_name}' não reconhecida ou não suportada",
        }


# Dicionário para armazenar manipuladores de intenção
INTENT_HANDLERS = {}


# Função para registrar manipuladores de intenção
def register_intent_handler(
    intent_name: str,
    handler_func: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
):
    """Registra um manipulador para uma intenção específica.

    Args:
        intent_name: Nome da intenção
        handler_func: Função manipuladora
    """
    INTENT_HANDLERS[intent_name] = handler_func
    print(f"Manipulador registrado para intenção '{intent_name}'")


# Manipulador para a intenção de resumir
async def handle_summarize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de resumir.

    Args:
        params: Parâmetros da intenção

    Returns:
        Resultado do processamento
    """
    url = params.get("source_url", "https://example.com")
    max_length = params.get("max_length", 150)

    print(f"Resumindo conteúdo de {url} com tamanho máximo de {max_length} palavras")

    # Simulação de resumo
    summary = (
        f"Este é um resumo simulado do conteúdo de {url}. "
        f"O resumo foi limitado a {max_length} palavras conforme solicitado."
    )

    return {
        "status": "success",
        "summary": summary,
        "message": "Resumo gerado com sucesso",
    }


# Manipulador para a intenção de traduzir
async def handle_translate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de traduzir.

    Args:
        params: Parâmetros da intenção

    Returns:
        Resultado do processamento
    """
    text = params.get("text", "")
    target_language = params.get("target_language", "en")

    print(f"Traduzindo texto para {target_language}")

    # Simulação de tradução
    if target_language == "en":
        translation = f"This is a simulated translation of: {text}"
    elif target_language == "es":
        translation = f"Esta es una traducción simulada de: {text}"
    elif target_language == "fr":
        translation = f"C'est une traduction simulée de: {text}"
    else:
        translation = f"Translated text (to {target_language}): {text}"

    return {
        "status": "success",
        "translation": translation,
        "message": f"Texto traduzido com sucesso para {target_language}",
    }


async def setup():
    """Configuração inicial do exemplo."""
    # Registrar manipuladores de intenção
    register_intent_handler("summarize", handle_summarize)
    register_intent_handler("translate", handle_translate)


async def demo_intent_recognition():
    """Demonstra o reconhecimento de intenção."""
    print("\n=== Reconhecimento de Intenção ===")

    # Exemplos de comandos
    commands = [
        "resumir o artigo em https://example.com/article em 200 palavras",
        "traduzir 'olá mundo' para inglês",
        "qual é o clima hoje?",
    ]

    for command in commands:
        print(f"\nComando: '{command}'")
        intent = await custom_recognize_intent(command)
        print(f"Intenção reconhecida: {intent['intent']}")
        print(f"Confiança: {intent['confidence']}")
        print(f"Parâmetros: {intent['parameters']}")


async def demo_intent_processing():
    """Demonstra o processamento de intenção."""
    print("\n=== Processamento de Intenção ===")

    # Configurar manipuladores
    await setup()

    # Exemplo de processamento de intenção de resumo
    print("\nProcessando intenção de resumo:")
    intent = {
        "intent": "summarize",
        "type": IntentType.COMMAND.value,
        "confidence": 0.9,
        "parameters": {"source_url": "https://example.com/article", "max_length": 100},
        "text": "resumir o artigo em https://example.com/article em 100 palavras",
    }

    result = await process_intent(intent)
    print(f"Resultado: {result}")

    # Exemplo de processamento de intenção de tradução
    print("\nProcessando intenção de tradução:")
    intent = {
        "intent": "translate",
        "type": IntentType.COMMAND.value,
        "confidence": 0.85,
        "parameters": {"text": "olá mundo", "target_language": "en"},
        "text": "traduzir 'olá mundo' para inglês",
    }

    result = await process_intent(intent)
    print(f"Resultado: {result}")


async def demo_intent_builder():
    """Demonstra a construção manual de intenções."""
    print("\n=== Construção Manual de Intenção ===")

    # Criar uma intenção manualmente
    intent = {
        "intent": "play_music",
        "type": IntentType.COMMAND.value,
        "confidence": 0.95,
        "parameters": {"song": "Bohemian Rhapsody", "artist": "Queen"},
        "text": "tocar Bohemian Rhapsody do Queen",
    }

    print("Intenção construída manualmente:")
    print(f"Nome: {intent['intent']}")
    print(f"Tipo: {intent['type']}")
    print(f"Confiança: {intent['confidence']}")
    print(f"Entidades: {intent['parameters']}")
    print(f"Texto original: {intent['text']}")


async def main():
    """Função principal."""
    print("=== Exemplo Básico de Reconhecimento de Intenção ===")
    print("Este exemplo demonstra o uso básico da API de intenção do PepperPy.")

    # Demonstrar reconhecimento de intenção
    await demo_intent_recognition()

    # Demonstrar processamento de intenção
    await demo_intent_processing()

    # Demonstrar construção manual de intenção
    await demo_intent_builder()

    print("\n=== Conceitos Demonstrados ===")
    print("1. Reconhecimento de intenção a partir de texto")
    print("2. Extração de parâmetros de comandos em linguagem natural")
    print("3. Processamento de intenções com manipuladores específicos")
    print("4. Construção manual de intenções")


if __name__ == "__main__":
    asyncio.run(main())
