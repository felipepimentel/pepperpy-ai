#!/usr/bin/env python
"""Advanced Document Processing Example.

This example demonstrates the advanced document processing capabilities
provided by PepperPy, including:

1. Document processing with different providers
2. Caching for improved performance
3. Archive extraction for handling compressed files
4. Batch processing for efficiency
5. Advanced OCR for text extraction from images
6. Text normalization for cleaning and standardizing text
7. Semantic extraction for entity and relationship detection
8. Document filtering for focusing on relevant content
9. Password protection handling for secure documents
10. Integration with RAG for knowledge retrieval

Note: Some features may require additional dependencies.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import PepperPy document processing module
from pepperpy.document_processing import (
    # Base functionality
    get_processor,
    
    # Cache for improved performance
    get_document_cache,
    
    # Archive extraction
    get_archive_handler,
    
    # Batch processing
    get_batch_processor, BatchResult,
    
    # OCR for image text extraction
    get_ocr_processor,
    
    # Text normalization
    get_text_normalizer,
    
    # Semantic extraction
    get_semantic_extractor, Entity, Relationship,
    
    # Document filtering
    get_section_extractor, DocumentFilter, FilterType, FilterOperator,
    
    # Password protection
    get_protected_document_handler,
    
    # RAG integration
    get_document_rag_processor,
)


def setup_example_files() -> Path:
    """Create example files for demonstration.
    
    Returns:
        Path to the directory containing example files
    """
    # Create a temporary directory
    example_dir = Path(tempfile.mkdtemp()) / "document_examples"
    example_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple text file
    text_file = example_dir / "sample.txt"
    with open(text_file, "w") as f:
        f.write("""# Sample Document
        
This is a sample document for demonstrating the document processing capabilities of PepperPy.

## Features

- Document processing with different providers
- Caching for improved performance
- Archive extraction for handling compressed files
- Batch processing for efficiency
- Advanced OCR for text extraction from images
- Text normalization for cleaning and standardizing text
- Semantic extraction for entity and relationship detection
- Document filtering for focusing on relevant content
- Password protection handling for secure documents
- Integration with RAG for knowledge retrieval

## Example Content

John Smith from Acme Corporation visited New York on January 15, 2023 to meet with Sarah Johnson from XYZ Industries.
They discussed a potential partnership worth $1.5 million starting in Q3 2023.

The meeting took place at 123 Broadway St., New York, NY 10001.

Contact information:
- john.smith@acme.com
- (555) 123-4567
- https://www.acmecorp.com
        """)
    
    # Create a markdown file
    md_file = example_dir / "technical.md"
    with open(md_file, "w") as f:
        f.write("""# Technical Documentation

## System Architecture

The system uses a microservices architecture with the following components:

1. API Gateway
2. Authentication Service
3. User Service
4. Document Processing Service
5. Analytics Service

## Database Schema

| Table | Primary Key | Description |
|-------|------------|-------------|
| users | user_id | Stores user information |
| documents | doc_id | Stores document metadata |
| permissions | perm_id | Stores access permissions |

## Code Example

