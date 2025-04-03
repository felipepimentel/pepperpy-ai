"""Example demonstrating intelligent text refactoring with PepperPy.

This example shows how to use PepperPy to improve text by analyzing
its structure and content.
"""

import asyncio

from pepperpy import PepperPy

# Sample text to refactor
SAMPLE_TEXT = """Chapter 1: Introduction to Machine Learning
    
Machine learning is a fascinating field that combines statistics, 
computer science, and data analysis. It's a field that's growing rapidly
and has many applications. Machine learning is used in many areas and
has lots of uses in different domains. The applications are numerous
and varied across different fields.
    
The history of machine learning goes back many years. It started
with early statistical methods. Then it evolved over time. Many
researchers contributed to its development. The field grew as
computers became more powerful. Now it's a major area of study.
"""

# Style guide
STYLE_GUIDE = """
Writing Style Guide:
1. Be concise but thorough
2. Use active voice
3. Maintain technical accuracy
4. Avoid redundancy
5. Use clear transitions
6. Keep consistent terminology
"""


async def main():
    """Run the text refactoring example."""
    print("Text Refactoring Example")
    print("=" * 50)

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Analyze text structure
        print("Analyzing text structure...")

        # Execute structure analysis
        structure_result = await app.execute(
            query="Analyze this text structure and identify main sections",
            context={"text": SAMPLE_TEXT},
        )
        print(f"Structure analysis: {structure_result[:100]}...")

        # Improve the text content
        print("\nImproving text content...")

        # Execute text improvement
        improved_text = await app.execute(
            query="Improve this text while following the style guide",
            context={"text": SAMPLE_TEXT, "style_guide": STYLE_GUIDE},
        )

        # Display results
        print("\nImproved Text:")
        print("-" * 50)
        print(improved_text)

    finally:
        # Clean up resources
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
