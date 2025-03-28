"""Docling document processing provider."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import docling

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

from ..base import (
    DocumentMetadata,
    DocumentProcessingError,
    DocumentProcessingProvider,
    DocumentType,
)


class DoclingProvider(DocumentProcessingProvider):
    """Document processing provider using Docling."""

    def __init__(
        self,
        name: str = "docling",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Docling provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional configuration options
        """
        super().__init__(name=name, config=config, **kwargs)

        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling is not installed. " "Install it with: pip install docling"
            )

        # Initialize Docling specific configuration
        self._model_name = kwargs.get("model_name", "default")
        self._ocr_enabled = kwargs.get("ocr_enabled", True)
        self._language = kwargs.get("language", "eng")

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
        """Extract text from document using Docling.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments
                - ocr_enabled: Whether to use OCR for images
                - language: Language for OCR
                - model_name: Model to use for extraction

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

            # Get optional parameters
            ocr_enabled = kwargs.get("ocr_enabled", self._ocr_enabled)
            language = kwargs.get("language", self._language)
            model_name = kwargs.get("model_name", self._model_name)

            # Create a Docling parser with the specified options
            # Note: This is an example implementation as Docling's exact API may differ
            parser = docling.Parser(
                use_ocr=ocr_enabled, language=language, model=model_name
            )

            # Parse document with Docling
            document = parser.parse(str(file_path))

            # Extract text from the document
            text = document.get_text()

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
        """Extract metadata from document using Docling.

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

            # Get file stats
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Determine content type based on file extension
            content_type = self._get_content_type(file_path)

            # Create a Docling parser to extract metadata
            # Note: This is an example implementation as Docling's exact API may differ
            parser = docling.Parser(
                use_ocr=self._ocr_enabled,
                language=self._language,
                model=self._model_name,
            )

            # Parse document for metadata
            document = parser.parse(str(file_path))

            # Extract available metadata from Docling
            doc_meta = document.get_metadata()

            # Create metadata object
            metadata = DocumentMetadata(
                filename=file_path.name,
                content_type=content_type,
                creation_date=doc_meta.get("creation_date"),
                modification_date=modified_time,
                author=doc_meta.get("author"),
                title=doc_meta.get("title"),
                page_count=doc_meta.get("page_count"),
                word_count=doc_meta.get("word_count"),
                language=doc_meta.get("language"),
                custom={
                    "docling_metadata": doc_meta,
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

    async def extract_tables(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract tables from document using Docling.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments

        Returns:
            List of extracted tables

        Raises:
            DocumentProcessingError: If table extraction fails
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

            # Create a Docling parser to extract tables
            parser = docling.Parser(
                use_ocr=self._ocr_enabled,
                language=self._language,
                model=self._model_name,
            )

            # Parse document for tables
            document = parser.parse(str(file_path))

            # Extract tables
            tables = []
            for i, table in enumerate(document.get_tables()):
                tables.append({
                    "index": i,
                    "page": table.page_number,
                    "rows": table.num_rows,
                    "columns": table.num_columns,
                    "data": table.as_dict(),
                    "text": table.as_text(),
                })

            return tables

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise e
            raise DocumentProcessingError(
                f"Table extraction failed: {e}",
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
            ".doc": "application/msword",
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
            DocumentType.IMAGE,
        ]
