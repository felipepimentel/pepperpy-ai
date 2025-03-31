#!/usr/bin/env python3

"""
Provider implementation for PyMuPDF document processing.
"""

import os
import tempfile
from typing import List, Optional

import fitz  # PyMuPDF

from pepperpy.content_processing.base import (
    ContentProcessor,
    ContentType,
    DocumentMetadata,
    ProcessingResult,
)


class PymupdfProvider(ContentProcessor):
    """Provider for processing documents using PyMuPDF."""

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[Any]

    def __init__(self, **kwargs):
        """Initialize the PyMuPDF document processor."""
        super().__init__(**kwargs)
        self.config = kwargs

    async def process(
        self, content: bytes, content_type: Optional[ContentType] = None, **kwargs
    ) -> ProcessingResult:
        """
        Process a document using PyMuPDF.

        Args:
            content: The document content as bytes
            content_type: The content type of the document
            **kwargs: Additional arguments

        Returns:
            ProcessingResult: The processing result

        Raises:
            ValueError: If the document format is not supported
        """
        # Determine content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(content)

        # Ensure we're dealing with a document
        if not content_type.is_document():
            raise ValueError(f"Content type {content_type} is not a document")

        # Process the document
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{content_type.extension}"
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Open the document
            doc = fitz.open(temp_file_path)

            # Extract text
            text = ""
            for page in doc:
                text += page.get_text()

            # Extract metadata
            metadata = self._extract_metadata(doc)

            # Extract images if requested
            images = []
            if kwargs.get("extract_images", False):
                images = self._extract_images(doc)

            return ProcessingResult(
                text=text,
                metadata=metadata,
                images=images,
                original_content=content,
                content_type=content_type,
            )

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def _extract_metadata(self, doc) -> DocumentMetadata:
        """Extract metadata from a PyMuPDF document."""
        meta = doc.metadata
        return DocumentMetadata(
            title=meta.get("title", ""),
            author=meta.get("author", ""),
            subject=meta.get("subject", ""),
            keywords=meta.get("keywords", ""),
            creator=meta.get("creator", ""),
            producer=meta.get("producer", ""),
            page_count=len(doc),
            file_size=0,  # We don't have the file size here
        )

    def _extract_images(self, doc) -> List[bytes]:
        """Extract images from a PyMuPDF document."""
        images = []
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append(image_bytes)
        return images

    def _detect_content_type(self, content: bytes) -> ContentType:
        """
        Detect the content type from the bytes.

        This is a simple detection based on magic numbers.
        """
        # PDF: %PDF
        if content[:4] == b"%PDF":
            return ContentType.PDF

        # DOCX: PK.. (ZIP magic) + word/ in the file
        if content[:2] == b"PK" and b"word/" in content[:200]:
            return ContentType.DOCX

        # Default to PDF if we can't detect
        return ContentType.PDF
