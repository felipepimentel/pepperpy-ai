"""AI Learning Assistant Example.

This example demonstrates how to use PepperPy to create an AI learning assistant
that can help with learning new topics, answer questions, and provide explanations.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import cast

from pepperpy import PepperPy
from pepperpy.rag.base import Document, RAGProvider
from plugins.rag_memory.provider import InMemoryProvider


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

    # Generate audio summary if TTS is available
    if hasattr(pepper, "tts"):
        print("\nGenerating audio summary...")
        test_mode = os.environ.get("PEPPERPY_DEV__MODE", "").lower() == "true"
        file_ext = "wav" if test_mode else "mp3"

        audio = await pepper.tts.with_text(response.content[:200]).generate()

        audio_file = (
            output_dir / f"{topic.lower().replace(' ', '_')}_summary.{file_ext}"
        )
        audio.save(str(audio_file))
        print(f"Audio summary saved to: {audio_file}")


async def process_question(pepper: PepperPy, question: str) -> None:
    """Process a specific question about a topic."""
    print(f"\nQuestion: {question}")
    print("-" * 50)

    # Search knowledge base for relevant information
    results = await pepper.search(question, limit=3)
    context = (
        "\n".join([result.document.text for result in results])
        if results
        else "No context available."
    )

    # Generate answer using RAG results
    response = await (
        pepper.chat.with_system(
            "You are a helpful tutor. Use the provided context to answer the question."
        )
        .with_user(f"Context: {context}\n\nQuestion: {question}")
        .generate()
    )

    print("\nAnswer:")
    print(response.content)


async def main() -> None:
    """Run the AI learning assistant example."""
    print("AI Learning Assistant Example")
    print("=" * 50)

    # Check if running in test mode
    test_mode = os.environ.get("PEPPERPY_DEV__MODE", "").lower() == "true"
    if test_mode:
        print("\nRunning in DEVELOPMENT MODE")
        print("No actual API calls will be made for LLM and TTS")

    # Initialize PepperPy with required providers
    # Provider configuration comes from environment variables:
    # - LLM provider: PEPPERPY_LLM__PROVIDER (default: openai)
    # - RAG provider: Criado explicitamente como "memory"
    # - TTS provider: PEPPERPY_TTS__PROVIDER (optional)
    async with (
        PepperPy()
        .with_llm("openrouter")
        .with_rag(cast(RAGProvider, InMemoryProvider()))
        .with_tts()
    ) as pepper:
        # Add example documents for RAG
        await pepper.add_documents([
            Document(
                text="Python decorators allow you to modify or extend the behavior of functions or methods without changing their code. They are prefixed with @ and are a powerful metaprogramming feature."
            ),
            Document(
                text="Common use cases for Python decorators include logging, access control, caching, and measuring execution time of functions."
            ),
            Document(
                text="Machine learning is a field of AI that enables systems to learn and improve from experience without being explicitly programmed."
            ),
            Document(
                text="Supervised learning requires labeled training data, while unsupervised learning works with unlabeled data to find patterns or structures."
            ),
        ])

        # Process learning requests
        await process_learning_request(pepper, "Python Decorators")

        # Only process additional examples in production mode to save time during testing
        if not test_mode:
            await process_learning_request(pepper, "Machine Learning Basics")

            # Process specific questions
            await process_question(
                pepper, "What are some common use cases for Python decorators?"
            )
            await process_question(
                pepper,
                "How does supervised learning differ from unsupervised learning?",
            )


if __name__ == "__main__":
    # For automated testing, activate development mode:
    # export PEPPERPY_DEV__MODE=true
    # export PEPPERPY_LLM__PROVIDER=mock (if you have created a mock LLM provider)
    # export PEPPERPY_TTS__PROVIDER=mock
    #
    # For production use, configure your API keys in .env:
    # PEPPERPY_LLM__PROVIDER=openai (or other provider)
    # PEPPERPY_LLM__OPENAI__API_KEY=your_api_key
    # PEPPERPY_TTS__PROVIDER=elevenlabs (or other provider)
    # PEPPERPY_TTS__ELEVENLABS__API_KEY=your_api_key
    asyncio.run(main())
