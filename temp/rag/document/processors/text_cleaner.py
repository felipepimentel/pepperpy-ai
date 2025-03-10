"""Text cleaning processor module.

This module provides functionality for cleaning and normalizing text content.
"""

import re
from typing import Any, List, Union

from pepperpy.errors import DocumentProcessError
from pepperpy.rag.document.processors.base import BaseDocumentProcessor
from pepperpy.rag.document.types import Document, DocumentChunk


class TextCleanerProcessor(BaseDocumentProcessor):
    """Text cleaning processor for normalizing document content.

    This processor performs various text cleaning operations such as:
    - Removing extra whitespace
    - Normalizing line endings
    - Removing HTML tags
    - Removing special characters
    - Converting text to lowercase (optional)
    - Removing URLs (optional)
    - Removing email addresses (optional)
    - Removing numbers (optional)
    """

    def __init__(
        self,
        lowercase: bool = False,
        remove_urls: bool = False,
        remove_emails: bool = False,
        remove_numbers: bool = False,
        remove_html: bool = True,
        remove_special_chars: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the text cleaner processor.

        Args:
            lowercase: Whether to convert text to lowercase.
            remove_urls: Whether to remove URLs from the text.
            remove_emails: Whether to remove email addresses from the text.
            remove_numbers: Whether to remove numbers from the text.
            remove_html: Whether to remove HTML tags from the text.
            remove_special_chars: Whether to remove special characters.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.lowercase = lowercase
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.remove_numbers = remove_numbers
        self.remove_html = remove_html
        self.remove_special_chars = remove_special_chars

        # Compile regex patterns
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        self.email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
        self.html_pattern = re.compile(r"<[^>]+>")
        self.special_chars_pattern = re.compile(r"[^a-zA-Z0-9\s]")
        self.whitespace_pattern = re.compile(r"\s+")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content.

        Args:
            text: The text to clean.

        Returns:
            The cleaned text.
        """
        if not text:
            return text

        # Remove HTML tags
        if self.remove_html:
            text = self.html_pattern.sub(" ", text)

        # Remove URLs
        if self.remove_urls:
            text = self.url_pattern.sub(" ", text)

        # Remove email addresses
        if self.remove_emails:
            text = self.email_pattern.sub(" ", text)

        # Remove numbers
        if self.remove_numbers:
            text = re.sub(r"\d+", " ", text)

        # Remove special characters
        if self.remove_special_chars:
            text = self.special_chars_pattern.sub(" ", text)

        # Convert to lowercase
        if self.lowercase:
            text = text.lower()

        # Normalize whitespace
        text = self.whitespace_pattern.sub(" ", text)
        text = text.strip()

        return text

    async def process(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> Union[Document, List[Document]]:
        """Process one or more documents by cleaning their text content.

        Args:
            documents: A single document or list of documents to process.
            **kwargs: Additional keyword arguments for processing.

        Returns:
            The processed document(s) with cleaned text content.

        Raises:
            DocumentProcessError: If an error occurs during processing.
        """
        try:
            if isinstance(documents, Document):
                documents = [documents]

            processed_docs = []
            for doc in documents:
                # Create new chunks with cleaned text
                cleaned_chunks = []
                for chunk in doc.chunks:
                    cleaned_text = self._clean_text(chunk.content)
                    cleaned_chunk = DocumentChunk(
                        content=cleaned_text,
                        metadata=chunk.metadata,
                    )
                    cleaned_chunks.append(cleaned_chunk)

                # Create new document with cleaned chunks
                processed_doc = Document(
                    chunks=cleaned_chunks,
                    metadata=doc.metadata,
                )
                processed_docs.append(processed_doc)

            return processed_docs[0] if len(processed_docs) == 1 else processed_docs

        except Exception as e:
            raise DocumentProcessError(f"Error cleaning text content: {str(e)}") from e
