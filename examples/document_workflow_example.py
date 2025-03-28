#!/usr/bin/env python
"""Example of using document processing workflow stages.

This script demonstrates how to use the simplified document processing
workflow stages for basic document processing capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

# Import only the workflow components we need
from pepperpy.workflow.recipes.document_processing import (
    DocumentClassificationStage,
    MetadataExtractionStage,
    TextExtractionStage,
)


# Create a simple context class if pepperpy.workflow.base can't be imported
@dataclass
class SimpleContext:
    """Simple context for pipeline execution."""

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in data."""
        self.data[key] = value


async def setup_example_files():
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


async def demo_text_extraction(file_path):
    """Demonstrate text extraction from document."""
    print("\n=== Text Extraction Demo ===")

    # Create context
    context = SimpleContext()

    # Create text extraction stage
    extractor = TextExtractionStage()
    await extractor._initialize()

    # Process document
    text = await extractor.process(file_path, context)

    print(f"Extracted text from {file_path.name} ({len(text)} chars):")
    print(f"{text[:150]}...")  # Print first 150 chars
    print(f"Metadata: {context.metadata}")

    return text


async def demo_document_classification(text):
    """Demonstrate document classification."""
    print("\n=== Document Classification Demo ===")

    # Create context
    context = SimpleContext()

    # Create classification stage
    classifier = DocumentClassificationStage()
    await classifier._initialize()

    # Classify document
    results = await classifier.process(text, context)

    print("Classification results:")
    print(f"  Document type: {results['document_type']}")
    print(f"  Content category: {results['content_category']}")
    print(f"  Language: {results['language']}")
    print(f"  Confidence: {results['confidence']}")
    print(f"Context metadata: {context.metadata}")

    return results


async def demo_metadata_extraction(text):
    """Demonstrate metadata extraction."""
    print("\n=== Metadata Extraction Demo ===")

    # Create context
    context = SimpleContext()

    # Create metadata extraction stage
    extractor = MetadataExtractionStage()
    await extractor._initialize()

    # Extract metadata
    metadata = await extractor.process(text, context)

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

    return metadata


async def create_pipeline_workflow():
    """Demonstrate how to create a complete document processing pipeline."""
    print("\n=== Complete Document Processing Pipeline ===")

    # Define pipeline stages
    text_extraction = TextExtractionStage()
    classification = DocumentClassificationStage()
    metadata_extraction = MetadataExtractionStage()

    # Initialize all stages
    await text_extraction._initialize()
    await classification._initialize()
    await metadata_extraction._initialize()

    # Create shared context
    context = SimpleContext()

    # Process example document
    example_dir = await setup_example_files()
    document_path = example_dir / "technical.md"

    print(f"Processing document: {document_path}")

    # Execute pipeline steps
    text = await text_extraction.process(document_path, context)
    print(f"Step 1: Extracted {len(text)} characters of text")

    classification_results = await classification.process(text, context)
    print(
        f"Step 2: Classified document as {classification_results['document_type']} / {classification_results['content_category']}"
    )

    metadata = await metadata_extraction.process(text, context)
    print(f"Step 3: Extracted {len(metadata)} metadata fields")

    # Print final context
    print("\nFinal pipeline context:")
    for key, value in context.metadata.items():
        print(f"  {key}: {value}")


async def main():
    """Run document processing workflow examples."""
    try:
        # Create example files
        example_dir = await setup_example_files()
        print(f"Created example files in {example_dir}")

        # Text extraction example
        text_file = example_dir / "sample.txt"
        extracted_text = await demo_text_extraction(text_file)

        # Classification example
        await demo_document_classification(extracted_text)

        # Metadata extraction example
        await demo_metadata_extraction(extracted_text)

        # Complete pipeline example
        await create_pipeline_workflow()

    except Exception as e:
        print(f"Error during demonstration: {e}")
    finally:
        print("\nExample completed.")


if __name__ == "__main__":
    asyncio.run(main())
