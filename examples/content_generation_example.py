"""Example script demonstrating content generation workflow with PepperPy."""

import asyncio
from typing import Any, Dict

import pepperpy
from pepperpy.llm import Message, MessageRole


async def generate_article(topic: str) -> Dict[str, Any]:
    """Generate an article about a topic.

    Args:
        topic: Topic to write about

    Returns:
        Generated article content
    """
    # Initialize PepperPy with fluent API
    pepper = pepperpy.PepperPy().with_llm()

    async with pepper:
        # Generate the article using the correct LLM API
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are a professional content writer specializing in informative articles. "
                    "Write a well-structured article on the provided topic. "
                    "Include proper citations and references to support your points."
                ),
            ),
            Message(
                role=MessageRole.USER,
                content=f"Write an informative article about: {topic}",
            ),
        ]

        result = await pepper.llm.generate(messages)

        # Format response into article structure
        article = {
            "title": topic,
            "content": result.content,
            "references": ["Example Reference 1", "Example Reference 2"],
            "metadata": {
                "style": "informative",
                "word_count": len(result.content.split()),
            },
        }

        return article


async def generate_blog_post(topic: str) -> Dict[str, Any]:
    """Generate a blog post about a topic.

    Args:
        topic: Topic to write about

    Returns:
        Generated blog post content
    """
    # Initialize PepperPy with fluent API
    pepper = pepperpy.PepperPy().with_llm()

    async with pepper:
        # Generate the blog post using the correct LLM API
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are a conversational blog writer who specializes in engaging content. "
                    "Write a blog post on the provided topic in a friendly, approachable style. "
                    "Use a conversational tone throughout."
                ),
            ),
            Message(
                role=MessageRole.USER,
                content=f"Write an engaging blog post about: {topic}",
            ),
        ]

        result = await pepper.llm.generate(messages)

        # Format response into blog post structure
        blog_post = {
            "title": topic,
            "content": result.content,
            "metadata": {
                "style": "conversational",
                "word_count": len(result.content.split()),
            },
        }

        return blog_post


async def main() -> None:
    """Run example content generation workflows."""
    print("Content Generation Example")
    print("=" * 50)

    # Generate article
    print("\nGenerating article...")
    article = await generate_article("Artificial Intelligence Ethics")

    print("\nGenerated Article:")
    print(f"Title: {article['title']}")
    print(f"Content (excerpt):\n{article['content'][:300]}...")
    print(f"References: {len(article['references'])} sources")

    # Generate blog post
    print("\nGenerating blog post...")
    blog_post = await generate_blog_post("Getting Started with Python")

    print("\nGenerated Blog Post:")
    print(f"Title: {blog_post['title']}")
    print(f"Content (excerpt):\n{blog_post['content'][:300]}...")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    asyncio.run(main())
