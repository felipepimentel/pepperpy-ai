"""Example of content processing workflow with PepperPy.

This example demonstrates how to use the content processing workflow module to:
1. Extract text from various content types
2. Process archive contents
3. Handle password-protected content
4. Integrate with RAG systems
5. Process directories and batches of files
"""

import asyncio
import logging
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.content_processing.errors import ContentProcessingError
from pepperpy.workflow.recipes.content_processing import (
    ArchiveExtractionStage,
    BatchProcessingStage,
    ContentRAGStage,
    DirectoryProcessingStage,
    ProtectedContentStage,
    TextExtractionStage,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def text_extraction_workflow() -> None:
    """Run text extraction workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor with multiple providers
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {
                        "extract_images": True,
                        "extract_tables": True,
                    },
                },
                {
                    "type": "pandoc",
                    "config": {
                        "output_format": "markdown",
                    },
                },
            ],
        )

        # Create text extraction stage
        stage = TextExtractionStage(
            content_processor=pepperpy.content_processor,
            extract_metadata=True,
        )

        # Process PDF document
        pdf_path = Path("examples/data/document.pdf")
        pdf_result = await stage.process(
            content_path=pdf_path,
        )
        logger.info("PDF extraction result: %s", pdf_result)

        # Process Word document
        docx_path = Path("examples/data/document.docx")
        docx_result = await stage.process(
            content_path=docx_path,
        )
        logger.info("Word extraction result: %s", docx_result)

    except ContentProcessingError as e:
        logger.error("Error in text extraction workflow: %s", e)


async def archive_workflow() -> None:
    """Run archive processing workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Create archive extraction stage
        stage = ArchiveExtractionStage(
            content_processor=pepperpy.content_processor,
            output_path=Path("examples/data/extracted"),
            file_extensions={".pdf", ".docx"},
            recursive=True,
        )

        # Process archive
        archive_path = Path("examples/data/documents.zip")
        result = await stage.process(
            archive_path=archive_path,
            password="secret123",  # Optional password
        )
        logger.info("Archive processing result: %s", result)

    except ContentProcessingError as e:
        logger.error("Error in archive workflow: %s", e)


async def protected_content_workflow() -> None:
    """Run protected content workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Create protected content stage
        stage = ProtectedContentStage(
            content_processor=pepperpy.content_processor,
            output_path=Path("examples/data/unlocked"),
        )

        # Process protected PDF
        pdf_path = Path("examples/data/protected.pdf")
        result = await stage.process(
            content_path=pdf_path,
            password="secret123",
        )
        logger.info("Protected content processing result: %s", result)

    except ContentProcessingError as e:
        logger.error("Error in protected content workflow: %s", e)


async def rag_workflow() -> None:
    """Run RAG integration workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Create text chunker (example)
        class SimpleChunker:
            def create_chunks(self, text: str) -> list[str]:
                return [text[i:i + 1000] for i in range(0, len(text), 1000)]

        # Create RAG system (example)
        class SimpleRAG:
            def __init__(self) -> None:
                self.documents = []

            class Document:
                def __init__(self, page_content: str, metadata: dict) -> None:
                    self.page_content = page_content
                    self.metadata = metadata

            def add_documents(
                self,
                documents: list,
                collection_name: str,
            ) -> None:
                self.documents.extend(documents)

        # Create RAG stage
        stage = ContentRAGStage(
            content_processor=pepperpy.content_processor,
            chunker=SimpleChunker(),
            rag=SimpleRAG(),
            collection_name="documents",
            include_metadata=True,
        )

        # Process document for RAG
        pdf_path = Path("examples/data/document.pdf")
        result = await stage.process(
            content_path=pdf_path,
            content_id="doc1",
        )
        logger.info("RAG processing result: %s", result)

    except ContentProcessingError as e:
        logger.error("Error in RAG workflow: %s", e)


async def directory_workflow() -> None:
    """Run directory processing workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Create directory processing stage
        stage = DirectoryProcessingStage(
            content_processor=pepperpy.content_processor,
            file_extensions={".pdf", ".docx"},
            recursive=True,
        )

        # Process directory
        directory_path = Path("examples/data/documents")
        result = await stage.process(
            directory_path=directory_path,
        )
        logger.info("Directory processing result: %s", result)

    except ContentProcessingError as e:
        logger.error("Error in directory workflow: %s", e)


async def batch_workflow() -> None:
    """Run batch processing workflow."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Create batch processing stage
        stage = BatchProcessingStage(
            content_processor=pepperpy.content_processor,
            max_concurrent=3,
        )

        # Process batch of files
        files = [
            Path("examples/data/document1.pdf"),
            Path("examples/data/document2.pdf"),
            Path("examples/data/document3.docx"),
        ]
        result = await stage.process(
            content_paths=files,
        )
        logger.info("Batch processing result: %s", result)

    except ContentProcessingError as e:
        logger.error("Error in batch workflow: %s", e)


async def main() -> None:
    """Run content processing workflow examples."""
    # Run different workflows
    await text_extraction_workflow()
    await archive_workflow()
    await protected_content_workflow()
    await rag_workflow()
    await directory_workflow()
    await batch_workflow()


if __name__ == "__main__":
    asyncio.run(main()) 