```python
def process_document(doc_id: str) -> Dict[str, Any]:
    """Process a document and return the results."""
    # Load document
    document = Document.get(doc_id)
    
    # Process document
    result = processor.process(document)
    
    # Store results
    result.save()
    
    return result.to_dict()
```
        """)
    
    print(f"Example files created in: {example_dir}")
    return example_dir


def demo_basic_processing(example_dir: Path) -> None:
    """Demonstrate basic document processing."""
    print("\n=== Basic Document Processing ===")
    
    # Get document processor
    processor = get_processor()
    
    # Process text file
    text_file = example_dir / "sample.txt"
    print(f"Processing text file: {text_file}")
    result = processor.process_document(text_file)
    
    # Print extracted text (truncated)
    text = result.get("text", "")
    print(f"Extracted text (first 100 chars): {text[:100]}...")
    
    # Print metadata
    print(f"Metadata: {result.get('metadata', {})}")


def demo_caching(example_dir: Path) -> None:
    """Demonstrate document caching."""
    print("\n=== Document Caching ===")
    
    # Get document cache
    cache = get_document_cache()
    
    # Get document processor
    processor = get_processor()
    
    # Process file first time (cache miss)
    text_file = example_dir / "sample.txt"
    print(f"Processing file (first time): {text_file}")
    
    # Generate cache key
    cache_key = cache.get_cache_key(
        file_path=text_file,
        provider_name="default",
        operation="extract_text",
    )
    
    # Check if in cache (should be a miss)
    cached_result = cache.get(cache_key)
    print(f"Cache hit: {cached_result is not None}")
    
    # Process file
    start_time = __import__('time').time()
    result = processor.process_document(text_file)
    processing_time = __import__('time').time() - start_time
    
    # Store in cache
    cache.set(cache_key, {"text": result.get("text", "")})
    
    # Process again (cache hit)
    print(f"Processing file (second time): {text_file}")
    cached_result = cache.get(cache_key)
    print(f"Cache hit: {cached_result is not None}")
    
    # Print cache statistics
    print(f"Cache stats: {cache.get_stats()}")


def demo_text_normalization(example_dir: Path) -> None:
    """Demonstrate text normalization."""
    print("\n=== Text Normalization ===")
    
    # Get text normalizer
    normalizer = get_text_normalizer(
        transformations=[
            "normalize_unicode",
            "normalize_whitespace",
            "remove_control_chars",
            "fix_line_breaks",
            "fix_spacing",
        ]
    )
    
    # Read text file
    text_file = example_dir / "sample.txt"
    with open(text_file, "r") as f:
        text = f.read()
    
    # Normalize text
    normalized_text = normalizer.normalize(text)
    
    # Print sample before and after
    print("Original text (first 100 chars):")
    print(text[:100])
    print("Normalized text (first 100 chars):")
    print(normalized_text[:100])
    
    # Show specialized transformations
    print("\nRemoving PII:")
    pii_normalizer = get_text_normalizer(
        transformations=["redact_pii"]
    )
    redacted_text = pii_normalizer.normalize(text)
    for line in redacted_text.split("\n"):
        if "[" in line:  # Show only lines with redactions
            print(line)


def demo_semantic_extraction(example_dir: Path) -> None:
    """Demonstrate semantic extraction."""
    print("\n=== Semantic Extraction ===")
    
    # Skip if spaCy is not available
    try:
        import spacy
        spacy_available = True
    except ImportError:
        spacy_available = False
        print("spaCy is not available. Skipping semantic extraction demo.")
        return
    
    # Get semantic extractor
    extractor = get_semantic_extractor(
        extract_relationships=True
    )
    
    # Read text file
    text_file = example_dir / "sample.txt"
    with open(text_file, "r") as f:
        text = f.read()
    
    # Extract entities and relationships
    result = extractor.process_text(text)
    
    # Print entities
    print(f"Found {len(result.entities)} entities:")
    for entity in result.entities[:5]:  # Show only first 5
        print(f" - {entity}")
    
    if len(result.entities) > 5:
        print(f"   ... and {len(result.entities) - 5} more")
    
    # Print relationships
    print(f"Found {len(result.relationships)} relationships:")
    for rel in result.relationships[:3]:  # Show only first 3
        print(f" - {rel}")
    
    if len(result.relationships) > 3:
        print(f"   ... and {len(result.relationships) - 3} more")


def demo_section_extraction(example_dir: Path) -> None:
    """Demonstrate section extraction and filtering."""
    print("\n=== Section Extraction and Filtering ===")
    
    # Get section extractor
    section_extractor = get_section_extractor()
    
    # Read markdown file
    md_file = example_dir / "technical.md"
    with open(md_file, "r") as f:
        text = f.read()
    
    # Extract sections
    sections = section_extractor.extract_sections(text)
    
    # Print sections
    print(f"Found sections:")
    for heading in sections.get("headings", []):
        print(f" - {heading}")
    
    # Extract specific section
    system_arch = section_extractor.extract_section_by_name(text, "System Architecture")
    if system_arch:
        print("\nSystem Architecture section:")
        print(system_arch[:100] + "...")
    
    # Extract all code blocks
    code_blocks = section_extractor.extract_section_by_type(text, "code_block")
    print(f"\nFound {len(code_blocks)} code blocks")
    
    # Create document filter
    filter = DocumentFilter()
    filter.add_content_filter("microservices", operator=FilterOperator.CONTAINS)
    
    # Create a document dict for filtering
    doc = {
        "content": text,
        "sections": {name: section["content"] for name, section in sections.get("sections", {}).items()}
    }
    
    # Apply filter
    matches = filter.matches(doc)
    print(f"Document contains 'microservices': {matches}")
    
    # Add another filter condition
    filter.add_content_filter("blockchain", operator=FilterOperator.CONTAINS)
    filter.match_all = True  # Require all conditions to match
    
    # Apply filter again
    matches = filter.matches(doc)
    print(f"Document contains both 'microservices' and 'blockchain': {matches}")


def demo_batch_processing(example_dir: Path) -> None:
    """Demonstrate batch processing."""
    print("\n=== Batch Processing ===")
    
    # Get batch processor
    batch_processor = get_batch_processor(max_workers=2)
    
    # Get document processor
    processor = get_processor()
    
    # Create a function for batch processing
    def process_file(file_path):
        result = processor.process_document(file_path)
        return True
    
    # Get list of files
    files = list(example_dir.glob("*.*"))
    print(f"Processing {len(files)} files in batch")
    
    # Process files in batch
    result = batch_processor.process_files(
        file_paths=files,
        processor_func=process_file,
    )
    
    # Print results
    print(f"Batch processing result: {result}")
    print(f" - Success: {result.success_count}/{result.total_count} ({result.success_rate:.1f}%)")
    print(f" - Duration: {result.duration:.2f} seconds")


def demo_rag_integration(example_dir: Path) -> None:
    """Demonstrate RAG integration."""
    print("\n=== RAG Integration ===")
    
    # Check if RAG module is available
    try:
        from pepperpy import rag
        rag_available = True
    except ImportError:
        rag_available = False
        print("RAG module is not available. Skipping RAG integration demo.")
        print("You can install RAG support with: pip install pepperpy[rag]")
        return
    
    try:
        # Get document RAG processor
        rag_processor = get_document_rag_processor()
        
        # Process files
        collection_name = "example_docs"
        print(f"Processing files and indexing in collection: {collection_name}")
        
        # Process each file
        for file_path in example_dir.glob("*.*"):
            print(f" - Processing {file_path.name}")
            result = rag_processor.process_document(
                document_path=file_path,
                collection_name=collection_name,
            )
            print(f"   Indexed {result['num_chunks']} chunks")
        
        # Query the indexed documents
        query = "What is the system architecture?"
        print(f"\nQuerying: '{query}'")
        result = rag_processor.query(
            query_text=query,
            collection_name=collection_name,
            num_results=2,
        )
        
        # Print results
        print(f"Found {result['num_results']} relevant chunks:")
        for i, item in enumerate(result["results"]):
            print(f"\nResult {i+1}:")
            print(f"Source: {item['source']}")
            print(f"Content: {item['content'][:150]}...")
    
    except Exception as e:
        print(f"Error in RAG integration demo: {e}")


def main() -> None:
    """Run the document processing examples."""
    print("Advanced Document Processing Examples")
    print("====================================")
    
    # Setup example files
    example_dir = setup_example_files()
    
    try:
        # Run demonstrations
        demo_basic_processing(example_dir)
        demo_caching(example_dir)
        demo_text_normalization(example_dir)
        demo_semantic_extraction(example_dir)
        demo_section_extraction(example_dir)
        demo_batch_processing(example_dir)
        demo_rag_integration(example_dir)
        
        print("\n=== Example Complete ===")
        print(f"Example files are in: {example_dir}")
        print("You can delete this directory when you're done.")
    
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    main() 