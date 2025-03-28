"""LangChain document processing provider."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    # Langchain document loaders
    from langchain.document_loaders import (
        CSVLoader,
        Docx2txtLoader,
        PyMuPDFLoader,
        TextLoader,
        UnstructuredHTMLLoader,
        UnstructuredImageLoader,
        UnstructuredMarkdownLoader,
    )

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from ..base import (
    DocumentMetadata,
    DocumentProcessingError,
    DocumentProcessingProvider,
    DocumentType,
)


class LangChainProvider(DocumentProcessingProvider):
    """Document processing provider using LangChain document loaders."""

    def __init__(
        self,
        name: str = "langchain",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LangChain provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional configuration options
        """
        super().__init__(name=name, config=config, **kwargs)

        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. " "Install it with: pip install langchain"
            )

    async def _initialize(self) -> None:
        """Initialize provider."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def extract_text(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> str:
        """Extract text from document using LangChain loaders.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments

        Returns:
            Extracted text

        Raises:
            DocumentProcessingError: If text extraction fails
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                raise DocumentProcessingError(
                    f"File not found: {file_path}",
                    provider=self.name,
                    document_path=str(file_path),
                )

            # Get loader for file type
            loader = self._get_loader(file_path)

            # Load documents
            docs = loader.load()

            # Combine text from all documents
            text = "\n\n".join(doc.page_content for doc in docs)

            return text

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise e
            raise DocumentProcessingError(
                f"Text extraction failed: {e}",
                provider=self.name,
                document_path=str(file_path),
            )

    async def extract_metadata(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> DocumentMetadata:
        """Extract metadata from document using LangChain.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments

        Returns:
            Document metadata

        Raises:
            DocumentProcessingError: If metadata extraction fails
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                raise DocumentProcessingError(
                    f"File not found: {file_path}",
                    provider=self.name,
                    document_path=str(file_path),
                )

            # Get loader for file type
            loader = self._get_loader(file_path)

            # Load documents
            docs = loader.load()

            # Determine content type based on file extension
            content_type = self._get_content_type(file_path)

            # Get file stats
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Calculate simple word count from all documents
            word_count = sum(len(doc.page_content.split()) for doc in docs)

            # Create metadata object
            metadata = DocumentMetadata(
                filename=file_path.name,
                content_type=content_type,
                modification_date=modified_time,
                page_count=len(docs),
                word_count=word_count,
                custom={
                    "langchain_metadata": [doc.metadata for doc in docs],
                    "file_size": stat.st_size,
                },
            )

            return metadata

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise e
            raise DocumentProcessingError(
                f"Metadata extraction failed: {e}",
                provider=self.name,
                document_path=str(file_path),
            )

    def _get_loader(self, file_path: Path) -> Any:
        """Get appropriate LangChain loader for file type.

        Args:
            file_path: Path to document

        Returns:
            LangChain document loader

        Raises:
            DocumentProcessingError: If no loader is available for the file type
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return PyMuPDFLoader(str(file_path))
        elif suffix == ".docx":
            return Docx2txtLoader(str(file_path))
        elif suffix in [".md", ".markdown"]:
            return UnstructuredMarkdownLoader(str(file_path))
        elif suffix in [".html", ".htm"]:
            return UnstructuredHTMLLoader(str(file_path))
        elif suffix == ".csv":
            return CSVLoader(str(file_path))
        elif suffix in [".txt", ".text"]:
            return TextLoader(str(file_path))
        elif suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            return UnstructuredImageLoader(str(file_path))
        else:
            # Default to text loader as fallback
            try:
                return TextLoader(str(file_path))
            except Exception:
                raise DocumentProcessingError(
                    f"Unsupported file type: {suffix}",
                    provider=self.name,
                    document_path=str(file_path),
                )

    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME content type for file.

        Args:
            file_path: Path to document

        Returns:
            MIME content type
        """
        suffix = file_path.suffix.lower()

        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown",
            ".markdown": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".text": "text/plain",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }

        return content_types.get(suffix, "application/octet-stream")

    def get_supported_document_types(self) -> List[DocumentType]:
        """Get list of document types supported by this provider.

        Returns:
            List of supported document types
        """
        return [
            DocumentType.PDF,
            DocumentType.TEXT,
            DocumentType.MARKDOWN,
            DocumentType.HTML,
            DocumentType.DOCX,
            DocumentType.CSV,
            DocumentType.IMAGE,
        ]
