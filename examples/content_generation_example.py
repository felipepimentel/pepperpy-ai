"""Example script demonstrating content generation workflow with PepperPy."""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run example content generation workflows."""
    print("Content Generation Example")
    print("=" * 50)

    # Initialize PepperPy with LLM support
    async with (
        PepperPy()
        .with_llm()
        .with_llm_config(
            temperature=0.7,
            max_tokens=1000,
        )
    ) as pepper:
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
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    asyncio.run(main())
