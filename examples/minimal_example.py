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
    if not (
        os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    ):
        print("\n⚠️ API key não configurada!")
        print("Por favor, configure a chave API de uma das seguintes formas:")
        print(
            "1. Defina a variável de ambiente PEPPERPY_LLM__OPENROUTER_API_KEY (recomendado)"
        )
        print(
            "2. Crie um arquivo .env na raiz do projeto com PEPPERPY_LLM__OPENROUTER_API_KEY=sua_chave_aqui"
        )
        print(
            "3. Alternativamente, para compatibilidade, você pode usar OPENROUTER_API_KEY"
        )
        print("\nObtenha sua chave em: https://openrouter.ai/keys")
        return

    # Initialize PepperPy with LLM support directly using provider name
    async with PepperPy().with_llm("openrouter") as pepper:
        # Generate text using chat interface
        response = await pepper.chat.with_user("Say hello!").generate()
        print("\nChat response:")
        print(response.content)

        # Generate text using text interface
        response = await pepper.text.with_prompt("Write a haiku about AI").generate()
        print("\nText response:")
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
