"""Tika provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    from tika import parser as tika_parser
    from tika import detector as tika_detector
except ImportError:
    tika_parser = None
    tika_detector = None


@lazy_provider_class("content_processing.document", "tika")
class TikaProvider:
    """Provider for document processing using Apache Tika."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Tika provider.

        Args:
            **kwargs: Additional configuration options
                - tika_jar_path: str - Path to Tika JAR file
                - tika_server_url: str - URL of Tika server
                - tika_server_endpoint: str - Endpoint for Tika server
                - tika_client_only: bool - Use client-only mode
                - tika_server_timeout: int - Server request timeout
        """
        self._config = kwargs
        self._initialized = False

        # Configure Tika
        if 'tika_jar_path' in kwargs:
            os.environ['TIKA_PATH'] = str(kwargs['tika_jar_path'])
        if 'tika_server_url' in kwargs:
            os.environ['TIKA_SERVER_ENDPOINT'] = str(kwargs['tika_server_url'])
        if 'tika_server_endpoint' in kwargs:
            os.environ['TIKA_SERVER_ENDPOINT'] = str(kwargs['tika_server_endpoint'])
        if 'tika_client_only' in kwargs:
            os.environ['TIKA_CLIENT_ONLY'] = str(kwargs['tika_client_only']).lower()
        if 'tika_server_timeout' in kwargs:
            os.environ['TIKA_STARTUP_TIMEOUT'] = str(kwargs['tika_server_timeout'])

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if tika_parser is None or tika_detector is None:
                raise ContentProcessingError(
                    "Tika is not installed. Install with: pip install tika"
                )

            # Test Tika installation
            try:
                from tika import tika
                tika.initVM()
            except Exception as e:
                raise ContentProcessingError(f"Failed to initialize Tika: {e}")

            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

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

        try:
            # Validate input path
            content_path = Path(content_path)
            if not content_path.exists():
                raise ContentProcessingError(f"Input file not found: {content_path}")

            # Detect content type
            content_type = tika_detector.from_file(str(content_path))

            # Parse options
            parse_options = {
                'xmlContent': options.get('extract_content', False),
                'headers': {
                    'X-Tika-OCRLanguage': options.get('ocr_language', 'eng') if options.get('ocr') else None,
                    'X-Tika-OCR': str(options.get('ocr', False)).lower(),
                    'X-Tika-Recursion-Level': str(options.get('recursion_level', 1)),
                    'X-Tika-Max-Length': str(options.get('max_length', -1)),
                },
            }

            if 'timeout' in options:
                parse_options['timeout'] = options['timeout']

            # Parse document
            parsed = tika_parser.from_file(str(content_path), **parse_options)

            # Initialize metadata
            metadata = {
                'engine': 'tika',
                'content_type': content_type,
            }

            # Add extracted metadata if requested
            if options.get('extract_metadata', True) and parsed.get('metadata'):
                metadata.update(parsed['metadata'])

            # Add extracted text if requested
            if options.get('extract_text', True) and parsed.get('content'):
                metadata['text'] = parsed['content']

            # Add language detection if requested
            if options.get('detect_language') and parsed.get('metadata', {}).get('language'):
                metadata['language'] = parsed['metadata']['language']

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
            'supports_metadata': True,
            'supports_text_extraction': True,
            'supports_content_extraction': True,
            'supports_language_detection': True,
            'supports_ocr': True,
            'supports_recursion': True,
            'supported_formats': [
                # Text formats
                '.txt', '.rtf', '.md', '.csv', '.tsv',
                # Office formats
                '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.odt', '.ods', '.odp', '.odg', '.odf',
                # PDF formats
                '.pdf',
                # Archive formats
                '.zip', '.tar', '.gz', '.bz2', '.7z',
                # Email formats
                '.eml', '.msg',
                # HTML/XML formats
                '.html', '.htm', '.xhtml', '.xml',
                # Image formats
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
                # Audio formats
                '.mp3', '.wav', '.ogg', '.flac', '.m4a',
                # Video formats
                '.mp4', '.avi', '.mov', '.wmv', '.flv',
            ],
        } 