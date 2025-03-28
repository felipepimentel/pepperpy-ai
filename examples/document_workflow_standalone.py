#!/usr/bin/env python
"""Standalone document processing workflow example.

This script demonstrates a simplified document processing workflow
without any dependencies on the pepperpy package.
"""

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class Context:
    """Simple context for workflow execution."""

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in data."""
        self.data[key] = value


class PipelineStage:
    """Base class for pipeline stages."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize pipeline stage."""
        self.name = name
        self.description = description

    async def _initialize(self) -> None:
        """Initialize resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def process(self, input_data: Any, context: Context) -> Any:
        """Process input data."""
        raise NotImplementedError("Subclasses must implement process")


class TextExtractionStage(PipelineStage):
    """Stage for extracting text from various document formats."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize text extraction stage."""
        super().__init__(
            name="text_extraction", description="Extract text from documents"
        )
        self._config = kwargs

    async def process(self, document_path: Union[str, Path], context: Context) -> str:
        """Extract text from document."""
        try:
            # Convert to Path object if string
            if isinstance(document_path, str):
                document_path = Path(document_path)

            # Check if file exists
            if not document_path.exists():
                raise ValueError(f"File not found: {document_path}")

            # Get file extension (lowercase)
            ext = document_path.suffix.lower()

            # Set document format in context
            context.metadata["document_format"] = (
                ext[1:] if ext.startswith(".") else ext
            )
            context.metadata["document_path"] = str(document_path)
            context.metadata["document_name"] = document_path.name

            # Extract text based on format
            if ext in [".pdf"]:
                # Try to extract PDF text with PyMuPDF if available
                try:
                    import fitz  # PyMuPDF

                    return self._extract_pdf_with_pymupdf(document_path)
                except ImportError:
                    # Fallback to basic text reading
                    return f"PDF file: {document_path.name} (PDF extraction requires PyMuPDF)"

            elif ext in [".docx", ".doc"]:
                # Try to extract DOCX text with python-docx if available
                try:
                    import docx

                    return self._extract_docx(document_path)
                except ImportError:
                    # Fallback to basic text reading
                    return f"Word document: {document_path.name} (DOCX extraction requires python-docx)"

            elif ext in [".txt", ".md", ".json", ".csv"]:
                # Text file - read directly
                with open(document_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                # Unsupported format
                return f"Unsupported document format: {ext} - {document_path.name}"

        except Exception as e:
            raise ValueError(f"Text extraction failed: {e}")

    def _extract_pdf_with_pymupdf(self, document_path: Path) -> str:
        """Extract text from PDF document using PyMuPDF."""
        import fitz  # PyMuPDF

        pdf = fitz.open(document_path)
        text = ""

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text += page.get_text()
            # Add page separator
            text += f"\n\n--- Page {page_num + 1} ---\n\n"

        return text

    def _extract_docx(self, document_path: Path) -> str:
        """Extract text from DOCX document using python-docx."""
        import docx

        doc = docx.Document(document_path)
        return "\n".join(p.text for p in doc.paragraphs)


class DocumentClassificationStage(PipelineStage):
    """Stage for classifying documents by type and content."""

    def __init__(
        self,
        model: str = "default",
        **kwargs: Any,
    ) -> None:
        """Initialize classification stage."""
        super().__init__(name="classification", description="Classify document content")
        self._model = model
        self._config = kwargs

    async def process(self, text: str, context: Context) -> Dict[str, Any]:
        """Classify document content."""
        try:
            # Perform basic classification
            results = {
                "document_type": self._classify_type(text),
                "content_category": self._classify_category(text),
                "language": self._detect_language(text),
                "confidence": 0.85,  # Placeholder
            }

            # Store metadata
            context.metadata["classification_model"] = self._model
            context.metadata["classification_results"] = results

            return results

        except Exception as e:
            raise ValueError(f"Classification failed: {e}")

    def _classify_type(self, text: str) -> str:
        """Classify document type based on content patterns."""
        # Simplified classification logic
        text_lower = text.lower()

        if "invoice" in text_lower or "receipt" in text_lower:
            return "invoice"
        elif "report" in text_lower:
            return "report"
        elif "agreement" in text_lower or "contract" in text_lower:
            return "legal"
        elif "resume" in text_lower or "cv" in text_lower:
            return "resume"
        else:
            return "other"

    def _classify_category(self, text: str) -> str:
        """Classify document category based on content."""
        # Simplified classification logic
        text_lower = text.lower()

        if "financial" in text_lower or "budget" in text_lower or "cost" in text_lower:
            return "financial"
        elif "technical" in text_lower or "specification" in text_lower:
            return "technical"
        elif (
            "legal" in text_lower
            or "agreement" in text_lower
            or "contract" in text_lower
        ):
            return "legal"
        else:
            return "general"

    def _detect_language(self, text: str) -> str:
        """Detect document language."""
        # Simplified language detection
        # Real implementation would use a language detection library
        return "en"  # Default to English


class MetadataExtractionStage(PipelineStage):
    """Stage for extracting metadata from documents."""

    def __init__(
        self,
        extractors: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize metadata extraction stage."""
        super().__init__(name="metadata", description="Extract metadata from documents")
        self._extractors = extractors or ["dates", "entities", "keywords"]
        self._config = kwargs

    async def process(self, text: str, context: Context) -> Dict[str, Any]:
        """Extract metadata from document."""
        try:
            metadata = {}

            # Apply each extractor
            for extractor in self._extractors:
                if extractor == "dates":
                    metadata["dates"] = self._extract_dates(text)
                elif extractor == "entities":
                    metadata["entities"] = self._extract_entities(text)
                elif extractor == "keywords":
                    metadata["keywords"] = self._extract_keywords(text)

            # Store metadata
            context.metadata["metadata_extractors"] = self._extractors
            context.metadata["extraction_results"] = metadata

            return metadata

        except Exception as e:
            raise ValueError(f"Metadata extraction failed: {e}")

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Simple regex-based date extraction
        date_pattern = r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
        return re.findall(date_pattern, text)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        # Simplified entity extraction - real implementation would use NLP
        entities = {
            "organizations": [],
            "persons": [],
            "locations": [],
        }

        # Very simple rule-based extraction as fallback
        words = text.split()
        for word in words:
            if word.startswith("@"):
                entities["persons"].append(word[1:])
            elif word.startswith("#"):
                entities["organizations"].append(word[1:])

        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple word frequency analysis
        words = text.lower().split()
        # Filter out common stop words and short words
        stop_words = {
            "the",
            "and",
            "a",
            "an",
            "in",
            "of",
            "to",
            "is",
            "for",
            "on",
            "with",
        }
        filtered_words = [w for w in words if len(w) > 4 and w not in stop_words]

        # Count word frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top 10 keywords
        return [word for word, _ in sorted_words[:10]]


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
    context = Context()

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
    context = Context()

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
    context = Context()

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
    context = Context()

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
