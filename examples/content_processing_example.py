"""Example of content processing with PepperPy.

This example demonstrates how to use the content processing module to:
1. Process different types of content (documents, images, audio, video)
2. Extract text and metadata from content
"""

import asyncio
from pathlib import Path
from typing import cast

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.plugin_manager import plugin_manager


async def process_document() -> None:
    """Process a document using different providers."""
    # Create document processor
    provider = cast(
        ContentProcessor,
        plugin_manager.create_provider("content/processing/document", "pymupdf"),
    )
    await provider.initialize()

    try:
        # Process a PDF document
        pdf_path = Path("examples/data/sample.pdf")
        pdf_result: ProcessingResult = await provider.process(pdf_path)
        print(
            f"PDF text (excerpt):\n{pdf_result.text[:150] if pdf_result.text else ''}..."
        )
        print(f"PDF metadata: {pdf_result.metadata}")

        # Process a text file
        text_path = Path("examples/data/sample.txt")
        text_result: ProcessingResult = await provider.process(text_path)
        print(
            f"\nText file content (excerpt):\n{text_result.text[:150] if text_result.text else ''}..."
        )
    finally:
        await provider.cleanup()


async def process_image() -> None:
    """Process an image using OCR."""
    # Create image processor
    provider = cast(
        ContentProcessor,
        plugin_manager.create_provider("content/processing/document", "tesseract"),
    )
    await provider.initialize()

    try:
        # Process an image with text
        image_path = Path("examples/data/image.png")
        image_result: ProcessingResult = await provider.process(image_path)
        print(
            f"\nExtracted text from image:\n{image_result.text if image_result.text else ''}"
        )
    finally:
        await provider.cleanup()


async def process_audio() -> None:
    """Process an audio file."""
    # Create audio processor
    provider = cast(
        ContentProcessor,
        plugin_manager.create_provider("content/processing/audio", "ffmpeg"),
    )
    await provider.initialize()

    try:
        # Process an audio file
        audio_path = Path("examples/data/audio.mp3")
        audio_result: ProcessingResult = await provider.process(audio_path)
        print(f"\nTranscribed audio:\n{audio_result.text if audio_result.text else ''}")
    finally:
        await provider.cleanup()


async def process_archive() -> None:
    """Process an archive file."""
    # Create archive processor
    provider = cast(
        ContentProcessor,
        plugin_manager.create_provider("content/processing/archive", "zipfile"),
    )
    await provider.initialize()

    try:
        # Process an archive file
        archive_path = Path("examples/data/documents.zip")
        archive_result: ProcessingResult = await provider.process(
            archive_path,
            password="secret123",
            output_dir="examples/data/extracted",
            include_extensions=[".pdf", ".docx"],
            recursive=True,
        )
        print(
            f"\nExtracted {len(archive_result.metadata.get('files', []))} files from archive"
        )
    finally:
        await provider.cleanup()


async def main() -> None:
    """Run content processing examples."""
    print("Content Processing Example")
    print("=" * 50)
    await process_document()


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
