"""Tika provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, Union, cast

from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError
from pepperpy.core.utils import lazy_provider_class


@lazy_provider_class("content_processing.document", "tika")
class TikaProvider:
    """Provider for document processing using Apache Tika."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Tika provider.

        Args:
            **kwargs: Additional configuration options
                - tika_server_url: str - URL of Tika server
                - tika_server_endpoint: str - Endpoint for Tika server
                - tika_server_timeout: int - Server request timeout
        """
        self._config = kwargs
        self._initialized = False
        self._tika_parser = None
        self._tika_detector = None

        # Configure Tika in client-only mode
        os.environ["TIKA_CLIENT_ONLY"] = "true"
        if "tika_server_url" in kwargs:
            os.environ["TIKA_SERVER_ENDPOINT"] = str(kwargs["tika_server_url"])
        if "tika_server_endpoint" in kwargs:
            os.environ["TIKA_SERVER_ENDPOINT"] = str(kwargs["tika_server_endpoint"])
        if "tika_server_timeout" in kwargs:
            os.environ["TIKA_STARTUP_TIMEOUT"] = str(kwargs["tika_server_timeout"])

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            try:
                from tika import detector as tika_detector
                from tika import parser as tika_parser

                self._tika_parser = tika_parser
                self._tika_detector = tika_detector
                self._initialized = True
            except ImportError:
                raise ContentProcessingError(
                    "Tika is not installed. Install with: pip install tika"
                )

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
        self._tika_parser = None
        self._tika_detector = None

    def _ensure_initialized(self) -> None:
        """Ensure provider is initialized."""
        if not self._initialized:
            raise ContentProcessingError(
                "Tika provider not initialized. Call initialize() first."
            )

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using Tika.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - extract_text: bool - Extract text content
                - extract_metadata: bool - Extract document metadata
                - extract_content: bool - Extract structured content
                - detect_language: bool - Detect document language
                - ocr: bool - Use OCR for text extraction
                - ocr_language: str - Language for OCR
                - recursion_level: int - Recursion level for container formats
                - max_length: int - Maximum length of extracted text
                - timeout: int - Request timeout in seconds

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        self._ensure_initialized()

        try:
            # Validate input path
            content_path = Path(content_path)
            if not content_path.exists():
                raise ContentProcessingError(f"Input file not found: {content_path}")

            # Detect content type
            if not self._tika_detector:
                raise ContentProcessingError("Tika detector not initialized")
            content_type = self._tika_detector.from_file(str(content_path))

            # Parse options
            parse_options = {
                "xmlContent": options.get("extract_content", False),
                "headers": {
                    "X-Tika-OCRLanguage": options.get("ocr_language", "eng")
                    if options.get("ocr")
                    else None,
                    "X-Tika-OCR": str(options.get("ocr", False)).lower(),
                    "X-Tika-Recursion-Level": str(options.get("recursion_level", 1)),
                    "X-Tika-Max-Length": str(options.get("max_length", -1)),
                },
            }

            if "timeout" in options:
                parse_options["timeout"] = options["timeout"]

            # Parse document
            if not self._tika_parser:
                raise ContentProcessingError("Tika parser not initialized")
            parsed = self._tika_parser.from_file(str(content_path), **parse_options)

            # Initialize metadata
            metadata: Dict[str, Any] = {
                "engine": "tika",
                "content_type": content_type,
            }

            # Add extracted metadata if requested
            if (
                options.get("extract_metadata", True)
                and isinstance(parsed, dict)
                and "metadata" in parsed
            ):
                parsed_metadata = cast(Dict[str, Any], parsed["metadata"])
                metadata.update(parsed_metadata)

            # Add extracted text if requested
            if (
                options.get("extract_text", True)
                and isinstance(parsed, dict)
                and "content" in parsed
            ):
                metadata["text"] = str(parsed["content"])

            # Add language detection if requested
            if (
                options.get("detect_language")
                and isinstance(parsed, dict)
                and "metadata" in parsed
                and isinstance(parsed["metadata"], dict)
                and "language" in parsed["metadata"]
            ):
                metadata["language"] = str(parsed["metadata"]["language"])

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with Tika: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            "supports_metadata": True,
            "supports_text_extraction": True,
            "supports_content_extraction": True,
            "supports_language_detection": True,
            "supports_ocr": True,
            "supports_recursion": True,
            "supported_formats": [
                # Text formats
                "text/plain",
                "text/csv",
                "text/html",
                "text/xml",
                "text/rtf",
                # Office formats
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.oasis.opendocument.text",
                "application/vnd.oasis.opendocument.spreadsheet",
                "application/vnd.oasis.opendocument.presentation",
                # PDF formats
                "application/pdf",
                # Archive formats
                "application/zip",
                "application/x-tar",
                "application/x-gzip",
                "application/x-bzip2",
                # Email formats
                "message/rfc822",
                # HTML/XML formats
                "application/xhtml+xml",
                "application/xml",
                # Image formats
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/tiff",
                # Audio formats
                "audio/mpeg",
                "audio/wav",
                # Video formats
                "video/mp4",
                "video/quicktime",
            ],
        }
