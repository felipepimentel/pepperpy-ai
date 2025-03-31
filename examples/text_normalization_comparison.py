"""Example comparing basic and NLTK text normalization in PepperPy."""

import asyncio

from pepperpy import plugin_manager


async def run_example():
    """Run the text normalization comparison example."""
    print("PepperPy Text Normalization Comparison")
    print("=====================================\n")

    # Example text with various normalization needs
    example_texts = [
        "Running quickly through the forest!",
        "The cats are playing with their toys...",
        "She's been studying for hours and hours",
        "The URL is https://example.com and her email is user@email.com",
        """This is a text with "fancy quotes" and multiple     spaces,
        as well as line\nbreaks and © copyright symbols.""",
    ]

    # Initialize normalizers
    basic_provider = plugin_manager.create_provider("text_normalization", "basic")
    nltk_provider = plugin_manager.create_provider("text_normalization", "nltk")

    # Cast providers to their correct types
    basic_normalizer = basic_provider  # type: BasicTextNormalizer
    nltk_normalizer = nltk_provider  # type: NLTKTextNormalizer

    # Initialize the providers
    await basic_normalizer.initialize()
    await nltk_normalizer.initialize()

    try:
        # Process each example text
        for i, text in enumerate(example_texts, 1):
            print(f"\nExample {i}:")
            print("Original:", text)
            print("-" * 50)

            # Basic normalization
            basic_result = basic_normalizer.normalize(text)
            print("Basic:", basic_result)

            # NLTK normalization
            nltk_result = nltk_normalizer.normalize(text)
            print("NLTK:", nltk_result)

            print("=" * 50)

    finally:
        # Clean up resources
        await basic_normalizer.cleanup()
        await nltk_normalizer.cleanup()


if __name__ == "__main__":
    asyncio.run(run_example())
