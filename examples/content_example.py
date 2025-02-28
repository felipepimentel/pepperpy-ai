"""Example demonstrating the content module functionality.

This example shows how to:
- Create and manage text content
- Process text with common operations
- Store and retrieve content
- Handle errors and cleanup resources

Requirements:
- Python 3.12+
- Pepperpy library

Usage:
    poetry run python examples/content_example.py
"""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, cast
from uuid import UUID, uuid4

from pepperpy.content.base import (
    ContentConfig,
    ContentMetadata,
    ContentType,
)
from pepperpy.content.loaders import TextContent
from pepperpy.content.processors import TextProcessor
from pepperpy.content.storage import LocalContentStorage
from pepperpy.core.common.base import BaseComponent, Metadata
from pepperpy.core.common.errors import ContentError, PepperpyError
from pepperpy.core.common.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Test data
TEST_CONTENT = [
    {
        "name": "introduction",
        "text": """
        The Pepperpy framework provides powerful tools for managing and processing content.
        It supports different content types, including text and files.
        The content module offers features like:
        - Content creation and management
        - Text processing operations
        - Local storage and retrieval
        - Error handling and resource cleanup
        """,
        "operations": ["strip", "normalize"],
    },
    {
        "name": "features",
        "text": """
        Key features of the content module:
        1. Content Types:
           - Text content with metadata
           - File content with paths
           - Custom content types
        2. Processing:
           - Text normalization
           - Tokenization
           - Custom processors
        3. Storage:
           - Local file storage
           - Content versioning
           - Metadata management
        """,
        "operations": ["strip", "normalize", "lower"],
    },
    {
        "name": "examples",
        "text": """
        Example usage scenarios:
        - Document processing
        - Content analysis
        - Text transformation
        - Data extraction
        - Content storage
        - Resource management
        """,
        "operations": ["strip", "normalize", "upper"],
    },
]


