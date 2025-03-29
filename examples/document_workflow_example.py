#!/usr/bin/env python
"""Example of using document processing workflow stages.

This script demonstrates how to use the simplified document processing
workflow stages for basic document processing capabilities.
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy


async def setup_example_files() -> Path:
    """Create example files for demonstration."""
    # Create a sample directory
    example_dir = Path("example_docs")
    example_dir.mkdir(exist_ok=True)

    # Create a sample text file
    text_file = example_dir / "sample.txt"
    with open(text_file, "w") as f:
        f.write("""
        PepperPy Framework Documentation
        
        This is a sample document for testing document processing capabilities.
        The PepperPy framework provides comprehensive tools for document processing,
        including text extraction, OCR, classification, and metadata extraction.
        
        Contact: support@pepperpy.ai
        Date: 01/01/2023
        """)

    # Create a sample markdown file
    md_file = example_dir / "technical.md"
    with open(md_file, "w") as f:
        f.write("""
        # Technical Specification
        
        ## Overview
        
        This technical specification outlines the requirements for the new financial 
        reporting system to be implemented by XYZ Corporation.
        
        ## Requirements
        
        1. The system must generate monthly financial reports
        2. Reports must be exportable in PDF, Excel, and CSV formats
        3. Data must be encrypted during transfer
        
        ## Budget
        
        The project budget is $150,000 with a timeline of 6 months.
        
        ## Contact
        
        For technical questions, contact @john.smith at #XYZCorp.
        """)

    return example_dir


async def process_single_document(file_path: Path) -> None:
    """Process a single document with individual stages."""
    print(f"\nProcessing document: {file_path}")

    async with (
        PepperPy()
        .with_workflow()
        .with_workflow_config(
            providers={
                "text_extractor": {"type": "basic"},
                "classifier": {"type": "llm"},
                "metadata_extractor": {"type": "llm"},
            }
        )
    ) as pepper:
        # Extract text
        print("\n=== Text Extraction ===")
        text = await (
            pepper.document
            .from_file(file_path)
            .extract_text()
            .execute()
        )
        print(f"Extracted {len(text)} characters of text:")
        print(f"{text[:150]}...")

        # Classify document
        print("\n=== Document Classification ===")
        classification = await (
            pepper.document
            .from_text(text)
            .classify()
            .execute()
        )
        print("Classification results:")
        print(f"  Document type: {classification['document_type']}")
        print(f"  Content category: {classification['content_category']}")
        print(f"  Language: {classification['language']}")
        print(f"  Confidence: {classification['confidence']}")

        # Extract metadata
        print("\n=== Metadata Extraction ===")
        metadata = await (
            pepper.document
            .from_text(text)
            .extract_metadata()
            .execute()
        )
        print("Extracted metadata:")
        if "dates" in metadata:
            print(f"  Dates: {metadata['dates']}")
        if "entities" in metadata:
            print("  Entities:")
            for entity_type, entities in metadata["entities"].items():
                if entities:
                    print(f"    {entity_type}: {entities}")
        if "keywords" in metadata:
            print(f"  Keywords: {metadata['keywords']}")


async def process_document_pipeline(file_path: Path) -> None:
    """Process a document using a complete pipeline."""
    print(f"\nProcessing document with pipeline: {file_path}")

    async with (
        PepperPy()
        .with_workflow()
        .with_workflow_config(
            providers={
                "text_extractor": {"type": "basic"},
                "classifier": {"type": "llm"},
                "metadata_extractor": {"type": "llm"},
            }
        )
    ) as pepper:
        # Process document through complete pipeline
        result = await (
            pepper.document
            .from_file(file_path)
            .extract_text()
            .classify()
            .extract_metadata()
            .execute()
        )

        print("\nPipeline results:")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Document type: {result['classification']['document_type']}")
        print(f"Content category: {result['classification']['content_category']}")
        print(f"Metadata fields: {len(result['metadata'])} extracted")

        # Print metadata details
        print("\nExtracted metadata:")
        for key, value in result["metadata"].items():
            print(f"  {key}: {value}")


async def main() -> None:
    """Run document processing workflow examples."""
    try:
        # Create example files
        example_dir = await setup_example_files()
        print(f"Created example files in {example_dir}")

        # Process sample.txt with individual stages
        text_file = example_dir / "sample.txt"
        await process_single_document(text_file)

        # Process technical.md with complete pipeline
        md_file = example_dir / "technical.md"
        await process_document_pipeline(md_file)

    except Exception as e:
        print(f"Error during demonstration: {e}")
    finally:
        print("\nExample completed.")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_WORKFLOW__PROVIDER=basic
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    asyncio.run(main())
