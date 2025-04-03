#!/usr/bin/env python3
"""Example of content processing using PepperPy."""

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


@dataclass
class ContentResult:
    """Represents the result of content processing."""

    content: str = ""
    raw_content: bytes = b""
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None


class ContentProvider(Protocol):
    """Protocol defining the interface for content providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def process(self) -> ContentResult:
        """Process content and return the result."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...


class MockTextContentProvider:
    """Mock implementation of a text content provider."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        print(f"[Text Provider] Initializing with file: {self.file_path}")
        self.initialized = True

        # Create sample file if it doesn't exist
        if not self.file_path.exists():
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, "w") as f:
                f.write(
                    "This is a sample text file for PepperPy content processing example.\n"
                )
                f.write("It contains multiple lines of text that can be processed.\n")
                f.write("PepperPy makes it easy to work with different content types.")

    async def process(self) -> ContentResult:
        """Process text file and return the result."""
        if not self.initialized:
            await self.initialize()

        print(f"[Text Provider] Processing file: {self.file_path}")

        with open(self.file_path) as f:
            content = f.read()

        with open(self.file_path, "rb") as f:
            raw_content = f.read()

        metadata = {
            "size_bytes": len(raw_content),
            "lines": len(content.splitlines()),
            "format": "text/plain",
        }

        return ContentResult(
            content=content,
            raw_content=raw_content,
            metadata=metadata,
            file_path=self.file_path,
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("[Text Provider] Cleaning up")
        self.initialized = False


class MockImageContentProvider:
    """Mock implementation of an image content provider."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        print(f"[Image Provider] Initializing with file: {self.file_path}")
        self.initialized = True

        # Create sample file if it doesn't exist
        if not self.file_path.exists():
            os.makedirs(self.file_path.parent, exist_ok=True)
            # Create a dummy file with some bytes
            with open(self.file_path, "wb") as f:
                f.write(
                    b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
                )  # Simple PNG header + dummy data

    async def process(self) -> ContentResult:
        """Process image file and return the result."""
        if not self.initialized:
            await self.initialize()

        print(f"[Image Provider] Processing file: {self.file_path}")

        # In a real provider, we would parse the image
        with open(self.file_path, "rb") as f:
            raw_content = f.read()

        # Mock metadata as if we analyzed the image
        metadata = {
            "size_bytes": len(raw_content),
            "dimensions": {"width": 800, "height": 600},
            "format": "image/png",
            "color_mode": "RGB",
        }

        return ContentResult(
            content="",  # No text content for images
            raw_content=raw_content,
            metadata=metadata,
            file_path=self.file_path,
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("[Image Provider] Cleaning up")
        self.initialized = False


class MockArchiveContentProvider:
    """Mock implementation of an archive content provider."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        print(f"[Archive Provider] Initializing with file: {self.file_path}")
        self.initialized = True

        # Create sample archive if it doesn't exist
        if not self.file_path.exists():
            os.makedirs(self.file_path.parent, exist_ok=True)
            # Create a dummy ZIP file header
            with open(self.file_path, "wb") as f:
                f.write(b"PK\x03\x04" + b"\x00" * 100)  # Simple ZIP header + dummy data

    async def process(self) -> ContentResult:
        """Process archive file and return the result."""
        if not self.initialized:
            await self.initialize()

        print(f"[Archive Provider] Processing file: {self.file_path}")

        # In a real provider, we would extract and analyze the archive
        with open(self.file_path, "rb") as f:
            raw_content = f.read()

        # Mock metadata as if we analyzed the archive
        metadata = {
            "size_bytes": len(raw_content),
            "format": "application/zip",
            "files": [
                {"name": "document1.txt", "size": 1024},
                {"name": "image1.png", "size": 45678},
                {"name": "data/report.pdf", "size": 102400},
            ],
            "compression_ratio": 0.7,
        }

        return ContentResult(
            content="",  # No direct text content for archives
            raw_content=raw_content,
            metadata=metadata,
            file_path=self.file_path,
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("[Archive Provider] Cleaning up")
        self.initialized = False


class MockPepperPy:
    """Mock implementation of the PepperPy class."""

    @staticmethod
    def create():
        """Create a new builder."""
        return MockPepperPyBuilder()

    def __init__(self, provider_config: Dict[str, Any]):
        self.provider_config = provider_config
        self.provider = None

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.provider:
            await self.provider.cleanup()

    def get_provider(self, provider_type: str):
        """Get a provider by type."""
        provider_info = self.provider_config.get(provider_type)
        if not provider_info:
            raise ValueError(f"No provider configured for type: {provider_type}")

        provider_name = provider_info["name"]
        file_path = provider_info["file_path"]

        if provider_name == "text":
            self.provider = MockTextContentProvider(file_path)
        elif provider_name == "image":
            self.provider = MockImageContentProvider(file_path)
        elif provider_name == "archive":
            self.provider = MockArchiveContentProvider(file_path)
        else:
            raise ValueError(f"Unknown provider name: {provider_name}")

        return self.provider


class MockPepperPyBuilder:
    """Builder for MockPepperPy."""

    def __init__(self):
        self.providers = {}

    def with_plugin(self, provider_type: str, provider_name: str, **kwargs):
        """Add a plugin configuration."""
        self.providers[provider_type] = {"name": provider_name, **kwargs}
        return self

    def build(self):
        """Build and return a MockPepperPy instance."""
        return MockPepperPy(self.providers)


async def process_document() -> None:
    """Process a text document."""
    print("\n=== Processing Text Document ===")

    # Create PepperPy instance with text provider
    pepper = (
        MockPepperPy.create()
        .with_plugin(
            "content",
            "text",
            file_path=Path("examples/data/sample.txt"),
        )
        .build()
    )

    async with pepper as p:
        # Get text provider
        provider = p.get_provider("content")

        # Process text file
        result = await provider.process()
        print(f"Text content excerpt: {result.content[:100]}")
        print(f"Metadata: {result.metadata}")


async def process_image() -> None:
    """Process an image file."""
    print("\n=== Processing Image ===")

    # Create PepperPy instance with image provider
    pepper = (
        MockPepperPy.create()
        .with_plugin(
            "content",
            "image",
            file_path=Path("examples/data/sample.png"),
        )
        .build()
    )

    async with pepper as p:
        # Get image provider
        provider = p.get_provider("content")

        # Process image file
        result = await provider.process()
        print(f"Image metadata: {result.metadata}")


async def process_archive() -> None:
    """Process a ZIP archive."""
    print("\n=== Processing Archive ===")

    # Create PepperPy instance with archive provider
    pepper = (
        MockPepperPy.create()
        .with_plugin(
            "content",
            "archive",
            file_path=Path("examples/data/sample.zip"),
        )
        .build()
    )

    async with pepper as p:
        # Get archive provider
        provider = p.get_provider("content")

        # Process ZIP file
        result = await provider.process()
        print(f"Archive contents: {result.metadata.get('files', [])}")


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("examples/data", exist_ok=True)

    # Run examples
    asyncio.run(process_document())
    asyncio.run(process_image())
    asyncio.run(process_archive())

    print("\nContent processing examples completed!")
