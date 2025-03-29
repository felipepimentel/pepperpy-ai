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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example document path
EXAMPLE_DOC = Path(__file__).parent / "data" / "example.pdf"


async def main():
    """Run the example."""
    # Initialize PepperPy with content processing
    async with (
        PepperPy()
        .with_content()
        .with_content_config(
            providers={
                "pymupdf": {
                    "extract_images": False,
                    "extract_tables": False,
                }
            }
        )
    ) as pepper:
        # Extract text
        logger.info("Extracting text...")
        text_result = await (
            pepper.content.from_file(EXAMPLE_DOC).extract_text().execute()
        )
        logger.info("Extracted text: %s", text_result["text"][:100] + "...")

        # Extract metadata
        logger.info("Extracting metadata...")
        metadata_result = await (
            pepper.content.from_file(EXAMPLE_DOC).with_metadata().execute()
        )
        logger.info("Extracted metadata: %s", metadata_result["metadata"])

        # Process with both text and metadata
        logger.info("Processing document...")
        result = await (
            pepper.content.from_file(EXAMPLE_DOC)
            .extract_text()
            .with_metadata()
            .execute()
        )
        logger.info("Processed document:")
        logger.info("- Text: %s", result["text"][:100] + "...")
        logger.info("- Metadata: %s", result["metadata"])

        # Get provider capabilities
        logger.info("Provider capabilities: %s", pepper.content.get_capabilities())


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
