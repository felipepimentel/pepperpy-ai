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
from typing import Dict, List, Optional

from pepperpy import PepperPy
from pepperpy.content_processing.base import ContentType
from pepperpy.content_processing.providers.document.pymupdf import PyMuPDFProvider
from pepperpy.llm import LLMProvider, OpenAIProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example document path
EXAMPLE_DOC = Path(__file__).parent / "data" / "example.pdf"


class SmartPDFSummarizer:
    """Smart PDF summarizer using PepperPy."""

    def __init__(
        self,
        content_provider: Optional[PyMuPDFProvider] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        """Initialize summarizer.

        Args:
            content_provider: Content processing provider (optional)
            llm_provider: LLM provider (optional)
        """
        self.content_provider = content_provider or PyMuPDFProvider()
        self.llm_provider = llm_provider or OpenAIProvider()

    async def initialize(self) -> None:
        """Initialize providers."""
        await self.content_provider.initialize()
        await self.llm_provider.initialize()

    async def cleanup(self) -> None:
        """Clean up providers."""
        await self.content_provider.cleanup()
        await self.llm_provider.cleanup()

    async def summarize(
        self,
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
        # Process document
        content = await self.content_provider.process(
            file_path,
            extract_text=True,
            extract_metadata=True,
        )

        # Generate prompt
        prompt = self._generate_prompt(content["text"], content["metadata"])

        # Generate summary
        summary = await self.llm_provider.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return {
            "summary": summary,
            "metadata": content["metadata"],
        }

    def _generate_prompt(self, text: str, metadata: Dict) -> str:
        """Generate prompt for LLM.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            Prompt string
        """
        return f"""Please provide a concise summary of the following document:

Title: {metadata.get('title', 'Unknown')}
Author: {metadata.get('author', 'Unknown')}
Pages: {metadata.get('pages', 'Unknown')}

Content:
{text[:2000]}...

Please include:
1. Main topics and key points
2. Important findings or conclusions
3. Relevant context and background
4. Any notable quotes or statistics

Summary:"""


async def main():
    """Run the example."""
    # Create summarizer
    summarizer = SmartPDFSummarizer()

    # Initialize
    await summarizer.initialize()

    try:
        # Summarize document
        logger.info("Summarizing document: %s", EXAMPLE_DOC)
        result = await summarizer.summarize(EXAMPLE_DOC)

        # Print results
        logger.info("\nDocument Summary:")
        logger.info("-" * 40)
        logger.info("Title: %s", result["metadata"].get("title", "Unknown"))
        logger.info("Author: %s", result["metadata"].get("author", "Unknown"))
        logger.info("Pages: %s", result["metadata"].get("pages", "Unknown"))
        logger.info("-" * 40)
        logger.info(result["summary"])

    finally:
        # Cleanup
        await summarizer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
