"""PyMuPDF document processing provider."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from ..base import (
    DocumentMetadata,
    DocumentProcessingError,
    DocumentProcessingProvider,
    DocumentType,
)


class PyMuPDFProvider(DocumentProcessingProvider):
    """Document processing provider using PyMuPDF."""

    def __init__(
        self,
        name: str = "pymupdf",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize PyMuPDF provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional configuration options
        """
        super().__init__(name=name, config=config, **kwargs)

        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF (fitz) is not installed. "
                "Install it with: pip install pymupdf"
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
        """Extract text from document using PyMuPDF.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments
                - page_numbers: List of page numbers to extract (zero-based)
                - extract_tables: Whether to extract tables as text
                - extract_images: Whether to extract image captions/OCR

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
            page_numbers = kwargs.get("page_numbers", None)

            # Open document with PyMuPDF
            doc = fitz.open(file_path)

            # Extract text
            if page_numbers is not None:
                # Extract specific pages
                pages = [doc[i] for i in page_numbers if 0 <= i < len(doc)]
                text = "\n\n".join(page.get_text() for page in pages)
            else:
                # Extract all pages
                text = ""
                for page in doc:
                    text += page.get_text() + "\n\n"

            return text.strip()

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
        """Extract metadata from document using PyMuPDF.

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

            # Open document with PyMuPDF
            doc = fitz.open(file_path)

            # Get basic metadata
            meta = doc.metadata

            # Calculate additional metadata
            page_count = len(doc)
            word_count = sum(len(page.get_text().split()) for page in doc)

            # Extract dates
            creation_date = meta.get("creationDate", None)
            modification_date = meta.get("modDate", None)

            # Convert PDF dates to ISO format if available
            if creation_date and creation_date.startswith("D:"):
                try:
                    # PDF dates are in format "D:YYYYMMDDHHmmSSOHH'mm'"
                    # Extract the date part and convert to ISO format
                    date_str = creation_date[2:14]  # YYYYMMDDHHmm
                    date = datetime.strptime(date_str, "%Y%m%d%H%M")
                    creation_date = date.isoformat()
                except Exception:
                    # Keep original if parsing fails
                    pass

            if modification_date and modification_date.startswith("D:"):
                try:
                    date_str = modification_date[2:14]
                    date = datetime.strptime(date_str, "%Y%m%d%H%M")
                    modification_date = date.isoformat()
                except Exception:
                    pass

            # Create metadata object
            metadata = DocumentMetadata(
                filename=file_path.name,
                content_type="application/pdf",
                creation_date=creation_date,
                modification_date=modification_date,
                author=meta.get("author", None),
                title=meta.get("title", None),
                page_count=page_count,
                word_count=word_count,
                language=meta.get("language", None),
                custom={
                    "producer": meta.get("producer", None),
                    "creator": meta.get("creator", None),
                    "keywords": meta.get("keywords", None),
                    "format": "PDF " + (meta.get("format", "Unknown")),
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

    async def extract_images(
        self,
        file_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract images from document using PyMuPDF.

        Args:
            file_path: Path to document
            output_dir: Directory to save extracted images
            **kwargs: Additional provider-specific arguments
                - min_size: Minimum image size in pixels (width*height)
                - page_numbers: List of page numbers to extract images from

        Returns:
            List of image information

        Raises:
            DocumentProcessingError: If image extraction fails
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
            min_size = kwargs.get("min_size", 100)  # Minimum pixels
            page_numbers = kwargs.get("page_numbers", None)

            # Prepare output directory if provided
            if output_dir:
                if isinstance(output_dir, str):
                    output_dir = Path(output_dir)
                os.makedirs(output_dir, exist_ok=True)

            # Open document with PyMuPDF
            doc = fitz.open(file_path)

            # List to store image information
            images = []

            # Process pages
            pages_to_process = range(len(doc))
            if page_numbers is not None:
                pages_to_process = [i for i in page_numbers if 0 <= i < len(doc)]

            # Extract images
            for page_num in pages_to_process:
                page = doc[page_num]

                # Get images
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]

                    # Extract image
                    base_img = doc.extract_image(xref)
                    if base_img:
                        # Get image info
                        image_bytes = base_img["image"]
                        width = base_img.get("width", 0)
                        height = base_img.get("height", 0)

                        # Skip small images
                        if width * height < min_size:
                            continue

                        # Create filename for extracted image
                        image_filename = (
                            f"page{page_num + 1}_img{img_index + 1}.{base_img['ext']}"
                        )

                        # Save to disk if output directory provided
                        image_path = None
                        if output_dir:
                            image_path = output_dir / image_filename
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)

                        # Add to result list
                        images.append({
                            "page_number": page_num + 1,
                            "index": img_index + 1,
                            "width": width,
                            "height": height,
                            "format": base_img["ext"],
                            "colorspace": base_img.get("colorspace", None),
                            "size_bytes": len(image_bytes),
                            "path": str(image_path) if image_path else None,
                            # Include image bytes in memory if no output path
                            "data": image_bytes if not output_dir else None,
                        })

            return images

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise e
            raise DocumentProcessingError(
                f"Image extraction failed: {e}",
                provider=self.name,
                document_path=str(file_path),
            )

    def get_supported_document_types(self) -> List[DocumentType]:
        """Get list of document types supported by this provider.

        Returns:
            List of supported document types
        """
        return [
            DocumentType.PDF,
            DocumentType.TEXT,  # PyMuPDF can also open text files
        ]
