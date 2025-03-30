"""Minimal example of using PepperPy.

This example demonstrates basic usage of the PepperPy framework
with minimal configuration.
"""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy import PepperPy


async def main() -> None:
    """Run minimal example."""
    print("Minimal Example")
    print("=" * 50)

    # Load environment variables from .env file if it exists
    load_dotenv()

    # Check if API key is configured
    # PepperPy usa o formato PEPPERPY_DOMAIN__PROVIDER_SETTING para variáveis de ambiente
    api_key = os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY") or os.getenv(
        "OPENROUTER_API_KEY"
    )

    print(f"\nAPI Key encontrada: {api_key}")
    print(f"É válida? {api_key is not None and api_key != 'sua_chave_openrouter_aqui'}")

    if not api_key or api_key == "sua_chave_openrouter_aqui":
        print("\n⚠️ VOCÊ PRECISA CONFIGURAR UMA API KEY VÁLIDA!")
        print("Por favor, configure a chave API de uma das seguintes formas:")
        print(
            "1. Defina a variável de ambiente PEPPERPY_LLM__OPENROUTER_API_KEY (recomendado)"
        )
        print("2. Edite o arquivo .env na raiz do projeto com sua chave real")
        print("\nObtenha sua chave em: https://openrouter.ai/keys")
        print("\nSimulando resposta para demonstração:")
        print("\nChat response:")
        print(
            "Olá! Sou um assistente simulado porque você não configurou uma API key real."
        )
        print("\nText response:")
        print("Inteligência virtual\nCódigos que sonham acordados\nHumanos se inspiram")
        return

    try:
        # Initialize PepperPy with LLM support directly using provider name
        async with PepperPy().with_llm("openrouter") as pepper:
            # Generate text using chat interface
            response = await pepper.chat.with_user("Say hello!").generate()
            print("\nChat response:")
            print(response.content)

            # Generate text using text interface
            response = await pepper.text.with_prompt(
                "Write a haiku about AI"
            ).generate()
            print("\nText response:")
            print(response)
    except Exception as e:
        print(f"\n❌ Erro ao usar a API: {e!s}")
        print("Verifique se sua chave API é válida.")


if __name__ == "__main__":
    asyncio.run(main())
