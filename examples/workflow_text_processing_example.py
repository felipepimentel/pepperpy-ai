#!/usr/bin/env python3
"""Example demonstrating text processing with PepperPy.

This example shows how to use PepperPy to process text using NLP capabilities.
"""

import asyncio

from pepperpy import PepperPy

# Sample texts for processing
SAMPLE_TEXTS = [
    "PepperPy is a Python framework for building AI applications.",
    "Machine learning models can analyze data efficiently.",
    "Natural language processing helps computers understand human language.",
    "Vector databases store embeddings for semantic search.",
]


async def main():
    """Run the text processing example."""
    print("Text Processing Example")
    print("=" * 50)

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Process a single text
        print("\nProcessing single text...")
        text = SAMPLE_TEXTS[0]
        print(f"Input: {text}")

        # Execute text processing query
        result = await app.execute(
            query="Process this text and identify entities", context={"text": text}
        )

        # Print result
        print(f"Result: {result}")

        # Process multiple texts
        print("\nProcessing multiple texts...")

        # Process each text
        for i, text in enumerate(SAMPLE_TEXTS[1:], 1):
            print(f"\n{i}. Input: {text}")

            # Execute processing
            result = await app.execute(
                query="Analyze this text", context={"text": text}
            )

            print(f"   Result: {result}")

        # Execute advanced processing
        print("\nAdvanced text processing...")

        advanced_result = await app.execute(
            query="Analyze this text with advanced options",
            context={
                "text": "PepperPy makes AI integration easy and efficient.",
                "options": {"include_sentiment": True, "extract_keywords": True},
            },
        )

        print(f"Advanced result: {advanced_result}")

    finally:
        # Clean up
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
