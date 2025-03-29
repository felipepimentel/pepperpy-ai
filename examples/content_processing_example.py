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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_document() -> None:
    """Process a document using different providers."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "pymupdf": {
                        "extract_images": True,
                        "extract_tables": True,
                    },
                    "pandoc": {
                        "output_format": "markdown",
                    },
                    "tika": {
                        "tika_server_url": "http://localhost:9998",
                    },
                    "textract": {
                        "ocr_strategy": "tesseract",
                    },
                }
            )
        ) as pepper:
            # Process a PDF document
            pdf_path = Path("examples/data/document.pdf")
            pdf_result = await (
                pepper.content.from_file(pdf_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("PDF processing result: %s", pdf_result)

            # Process a Word document
            docx_path = Path("examples/data/document.docx")
            docx_result = await (
                pepper.content.from_file(docx_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Word processing result: %s", docx_result)

            # Process a password-protected PDF
            protected_pdf_path = Path("examples/data/protected.pdf")
            protected_result = await (
                pepper.content.from_file(protected_pdf_path)
                .with_password("secret123")
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Protected PDF processing result: %s", protected_result)

    except Exception as e:
        logger.error("Error processing document: %s", e)


async def process_image() -> None:
    """Process an image using different providers."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "tesseract": {
                        "language": "eng",
                        "psm": 3,
                    },
                    "easyocr": {
                        "languages": ["en"],
                    },
                }
            )
        ) as pepper:
            # Process an image with text
            image_path = Path("examples/data/image.png")
            image_result = await (
                pepper.content.from_file(image_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Image processing result: %s", image_result)

    except Exception as e:
        logger.error("Error processing image: %s", e)


async def process_audio() -> None:
    """Process an audio file using different providers."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "ffmpeg": {},
                }
            )
        ) as pepper:
            # Process an audio file
            audio_path = Path("examples/data/audio.mp3")
            audio_result = await (
                pepper.content.from_file(audio_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Audio processing result: %s", audio_result)

    except Exception as e:
        logger.error("Error processing audio: %s", e)


async def process_video() -> None:
    """Process a video file using different providers."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "ffmpeg": {
                        "extract_thumbnail": True,
                    },
                }
            )
        ) as pepper:
            # Process a video file
            video_path = Path("examples/data/video.mp4")
            video_result = await (
                pepper.content.from_file(video_path)
                .extract_text()
                .with_metadata()
                .execute()
            )
            logger.info("Video processing result: %s", video_result)

    except Exception as e:
        logger.error("Error processing video: %s", e)


async def process_archive() -> None:
    """Process an archive file."""
    try:
        # Initialize PepperPy with content processing
        async with (
            PepperPy()
            .with_content()
            .with_content_config(
                providers={
                    "pymupdf": {},
                }
            )
        ) as pepper:
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
            logger.info("Archive processing result: %s", archive_result)

    except Exception as e:
        logger.error("Error processing archive: %s", e)


async def main() -> None:
    """Run content processing examples."""
    print("Starting content processing examples...\n")
    await process_document()
    await process_image()
    await process_audio()
    await process_video()
    await process_archive()
    print("\nContent processing examples completed.")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
