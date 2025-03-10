"""CSV document loader implementation.

This module provides functionality for loading CSV documents.
"""

import asyncio
import csv
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pepperpy.errors import DocumentLoadError
from pepperpy.rag.document.loaders.base import BaseDocumentLoader
from pepperpy.rag.storage.types import Document


class CSVLoader(BaseDocumentLoader):
    """CSV document loader.

    This loader handles CSV documents, with support for custom column selection,
    metadata extraction, and chunking.
    """

    def __init__(
        self,
        content_columns: Optional[Union[str, Sequence[str]]] = None,
        metadata_columns: Optional[Union[str, Sequence[str]]] = None,
        delimiter: str = ",",
        quotechar: str = '"',
        encoding: str = "utf-8",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the CSV loader.

        Args:
            content_columns: Column(s) to use as document content.
            metadata_columns: Column(s) to include as metadata.
            delimiter: CSV delimiter character.
            quotechar: CSV quote character.
            encoding: Text encoding to use when reading files.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            metadata: Optional metadata to associate with loaded documents.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(metadata=metadata, **kwargs)
        self.content_columns = (
            [content_columns] if isinstance(content_columns, str) else content_columns
        )
        self.metadata_columns = (
            [metadata_columns]
            if isinstance(metadata_columns, str)
            else metadata_columns
        )
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.chunk_size = max(1, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))

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

            # If this is not the last chunk, try to break at newline
            if end < len(text):
                # Try to break at newline
                newline = text.rfind("\n", start, end)
                if newline != -1 and newline > start:
                    end = newline

                # Try to break at space
                elif (space := text.rfind(" ", start, end)) != -1 and space > start:
                    end = space

            # Add chunk
            chunks.append(text[start:end].strip())

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap

        return chunks

    def _extract_row_content(
        self,
        row: Dict[str, str],
        headers: Sequence[str],
    ) -> str:
        """Extract content from a CSV row.

        Args:
            row: Row data as a dictionary.
            headers: List of column headers.

        Returns:
            Content string.
        """
        # Use specified columns or all columns
        content_columns = self.content_columns or list(headers)

        # Build content string
        content_parts = []
        for col in content_columns:
            if col in row and row[col]:
                content_parts.append(f"{col}: {row[col]}")

        return "\n".join(content_parts)

    def _extract_row_metadata(
        self,
        row: Dict[str, str],
        headers: Sequence[str],
        row_index: int,
    ) -> Dict[str, Any]:
        """Extract metadata from a CSV row.

        Args:
            row: Row data as a dictionary.
            headers: List of column headers.
            row_index: Index of the row.

        Returns:
            Row metadata.
        """
        metadata: Dict[str, Any] = {"row_index": row_index}

        # Use specified columns or none
        if self.metadata_columns:
            for col in self.metadata_columns:
                if col in row:
                    metadata[col] = row[col]

        return metadata

    async def _process_csv_data(
        self,
        content: str,
        source: Optional[str] = None,
    ) -> List[Document]:
        """Process CSV data into document chunks.

        Args:
            content: CSV content.
            source: Optional source identifier.

        Returns:
            List of documents.

        Raises:
            DocumentLoadError: If CSV processing fails.
        """
        try:
            # Parse CSV
            reader = csv.DictReader(
                StringIO(content),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )

            # Get headers
            headers = reader.fieldnames
            if not headers:
                raise DocumentLoadError("CSV has no headers")

            # Process rows
            documents = []
            for row_index, row in enumerate(reader):
                # Extract content and metadata
                content = self._extract_row_content(row, headers)
                if not content:
                    continue

                row_metadata = self._extract_row_metadata(row, headers, row_index)

                # Split content into chunks if needed
                chunk_texts = self._chunk_text(content)
                if not chunk_texts:
                    continue

                # Create document chunks
                chunks = []
                for i, chunk_text in enumerate(chunk_texts):
                    chunk = Document.Chunk(
                        content=chunk_text,
                        metadata={
                            "chunk_index": i,
                            "total_chunks": len(chunk_texts),
                            **row_metadata,
                        },
                    )
                    chunks.append(chunk)

                # Create document
                doc = Document(
                    chunks=chunks,
                    metadata={
                        "source": source,
                        "content_type": "text/csv",
                        "encoding": self.encoding,
                        "delimiter": self.delimiter,
                        "quotechar": self.quotechar,
                        "headers": headers,
                        "content_columns": self.content_columns,
                        "metadata_columns": self.metadata_columns,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                        "row_index": row_index,
                    }
                    if source
                    else None,
                )
                documents.append(doc)

            return documents

        except csv.Error as e:
            raise DocumentLoadError(f"Error parsing CSV: {str(e)}") from e
        except Exception as e:
            raise DocumentLoadError(f"Error processing CSV: {str(e)}") from e

    async def _load_from_file(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Document]:
        """Load CSV from a file.

        Args:
            file_path: Path to the CSV file.
            **kwargs: Additional arguments.

        Returns:
            List of loaded documents.

        Raises:
            DocumentLoadError: If file reading fails.
        """
        try:
            # Read file asynchronously
            path = Path(file_path)
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: path.read_text(encoding=self.encoding),
            )

            # Process CSV data
            return await self._process_csv_data(content, source=str(path))

        except Exception as e:
            raise DocumentLoadError(f"Error reading CSV file: {str(e)}") from e

    async def _load_from_string(
        self,
        content: str,
        **kwargs: Any,
    ) -> List[Document]:
        """Load CSV from a string.

        Args:
            content: CSV content.
            **kwargs: Additional arguments.

        Returns:
            List of loaded documents.

        Raises:
            DocumentLoadError: If CSV processing fails.
        """
        try:
            # Get source if provided
            source = kwargs.get("file_path")
            source = str(source) if source else None

            # Process CSV data
            return await self._process_csv_data(content, source=source)

        except Exception as e:
            raise DocumentLoadError(f"Error processing CSV content: {str(e)}") from e
