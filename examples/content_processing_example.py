"""Example of content processing using PepperPy."""

from pathlib import Path

from pepperpy import PepperPy


async def process_document() -> None:
    """Process a text document."""
    # Create PepperPy instance with text provider
    pepper = PepperPy.create().with_plugin(
        "content",
        "text",
        file_path=Path("examples/data/sample.txt"),
    ).build()

    async with pepper as p:
        # Get text provider
        provider = p.get_provider("content")

        # Process text file
        result = await provider.process()
        print(f"Text content excerpt: {result.content[:100]}")


async def process_image() -> None:
    """Process an image file."""
    # Create PepperPy instance with image provider
    pepper = PepperPy.create().with_plugin(
        "content",
        "image",
        file_path=Path("examples/data/sample.png"),
    ).build()

    async with pepper as p:
        # Get image provider
        provider = p.get_provider("content")

        # Process image file
        result = await provider.process()
        print(f"Image metadata: {result.metadata}")


async def process_archive() -> None:
    """Process a ZIP archive."""
    # Create PepperPy instance with archive provider
    pepper = PepperPy.create().with_plugin(
        "content",
        "archive",
        file_path=Path("examples/data/sample.zip"),
    ).build()

    async with pepper as p:
        # Get archive provider
        provider = p.get_provider("content")

        # Process ZIP file
        result = await provider.process()
        print(f"Archive contents: {result.metadata.get('files', [])}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(process_document())
    asyncio.run(process_image())
    asyncio.run(process_archive())
