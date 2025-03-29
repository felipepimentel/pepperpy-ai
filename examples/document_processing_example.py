#!/usr/bin/env python
"""Example of using the content processing module.

This example demonstrates how to use the content processing module to:
1. Extract text from documents
2. Extract metadata from documents
3. Process documents with different providers
"""

import asyncio
import logging
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.content_processing.base import ContentType
from pepperpy.content_processing.providers.document.pymupdf import PyMuPDFProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example document path
EXAMPLE_DOC = Path(__file__).parent / "data" / "example.pdf"


async def main():
    """Run the example."""
    # Initialize PepperPy
    pp = PepperPy()

    # Create content processor with PyMuPDF provider
    provider = PyMuPDFProvider()

    # Initialize provider
    await provider.initialize()

    try:
        # Extract text
        logger.info("Extracting text...")
        text = await provider.process(
            EXAMPLE_DOC,
            extract_text=True,
            extract_metadata=False,
        )
        logger.info("Extracted text: %s", text[:100] + "...")

        # Extract metadata
        logger.info("Extracting metadata...")
        metadata = await provider.process(
            EXAMPLE_DOC,
            extract_text=False,
            extract_metadata=True,
        )
        logger.info("Extracted metadata: %s", metadata)

        # Process with both text and metadata
        logger.info("Processing document...")
        result = await provider.process(
            EXAMPLE_DOC,
            extract_text=True,
            extract_metadata=True,
        )
        logger.info("Processed document:")
        logger.info("- Text: %s", result["text"][:100] + "...")
        logger.info("- Metadata: %s", result["metadata"])

        # Get provider capabilities
        logger.info("Provider capabilities: %s", provider.get_capabilities())

    finally:
        # Cleanup
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
