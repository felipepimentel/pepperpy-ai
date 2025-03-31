"""Example demonstrating text normalization in PepperPy."""

import asyncio

from pepperpy import plugin_manager
from pepperpy.content_processing.processors.text_normalization_base import (
    BaseTextNormalizer,
    TextNormalizerRegistry,
)


async def run_example():
    """Run the text normalization example."""
    print("PepperPy Text Normalization Example")
    print("===================================\n")

    # Example text with various normalization issues
    example_text = """
    This is an  example  text with   multiple    spaces,
    weird "quotes", em—dashes, and   other    formatting  issues.
    
    It includes special characters like © and ® symbols.
    
    URLs like https://example.com should be handled properly.
    """

    print("Original text:")
    print(example_text)
    print("\n" + "-" * 50 + "\n")

    # Method 1: Use the built-in BaseTextNormalizer directly
    print("Using BaseTextNormalizer directly:")
    base_normalizer = BaseTextNormalizer()
    normalized_text = base_normalizer.normalize(example_text)
    print(normalized_text)
    print("\n" + "-" * 50 + "\n")

    # Method 2: Use the TextNormalizerRegistry to create a normalizer
    print("Using TextNormalizerRegistry:")
    registry_normalizer = TextNormalizerRegistry.create("base")
    normalized_text = registry_normalizer.normalize(example_text)
    print(normalized_text)
    print("\n" + "-" * 50 + "\n")

    # Method 3: Use the plugin system (if plugin is available)
    try:
        print("Using plugin system:")
        plugin_normalizer = plugin_manager.create_provider(
            "text_normalization", "basic"
        )
        await plugin_normalizer.initialize()
        # Cast the provider to the correct type
        text_normalizer = plugin_normalizer  # type: BasicTextNormalizer
        normalized_text = text_normalizer.normalize(example_text)
        print(normalized_text)
        await plugin_normalizer.cleanup()
    except Exception as e:
        print(f"Plugin-based normalization failed: {e}")

    print("\n" + "-" * 50 + "\n")

    # Custom configuration example
    print("Using custom configuration:")
    custom_normalizer = BaseTextNormalizer(
        transformations=[
            "strip_whitespace",
            "normalize_whitespace",
            "replace_chars",
            "lowercase",
        ],
        custom_replacements={"-": "_", ":": ""},
    )
    normalized_text = custom_normalizer.normalize(example_text)
    print(normalized_text)


if __name__ == "__main__":
    asyncio.run(run_example())
