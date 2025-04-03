"""Text Processing Workflow Example with PepperPy.

This example demonstrates how to use PepperPy for text processing workflows.
"""

import asyncio

from pepperpy import PepperPy

# Sample corpus of texts
SAMPLE_CORPUS = [
    "Python is a versatile programming language created by Guido van Rossum in 1991.",
    "The Django framework is written in Python and enables rapid development of secure and scalable web applications.",
    "NumPy is essential for scientific computing in Python, providing support for multidimensional arrays and mathematical operations.",
    "Machine Learning is a subfield of Artificial Intelligence focused on developing algorithms that can learn from data.",
    "PepperPy is an AI framework for simplifying LLM-based application development.",
]


async def main():
    """Run the text processing examples with PepperPy."""
    print("Text Processing Example with PepperPy")
    print("=" * 50)

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Process text with RAG-like functionality
        print("\n=== Text Processing with Knowledge Base ===")

        # Add documents to knowledge base
        print(f"Adding {len(SAMPLE_CORPUS)} documents to context...")

        # Execute query to add documents
        for i, text in enumerate(SAMPLE_CORPUS):
            await app.execute(
                query="Add document to knowledge base",
                context={"text": text, "metadata": {"source": "example", "id": str(i)}},
            )

        # Query about Python
        print("\nQuerying about Python...")
        python_answer = await app.execute(
            query="What is Python and who created it?",
            context={"use_knowledge_base": True},
        )
        print(f"Answer: {python_answer}")

        # Query about Machine Learning
        print("\nQuerying about Machine Learning...")
        ml_answer = await app.execute(
            query="Explain what Machine Learning is in a few words.",
            context={"use_knowledge_base": True},
        )
        print(f"Answer: {ml_answer}")

        # Process text with custom pipeline
        print("\n=== Text Processing with Custom Pipeline ===")

        # Sample texts to process
        sample_texts = [
            "Python is a versatile programming language with clear and readable syntax.",
            "Natural Language Processing (NLP) enables computers to understand human language.",
        ]

        print("Processing texts with custom pipeline...")
        for i, text in enumerate(sample_texts, 1):
            # Transform and summarize text
            result = await app.execute(
                query="Summarize this text in one sentence", context={"text": text}
            )
            print(f"Summary {i}: {result}")

    finally:
        # Clean up resources
        await app.cleanup()

    print("\nText processing examples completed.")


if __name__ == "__main__":
    asyncio.run(main())
