"""LlamaParse document processing provider."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import requests

    LLAMAPARSE_AVAILABLE = True
except ImportError:
    LLAMAPARSE_AVAILABLE = False

from ..base import (
    DocumentMetadata,
    DocumentProcessingError,
    DocumentProcessingProvider,
    DocumentType,
)


class LlamaParseProvider(DocumentProcessingProvider):
    """Document processing provider using LlamaParse API."""

    def __init__(
        self,
        name: str = "llamaparse",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LlamaParse provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional configuration options
                - api_key: LlamaParse API key
                - base_url: LlamaParse API base URL
        """
        super().__init__(name=name, config=config, **kwargs)

        if not LLAMAPARSE_AVAILABLE:
            raise ImportError(
                "Requests library is not installed. "
                "Install it with: pip install requests"
            )

        # Get API key from kwargs or environment
        self.api_key = kwargs.get("api_key") or os.environ.get(
            "PEPPERPY_DOCUMENT_PROCESSING__LLAMAPARSE__API_KEY"
        )
        if not self.api_key:
            raise ValueError(
                "LlamaParse API key not provided. "
                "Pass it as api_key or set PEPPERPY_DOCUMENT_PROCESSING__LLAMAPARSE__API_KEY"
            )

        # Set base URL from kwargs or default
        self.base_url = kwargs.get("base_url") or os.environ.get(
            "PEPPERPY_DOCUMENT_PROCESSING__LLAMAPARSE__BASE_URL",
            "https://api.llamaindex.ai/llamaparse",
        )

        # Configure additional options
        self.max_retries = kwargs.get("max_retries", 3)
        self.retry_delay = kwargs.get("retry_delay", 2)
        self.timeout = kwargs.get("timeout", 300)  # 5 minutes

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
        """Extract text from document using LlamaParse.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments
                - result_type: Type of result (markdown, text, etc.)
                - wait_for_result: Whether to wait for completion or return job ID

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
            result_type = kwargs.get("result_type", "text")
            wait_for_result = kwargs.get("wait_for_result", True)

            # Parse document with LlamaParse API
            parse_result = self._call_llamaparse_api(file_path)

            # If we should wait for the result
            if wait_for_result and "job_id" in parse_result:
                parse_result = self._wait_for_completion(parse_result["job_id"])

            # Extract the requested result format
            if "result" in parse_result:
                result = parse_result["result"]

                if result_type == "text":
                    text = result.get("text", "")
                elif result_type == "markdown":
                    text = result.get("markdown", "")
                else:
                    # Default to full result as JSON string
                    text = json.dumps(result)

                return text
            elif "job_id" in parse_result and not wait_for_result:
                # Return job ID as text if not waiting for result
                return f"LlamaParse job submitted: {parse_result['job_id']}"
            else:
                raise DocumentProcessingError(
                    "No result returned from LlamaParse API",
                    provider=self.name,
                    document_path=str(file_path),
                )

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
        """Extract metadata from document using LlamaParse.

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

            # Wait for result to get metadata
            parse_result = self._call_llamaparse_api(file_path)

            # If there's a job ID, wait for completion
            if "job_id" in parse_result:
                parse_result = self._wait_for_completion(parse_result["job_id"])

            # Extract metadata from API result
            result = parse_result.get("result", {})
            metadata_result = result.get("metadata", {})

            # Create metadata object
            metadata = DocumentMetadata(
                filename=file_path.name,
                content_type=content_type,
                creation_date=metadata_result.get("creation_date"),
                modification_date=modified_time,
                author=metadata_result.get("author"),
                title=metadata_result.get("title"),
                page_count=metadata_result.get("page_count"),
                word_count=metadata_result.get("word_count"),
                language=metadata_result.get("language"),
                custom={
                    "llamaparse_metadata": metadata_result,
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
        """Extract tables from document using LlamaParse.

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

            # Parse document with LlamaParse API
            parse_result = self._call_llamaparse_api(file_path)

            # If there's a job ID, wait for completion
            if "job_id" in parse_result:
                parse_result = self._wait_for_completion(parse_result["job_id"])

            # Extract tables from API result
            result = parse_result.get("result", {})
            tables_result = result.get("tables", [])

            # Format tables for return
            tables = []
            for i, table in enumerate(tables_result):
                tables.append({
                    "index": i,
                    "page": table.get("page", 0),
                    "caption": table.get("caption", ""),
                    "data": table.get("data", []),
                    "headers": table.get("headers", []),
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

    def _call_llamaparse_api(self, file_path: Path) -> Dict[str, Any]:
        """Call LlamaParse API to process document.

        Args:
            file_path: Path to document

        Returns:
            API response

        Raises:
            DocumentProcessingError: If API call fails
        """
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Open file for upload
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, self._get_content_type(file_path))}

            # Make API request
            response = requests.post(
                f"{self.base_url}/process",
                headers=headers,
                files=files,
                timeout=self.timeout,
            )

        # Handle API response
        if response.status_code == 200:
            return response.json()
        else:
            raise DocumentProcessingError(
                f"LlamaParse API error: {response.status_code} - {response.text}",
                provider=self.name,
                document_path=str(file_path),
            )

    def _wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        """Wait for LlamaParse job to complete.

        Args:
            job_id: LlamaParse job ID

        Returns:
            Job result

        Raises:
            DocumentProcessingError: If waiting for result fails
        """
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Poll for job completion
        retries = 0
        while retries < self.max_retries:
            # Make API request
            response = requests.get(
                f"{self.base_url}/jobs/{job_id}", headers=headers, timeout=self.timeout
            )

            # Handle API response
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                # If job completed, return result
                if status == "completed":
                    return data
                # If job failed, raise error
                elif status == "failed":
                    raise DocumentProcessingError(
                        f"LlamaParse job failed: {data.get('error', 'Unknown error')}",
                        provider=self.name,
                    )
                # If job still running, wait and retry
                else:
                    time.sleep(self.retry_delay)
                    retries += 1
            else:
                raise DocumentProcessingError(
                    f"LlamaParse API error: {response.status_code} - {response.text}",
                    provider=self.name,
                )

        # If reached max retries, raise error
        raise DocumentProcessingError(
            f"LlamaParse job timed out after {self.max_retries} retries",
            provider=self.name,
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
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
        ]
