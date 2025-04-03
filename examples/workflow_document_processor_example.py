#!/usr/bin/env python3
"""Example demonstrating document processing with PepperPy.

This example shows how to use PepperPy to extract text and metadata from documents.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
OUTPUT_DIR = EXAMPLES_DIR / "output"

# Create directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Create sample document if needed
def create_sample_document():
    """Create a sample document for testing if none exists."""
    sample_file = DATA_DIR / "sample.txt"
    if not list(DATA_DIR.glob("**/*.pdf")) and not sample_file.exists():
        print("Creating a sample text file...")
        with open(sample_file, "w") as f:
            f.write(
                "This is a sample document for testing the document processor workflow.\n"
                "It contains multiple lines of text that can be processed.\n"
                "PepperPy makes it easy to work with different document types."
            )


async def main():
    """Run the document processing example."""
    print("Document Processing Example")
    print("=" * 50)

    # Create sample document if needed
    create_sample_document()

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Find documents to process
        sample_files = list(DATA_DIR.glob("**/*.pdf"))
        if not sample_files:
            sample_files = list(DATA_DIR.glob("**/*.txt"))

        if not sample_files:
            print("No documents found for processing.")
            return

        # Process a single document
        doc_path = sample_files[0]
        print(f"\nProcessing document: {doc_path}")

        # Execute document processing
        result = await app.execute(
            query="Extract text and metadata from document",
            context={"document_path": str(doc_path)},
        )

        print(f"Processing result: {result}")

        # Process multiple documents if available
        if len(sample_files) > 1:
            print(f"\nProcessing batch of {min(3, len(sample_files))} documents...")

            # Convert Path objects to strings
            doc_paths = [str(path) for path in sample_files[:3]]

            # Execute batch processing
            batch_result = await app.execute(
                query="Process multiple documents",
                context={"document_paths": doc_paths},
            )

            print(f"Batch processing result: {batch_result}")

        # Process a directory
        print(f"\nProcessing all documents in {DATA_DIR}")

        # Execute directory processing
        dir_result = await app.execute(
            query="Process all documents in directory",
            context={"directory_path": str(DATA_DIR)},
        )

        print(f"Directory processing result: {dir_result}")

    finally:
        # Clean up
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
