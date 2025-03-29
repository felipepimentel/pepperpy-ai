"""Text Processing Workflow Example with PepperPy.

This example demonstrates how to use PepperPy for text processing workflows.
"""

import asyncio

from pepperpy import PepperPy


async def process_text_with_rag() -> None:
    """Process text with RAG."""
    print("\n=== Text Processing with RAG ===")

    # Initialize PepperPy with RAG and LLM
    async with PepperPy().with_rag().with_llm() as pepper:
        # Sample knowledge corpus
        corpus = [
            "Python is a versatile programming language created by Guido van Rossum in 1991.",
            "The Django framework is written in Python and enables rapid development of secure and scalable web applications.",
            "NumPy is essential for scientific computing in Python, providing support for multidimensional arrays and mathematical operations.",
            "Machine Learning is a subfield of Artificial Intelligence focused on developing algorithms that can learn from data.",
            "PepperPy is an AI framework for simplifying LLM-based application development.",
        ]

        print(f"Adding {len(corpus)} documents to context...")

        # Store documents in RAG using fluent API
        await pepper.rag.add_documents(corpus).with_auto_embeddings().store()

        # Query the knowledge base using fluent API
        print("\nQuerying about Python...")
        results = await (
            pepper.rag.search("What is Python and who created it?").limit(2).execute()
        )
        print(f"Answer: {results[0].content}")

        print("\nQuerying about Machine Learning...")
        results = await (
            pepper.rag.search("Explain what Machine Learning is in a few words.")
            .limit(1)
            .execute()
        )
        print(f"Answer: {results[0].content}")


async def process_text_with_custom_pipeline() -> None:
    """Process text with a custom pipeline."""
    print("\n=== Text Processing with Custom Pipeline ===")

    async with PepperPy().with_llm() as pepper:
        # Sample texts to process
        sample_texts = [
            "Python is a versatile programming language with clear and readable syntax. "
            "It is used in many areas like web development, data analysis, AI, and automation.",
            "Natural Language Processing (NLP) enables computers to understand, interpret, "
            "and manipulate human language. It uses machine learning and computational linguistics techniques.",
        ]

        print("\nProcessing texts with custom pipeline...")
        results = await (
            pepper.text.process(sample_texts)
            .transform(lambda x: x.upper())
            .summarize("Summarize the text in one sentence")
            .execute()
        )

        print("\nProcessing results:")
        for i, result in enumerate(results, 1):
            print(f"Summary {i}: {result}")


async def main() -> None:
    """Run the text processing examples."""
    print("Starting text processing examples with PepperPy...\n")
    await process_text_with_rag()
    await process_text_with_custom_pipeline()
    print("\nText processing examples completed.")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=memory
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    asyncio.run(main())
