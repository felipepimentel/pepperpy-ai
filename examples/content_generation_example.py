"""Example script demonstrating content generation workflow."""

from typing import Any, Dict

from pepperpy.workflow.base import Pipeline, PipelineContext
from pepperpy.workflow.recipes.content_generation import (
    ContentDraftStage,
    ContentOutlineStage,
    ContentRefinementStage,
    TopicResearchStage,
)


def generate_article(topic: str) -> Dict[str, Any]:
    """Generate an article about a topic.

    Args:
        topic: Topic to write about

    Returns:
        Generated article content
    """
    # Create workflow stages
    stages = [
        TopicResearchStage(search_provider="google", num_sources=5),
        ContentOutlineStage(outline_type="article"),
        ContentDraftStage(model="gpt-4", style="informative"),
        ContentRefinementStage(
            refinements=["grammar", "style", "clarity", "citations"]
        ),
    ]

    # Create pipeline
    pipeline = Pipeline(name="article_generation", stages=stages)

    # Create context
    context = PipelineContext()

    # Process topic through pipeline
    result = pipeline.process(topic, context)

    # Extract final content
    article = {
        "title": result["title"],
        "content": result["content"],
        "references": result["references"],
        "metadata": context.metadata,
    }

    return article


def generate_blog_post(topic: str) -> Dict[str, Any]:
    """Generate a blog post about a topic.

    Args:
        topic: Topic to write about

    Returns:
        Generated blog post content
    """
    # Create workflow stages with blog-specific settings
    stages = [
        TopicResearchStage(
            search_provider="google",
            num_sources=3,  # Fewer sources for blog posts
        ),
        ContentOutlineStage(outline_type="blog_post"),
        ContentDraftStage(
            model="gpt-4",
            style="conversational",  # More casual style
        ),
        ContentRefinementStage(
            refinements=[
                "grammar",
                "style",
                "clarity",  # No citations needed for blog posts
            ]
        ),
    ]

    # Create pipeline
    pipeline = Pipeline(name="blog_post_generation", stages=stages)

    # Create context
    context = PipelineContext()

    # Process topic through pipeline
    result = pipeline.process(topic, context)

    # Extract final content
    blog_post = {
        "title": result["title"],
        "content": result["content"],
        "metadata": context.metadata,
    }

    return blog_post


def main() -> None:
    """Run example content generation workflows."""
    # Generate article
    article = generate_article("Artificial Intelligence Ethics")
    print("\nGenerated Article:")
    print(f"Title: {article['title']}")
    print(f"Content:\n{article['content']}")
    print(f"References: {article['references']}")
    print(f"Metadata: {article['metadata']}")

    # Generate blog post
    blog_post = generate_blog_post("Getting Started with Python")
    print("\nGenerated Blog Post:")
    print(f"Title: {blog_post['title']}")
    print(f"Content:\n{blog_post['content']}")
    print(f"Metadata: {blog_post['metadata']}")


if __name__ == "__main__":
    main()
