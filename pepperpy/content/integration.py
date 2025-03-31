"""Integration module for content processing.

This module provides integration between content processing and other
PepperPy modules, such as RAG (Retrieval Augmented Generation).
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pepperpy.core.base import PepperpyError
from pepperpy.content.base import (
    ContentProcessor,
    ContentProcessingError,
    ContentType,
)

logger = logging.getLogger(__name__)


class ContentRAGError(PepperpyError):
    """Error raised during RAG integration."""

    pass


class ContentRAGProcessor:
    """Processor for integrating content processing with RAG."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        chunker: Any,
        rag: Any,
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize content RAG processor.

        Args:
            content_processor: Content processor instance
            chunker: Text chunker instance
            rag: RAG system instance
            include_metadata: Whether to include content metadata in RAG documents
            **kwargs: Additional configuration options
        """
        self.content_processor = content_processor
        self.chunker = chunker
        self.rag = rag
        self.include_metadata = include_metadata
        self._config = kwargs

    async def process_content(
        self,
        content_path: Union[str, Path],
        collection_name: Optional[str] = None,
        content_id: Optional[str] = None,
        extract_metadata: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process content and index it for RAG.

        Args:
            content_path: Path to content file
            collection_name: Name of RAG collection/namespace
            content_id: Unique ID for the content
            extract_metadata: Whether to extract metadata
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentRAGError: If processing fails
        """
        if isinstance(content_path, str):
            content_path = Path(content_path)

        if not content_path.exists():
            raise ContentRAGError(f"Content not found: {content_path}")

        try:
            # Set content ID if not provided
            if content_id is None:
                content_id = str(content_path.stem)

            # Set collection name if not provided
            if collection_name is None:
                collection_name = "content"

            # Process content
            result = await self.content_processor.process(
                content_path,
                extract_metadata=extract_metadata,
                **kwargs,
            )

            # Check if text was extracted
            if not result.metadata.get("text"):
                raise ContentRAGError(
                    f"No text extracted from content: {content_path}"
                )

            # Chunk text
            chunks = self.chunker.create_chunks(result.metadata["text"])

            # Prepare documents for indexing
            rag_documents = []
            for i, chunk in enumerate(chunks):
                # Create document metadata
                metadata = {
                    "source": str(content_path),
                    "content_id": content_id,
                    "chunk_index": i,
                }

                # Add content metadata if available and requested
                if self.include_metadata:
                    for key, value in result.metadata.items():
                        # Skip non-serializable values
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            metadata[f"content_{key}"] = value

                # Create RAG document
                rag_document = self.rag.Document(
                    page_content=chunk,
                    metadata=metadata,
                )
                rag_documents.append(rag_document)

            # Add documents to RAG system
            self.rag.add_documents(
                documents=rag_documents,
                collection_name=collection_name,
            )

            # Return results
            return {
                "collection_name": collection_name,
                "content_id": content_id,
                "num_chunks": len(chunks),
                "metadata": result.metadata,
            }

        except Exception as e:
            raise ContentRAGError(f"Error processing content for RAG: {e}")

    async def process_directory(
        self,
        directory_path: Union[str, Path],
        collection_name: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[Set[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process all content files in a directory.

        Args:
            directory_path: Path to directory
            collection_name: Name of RAG collection/namespace
            recursive: Whether to process subdirectories
            file_extensions: Set of file extensions to process
            progress_callback: Optional callback for progress updates
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentRAGError: If processing fails
        """
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        if not directory_path.exists():
            raise ContentRAGError(f"Directory not found: {directory_path}")

        if not directory_path.is_dir():
            raise ContentRAGError(f"Not a directory: {directory_path}")

        try:
            # Set collection name if not provided
            if collection_name is None:
                collection_name = directory_path.name

            # Collect files to process
            files_to_process = []
            if recursive:
                # Use rglob to find files recursively
                all_files = list(directory_path.rglob("*"))
            else:
                # Use glob to find files in current directory only
                all_files = list(directory_path.glob("*"))

            # Filter by file extension if provided
            for file_path in all_files:
                if file_path.is_file():
                    if (
                        file_extensions is None
                        or file_path.suffix.lower() in file_extensions
                    ):
                        files_to_process.append(file_path)

            # Check if any files found
            if not files_to_process:
                return {
                    "collection_name": collection_name,
                    "num_contents": 0,
                    "num_chunks": 0,
                    "processed_contents": [],
                }

            # Process each file
            processed_contents = []
            total_chunks = 0

            for i, file_path in enumerate(files_to_process):
                # Report progress
                if progress_callback:
                    progress_callback(i, len(files_to_process), str(file_path))

                try:
                    # Process content
                    content_id = str(file_path.relative_to(directory_path))
                    result = await self.process_content(
                        content_path=file_path,
                        collection_name=collection_name,
                        content_id=content_id,
                        **kwargs,
                    )
                    processed_contents.append(result)
                    total_chunks += result.get("num_chunks", 0)
                except Exception as e:
                    logger.warning(f"Error processing content {file_path}: {e}")

            # Return results
            return {
                "collection_name": collection_name,
                "num_contents": len(processed_contents),
                "num_chunks": total_chunks,
                "processed_contents": processed_contents,
            }

        except Exception as e:
            raise ContentRAGError(f"Error processing directory for RAG: {e}") 