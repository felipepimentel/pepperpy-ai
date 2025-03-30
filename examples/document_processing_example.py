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
from pepperpy.content_processing.base import create_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example document path
EXAMPLE_DOC = Path(__file__).parent / "data" / "sample.pdf"


async def main():
    """Run the example."""
    # Create content processor with PyMuPDF provider
    content_processor = await create_processor(
        "document", provider_name="pymupdf", extract_images=False, extract_tables=False
    )

    # Initialize PepperPy
    async with PepperPy() as pepper:
        # Extract text
        logger.info("Extracting text...")
        result = await content_processor.process(EXAMPLE_DOC)
        text_excerpt = result.text[:100] + "..." if result.text else "No text extracted"
        logger.info("Extracted text: %s", text_excerpt)

        # Extract metadata
        logger.info("Extracted metadata: %s", result.metadata)

        # Get provider capabilities
        logger.info("Provider capabilities: %s", content_processor.get_capabilities())


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
