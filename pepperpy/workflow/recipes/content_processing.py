"""Content processing workflow recipes.

This module provides workflow recipes for content processing tasks.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.content_processing.base import ContentProcessor
from pepperpy.content_processing.errors import ContentProcessingError
from pepperpy.core.base import PepperpyError
from pepperpy.workflow.base import WorkflowStage

logger = logging.getLogger(__name__)


class ContentProcessingError(PepperpyError):
    """Error raised during content processing workflow."""

    pass


class TextExtractionStage(WorkflowStage):
    """Stage for extracting text from various content types."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        content_type: Optional[str] = None,
        extract_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize text extraction stage.

        Args:
            content_processor: Content processor instance
            content_type: Content type to process (optional)
            extract_metadata: Whether to extract metadata
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.content_type = content_type
        self.extract_metadata = extract_metadata

    async def process(
        self,
        content_path: Union[str, Path],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process content and extract text.

        Args:
            content_path: Path to content file
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Process content
            result = await self.content_processor.process(
                content_path=content_path,
                content_type=self.content_type,
                extract_metadata=self.extract_metadata,
                **kwargs,
            )

            # Check if text was extracted
            if not result.metadata.get("text"):
                raise ContentProcessingError(
                    f"No text extracted from content: {content_path}"
                )

            return {
                "text": result.metadata["text"],
                "metadata": result.metadata,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error extracting text: {e}")


class ArchiveExtractionStage(WorkflowStage):
    """Stage for extracting and processing archive contents."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        output_path: Optional[Union[str, Path]] = None,
        file_extensions: Optional[Set[str]] = None,
        recursive: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize archive extraction stage.

        Args:
            content_processor: Content processor instance
            output_path: Path to extract contents (optional)
            file_extensions: Set of file extensions to process
            recursive: Whether to process subdirectories
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.output_path = output_path
        self.file_extensions = file_extensions
        self.recursive = recursive

    async def process(
        self,
        archive_path: Union[str, Path],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract and process archive contents.

        Args:
            archive_path: Path to archive file
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Extract archive
            extract_result = await self.content_processor.extract_archive(
                archive_path=archive_path,
                output_path=self.output_path,
                **kwargs,
            )

            # Process extracted files
            processed_files = []
            output_path = Path(extract_result["output_path"])

            # Find files to process
            if self.recursive:
                all_files = list(output_path.rglob("*"))
            else:
                all_files = list(output_path.glob("*"))

            # Filter by file extension
            for file_path in all_files:
                if file_path.is_file():
                    if (
                        self.file_extensions is None
                        or file_path.suffix.lower() in self.file_extensions
                    ):
                        try:
                            # Process file
                            result = await self.content_processor.process(
                                content_path=file_path,
                                **kwargs,
                            )
                            processed_files.append({
                                "path": str(file_path),
                                "result": result,
                            })
                        except Exception as e:
                            logger.warning(f"Error processing file {file_path}: {e}")

            return {
                "output_path": str(output_path),
                "num_files": len(processed_files),
                "processed_files": processed_files,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error processing archive: {e}")


class ProtectedContentStage(WorkflowStage):
    """Stage for handling password-protected content."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize protected content stage.

        Args:
            content_processor: Content processor instance
            output_path: Path to save unlocked content (optional)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.output_path = output_path

    async def process(
        self,
        content_path: Union[str, Path],
        password: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process password-protected content.

        Args:
            content_path: Path to protected content file
            password: Password to unlock content
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Unlock content
            unlock_result = await self.content_processor.unlock_content(
                content_path=content_path,
                password=password,
                output_path=self.output_path,
                **kwargs,
            )

            # Process unlocked content
            result = await self.content_processor.process(
                content_path=unlock_result["output_path"],
                **kwargs,
            )

            return {
                "unlocked_path": unlock_result["output_path"],
                "result": result,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error processing protected content: {e}")


class ContentRAGStage(WorkflowStage):
    """Stage for integrating content processing with RAG."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        chunker: Any,
        rag: Any,
        collection_name: Optional[str] = None,
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize content RAG stage.

        Args:
            content_processor: Content processor instance
            chunker: Text chunker instance
            rag: RAG system instance
            collection_name: Name of RAG collection/namespace
            include_metadata: Whether to include content metadata in RAG documents
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.chunker = chunker
        self.rag = rag
        self.collection_name = collection_name
        self.include_metadata = include_metadata

    async def process(
        self,
        content_path: Union[str, Path],
        content_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process content and index it for RAG.

        Args:
            content_path: Path to content file
            content_id: Unique ID for the content
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Process content
            result = await self.content_processor.process(
                content_path=content_path,
                **kwargs,
            )

            # Check if text was extracted
            if not result.metadata.get("text"):
                raise ContentProcessingError(
                    f"No text extracted from content: {content_path}"
                )

            # Set content ID if not provided
            if content_id is None:
                content_id = str(Path(content_path).stem)

            # Set collection name if not provided
            if self.collection_name is None:
                self.collection_name = "content"

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
                collection_name=self.collection_name,
            )

            return {
                "collection_name": self.collection_name,
                "content_id": content_id,
                "num_chunks": len(chunks),
                "metadata": result.metadata,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error processing content for RAG: {e}")


class DirectoryProcessingStage(WorkflowStage):
    """Stage for processing all content files in a directory."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        file_extensions: Optional[Set[str]] = None,
        recursive: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize directory processing stage.

        Args:
            content_processor: Content processor instance
            file_extensions: Set of file extensions to process
            recursive: Whether to process subdirectories
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.file_extensions = file_extensions
        self.recursive = recursive

    async def process(
        self,
        directory_path: Union[str, Path],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process all content files in a directory.

        Args:
            directory_path: Path to directory
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Convert to Path
            if isinstance(directory_path, str):
                directory_path = Path(directory_path)

            # Check if directory exists
            if not directory_path.exists():
                raise ContentProcessingError(f"Directory not found: {directory_path}")

            if not directory_path.is_dir():
                raise ContentProcessingError(f"Not a directory: {directory_path}")

            # Find files to process
            if self.recursive:
                all_files = list(directory_path.rglob("*"))
            else:
                all_files = list(directory_path.glob("*"))

            # Filter by file extension
            processed_files = []
            for file_path in all_files:
                if file_path.is_file():
                    if (
                        self.file_extensions is None
                        or file_path.suffix.lower() in self.file_extensions
                    ):
                        try:
                            # Process file
                            result = await self.content_processor.process(
                                content_path=file_path,
                                **kwargs,
                            )
                            processed_files.append({
                                "path": str(file_path),
                                "result": result,
                            })
                        except Exception as e:
                            logger.warning(f"Error processing file {file_path}: {e}")

            return {
                "directory_path": str(directory_path),
                "num_files": len(processed_files),
                "processed_files": processed_files,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error processing directory: {e}")


class BatchProcessingStage(WorkflowStage):
    """Stage for processing multiple content files in batch."""

    def __init__(
        self,
        content_processor: ContentProcessor,
        max_concurrent: int = 5,
        **kwargs: Any,
    ) -> None:
        """Initialize batch processing stage.

        Args:
            content_processor: Content processor instance
            max_concurrent: Maximum number of concurrent tasks
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.content_processor = content_processor
        self.max_concurrent = max_concurrent

    async def process(
        self,
        content_paths: List[Union[str, Path]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process multiple content files in batch.

        Args:
            content_paths: List of paths to content files
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            import asyncio

            # Convert paths to Path objects
            paths = [
                Path(path) if isinstance(path, str) else path for path in content_paths
            ]

            # Check if files exist
            for path in paths:
                if not path.exists():
                    raise ContentProcessingError(f"File not found: {path}")

            # Process files in batches
            processed_files = []
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def process_file(path: Path) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        result = await self.content_processor.process(
                            content_path=path,
                            **kwargs,
                        )
                        return {
                            "path": str(path),
                            "result": result,
                        }
                    except Exception as e:
                        logger.warning(f"Error processing file {path}: {e}")
                        return {
                            "path": str(path),
                            "error": str(e),
                        }

            # Create tasks
            tasks = [process_file(path) for path in paths]

            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)

            # Filter out failed tasks
            processed_files = [result for result in results if "error" not in result]

            return {
                "num_files": len(processed_files),
                "processed_files": processed_files,
            }

        except Exception as e:
            raise ContentProcessingError(f"Error processing batch: {e}")