class ContentManager(BaseComponent):
    """Content manager for handling text content operations.

    This class demonstrates proper resource management and error handling
    for content operations.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        """Initialize the content manager.

        Args:
            storage_dir: Optional storage directory path
        """
        super().__init__(
            id=uuid4(),
            metadata=Metadata(
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version="0.1.0",
                tags=["content-example"],
                properties={},
            ),
        )
        self.config = ContentConfig(
            name="content-example",
            description="Example content manager",
            parameters={},
            metadata={},
        )
        self.storage_dir = storage_dir
        self.storage: Optional[LocalContentStorage] = None
        self.processor = TextProcessor()
        self._logger = get_logger(__name__ + ".manager")

    async def initialize(self) -> None:
        """Initialize the content manager.

        Raises:
            PepperpyError: If initialization fails
        """
        try:
            if self.storage_dir:
                self.storage = LocalContentStorage(str(self.storage_dir))
            self._logger.info("Content manager initialized")
        except Exception as e:
            self._logger.error(
                "Failed to initialize content manager",
                extra={
                    "error": str(e),
                },
            )
            raise PepperpyError(f"Failed to initialize content manager: {e}")

    async def cleanup(self) -> None:
        """Clean up resources.

        Raises:
            PepperpyError: If cleanup fails
        """
        try:
            if self.storage:
                # Clean up storage
                pass
            self._logger.info("Content manager cleaned up")
        except Exception as e:
            self._logger.error(
                "Failed to clean up content manager",
                extra={
                    "error": str(e),
                },
            )
            raise PepperpyError(f"Failed to clean up content manager: {e}")

    async def create_content(self, name: str, text: str) -> TextContent:
        """Create text content.

        Args:
            name: Content name
            text: Content text

        Returns:
            Created text content

        Raises:
            ContentError: If content creation fails
        """
        try:
            now = datetime.now(UTC).isoformat()
            content = TextContent(
                name=name,
                text=text.strip(),
                metadata=ContentMetadata(
                    id=str(uuid4()),
                    type=ContentType.TEXT.name,
                    source="example",
                    created_at=now,
                    updated_at=now,
                    tags=[],
                    metadata={},
                ),
            )
            self._logger.info(
                "Created text content",
                extra={
                    "content_name": name,
                    "content_size": len(text),
                },
            )
            return content
        except Exception as e:
            self._logger.error(
                "Failed to create content",
                extra={
                    "content_name": name,
                    "error": str(e),
                },
            )
            raise ContentError(f"Failed to create content: {e}")

    def process_content(
        self, content: TextContent, operations: list[str]
    ) -> TextContent:
        """Process content with operations.

        Args:
            content: Content to process
            operations: List of operations to apply

        Returns:
            Processed content

        Raises:
            ContentError: If processing fails
        """
        try:
            processed = self.processor.process(content, operations=operations)
            return cast(TextContent, processed)
        except Exception as e:
            self._logger.error(
                "Failed to process content",
                extra={
                    "error": str(e),
                },
            )
            raise ContentError(f"Failed to process content: {e}")

    def store_content(self, content: TextContent) -> UUID:
        """Store content.

        Args:
            content: Content to store

        Returns:
            Content ID

        Raises:
            ContentError: If storage fails
        """
        try:
            if not self.storage:
                raise ContentError("Storage not initialized")
            return self.storage.save(content)
        except Exception as e:
            self._logger.error(
                "Failed to store content",
                extra={
                    "error": str(e),
                },
            )
            raise ContentError(f"Failed to store content: {e}")

    def load_content(self, content_id: UUID) -> TextContent:
        """Load content by ID.

        Args:
            content_id: Content ID

        Returns:
            Loaded content

        Raises:
            ContentError: If loading fails
        """
        try:
            if not self.storage:
                raise ContentError("Storage not initialized")
            content = self.storage.load(content_id)
            return cast(TextContent, content)
        except Exception as e:
            self._logger.error(
                "Failed to load content",
                extra={
                    "content_id": str(content_id),
                    "error": str(e),
                },
            )
            raise ContentError(f"Failed to load content: {e}")


async def main() -> None:
    """Run the content example.

    This function demonstrates the content module functionality with proper
    resource management and error handling.

    Raises:
        PepperpyError: If example execution fails
    """
    logger.info("Starting content example")
    manager = None

    try:
        # Create temporary directory for storage
        with TemporaryDirectory() as temp_dir:
            # Initialize content manager
            manager = ContentManager(storage_dir=Path(temp_dir))
            await manager.initialize()

            # Process test content
            for test_case in TEST_CONTENT:
                try:
                    # Create content
                    content = await manager.create_content(
                        name=test_case["name"],
                        text=test_case["text"],
                    )
                    logger.info(
                        "Created content",
                        extra={
                            "content_name": content.name,
                            "content_size": len(content.data),
                        },
                    )

                    # Process content
                    processed = manager.process_content(
                        content=content,
                        operations=test_case["operations"],
                    )
                    logger.info(
                        "Processed content",
                        extra={
                            "content_name": processed.name,
                            "operations": test_case["operations"],
                        },
                    )

                    # Store content
                    content_id = manager.store_content(processed)
                    logger.info(
                        "Stored content",
                        extra={
                            "content_name": processed.name,
                            "content_id": str(content_id),
                        },
                    )

                    # Load content
                    loaded = manager.load_content(content_id)
                    logger.info(
                        "Loaded content",
                        extra={
                            "content_name": loaded.name,
                            "content_size": len(loaded.data),
                        },
                    )

                    # Print results
                    print(f"\nProcessed content: {test_case['name']}")
                    print("-" * 80)
                    print(f"Original text:\n{test_case['text'].strip()}")
                    print("-" * 80)
                    print(f"Processed text:\n{processed.data.strip()}")
                    print("-" * 80)

                except Exception as e:
                    logger.error(
                        "Failed to process test case",
                        extra={
                            "content_name": test_case["name"],
                            "error": str(e),
                        },
                        exc_info=True,
                    )

    except Exception as e:
        logger.error(
            "Content example failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise PepperpyError(f"Content example failed: {e}")

    finally:
        # Clean up
        if manager:
            await manager.cleanup()
            logger.info("Content example completed")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
