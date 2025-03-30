#!/usr/bin/env python
"""Example of using document processing workflow stages.

This script demonstrates how to use the simplified document processing
workflow stages for basic document processing capabilities.
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy, create_workflow_provider


async def process_document(file_path: Path) -> None:
    """Process a single document with individual stages."""
    # Initialize workflow provider
    workflow = create_workflow_provider("local")

    async with PepperPy().with_workflow(workflow) as pepper:
        # Extract text
        text = await pepper.document.from_file(file_path).extract_text().execute()
        print(f"Extracted text (excerpt):\n{text[:150]}...")

        # Classify document
        classification = await pepper.document.from_text(text).classify().execute()
        print("\nClassification results:")
        print(f"  Document type: {classification['document_type']}")
        print(f"  Content category: {classification['content_category']}")
        print(f"  Language: {classification['language']}")

        # Extract metadata
        metadata = await pepper.document.from_text(text).extract_metadata().execute()
        print("\nExtracted metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")


async def process_document_pipeline(file_path: Path) -> None:
    """Process a document using a complete pipeline."""
    # Initialize workflow provider
    workflow = create_workflow_provider("local")

    async with PepperPy().with_workflow(workflow) as pepper:
        # Process document through complete pipeline
        result = await (
            pepper.document.from_file(file_path)
            .extract_text()
            .classify()
            .extract_metadata()
            .execute()
        )

        print("\nPipeline results:")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Document type: {result['classification']['document_type']}")
        print(f"Content category: {result['classification']['content_category']}")
        print("\nExtracted metadata:")
        for key, value in result["metadata"].items():
            print(f"  {key}: {value}")


async def main() -> None:
    """Run document processing workflow examples."""
    # Example document path (in practice, this would be provided by the user)
    doc_path = Path("examples/data/sample.pdf")

    print("Processing document with individual stages...")
    await process_document(doc_path)

    print("\nProcessing document with complete pipeline...")
    await process_document_pipeline(doc_path)


if __name__ == "__main__":
    asyncio.run(main())
