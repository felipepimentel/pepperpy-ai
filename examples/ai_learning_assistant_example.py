"""AI Learning Assistant Example.

A minimalist example showing how to use PepperPy.
"""

import asyncio

from pepperpy import PepperPy, publish_event


async def main():
    """Run the AI learning assistant example."""
    print("PepperPy Minimal Example")
    print("=" * 50)

    # Criar instância do PepperPy
    pepper = PepperPy()

    # Inicializar
    await pepper.initialize()

    try:
        # Executa uma consulta simples
        result = await pepper.execute("Qual é a função de decoradores em Python?")
        print(f"\nResposta: {result}")

        try:
            # Publica um evento (função assíncrona)
            context = await publish_event("example.completed", {"status": "success"})
            print(f"\nEvento publicado: {context.event_type}")
        except Exception as e:
            print(f"\nErro ao publicar evento: {e}")

    finally:
        # Limpar recursos
        await pepper.cleanup()


if __name__ == "__main__":
    # Definir variáveis de ambiente antes de executar:
    # PEPPERPY_CONFIG_FILE=config.json
    asyncio.run(main())
