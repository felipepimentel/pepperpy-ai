#!/usr/bin/env python3
"""Example demonstrating the Document Processing Workflow plugin.

This example shows how to use the Document Processing Workflow plugin
to extract text and metadata from documents.
"""

import asyncio
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentResult:
    """Result of document processing."""

    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class MockDocumentProcessorWorkflow:
    """Mock implementation of a document processor workflow."""

    def __init__(
        self,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
    ):
        self.extract_metadata = extract_metadata
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        print("[Document Processor] Initializing with options:")
        print(f"  - Extract metadata: {self.extract_metadata}")
        print(f"  - Extract images: {self.extract_images}")
        print(f"  - Extract tables: {self.extract_tables}")
        self.initialized = True

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the document processing workflow."""
        if not self.initialized:
            await self.initialize()

        # Check which operation to perform based on input data
        if "document_path" in input_data:
            return await self._process_single_document(
                input_data["document_path"], input_data.get("options", {})
            )
        elif "document_paths" in input_data:
            return await self._process_batch_documents(
                input_data["document_paths"], input_data.get("options", {})
            )
        elif "directory_path" in input_data:
            return await self._process_directory(
                input_data["directory_path"], input_data.get("options", {})
            )
        else:
            return {
                "error": "Invalid input: Must provide document_path, document_paths, or directory_path"
            }

    async def _process_single_document(
        self, document_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single document."""
        print(f"[Document Processor] Processing file: {document_path}")

        path = Path(document_path)
        if not path.exists():
            return {"error": f"File not found: {document_path}"}

        # Extract text content from file (in a real implementation this would be more sophisticated)
        try:
            if path.suffix.lower() in [".txt", ".md"]:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            elif path.suffix.lower() in [".pdf", ".docx", ".doc"]:
                # Mock extraction from PDF/Word
                text = f"This is mock extracted text from {path.name}. The document appears to contain information about PepperPy framework and document processing capabilities."
            else:
                text = (
                    f"Unsupported file type for direct text extraction: {path.suffix}"
                )

            # Generate mock metadata if requested
            metadata = {}
            if self.extract_metadata:
                metadata = {
                    "filename": path.name,
                    "file_size": os.path.getsize(path),
                    "pages": random.randint(1, 20)
                    if path.suffix.lower() == ".pdf"
                    else 1,
                    "created": "2023-01-15T10:30:00Z",
                    "mime_type": "application/pdf"
                    if path.suffix.lower() == ".pdf"
                    else "text/plain",
                }

            return {"text": text, "metadata": metadata, "path": str(path)}
        except Exception as e:
            return {"error": str(e), "path": str(path)}

    async def _process_batch_documents(
        self, document_paths: List[str], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a batch of documents."""
        print(f"[Document Processor] Processing batch of {len(document_paths)} files")

        results = {}
        for path in document_paths:
            result = await self._process_single_document(path, options)
            results[path] = result

        return {
            "results": results,
            "num_files": len(document_paths),
            "num_successful": sum(1 for r in results.values() if "error" not in r),
        }

    async def _process_directory(
        self, directory_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all documents in a directory."""
        print(f"[Document Processor] Processing directory: {directory_path}")

        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": f"Directory not found: {directory_path}"}

        # Find all document files (in a real implementation, this would be more sophisticated)
        document_paths = []
        for ext in [".txt", ".md", ".pdf", ".docx", ".doc"]:
            document_paths.extend([str(p) for p in dir_path.glob(f"**/*{ext}")])

        # Process each document
        return await self._process_batch_documents(document_paths, options)

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("[Document Processor] Cleaning up resources")
        self.initialized = False


class MockPluginManager:
    """Mock implementation of the PluginManager."""

    @staticmethod
    def create_provider(provider_type: str, provider_name: str, **kwargs) -> Any:
        """Create a provider instance."""
        if provider_type == "workflow" and provider_name == "document_processor":
            return MockDocumentProcessorWorkflow(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider_type}/{provider_name}")


# Setup paths
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Document Processing Workflow Example")
    print("=" * 50)

    # Create the document processor using plugin_manager
    workflow = MockPluginManager.create_provider(
        "workflow",
        "document_processor",
        extract_metadata=True,
        extract_images=False,
        extract_tables=False,
    )

    # Inicializar o workflow
    await workflow.initialize()

    # Find sample PDF files
    pdf_files = list(DATA_DIR.glob("**/*.pdf"))
    if not pdf_files:
        print(
            "No PDF files found in the data directory. Creating a sample text file instead."
        )
        # Create a sample text file
        sample_file = DATA_DIR / "sample.txt"
        with open(sample_file, "w") as f:
            f.write(
                "This is a sample document for testing the document processor workflow.\n"
                "It contains multiple lines of text that can be processed.\n"
                "PepperPy makes it easy to work with different document types."
            )

        # Process the sample file
        input_data = {"document_path": str(sample_file), "options": {}}
        result = await workflow.execute(input_data)

        print(f"\nProcessed: {sample_file}")
        print(f"Text content: {result['text']}")
    else:
        # Process a single document
        pdf_file = pdf_files[0]
        print(f"\nProcessing document: {pdf_file}")

        input_data = {"document_path": str(pdf_file), "options": {}}
        result = await workflow.execute(input_data)

        print(f"Extracted text (first 100 chars): {result['text'][:100]}...")
        print(f"Metadata: {result['metadata']}")

        # Process a batch of documents if available
        if len(pdf_files) > 1:
            print(f"\nProcessing batch of {min(3, len(pdf_files))} documents...")

            # Convert Path objects to strings
            doc_paths = [str(path) for path in pdf_files[:3]]

            input_data = {"document_paths": doc_paths, "options": {}}
            batch_results = await workflow.execute(input_data)

            for path, doc_result in batch_results["results"].items():
                if "error" in doc_result:
                    print(f"Error processing {path}: {doc_result['error']}")
                else:
                    text_preview = (
                        doc_result["text"][:50] + "..."
                        if doc_result["text"]
                        else "No text"
                    )
                    print(f"- {Path(path).name}: {text_preview}")

        # Process a directory
        print(f"\nProcessing all documents in {DATA_DIR}")

        input_data = {"directory_path": str(DATA_DIR), "options": {}}
        dir_results = await workflow.execute(input_data)

        print(f"Processed {dir_results['num_files']} files in directory")
        print(f"Found {len(dir_results['results'])} documents")

    # Clean up
    await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
