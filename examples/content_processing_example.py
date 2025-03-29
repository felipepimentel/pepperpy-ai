"""Example of content processing with PepperPy.

This example demonstrates how to use the content processing module to:
1. Process different types of content (documents, images, audio, video)
2. Extract text and metadata from content
3. Handle password-protected content
4. Work with archives
"""

import asyncio
import logging
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.content_processing.errors import ContentProcessingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_document() -> None:
    """Process a document using different providers."""
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
                {
                    "type": "tika",
                    "config": {
                        "tika_server_url": "http://localhost:9998",
                    },
                },
                {
                    "type": "textract",
                    "config": {
                        "ocr_strategy": "tesseract",
                    },
                },
            ],
        )

        # Process a PDF document
        pdf_path = Path("examples/data/document.pdf")
        pdf_result = await pepperpy.process_content(
            content_path=pdf_path,
            extract_metadata=True,
        )
        logger.info("PDF processing result: %s", pdf_result)

        # Process a Word document
        docx_path = Path("examples/data/document.docx")
        docx_result = await pepperpy.process_content(
            content_path=docx_path,
            extract_metadata=True,
        )
        logger.info("Word processing result: %s", docx_result)

        # Process a password-protected PDF
        protected_pdf_path = Path("examples/data/protected.pdf")
        protected_result = await pepperpy.process_content(
            content_path=protected_pdf_path,
            extract_metadata=True,
            password="secret123",
        )
        logger.info("Protected PDF processing result: %s", protected_result)

    except ContentProcessingError as e:
        logger.error("Error processing document: %s", e)


async def process_image() -> None:
    """Process an image using different providers."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure image processor with multiple providers
        pepperpy.configure_content_processor(
            content_type="image",
            providers=[
                {
                    "type": "tesseract",
                    "config": {
                        "language": "eng",
                        "psm": 3,
                    },
                },
                {
                    "type": "easyocr",
                    "config": {
                        "languages": ["en"],
                    },
                },
            ],
        )

        # Process an image with text
        image_path = Path("examples/data/image.png")
        image_result = await pepperpy.process_content(
            content_path=image_path,
            extract_metadata=True,
        )
        logger.info("Image processing result: %s", image_result)

    except ContentProcessingError as e:
        logger.error("Error processing image: %s", e)


async def process_audio() -> None:
    """Process an audio file using different providers."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure audio processor with FFmpeg provider
        pepperpy.configure_content_processor(
            content_type="audio",
            providers=[
                {
                    "type": "ffmpeg",
                    "config": {},
                },
            ],
        )

        # Process an audio file
        audio_path = Path("examples/data/audio.mp3")
        audio_result = await pepperpy.process_content(
            content_path=audio_path,
            extract_metadata=True,
        )
        logger.info("Audio processing result: %s", audio_result)

    except ContentProcessingError as e:
        logger.error("Error processing audio: %s", e)


async def process_video() -> None:
    """Process a video file using different providers."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure video processor with FFmpeg provider
        pepperpy.configure_content_processor(
            content_type="video",
            providers=[
                {
                    "type": "ffmpeg",
                    "config": {
                        "extract_thumbnail": True,
                    },
                },
            ],
        )

        # Process a video file
        video_path = Path("examples/data/video.mp4")
        video_result = await pepperpy.process_content(
            content_path=video_path,
            extract_metadata=True,
        )
        logger.info("Video processing result: %s", video_result)

    except ContentProcessingError as e:
        logger.error("Error processing video: %s", e)


async def process_archive() -> None:
    """Process an archive file."""
    try:
        # Initialize PepperPy
        pepperpy = PepperPy()

        # Configure document processor for extracted files
        pepperpy.configure_content_processor(
            content_type="document",
            providers=[
                {
                    "type": "pymupdf",
                    "config": {},
                },
            ],
        )

        # Extract and process files from archive
        archive_path = Path("examples/data/documents.zip")
        output_path = Path("examples/data/extracted")

        # Extract archive
        await pepperpy.extract_archive(
            archive_path=archive_path,
            output_path=output_path,
            password="secret123",  # Optional password
        )

        # Process extracted files
        for file_path in output_path.rglob("*.pdf"):
            result = await pepperpy.process_content(
                content_path=file_path,
                extract_metadata=True,
            )
            logger.info("Processing result for %s: %s", file_path, result)

    except ContentProcessingError as e:
        logger.error("Error processing archive: %s", e)


async def main() -> None:
    """Run content processing examples."""
    # Process different types of content
    await process_document()
    await process_image()
    await process_audio()
    await process_video()
    await process_archive()


if __name__ == "__main__":
    asyncio.run(main()) 