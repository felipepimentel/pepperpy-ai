"""Example of content processing with PepperPy.

This example demonstrates how to use the content processing module to:
1. Process different types of content (documents, images, audio, video)
2. Extract text and metadata from content
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.content_processing.base import ContentType, create_processor


async def process_document() -> None:
    """Process a document using different providers."""
    # Create document processor
    processor = await create_processor(ContentType.DOCUMENT, provider_name="pymupdf")

    # Process a PDF document
    pdf_path = Path("examples/data/sample.pdf")
    pdf_result = await processor.process(pdf_path)
    print(f"PDF text (excerpt):\n{pdf_result.text[:150]}...")
    print(f"PDF metadata: {pdf_result.metadata}")

    # Process a text file
    text_path = Path("examples/data/sample.txt")
    text_result = await processor.process(text_path)
    print(f"\nText file content (excerpt):\n{text_result.text[:150]}...")

    # Clean up
    await processor.cleanup()


async def process_image() -> None:
    """Process an image using OCR."""
    async with PepperPy().with_content(create_processor("tesseract")) as pepper:
        # Process an image with text
        image_path = Path("examples/data/image.png")
        image_result = await (
            pepper.content.from_file(image_path)
            .extract_text()
            .with_metadata()
            .execute()
        )
        print(f"\nExtracted text from image:\n{image_result['text']}")


async def process_audio() -> None:
    """Process an audio file."""
    async with PepperPy().with_content(create_processor("whisper")) as pepper:
        # Process an audio file
        audio_path = Path("examples/data/audio.mp3")
        audio_result = await (
            pepper.content.from_file(audio_path)
            .extract_text()
            .with_metadata()
            .execute()
        )
        print(f"\nTranscribed audio:\n{audio_result['text']}")


async def process_archive() -> None:
    """Process an archive file."""
    async with PepperPy().with_content(create_processor("zipfile")) as pepper:
        # Process an archive file
        archive_path = Path("examples/data/documents.zip")
        archive_result = await (
            pepper.content.from_archive(archive_path)
            .with_password("secret123")
            .extract_to("examples/data/extracted")
            .include_extensions(".pdf", ".docx")
            .recursive()
            .execute()
        )
        print(f"\nExtracted {len(archive_result['files'])} files from archive")


async def main() -> None:
    """Run content processing examples."""
    print("Content Processing Example")
    print("=" * 50)
    await process_document()


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
