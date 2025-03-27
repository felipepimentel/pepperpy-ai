"""Example of simplifying text processing with PepperPy."""

import asyncio

from pepperpy import PepperPy


async def process_text_with_rag() -> None:
    """Using RAG for text processing instead of workflows."""
    print("\n=== Text Processing with RAG ===")

    # Sample text to process
    text = "Apple Inc. is planning to open a new office in London next year."

    # Initialize PepperPy with RAG and LLM support
    async with PepperPy().with_rag().with_llm() as assistant:
        # Store the text
        await assistant.learn(text)

        # Ask questions about the processed text
        result = await assistant.ask("What company is mentioned in the text?")

        # Print results
        print("\nText Processing Results:")
        print(f"Original text: {text}")
        print(f"Analysis result: {result.content}")


async def process_batch_with_rag() -> None:
    """Processing multiple texts with RAG."""
    print("\n=== Batch Text Processing with RAG ===")

    # Sample texts to process
    texts = [
        "Google announced a new AI model yesterday.",
        "Microsoft is investing heavily in OpenAI.",
        "Tesla's new factory will be built in Texas.",
    ]

    # Initialize PepperPy with RAG and LLM
    async with PepperPy().with_rag().with_llm() as assistant:
        # Store all texts
        for text in texts:
            await assistant.learn(text)

        # Ask questions about the texts
        result = await assistant.ask("What companies are mentioned in the documents?")

        # Print results
        print("\nBatch Processing Results:")
        print("Companies mentioned:")
        print(result.content)

        # Ask about specific entities
        result = await assistant.ask("What locations are mentioned in the documents?")
        print("\nLocations mentioned:")
        print(result.content)


async def analyze_complex_text() -> None:
    """Analyzing complex text with PepperPy."""
    print("\n=== Complex Text Analysis ===")

    # Sample text for complex analysis
    text = """
    The European Union has announced new climate goals. The targets aim to reduce
    emissions by 55% by 2030. Several member states, including France and Germany,
    have pledged additional support.
    """

    # Initialize PepperPy with RAG and LLM
    async with PepperPy().with_rag().with_llm() as assistant:
        # Store the text
        await assistant.learn(text)

        # Perform various analyses through questions
        results = []

        questions = [
            "What organization is mentioned in the text?",
            "What specific goal was announced?",
            "Which countries are mentioned?",
            "What is the timeline for the climate goals?",
            "Summarize the text in one sentence.",
        ]

        # Get all results
        for question in questions:
            result = await assistant.ask(question)
            results.append((question, result.content))

        # Print results
        print("\nMulti-Aspect Analysis Results:")
        for question, answer in results:
            print(f"\nQ: {question}")
            print(f"A: {answer}")


async def main() -> None:
    """Run all examples."""
    print("Starting text processing examples with PepperPy...")

    # Run examples
    await process_text_with_rag()
    await process_batch_with_rag()
    await analyze_complex_text()

    print("\nAll examples completed!")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=chroma
    # PEPPERPY_LLM__PROVIDER=openai
    asyncio.run(main())
