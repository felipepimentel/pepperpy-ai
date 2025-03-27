"""Example script demonstrating text processing with PepperPy."""

import asyncio

from pepperpy import PepperPy


async def process_text_example() -> None:
    """Demonstrate text processing with PepperPy."""
    print("\n=== Text Processing Example ===")

    # Sample text documents to process
    documents = [
        """
        Natural language processing (NLP) is a field of artificial intelligence 
        that focuses on the interaction between computers and human language.
        
        Machine learning algorithms are used to process and analyze large amounts
        of natural language data. This enables computers to understand the meaning
        of text and speech.
        """,
        """
        Text chunking is the process of splitting large documents into smaller,
        manageable pieces while preserving meaning and context.
        
        Different chunking strategies can be used depending on the requirements:
        - Fixed-size chunks with overlap
        - Semantic boundaries like sentences and paragraphs
        - Dynamic sizing based on content
        """,
        """
        Transformers have revolutionized natural language processing by enabling
        better understanding of context and meaning in text.
        
        The attention mechanism allows models to focus on relevant parts of the
        input when making predictions. This has led to significant improvements
        in many NLP tasks.
        """,
    ]

    # Create PepperPy instance with RAG support
    async with PepperPy().with_rag() as assistant:
        # Process and learn each document
        for i, doc in enumerate(documents, 1):
            print(f"\nProcessing document {i}...")

            # Learn the document content
            await assistant.learn(doc)

            print(f"Document {i} processed successfully")

        # Ask a question that requires understanding of the processed text
        print("\nQuerying the processed documents...")
        result = await assistant.ask(
            "What are the main topics covered in these documents?"
        )

        print("\nResponse:")
        print(result.content)

        print("\nQuerying about a specific concept...")
        result = await assistant.ask(
            "Explain what text chunking is and why it's important."
        )

        print("\nResponse:")
        print(result.content)


async def main() -> None:
    """Run the text processing example."""
    await process_text_example()


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=chroma (or appropriate provider)
    # PEPPERPY_LLM__PROVIDER=openai (or appropriate provider)
    asyncio.run(main())
