"""AI Learning Assistant Example.

This example demonstrates how to use PepperPy to create an AI learning assistant
that can help with learning new topics, answer questions, and provide explanations.
"""

import asyncio
import json
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.tts import create_provider as create_tts_provider


async def process_learning_request(pepper: PepperPy, topic: str) -> None:
    """Process a learning request for a specific topic."""
    print(f"\nLearning about: {topic}")
    print("-" * 50)

    # Generate an explanation of the topic
    response = await (
        pepper.chat.with_system(
            "You are an expert tutor helping someone learn a new topic."
        )
        .with_user(f"Explain {topic} in simple terms.")
        .generate()
    )

    print("\nExplanation:")
    print(response.content)

    # Generate practice questions
    response = await (
        pepper.chat.with_system(
            "Generate 2 practice questions about the topic to test understanding."
        )
        .with_user(topic)
        .generate()
    )

    print("\nPractice Questions:")
    print(response.content)

    # Save learning materials
    materials = {
        "topic": topic,
        "explanation": response.content,
        "questions": response.content,
    }

    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{topic.lower().replace(' ', '_')}_materials.json"

    with open(output_file, "w") as f:
        json.dump(materials, f, indent=2)

    print(f"\nLearning materials saved to: {output_file}")

    # Generate audio summary
    print("\nGenerating audio summary...")
    audio_file = await pepper.tts.with_text(response.content[:200]).generate()
    print(f"Audio summary saved to: {audio_file}")


async def process_question(pepper: PepperPy, question: str) -> None:
    """Process a specific question about a topic."""
    print(f"\nQuestion: {question}")
    print("-" * 50)

    # Search knowledge base for relevant information
    results = await pepper.rag.search(question)

    # Generate answer using RAG results
    response = await (
        pepper.chat.with_system(
            "You are a helpful tutor. Use the provided context to answer the question."
        )
        .with_user(f"Context: {results}\n\nQuestion: {question}")
        .generate()
    )

    print("\nAnswer:")
    print(response.content)


async def main() -> None:
    """Run the AI learning assistant example."""
    print("AI Learning Assistant Example")
    print("=" * 50)

    # Create providers
    llm = create_llm_provider("openrouter")
    rag = create_rag_provider("memory")
    tts = create_tts_provider("ElevenLabsProvider")

    # Initialize PepperPy with required providers
    async with PepperPy().with_llm(llm).with_rag(rag).with_tts(tts) as pepper:
        # Process learning requests
        await process_learning_request(pepper, "Python Decorators")
        await process_learning_request(pepper, "Machine Learning Basics")

        # Process specific questions
        await process_question(
            pepper, "What are some common use cases for Python decorators?"
        )
        await process_question(
            pepper, "How does supervised learning differ from unsupervised learning?"
        )


if __name__ == "__main__":
    asyncio.run(main())
