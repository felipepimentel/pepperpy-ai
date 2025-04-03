#!/usr/bin/env python
"""
Simplified example of content processing with YAML configuration.

This example demonstrates how to simulate content processing using
PepperPy's YAML configuration without relying on the actual implementation.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class MockContentProvider:
    """Mock content provider to demonstrate content processing."""

    def __init__(self, provider_name: str, **config):
        """Initialize the mock content provider.

        Args:
            provider_name: Provider name (e.g., "text", "pymupdf")
            **config: Configuration parameters
        """
        self.provider_name = provider_name
        self.config = config
        self.initialized = False

        # Bind configuration to instance attributes
        for key, value in config.items():
            setattr(self, key, value)

        # Set file_path from constructor or config
        self.file_path = config.get("file_path", None)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        print(f"Initializing content/{self.provider_name} provider")
        self.initialized = True

    async def process(self, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """Process content from file.

        Args:
            file_path: Optional path to file (overrides config)

        Returns:
            Result with content and metadata
        """
        # Use file_path from argument or instance attribute
        path = file_path or self.file_path

        if not path:
            raise ValueError("No file path provided")

        if not Path(path).exists():
            print(f"Warning: File {path} does not exist. Using mock content.")

            # Return mock content based on file type
            suffix = Path(path).suffix.lower()
            if suffix in [".txt", ".md", ".rst"]:
                return {
                    "content": "This is sample text content for a document...",
                    "metadata": {
                        "type": "text",
                        "filename": Path(path).name,
                        "size": 1024,
                    },
                }
            elif suffix in [".png", ".jpg", ".jpeg", ".gif"]:
                return {
                    "content": "Binary image data...",
                    "metadata": {
                        "type": "image",
                        "filename": Path(path).name,
                        "size": 2048,
                        "dimensions": "800x600",
                    },
                }
            elif suffix in [".zip", ".tar", ".gz"]:
                return {
                    "content": "Archive contents...",
                    "metadata": {
                        "type": "archive",
                        "filename": Path(path).name,
                        "size": 4096,
                        "files": ["file1.txt", "file2.jpg", "directory/file3.md"],
                    },
                }
            else:
                return {
                    "content": "Unknown content type",
                    "metadata": {"type": "unknown", "filename": Path(path).name},
                }

        # In a real implementation, this would read and process the file
        print(f"Processing file: {path}")

        # Mock processing based on file type
        suffix = Path(path).suffix.lower()
        if suffix in [".txt", ".md", ".rst"]:
            # Simulate reading a small part of the file
            try:
                with open(path, encoding="utf-8") as f:
                    content = (
                        f.read(200) + "..." if path.exists() else "Mock text content"
                    )
            except Exception as e:
                content = f"Error reading file: {e}"

            return {
                "content": content,
                "metadata": {"type": "text", "filename": Path(path).name, "size": 1024},
            }
        elif suffix in [".png", ".jpg", ".jpeg", ".gif"]:
            return {
                "content": "Binary image data...",
                "metadata": {
                    "type": "image",
                    "filename": Path(path).name,
                    "size": 2048,
                    "dimensions": "800x600",
                },
            }
        elif suffix in [".zip", ".tar", ".gz"]:
            return {
                "content": "Archive contents...",
                "metadata": {
                    "type": "archive",
                    "filename": Path(path).name,
                    "size": 4096,
                    "files": ["file1.txt", "file2.jpg", "directory/file3.md"],
                },
            }
        else:
            return {
                "content": "Unknown content type",
                "metadata": {"type": "unknown", "filename": Path(path).name},
            }

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print(f"Cleaning up content/{self.provider_name} provider")
        self.initialized = False


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the config file

    Returns:
        Loaded configuration dictionary
    """
    config_file = Path(config_path).resolve()

    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        return {}

    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_plugin_config(
    config: Dict[str, Any], plugin_name: str
) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific plugin.

    Args:
        config: Configuration dictionary
        plugin_name: Plugin name

    Returns:
        Plugin configuration or None if not found
    """
    if "plugins" not in config:
        return None

    if plugin_name in config["plugins"]:
        return config["plugins"][plugin_name]

    return None


async def process_document() -> None:
    """Process a text document."""
    print("\n--- Processing Text Document ---")

    # Create mock provider for text processing
    provider = MockContentProvider("text", file_path=Path("examples/data/sample.txt"))

    # Process text file
    await provider.initialize()
    result = await provider.process()
    print(f"Text content excerpt: {result['content']}")
    print(f"Metadata: {result['metadata']}")
    await provider.cleanup()


async def process_image() -> None:
    """Process an image file."""
    print("\n--- Processing Image File ---")

    # Create mock provider for image processing
    provider = MockContentProvider("image", file_path=Path("examples/data/sample.png"))

    # Process image file
    await provider.initialize()
    result = await provider.process()
    print(f"Image metadata: {result['metadata']}")
    await provider.cleanup()


async def process_archive() -> None:
    """Process a ZIP archive."""
    print("\n--- Processing Archive File ---")

    # Create mock provider for archive processing
    provider = MockContentProvider(
        "archive", file_path=Path("examples/data/sample.zip")
    )

    # Process archive file
    await provider.initialize()
    result = await provider.process()
    print(f"Archive contents: {result['metadata'].get('files', [])}")
    await provider.cleanup()


async def process_with_config() -> None:
    """Process content using YAML configuration."""
    print("\n--- Processing with YAML Configuration ---")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))

    # Get configuration for PyMuPDF (our default content provider)
    pymupdf_config = get_plugin_config(config, "pymupdf") or {}

    # Create provider with config
    provider = MockContentProvider("pymupdf", **pymupdf_config)

    # Process a PDF file
    await provider.initialize()
    result = await provider.process(Path("examples/data/sample.pdf"))
    print(f"PDF content excerpt: {result['content']}")
    print(f"PDF metadata: {result['metadata']}")
    await provider.cleanup()


async def main() -> None:
    """Run the simplified content processing example."""
    print("=== Simplified Content Processing Example ===")

    # Ensure the data directory exists
    data_dir = Path("examples/data")
    data_dir.mkdir(exist_ok=True, parents=True)

    # Create sample files if they don't exist
    sample_txt = data_dir / "sample.txt"
    if not sample_txt.exists():
        with open(sample_txt, "w", encoding="utf-8") as f:
            f.write("This is a sample text file for testing content processing.\n")
            f.write("It contains multiple lines of text.\n")
            f.write("PepperPy is a powerful framework for AI applications.")

    # Process different content types
    await process_document()
    await process_image()
    await process_archive()
    await process_with_config()

    print("\nContent processing example completed!")


if __name__ == "__main__":
    asyncio.run(main())
