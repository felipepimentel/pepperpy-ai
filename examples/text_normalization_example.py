"""Example demonstrating text normalization with PepperPy.

This example shows how to use PepperPy for simple text normalization tasks.
"""

import asyncio

from pepperpy import PepperPy

# Example text with various normalization issues
EXAMPLE_TEXT = """
This is an  example  text with   multiple    spaces,
weird "quotes", em—dashes, and   other    formatting  issues.

It includes special characters like © and ® symbols.

URLs like https://example.com should be handled properly.
"""


async def main():
    """Run the text normalization example."""
    print("PepperPy Text Normalization Example")
    print("===================================\n")

    print("Original text:")
    print(EXAMPLE_TEXT)
    print("\n" + "-" * 50 + "\n")

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Basic normalization
        print("Basic normalization:")
        basic_result = await app.execute(
            query="Normalize this text with basic settings",
            context={"text": EXAMPLE_TEXT},
        )
        print(basic_result)
        print("\n" + "-" * 50 + "\n")

        # Custom normalization
        print("Custom normalization (with extra options):")
        custom_result = await app.execute(
            query="Normalize this text with custom settings",
            context={
                "text": EXAMPLE_TEXT,
                "options": {
                    "strip_whitespace": True,
                    "normalize_whitespace": True,
                    "lowercase": True,
                    "replace_chars": {"-": "_", ":": ""},
                },
            },
        )
        print(custom_result)
        print("\n" + "-" * 50 + "\n")

    finally:
        # Clean up resources
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
