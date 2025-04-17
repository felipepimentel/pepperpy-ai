"""Document processing workflow recipe plugin."""

import logging
from pathlib import Path
from typing import Any

from pepperpy.content.providers.document.pymupdf import PyMuPDFProvider
from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider

logger = logging.getLogger(__name__)


class TextExtractionStage(PipelineStage):
    """Stage for extracting text from documents."""

    def __init__(
        self,
        provider: PyMuPDFProvider | None = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: str | None = None,
    ) -> None:
        """Initialize stage.

        Args:
            provider: Content processing provider (optional)
            extract_metadata: Whether to extract metadata
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            password: Password for protected documents (optional)
        """
        super().__init__(
            name="text_extraction", description="Extract text from documents"
        )
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
        input_data: str | Path | dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (file path or dict)
            context: Pipeline context

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


class DocumentBatchStage(PipelineStage):
    """Stage for processing batches of documents."""

    def __init__(
        self,
        provider: PyMuPDFProvider | None = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: str | None = None,
    ) -> None:
        """Initialize stage.

        Args:
            provider: Content processing provider (optional)
            extract_metadata: Whether to extract metadata
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            password: Password for protected documents (optional)
        """
        super().__init__(
            name="document_batch", description="Process batches of documents"
        )
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
        input_data: list[str | Path] | dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (list of file paths or dict)
            context: Pipeline context

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


class DocumentDirectoryStage(PipelineStage):
    """Stage for processing directories of documents."""

    def __init__(
        self,
        provider: PyMuPDFProvider | None = None,
        extract_metadata: bool = True,
        extract_images: bool = False,
        extract_tables: bool = False,
        password: str | None = None,
        recursive: bool = True,
        file_types: list[str] | None = None,
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
        super().__init__(
            name="document_directory", description="Process directories of documents"
        )
        self.provider = provider or PyMuPDFProvider()
        self.extract_metadata = extract_metadata
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.password = password
        self.recursive = recursive
        self.file_types = file_types or [".pdf", ".xps", ".epub", ".cbz"]

    async def initialize(self) -> None:
        """Initialize stage."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up stage."""
        await self.provider.cleanup()

    async def process(
        self,
        input_data: str | Path | dict[str, Any],
        context: PipelineContext,
    ) -> dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data (directory path or dict)
            context: Pipeline context

        Returns:
            Dictionary with processing results
        """
        # Get directory path
        if isinstance(input_data, (str, Path)):
            dir_path = Path(input_data)
        elif isinstance(input_data, dict) and "directory_path" in input_data:
            dir_path = Path(input_data["directory_path"])
        else:
            raise ValueError("Invalid input data")

        # Check if directory exists
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory not found: {dir_path}")

        # Find document files
        file_paths = []
        pattern = "**/*" if self.recursive else "*"
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
        return {
            "directory": str(dir_path),
            "num_files": len(file_paths),
            "results": results,
        }


class DocumentProcessingWorkflow(WorkflowProvider, BasePluginProvider):
    """Document processing workflow provider."""

    async def initialize(self) -> None:
        """Initialize the workflow."""
        await super().initialize()

        # Get configuration
        self._extract_metadata = self.config.get("extract_metadata", True)
        self._extract_images = self.config.get("extract_images", False)
        self._extract_tables = self.config.get("extract_tables", False)
        self._password = self.config.get("password")
        self._recursive = self.config.get("recursive", True)
        self._file_types = self.config.get(
            "file_types", [".pdf", ".xps", ".epub", ".cbz"]
        )

        # Initialize pipeline stages
        self._provider = PyMuPDFProvider()
        await self._provider.initialize()

        self._document_stage = TextExtractionStage(
            provider=self._provider,
            extract_metadata=self._extract_metadata,
            extract_images=self._extract_images,
            extract_tables=self._extract_tables,
            password=self._password,
        )

        self._batch_stage = DocumentBatchStage(
            provider=self._provider,
            extract_metadata=self._extract_metadata,
            extract_images=self._extract_images,
            extract_tables=self._extract_tables,
            password=self._password,
        )

        self._directory_stage = DocumentDirectoryStage(
            provider=self._provider,
            extract_metadata=self._extract_metadata,
            extract_images=self._extract_images,
            extract_tables=self._extract_tables,
            password=self._password,
            recursive=self._recursive,
            file_types=self._file_types,
        )

        self.logger.debug(
            f"Document processing workflow initialized with extract_metadata={self._extract_metadata}, "
            f"extract_images={self._extract_images}, extract_tables={self._extract_tables}"
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, "_provider") and self._provider:
            await self._provider.cleanup()

        # Always call parent cleanup
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with task and parameters:
                {
                    "task": str,  # Task type: process_document, process_batch, process_directory
                    "document_path": str,  # Path to document (for process_document)
                    "document_paths": List[str],  # List of paths (for process_batch)
                    "directory_path": str,  # Directory path (for process_directory)
                    "options": Dict[str, Any]  # Processing options
                }

        Returns:
            Dictionary with processing results and status
        """
        try:
            # Get task type and options
            task = input_data.get("task", "process_document")
            options = input_data.get("options", {})

            if task == "process_document":
                if "document_path" not in input_data:
                    return {
                        "status": "error",
                        "message": "Missing document_path parameter",
                    }

                result = await self.process_document(
                    input_data["document_path"], **options
                )
                result["status"] = "success"
                return result

            elif task == "process_batch":
                if "document_paths" not in input_data:
                    return {
                        "status": "error",
                        "message": "Missing document_paths parameter",
                    }

                result = await self.process_batch(
                    input_data["document_paths"], **options
                )
                result["status"] = "success"
                return result

            elif task == "process_directory":
                if "directory_path" not in input_data:
                    return {
                        "status": "error",
                        "message": "Missing directory_path parameter",
                    }

                result = await self.process_directory(
                    input_data["directory_path"], **options
                )
                result["status"] = "success"
                return result

            else:
                return {"status": "error", "message": f"Unknown task: {task}"}

        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {"status": "error", "message": str(e)}

    # Keep the rest of the methods unchanged
    async def process_document(
        self, document_path: str | Path, **options: Any
    ) -> dict[str, Any]:
        """Process a single document.

        Args:
            document_path: Path to the document
            **options: Additional processing options

        Returns:
            Dictionary with processing results
        """
        context = PipelineContext()
        for key, value in options.items():
            context.set(key, value)
        return await self._document_stage.process(document_path, context)

    async def process_batch(
        self, document_paths: list[str | Path], **options: Any
    ) -> dict[str, Any]:
        """Process multiple documents.

        Args:
            document_paths: List of paths to documents
            **options: Additional processing options

        Returns:
            Dictionary with processing results
        """
        context = PipelineContext()
        for key, value in options.items():
            context.set(key, value)
        return await self._batch_stage.process(document_paths, context)

    async def process_directory(
        self, directory_path: str | Path, **options: Any
    ) -> dict[str, Any]:
        """Process all documents in a directory.

        Args:
            directory_path: Path to directory containing documents
            **options: Additional processing options

        Returns:
            Dictionary with processing results
        """
        context = PipelineContext()
        for key, value in options.items():
            context.set(key, value)
        return await self._directory_stage.process(directory_path, context)

    async def create_workflow(self, workflow_config: dict[str, Any]) -> Any:
        """Create a workflow instance.

        Args:
            workflow_config: Workflow configuration

        Returns:
            The workflow instance
        """
        return self

    async def execute_workflow(
        self, workflow: Any, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a workflow with the given input.

        Args:
            workflow: The workflow instance
            input_data: Input data

        Returns:
            The workflow results
        """
        return await self.execute(input_data)
