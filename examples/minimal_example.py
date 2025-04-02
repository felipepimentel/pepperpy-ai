#!/usr/bin/env python3
"""
Minimal example of using PepperPy with OpenRouter.

This example shows how to use the PepperPy framework with OpenRouter
using the improved plugin system that auto-manages API keys from environment variables.
"""

import asyncio

from dotenv import load_dotenv

from pepperpy.pepperpy import PepperPy, init_framework

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()


async def main():
    """Run basic chat example."""
    # Inicializar o framework para descobrir plugins
    await init_framework()

    # Criar instância do PepperPy configurada com OpenRouter
    # Não é necessário passar a API key explicitamente, a lib gerencia isso
    pepper = PepperPy().with_llm(provider_type="openrouter")

    # Usar o contexto assíncrono para inicializar recursos automaticamente
    async with pepper:
        # Construir uma conversa de chat fluente
        result = (
            await pepper.chat.with_system("Você é um assistente útil.")
            .with_user(
                "O que é o framework PepperPy e como ele facilita o uso de LLMs?"
            )
            .generate()
        )

        # Imprimir a resposta
        print("\n--- Resposta do LLM ---")
        print(result.content)
        print("----------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
