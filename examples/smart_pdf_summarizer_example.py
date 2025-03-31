"""Example of using PepperPy to create a smart PDF summarizer.

This example demonstrates how to:
1. Process PDF documents using content processing
2. Extract text and metadata
3. Use LLM to generate summaries
4. Handle different types of content
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict

from pepperpy import PepperPy
from pepperpy.content.base import create_processor
from pepperpy.llm import create_provider as create_llm_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example document path
EXAMPLE_DOC = Path(__file__).parent / "data" / "sample.pdf"


async def summarize_pdf(
    file_path: Path,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> Dict:
    """Summarize PDF document.

    Args:
        file_path: Path to PDF file
        max_tokens: Maximum tokens for summary
        temperature: Temperature for LLM

    Returns:
        Dictionary with summary and metadata
    """
    # Create LLM provider
    llm_provider = create_llm_provider(
        "openrouter", max_tokens=max_tokens, temperature=temperature
    )

    # Create content processor
    content_processor = await create_processor(
        "document", provider_name="pymupdf", extract_images=False
    )

    # Initialize PepperPy with LLM
    async with PepperPy().with_llm(llm_provider) as pepper:
        # Process document using content processor directly
        result = await content_processor.process(file_path)

        # Extract text and metadata
        text = result.text or ""
        metadata = result.metadata or {}

        # Generate summary
        summary = await (
            pepper.chat.with_system("You are a document summarization expert.")
            .with_user(
                f"""Please provide a concise summary of the following document:

Title: {metadata.get("title", "Unknown")}
Author: {metadata.get("author", "Unknown")}
Pages: {metadata.get("page_count", "Unknown")}

Content:
{text[:2000]}...

Please include:
1. Main topics and key points
2. Important findings or conclusions
3. Relevant context and background
4. Any notable quotes or statistics

Summary:"""
            )
            .generate()
        )

        return {
            "summary": summary.content,
            "metadata": metadata,
        }


async def main():
    """Run the example."""
    try:
        # Summarize document
        logger.info("Summarizing document: %s", EXAMPLE_DOC)
        result = await summarize_pdf(EXAMPLE_DOC)

        # Print results
        logger.info("\nDocument Summary:")
        logger.info("-" * 40)
        logger.info("Title: %s", result["metadata"].get("title", "Unknown"))
        logger.info("Author: %s", result["metadata"].get("author", "Unknown"))
        logger.info("Pages: %s", result["metadata"].get("pages", "Unknown"))
        logger.info("-" * 40)
        logger.info(result["summary"])

    except Exception as e:
        logger.error("Error during summarization: %s", e)


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    asyncio.run(main())
