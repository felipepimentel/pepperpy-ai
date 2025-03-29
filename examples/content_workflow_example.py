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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def text_extraction_workflow() -> None:
    """Run text extraction workflow."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "pymupdf": {"extract_images": True, "extract_tables": True},
                    "pandoc": {"output_format": "markdown"},
                }
            )
        ) as pepper:
            # Process PDF document
            pdf_path = Path("examples/data/document.pdf")
            pdf_result = await (
                pepper.content.from_file(pdf_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("PDF extraction result: %s", pdf_result)

            # Process Word document
            docx_path = Path("examples/data/document.docx")
            docx_result = await (
                pepper.content.from_file(docx_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Word extraction result: %s", docx_result)

    except Exception as e:
        logger.error("Error in text extraction workflow: %s", e)


async def archive_workflow() -> None:
    """Run archive processing workflow."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy().with_content().with_content_config(providers={"pymupdf": {}})
        ) as pepper:
            # Process archive
            archive_path = Path("examples/data/documents.zip")
            result = await (
                pepper.content.from_archive(archive_path)
                .with_password("secret123")
                .extract_to("examples/data/extracted")
                .include_extensions(".pdf", ".docx")
                .recursive()
                .execute()
            )
            logger.info("Archive processing result: %s", result)

    except Exception as e:
        logger.error("Error in archive workflow: %s", e)


async def protected_content_workflow() -> None:
    """Run protected content workflow."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy().with_content().with_content_config(providers={"pymupdf": {}})
        ) as pepper:
            # Process protected PDF
            pdf_path = Path("examples/data/protected.pdf")
            result = await (
                pepper.content.from_file(pdf_path)
                .with_password("secret123")
                .unlock_to("examples/data/unlocked")
                .execute()
            )
            logger.info("Protected content processing result: %s", result)

    except Exception as e:
        logger.error("Error in protected content workflow: %s", e)


async def rag_workflow() -> None:
    """Run RAG integration workflow."""
    try:
        # Initialize PepperPy with content and RAG
        async with (
            PepperPy()
            .with_content()
            .with_content_config(providers={"pymupdf": {}})
            .with_rag()
        ) as pepper:
            # Process document for RAG
            pdf_path = Path("examples/data/document.pdf")
            result = await (
                pepper.content.from_file(pdf_path)
                .extract_text()
                .chunk(size=1000)
                .store_in_rag("documents", doc_id="doc1")
                .with_metadata()
                .execute()
            )
            logger.info("RAG processing result: %s", result)

    except Exception as e:
        logger.error("Error in RAG workflow: %s", e)


async def directory_workflow() -> None:
    """Run directory processing workflow."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy().with_content().with_content_config(providers={"pymupdf": {}})
        ) as pepper:
            # Process directory
            directory_path = Path("examples/data/documents")
            result = await (
                pepper.content.from_directory(directory_path)
                .include_extensions(".pdf", ".docx")
                .recursive()
                .extract_text()
                .execute()
            )
            logger.info("Directory processing result: %s", result)

    except Exception as e:
        logger.error("Error in directory workflow: %s", e)


async def batch_workflow() -> None:
    """Run batch processing workflow."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy().with_content().with_content_config(providers={"pymupdf": {}})
        ) as pepper:
            # Process batch of files
            files = [
                Path("examples/data/batch/doc1.pdf"),
                Path("examples/data/batch/doc2.pdf"),
                Path("examples/data/batch/doc3.docx"),
            ]
            result = await (
                pepper.content.from_files(files)
                .extract_text()
                .with_metadata()
                .parallel()
                .execute()
            )
            logger.info("Batch processing result: %s", result)

    except Exception as e:
        logger.error("Error in batch workflow: %s", e)


async def main() -> None:
    """Run content processing workflow examples."""
    print("Starting content processing examples...\n")
    await text_extraction_workflow()
    await archive_workflow()
    await protected_content_workflow()
    await rag_workflow()
    await directory_workflow()
    await batch_workflow()
    print("\nContent processing examples completed.")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    # PEPPERPY_RAG__PROVIDER=memory
    asyncio.run(main())
