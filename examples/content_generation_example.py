"""Example script demonstrating content generation workflow with PepperPy."""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run example content generation workflows."""
    print("Content Generation Example")
    print("=" * 50)

    # Initialize PepperPy with LLM support (using PEPPERPY_LLM__PROVIDER from environment)
    async with PepperPy().with_llm() as pepper:
        # Generate article
        print("\nGenerating article...")
        article = await (
            pepper.content.article("Artificial Intelligence Ethics")
            .informative()
            .with_citations()
            .generate()
        )

        print("\nGenerated Article:")
        print(f"Title: {article['title']}")
        print(f"Content (excerpt):\n{article['content'][:300]}...")
        print(f"References: {len(article['references'])} sources")

        # Generate blog post
        print("\nGenerating blog post...")
        blog_post = await (
            pepper.content.blog_post("Getting Started with Python")
            .conversational()
            .engaging()
            .generate()
        )

        print("\nGenerated Blog Post:")
        print(f"Title: {blog_post['title']}")
        print(f"Content (excerpt):\n{blog_post['content'][:300]}...")


if __name__ == "__main__":
    # Using provider specified in PEPPERPY_LLM__PROVIDER environment variable
    # Required environment variables in .env:
    # PEPPERPY_LLM__PROVIDER=openrouter
    # PEPPERPY_LLM__OPENROUTER_API_KEY=your_api_key
    asyncio.run(main())
