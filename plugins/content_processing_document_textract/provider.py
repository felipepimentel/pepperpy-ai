"""Textract provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import textract
except ImportError:
    textract = None


@lazy_provider_class("content_processing.document", "textract")
class TextractProvider:
    """Provider for document processing using Textract."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Textract provider.

        Args:
            **kwargs: Additional configuration options
                - encoding: str - Character encoding for text extraction
                - extension: str - Force specific file extension
                - layout: bool - Maintain original layout
                - language: str - OCR language
                - ocr_strategy: str - OCR strategy (tesseract, pdfminer)
                - preserve_formatting: bool - Preserve text formatting
                - strip_line_breaks: bool - Strip line breaks from text
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if textract is None:
                raise ContentProcessingError(
                    "Textract is not installed. Install with: pip install textract"
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using Textract.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - encoding: str - Character encoding for text extraction
                - extension: str - Force specific file extension
                - layout: bool - Maintain original layout
                - language: str - OCR language
                - ocr_strategy: str - OCR strategy (tesseract, pdfminer)
                - preserve_formatting: bool - Preserve text formatting
                - strip_line_breaks: bool - Strip line breaks from text
                - output_encoding: str - Output text encoding
                - output_path: str - Path to save extracted text

        Returns:
            Processing result with extracted text and metadata

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

            # Prepare extraction options
            extract_options = {
                'encoding': options.get('encoding', self._config.get('encoding')),
                'extension': options.get('extension', self._config.get('extension')),
                'layout': options.get('layout', self._config.get('layout')),
                'language': options.get('language', self._config.get('language')),
                'method': options.get('ocr_strategy', self._config.get('ocr_strategy')),
                'preserve_formatting': options.get(
                    'preserve_formatting',
                    self._config.get('preserve_formatting'),
                ),
                'strip_line_breaks': options.get(
                    'strip_line_breaks',
                    self._config.get('strip_line_breaks'),
                ),
            }

            # Remove None values
            extract_options = {k: v for k, v in extract_options.items() if v is not None}

            # Extract text
            text = textract.process(
                str(content_path),
                **extract_options,
            )

            # Decode text with specified encoding
            output_encoding = options.get('output_encoding', 'utf-8')
            text = text.decode(output_encoding)

            # Initialize metadata
            metadata = {
                'engine': 'textract',
                'input_path': str(content_path),
                'text': text,
                'options': extract_options,
            }

            # Save output if path provided
            output_path = options.get('output_path')
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding=output_encoding) as f:
                    f.write(text)
                metadata['output_path'] = str(output_path)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with Textract: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_text_extraction': True,
            'supports_layout_preservation': True,
            'supports_ocr': True,
            'supports_encoding': True,
            'supported_formats': [
                # Text formats
                '.txt', '.text',
                # PDF formats
                '.pdf',
                # Word formats
                '.doc', '.docx', '.odt',
                # PowerPoint formats
                '.ppt', '.pptx',
                # Excel formats
                '.xls', '.xlsx',
                # Rich text formats
                '.rtf',
                # Image formats
                '.jpg', '.jpeg', '.png', '.gif', '.bmp',
                # HTML formats
                '.html', '.htm',
                # Email formats
                '.eml',
                # Compressed formats
                '.zip',
                # eBook formats
                '.epub',
            ],
            'supported_ocr_strategies': [
                'tesseract',
                'pdfminer',
            ],
        } 