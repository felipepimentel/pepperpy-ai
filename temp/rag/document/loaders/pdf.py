"""PDF document loader implementation.

This module provides functionality for loading PDF documents.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import fitz  # PyMuPDF

from pepperpy.errors import DocumentLoadError
from pepperpy.rag.document.loaders.base import BaseDocumentLoader
from pepperpy.rag.storage.types import Document


class PDFLoader(BaseDocumentLoader):
    """PDF document loader.

    This loader handles PDF documents, with support for text extraction,
    chunking, and optional image extraction.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_by_page: bool = True,
        extract_images: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the PDF loader.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            chunk_by_page: Whether to ensure chunks don't cross page boundaries.
            extract_images: Whether to extract and include images.
            metadata: Optional metadata to associate with loaded documents.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(metadata=metadata, **kwargs)
        self.chunk_size = max(1, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))
        self.chunk_by_page = chunk_by_page
        self.extract_images = extract_images

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks.

        Returns:
            List of text chunks.
        """
        # Handle empty or short text
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk of specified size
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at paragraph/sentence
            if end < len(text):
                # Try to break at paragraph
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break != -1 and paragraph_break > start:
                    end = paragraph_break

                # Try to break at newline
                elif (
                    newline := text.rfind("\n", start, end)
                ) != -1 and newline > start:
                    end = newline

                # Try to break at sentence
                elif (period := text.rfind(". ", start, end)) != -1 and period > start:
                    end = period + 1

                # Try to break at space
                elif (space := text.rfind(" ", start, end)) != -1 and space > start:
                    end = space

            # Add chunk
            chunks.append(text[start:end].strip())

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap

        return chunks

    def _extract_page_text(
        self,
        page: fitz.Page,
        page_number: int,
        total_pages: int,
    ) -> List[Document.Chunk]:
        """Extract text and image information from a PDF page.

        Args:
            page: PDF page to extract from.
            page_number: Current page number (0-based).
            total_pages: Total number of pages.

        Returns:
            List of document chunks.
        """
        chunks = []

        # Get page text
        text = page.get_text()
        if not text:
            return chunks

        # Get page size
        page_width = page.rect.width
        page_height = page.rect.height

        # Split text into chunks if needed
        if self.chunk_by_page:
            # Each page is a single chunk
            chunk = Document.Chunk(
                content=text,
                metadata={
                    "page_number": page_number + 1,
                    "total_pages": total_pages,
                    "page_width": page_width,
                    "page_height": page_height,
                },
            )
            chunks.append(chunk)
        else:
            # Split page text into chunks
            chunk_texts = self._chunk_text(text)
            for i, chunk_text in enumerate(chunk_texts):
                chunk = Document.Chunk(
                    content=chunk_text,
                    metadata={
                        "page_number": page_number + 1,
                        "total_pages": total_pages,
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts),
                        "page_width": page_width,
                        "page_height": page_height,
                    },
                )
                chunks.append(chunk)

        # Extract images if requested
        if self.extract_images:
            for img_index, img in enumerate(page.get_images()):
                # Get image metadata
                xref = img[0]  # Cross-reference number
                base_image = page.parent.extract_image(xref)
                if not base_image:
                    continue

                # Create image chunk
                image_chunk = Document.Chunk(
                    content=f"[Image {img_index + 1} on page {page_number + 1}]",
                    metadata={
                        "page_number": page_number + 1,
                        "total_pages": total_pages,
                        "content_type": base_image["ext"],
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "size": len(base_image["image"]),
                        "is_image": True,
                    },
                )
                chunks.append(image_chunk)

        return chunks

    async def _load_from_file(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Document]:
        """Load PDF from a file.

        Args:
            file_path: Path to the PDF file.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If file reading fails.
        """
        try:
            # Open PDF file in executor to avoid blocking
            path = Path(file_path)
            loop = asyncio.get_event_loop()
            pdf = await loop.run_in_executor(None, fitz.open, str(path))

            try:
                # Get document metadata
                metadata = {
                    "source": str(path),
                    "content_type": "application/pdf",
                    "title": pdf.metadata.get("title"),
                    "author": pdf.metadata.get("author"),
                    "subject": pdf.metadata.get("subject"),
                    "keywords": pdf.metadata.get("keywords"),
                    "creator": pdf.metadata.get("creator"),
                    "producer": pdf.metadata.get("producer"),
                    "creation_date": pdf.metadata.get("creationDate"),
                    "modification_date": pdf.metadata.get("modDate"),
                    "page_count": len(pdf),
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "chunk_by_page": self.chunk_by_page,
                }

                # Process each page
                chunks = []
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    page_chunks = self._extract_page_text(
                        page=page,
                        page_number=page_num,
                        total_pages=len(pdf),
                    )
                    chunks.extend(page_chunks)

                # Create document if we have chunks
                if chunks:
                    doc = Document(chunks=chunks, metadata=metadata)
                    return [doc]
                return []

            finally:
                # Always close the PDF
                pdf.close()

        except Exception as e:
            raise DocumentLoadError(f"Error reading PDF file: {str(e)}") from e

    async def _load_from_string(
        self,
        content: Union[str, bytes],
        **kwargs: Any,
    ) -> List[Document]:
        """Load PDF from a string.

        Args:
            content: PDF content as bytes or base64 string.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If PDF processing fails.
        """
        try:
            # Convert string to bytes if needed
            if isinstance(content, str):
                try:
                    # Try decoding as base64
                    import base64

                    pdf_bytes = base64.b64decode(content)
                except Exception:
                    # If not base64, encode as UTF-8
                    pdf_bytes = content.encode("utf-8")
            else:
                pdf_bytes = content

            # Open PDF from memory buffer
            loop = asyncio.get_event_loop()
            pdf = await loop.run_in_executor(
                None,
                lambda: fitz.open(stream=pdf_bytes, filetype="pdf"),
            )

            try:
                # Get document metadata
                metadata = {
                    "content_type": "application/pdf",
                    "title": pdf.metadata.get("title"),
                    "author": pdf.metadata.get("author"),
                    "subject": pdf.metadata.get("subject"),
                    "keywords": pdf.metadata.get("keywords"),
                    "creator": pdf.metadata.get("creator"),
                    "producer": pdf.metadata.get("producer"),
                    "creation_date": pdf.metadata.get("creationDate"),
                    "modification_date": pdf.metadata.get("modDate"),
                    "page_count": len(pdf),
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "chunk_by_page": self.chunk_by_page,
                }

                # Process each page
                chunks = []
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    page_chunks = self._extract_page_text(
                        page=page,
                        page_number=page_num,
                        total_pages=len(pdf),
                    )
                    chunks.extend(page_chunks)

                # Create document if we have chunks
                if chunks:
                    doc = Document(chunks=chunks, metadata=metadata)
                    return [doc]
                return []

            finally:
                # Always close the PDF
                pdf.close()

        except Exception as e:
            raise DocumentLoadError(f"Error processing PDF content: {str(e)}") from e
