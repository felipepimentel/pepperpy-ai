#!/usr/bin/env python
"""Document processing example for PepperPy.

This example demonstrates how to use the document processing module
to extract text and metadata from various document types.
"""

import asyncio
import os
from pathlib import Path

import pepperpy as pp
from pepperpy.document_processing import DocumentType


async def process_document(file_path, provider_type=None):
    """Process a document using the specified provider."""
    print(f"\n=== Processing document: {file_path} ===")

    # Create document processing provider
    provider = pp.create_document_processing_provider(provider_type)

    # Initialize the provider
    await provider.initialize()

    try:
        # Get document type from file extension
        doc_type = DocumentType.from_extension(file_path.suffix)
        print(f"Document type: {doc_type.name}")

        # Check if provider supports this document type
        if not provider.supports_document_type(doc_type):
            print(
                f"Provider {provider.name} does not support {doc_type.name} documents."
            )
            return

        # Extract text from document
        print("Extracting text...")
        text = await provider.extract_text(file_path)
        print(f"Text (first 200 chars): {text[:200]}...")

        # Extract metadata from document
        print("\nExtracting metadata...")
        metadata = await provider.extract_metadata(file_path)
        print(f"Title: {metadata.title or 'N/A'}")
        print(f"Author: {metadata.author or 'N/A'}")
        print(f"Creation date: {metadata.creation_date or 'N/A'}")
        print(f"Page count: {metadata.page_count or 'N/A'}")
        print(f"Word count: {metadata.word_count or 'N/A'}")

        # Process document to get all content
        print("\nProcessing full document...")
        content = await provider.process_document(
            file_path, extract_images=True, extract_tables=True
        )

        # Print info about extracted images
        if content.images:
            print(f"\nExtracted {len(content.images)} images")
            for i, img in enumerate(content.images[:3]):  # Show just first 3
                print(f"  Image {i + 1}: {img.get('width')}x{img.get('height')} pixels")

        # Print info about extracted tables
        if content.tables:
            print(f"\nExtracted {len(content.tables)} tables")
            for i, table in enumerate(content.tables[:3]):  # Show just first 3
                print(
                    f"  Table {i + 1}: {table.get('rows', 0)} rows x {table.get('columns', 0)} columns"
                )

    except Exception as e:
        print(f"Error processing document: {e}")
    finally:
        # Clean up resources
        await provider.cleanup()


async def run_examples():
    """Run document processing examples."""
    # Create directories for documents and output
    data_dir = Path("data/documents")
    os.makedirs(data_dir, exist_ok=True)

    # Check for example PDF
    example_pdf = data_dir / "example.pdf"
    if not example_pdf.exists():
        print(f"Example PDF not found at {example_pdf}")
        print("Creating a simple text file instead...")
        # Create simple text file as fallback
        example_text = data_dir / "example.txt"
        with open(example_text, "w") as f:
            f.write("This is an example text file.\n\n")
            f.write("It contains multiple paragraphs.\n\n")
            f.write(
                "This is used to demonstrate the document processing capabilities of PepperPy."
            )
        example_file = example_text
    else:
        example_file = example_pdf

    # Process document with default provider
    await process_document(example_file)

    # Try with specific providers
    for provider_type in ["pymupdf", "langchain"]:
        try:
            await process_document(example_file, provider_type)
        except ValueError as e:
            print(f"\nCouldn't use {provider_type} provider: {e}")


async def main():
    """Run the document processing example."""
    print("PepperPy Document Processing Example")
    print("-" * 40)
    await run_examples()
    print("\nExample completed.")


if __name__ == "__main__":
    asyncio.run(main())
