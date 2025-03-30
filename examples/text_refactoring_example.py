"""Example demonstrating intelligent text refactoring with PepperPy.

This example shows how to use PepperPy to improve large texts like ebooks by:
1. Breaking text into semantic chunks
2. Analyzing each chunk for improvements
3. Maintaining consistency across refactored sections
4. Preserving the original style and knowledge
"""

import asyncio
import json
from typing import Dict, List

from pepperpy import PepperPy
from pepperpy.llm import create_provider as create_llm_provider


async def analyze_text_structure(text: str) -> Dict[str, List[str]]:
    """Analyze text structure and identify semantic sections.

    Args:
        text: Large text to analyze

    Returns:
        Dict with sections and their chunks
    """
    # Create LLM provider
    llm_provider = create_llm_provider("openrouter")

    # Initialize PepperPy with LLM support
    async with PepperPy().with_llm(llm_provider) as pepper:
        # First, get high-level structure
        structure = await (
            pepper.chat.with_system("You are a text analysis expert.")
            .with_user(
                "Analyze this text and identify main sections. "
                "Return a JSON with section names as keys and their line ranges as values:\n\n"
                + text
            )
            .generate()
        )

        # Parse JSON response
        sections = {}
        structure_dict = json.loads(structure.content)

        # Then break each section into semantic chunks
        for section, lines in structure_dict.items():
            section_text = "\n".join(text.split("\n")[lines[0] : lines[1]])
            chunks = await (
                pepper.chat.with_system("You are a text analysis expert.")
                .with_user(
                    "Break this section into semantic chunks of related content. "
                    "Return a JSON array of chunks. "
                    "Each chunk should be self-contained but connected to the whole:\n\n"
                    + section_text
                )
                .generate()
            )
            sections[section] = json.loads(chunks.content)

        return sections


async def improve_chunk(chunk: str, style_guide: str) -> str:
    """Improve a single chunk while maintaining style and essence.

    Args:
        chunk: Text chunk to improve
        style_guide: Writing style to maintain

    Returns:
        Improved chunk
    """
    # Create LLM provider
    llm_provider = create_llm_provider("openrouter")

    # Initialize PepperPy with LLM support
    async with PepperPy().with_llm(llm_provider) as pepper:
        # Learn the style guide
        style_response = await (
            pepper.chat.with_system("You are a writing style expert.")
            .with_user(f"Learn and apply this style guide:\n\n{style_guide}")
            .generate()
        )

        # Analyze for improvements
        analysis = await (
            pepper.chat.with_system("You are a text improvement expert.")
            .with_user(
                "Analyze this text chunk and suggest improvements while maintaining style:\n\n"
                "1. Remove redundancies\n"
                "2. Clarify confusing parts\n"
                "3. Improve flow and transitions\n"
                "4. Keep the same technical depth\n\n" + chunk
            )
            .generate()
        )

        # Apply improvements
        improved = await (
            pepper.chat.with_system("You are a text improvement expert.")
            .with_user(
                "Rewrite this chunk incorporating the suggested improvements. "
                "Maintain the original style, technical depth, and key information:\n\n"
                f"Original: {chunk}\n\n"
                f"Analysis: {analysis.content}\n\n"
                f"Style Guide: {style_guide}"
            )
            .generate()
        )

        return improved.content


async def refactor_large_text(text: str, style_guide: str) -> str:
    """Refactor and improve a large text while maintaining its essence.

    Args:
        text: Large text to refactor
        style_guide: Writing style to maintain

    Returns:
        Improved text
    """
    # Break into semantic sections
    print("Analyzing text structure...")
    sections = await analyze_text_structure(text)

    # Improve each section while maintaining consistency
    print("\nImproving sections...")
    improved_sections = {}
    for section, chunks in sections.items():
        print(f"\nProcessing section: {section}")
        improved_chunks = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}/{len(chunks)}...")
            improved = await improve_chunk(chunk, style_guide)
            improved_chunks.append(improved)
        improved_sections[section] = improved_chunks

    # Combine sections with proper transitions
    llm_provider = create_llm_provider("openrouter")
    async with PepperPy().with_llm(llm_provider) as pepper:
        print("\nCombining sections...")
        final_text = await (
            pepper.chat.with_system("You are a text organization expert.")
            .with_user(
                "Combine these improved sections into a cohesive text. "
                "Add smooth transitions between sections while maintaining flow:\n\n"
                + str(improved_sections)
            )
            .generate()
        )

        return final_text.content


async def main() -> None:
    """Run the example."""
    # Sample large text (in practice, this would be loaded from a file)
    text = """
    Chapter 1: Introduction to Machine Learning
    
    Machine learning is a fascinating field that combines statistics, 
    computer science, and data analysis. It's a field that's growing rapidly
    and has many applications. Machine learning is used in many areas and
    has lots of uses in different domains. The applications are numerous
    and varied across different fields.
    
    The history of machine learning goes back many years. It started
    with early statistical methods. Then it evolved over time. Many
    researchers contributed to its development. The field grew as
    computers became more powerful. Now it's a major area of study.
    
    [... many more paragraphs ...]
    """

    # Style guide (in practice, this would be more comprehensive)
    style_guide = """
    Writing Style Guide:
    1. Be concise but thorough
    2. Use active voice
    3. Maintain technical accuracy
    4. Avoid redundancy
    5. Use clear transitions
    6. Keep consistent terminology
    """

    print("Text Refactoring Example")
    print("=" * 50)

    # Refactor the text
    improved_text = await refactor_large_text(text, style_guide)

    print("\nImproved Text:")
    print("-" * 50)
    print(improved_text)


if __name__ == "__main__":
    # Using openrouter provider (configured in .env)
    asyncio.run(main())
