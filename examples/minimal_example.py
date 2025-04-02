#!/usr/bin/env python3
"""
Minimal example of using PepperPy with OpenRouter.

This example shows how to use the PepperPy framework with OpenRouter
using the improved plugin system that auto-manages API keys from environment variables.
It also demonstrates the cache and enhanced intent analysis features.
"""

import asyncio
import time

from dotenv import load_dotenv

from pepperpy.agents.intent import analyze_intent
from pepperpy.cache import cached
from pepperpy.pepperpy import PepperPy, init_framework

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()


@cached(ttl=3600, namespace="minimal_example")
async def get_response(query: str) -> str:
    """Get response from LLM with caching.

    Args:
        query: The query to send to the LLM

    Returns:
        The LLM response
    """
    # Criar instância do PepperPy configurada com OpenRouter
    pepper = PepperPy().with_llm(provider_type="openrouter")

    # Usar o contexto assíncrono para inicializar recursos automaticamente
    async with pepper:
        # Construir uma conversa de chat fluente
        result = (
            await pepper.chat.with_system("Você é um assistente útil.")
            .with_user(query)
            .generate()
        )

        return result.content


async def main():
    """Run basic chat example."""
    # Inicializar o framework para descobrir plugins
    await init_framework()

    # Use a query that demonstrates intent analysis
    query = "O que é o framework PepperPy e como ele facilita o uso de LLMs?"

    # Analyze intent
    intent_type, parameters, confidence = analyze_intent(query)
    print("\n--- Análise de Intenção ---")
    print(f"Tipo de intenção: {intent_type}")
    print(f"Parâmetros: {parameters}")
    print(f"Confiança: {confidence:.2f}")
    print("-------------------------\n")

    # First call (not cached)
    print("\n--- Primeira chamada (não cacheada) ---")
    start_time = time.time()
    result = await get_response(query)
    end_time = time.time()
    print(f"Tempo de execução: {end_time - start_time:.2f} segundos")

    # Print the response
    print("\n--- Resposta do LLM ---")
    print(result)
    print("----------------------\n")

    # Second call (should be cached)
    print("\n--- Segunda chamada (deve usar cache) ---")
    start_time = time.time()
    result = await get_response(query)
    end_time = time.time()
    print(f"Tempo de execução: {end_time - start_time:.2f} segundos")
    print("-------------------------\n")

    # Try a different query to see intent analysis
    print("\n--- Testando outra consulta ---")
    new_query = "Crie uma imagem de um gato programando em Python"

    # Create full intent object using direct tuple unpacking
    new_intent_type, new_parameters, new_confidence = analyze_intent(new_query)
    print(f"Tipo de intenção: {new_intent_type}")
    print(f"Parâmetros: {new_parameters}")
    print(f"Confiança: {new_confidence:.2f}")
    print("-------------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
