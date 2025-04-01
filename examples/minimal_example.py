from pepperpy import PepperPy, init_framework


async def main() -> None:
    """Run minimal example."""
    print("PepperPy Minimal Example")
    print("=" * 50)

    # Initialize the framework
    init_framework()
    print("Framework initialized successfully")
    
    # Initialize PepperPy with default LLM provider (from environment variables)
    async with PepperPy().with_llm() as pepper:
        # Chat interface

        response = await pepper.chat.with_user("Say hello!").generate()
        print("\nChat response:")
        print(response.content)

        # Text interface

        response = await pepper.text.with_prompt("Write a haiku about AI").generate()
        print("\nText response:")
        print(response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
