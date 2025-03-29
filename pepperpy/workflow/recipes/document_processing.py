"""Document processing workflow recipes.

This module provides workflow recipes for document processing tasks.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.content_processing.base import ContentType
from pepperpy.content_processing.providers.document.pymupdf import PyMuPDFProvider
from pepperpy.workflow.base import WorkflowStage

logger = logging.getLogger(__name__)


class TextExtractionStage(WorkflowStage):
    """Stage for extracting text from documents."""

    def __init__(
        self,
        provider: Optional[PyMuPDFProvider] = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: Optional[str] = None,
    ) -> None:
        """Initialize stage.

        Args:
            provider: Content processing provider (optional)
            extract_metadata: Whether to extract metadata
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            password: Password for protected documents (optional)
        """
        super().__init__()
        self.provider = provider or PyMuPDFProvider()
        self.extract_metadata = extract_metadata
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.password = password

    async def initialize(self) -> None:
        """Initialize stage."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up stage."""
        await self.provider.cleanup()

    async def process(
        self,
        input_data: Union[str, Path, Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (file path or dict)
            **kwargs: Additional arguments

        Returns:
            Dictionary with processing results
        """
        # Get file path
        if isinstance(input_data, (str, Path)):
            file_path = Path(input_data)
        elif isinstance(input_data, dict) and "file_path" in input_data:
            file_path = Path(input_data["file_path"])
        else:
            raise ValueError("Invalid input data")

        # Process document
        result = await self.provider.process(
            file_path,
            extract_text=True,
            extract_metadata=self.extract_metadata,
            extract_images=self.extract_images,
            extract_tables=self.extract_tables,
            password=self.password,
        )

        # Return results
        return {
            "text": result["text"],
            "metadata": result.get("metadata", {}),
            "images": result.get("images", []),
            "tables": result.get("tables", []),
        }


class DocumentBatchStage(WorkflowStage):
    """Stage for processing batches of documents."""

    def __init__(
        self,
        provider: Optional[PyMuPDFProvider] = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: Optional[str] = None,
    ) -> None:
        """Initialize stage.

        Args:
            provider: Content processing provider (optional)
            extract_metadata: Whether to extract metadata
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            password: Password for protected documents (optional)
        """
        super().__init__()
        self.provider = provider or PyMuPDFProvider()
        self.extract_metadata = extract_metadata
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.password = password

    async def initialize(self) -> None:
        """Initialize stage."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up stage."""
        await self.provider.cleanup()

    async def process(
        self,
        input_data: Union[List[Union[str, Path]], Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (list of file paths or dict)
            **kwargs: Additional arguments

        Returns:
            Dictionary with processing results
        """
        # Get file paths
        if isinstance(input_data, list):
            file_paths = [Path(path) for path in input_data]
        elif isinstance(input_data, dict) and "file_paths" in input_data:
            file_paths = [Path(path) for path in input_data["file_paths"]]
        else:
            raise ValueError("Invalid input data")

        # Process documents
        results = {}
        for file_path in file_paths:
            try:
                result = await self.provider.process(
                    file_path,
                    extract_text=True,
                    extract_metadata=self.extract_metadata,
                    extract_images=self.extract_images,
                    extract_tables=self.extract_tables,
                    password=self.password,
                )
                results[str(file_path)] = {
                    "text": result["text"],
                    "metadata": result.get("metadata", {}),
                    "images": result.get("images", []),
                    "tables": result.get("tables", []),
                }
            except Exception as e:
                logger.error("Error processing %s: %s", file_path, e)
                results[str(file_path)] = {"error": str(e)}

        # Return results
        return {"results": results}


class DocumentDirectoryStage(WorkflowStage):
    """Stage for processing directories of documents."""

    def __init__(
        self,
        provider: Optional[PyMuPDFProvider] = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: Optional[str] = None,
        recursive: bool = True,
        file_types: Optional[List[str]] = None,
    ) -> None:
        """Initialize stage.

        Args:
            provider: Content processing provider (optional)
            extract_metadata: Whether to extract metadata
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            password: Password for protected documents (optional)
            recursive: Whether to process subdirectories
            file_types: List of file types to process (optional)
        """
        super().__init__()
        self.provider = provider or PyMuPDFProvider()
        self.extract_metadata = extract_metadata
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.password = password
        self.recursive = recursive
        self.file_types = file_types or [".pdf", ".docx", ".doc", ".txt"]

    async def initialize(self) -> None:
        """Initialize stage."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up stage."""
        await self.provider.cleanup()

    async def process(
        self,
        input_data: Union[str, Path, Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (directory path or dict)
            **kwargs: Additional arguments

        Returns:
            Dictionary with processing results
        """
        # Get directory path
        if isinstance(input_data, (str, Path)):
            dir_path = Path(input_data)
        elif isinstance(input_data, dict) and "dir_path" in input_data:
            dir_path = Path(input_data["dir_path"])
        else:
            raise ValueError("Invalid input data")

        # Get file paths
        pattern = "**/*" if self.recursive else "*"
        file_paths = []
        for file_type in self.file_types:
            file_paths.extend(dir_path.glob(f"{pattern}{file_type}"))

        # Process documents
        results = {}
        for file_path in file_paths:
            try:
                result = await self.provider.process(
                    file_path,
                    extract_text=True,
                    extract_metadata=self.extract_metadata,
                    extract_images=self.extract_images,
                    extract_tables=self.extract_tables,
                    password=self.password,
                )
                results[str(file_path)] = {
                    "text": result["text"],
                    "metadata": result.get("metadata", {}),
                    "images": result.get("images", []),
                    "tables": result.get("tables", []),
                }
            except Exception as e:
                logger.error("Error processing %s: %s", file_path, e)
                results[str(file_path)] = {"error": str(e)}

        # Return results
        return {"results": results}
