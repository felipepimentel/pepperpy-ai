"""Simple chat example using Pepperpy.

This example demonstrates how to create a simple chat application
using Pepperpy's simplified API.
"""

import asyncio

from pepperpy import PepperpyClient


async def main() -> None:
    """Run the chat example."""
    # Create client (automatically loads from environment)
    async with PepperpyClient() as client:
        print("Chat started! Running example messages...")
        print("-" * 50)

        # Lista de mensagens de exemplo
        example_messages = [
            "Olá! Como você está?",
            "Me conte uma curiosidade interessante sobre tecnologia",
            "Explique de forma simples como funciona a inteligência artificial",
        ]

        for message in example_messages:
            # Mostra a mensagem do usuário
            print(f"\nYou: {message}")

            # Get response
            print("\nAssistant: ", end="", flush=True)
            response = await client.chat(message)
            print(response)
            print()  # Nova linha após a resposta

            # Pequena pausa entre as mensagens
            await asyncio.sleep(1)

        print("-" * 50)
        print("Example chat completed!")


if __name__ == "__main__":
    asyncio.run(main())
