"""Example demonstrating text normalization with PepperPy.

This example shows how to use PepperPy for text normalization tasks.
"""

import asyncio

from pepperpy import PepperPy

# Example texts with various normalization needs
EXAMPLE_TEXTS = [
    "Running quickly through the forest!",
    "The cats are playing with their toys...",
    "She's been studying for hours and hours",
    "The URL is https://example.com and her email is user@email.com",
    """This is a text with "fancy quotes" and multiple     spaces,
    as well as line\nbreaks and © copyright symbols.""",
]


async def main():
    """Run the text normalization comparison example."""
    print("PepperPy Text Normalization Example")
    print("=====================================\n")

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Process each example text
        for i, text in enumerate(EXAMPLE_TEXTS, 1):
            print(f"\nExample {i}:")
            print("Original:", text)
            print("-" * 50)

            # Basic normalization
            basic_result = await app.execute(
                query="Normalize this text using basic normalization",
                context={"text": text},
            )
            print(f"Basic: {basic_result}")

            # Advanced normalization
            advanced_result = await app.execute(
                query="Normalize this text using advanced techniques",
                context={
                    "text": text,
                    "options": {"remove_punctuation": True, "lowercase": True},
                },
            )
            print(f"Advanced: {advanced_result}")

            print("=" * 50)

    finally:
        # Clean up resources
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
