"""Example demonstrating the Text Processing Workflow plugin.

This example shows how to use the Text Processing Workflow plugin
to process text using NLP tools.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.plugin_manager import plugin_manager

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Text Processing Workflow Example")
    print("=" * 50)

    # Initialize PepperPy
    async with PepperPy() as pepper:
        # Get workflow using plugin_manager
        workflow_provider = plugin_manager.create_provider(
            "workflow", "text_processing", processor="spacy"
        )

        # Initialize workflow
        await workflow_provider.initialize()

        # Process a single text
        print("\nProcessing single text...")
        text = "PepperPy is a Python framework for building AI applications."
        result = await workflow_provider.process_text(text)

        print(f"\nInput: {text}")
        print(f"Entities: {result.entities}")
        print(f"Tokens: {result.tokens}")

        # Process multiple texts
        print("\nProcessing multiple texts...")
        texts = [
            "Machine learning models can analyze data efficiently.",
            "Natural language processing helps computers understand human language.",
            "Vector databases store embeddings for semantic search.",
        ]

        results = await workflow_provider.process_batch(texts)

        for i, (input_text, processed) in enumerate(zip(texts, results), 1):
            print(f"\n{i}. Input: {input_text}")
            print(f"   Entities: {processed.entities}")

        # Try with a different processor if available
        print("\nProcessing with NLTK processor...")
        try:
            nltk_workflow = plugin_manager.create_provider(
                "workflow", "text_processing", processor="nltk"
            )
            await nltk_workflow.initialize()

            result = await nltk_workflow.process_text(
                "PepperPy makes AI integration easy and efficient."
            )
            print(f"Entities: {result.entities}")

            # Clean up
            await nltk_workflow.cleanup()
        except Exception as e:
            print(f"Error with NLTK processor: {e}")

        # Use the execute method directly
        print("\nUsing execute method...")
        result = await workflow_provider.execute(
            {
                "text": "This is a direct execution example.",
                "options": {"processing_options": {"include_pos": True}},
            }
        )

        processed = result["result"]
        print(f"Processed text has {len(processed.tokens)} tokens")

        # Clean up
        await workflow_provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
