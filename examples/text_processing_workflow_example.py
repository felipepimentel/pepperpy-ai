"""Text Processing Workflow Example with PepperPy.

This example demonstrates how to use PepperPy for text processing workflows.
"""

import asyncio

from pepperpy import PepperPy
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider


async def process_text_with_rag() -> None:
    """Process text with RAG."""
    print("\n=== Text Processing with RAG ===")

    # Create providers
    rag_provider = create_rag_provider("memory")
    llm_provider = create_llm_provider("openrouter")

    # Initialize PepperPy with RAG and LLM
    async with PepperPy().with_rag(rag_provider).with_llm(llm_provider) as pepper:
        # Sample knowledge corpus
        corpus = [
            "Python is a versatile programming language created by Guido van Rossum in 1991.",
            "The Django framework is written in Python and enables rapid development of secure and scalable web applications.",
            "NumPy is essential for scientific computing in Python, providing support for multidimensional arrays and mathematical operations.",
            "Machine Learning is a subfield of Artificial Intelligence focused on developing algorithms that can learn from data.",
            "PepperPy is an AI framework for simplifying LLM-based application development.",
        ]

        print(f"Adding {len(corpus)} documents to context...")

        # Store documents in RAG directly using the provider
        for text in corpus:
            await rag_provider.store_document(text, metadata={"source": "example"})

        # Query the knowledge base
        print("\nQuerying about Python...")
        python_results = await rag_provider.search_documents(
            "What is Python and who created it?", limit=2
        )

        # Use LLM to generate answer with context
        python_context = "\n".join([
            result.get("text", "") for result in python_results
        ])
        python_answer = await (
            pepper.chat.with_system("You are a helpful assistant.")
            .with_user(
                f"Based on this context: {python_context}\n\nWhat is Python and who created it?"
            )
            .generate()
        )
        print(f"Answer: {python_answer.content}")

        print("\nQuerying about Machine Learning...")
        ml_results = await rag_provider.search_documents(
            "Explain what Machine Learning is in a few words.", limit=1
        )

        # Use LLM to generate answer with context
        ml_context = "\n".join([result.get("text", "") for result in ml_results])
        ml_answer = await (
            pepper.chat.with_system("You are a helpful assistant.")
            .with_user(
                f"Based on this context: {ml_context}\n\nExplain what Machine Learning is in a few words."
            )
            .generate()
        )
        print(f"Answer: {ml_answer.content}")


async def process_text_with_custom_pipeline() -> None:
    """Process text with a custom pipeline."""
    print("\n=== Text Processing with Custom Pipeline ===")

    # Create LLM provider
    llm_provider = create_llm_provider("openrouter")

    async with PepperPy().with_llm(llm_provider) as pepper:
        # Sample texts to process
        sample_texts = [
            "Python is a versatile programming language with clear and readable syntax. "
            "It is used in many areas like web development, data analysis, AI, and automation.",
            "Natural Language Processing (NLP) enables computers to understand, interpret, "
            "and manipulate human language. It uses machine learning and computational linguistics techniques.",
        ]

        print("\nProcessing texts with custom pipeline...")
        results = []

        for text in sample_texts:
            # Transform text
            transformed_text = text.upper()

            # Summarize using LLM
            summary = await (
                pepper.chat.with_system("You are a text summarization expert.")
                .with_user(
                    f"Summarize the following text in one sentence:\n\n{transformed_text}"
                )
                .generate()
            )

            results.append(summary.content)

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
    # Using memory provider for RAG and openrouter for LLM
    asyncio.run(main())
