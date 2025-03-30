"""Mammoth provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import mammoth
except ImportError:
    mammoth = None


@lazy_provider_class("content_processing.document", "mammoth")
class MammothProvider:
    """Provider for document processing using Mammoth."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Mammoth provider.

        Args:
            **kwargs: Additional configuration options
                - style_map: str - Custom style map
                - include_default_style_map: bool - Include default style map
                - ignore_empty_paragraphs: bool - Ignore empty paragraphs
                - convert_markdown: bool - Convert to Markdown instead of HTML
                - embed_images: bool - Embed images as data URIs
                - image_handler: Callable - Custom image handler function
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if mammoth is None:
                raise ContentProcessingError(
                    "Mammoth is not installed. Install with: pip install mammoth"
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    def _create_converter(self, **options: Any) -> mammoth.DocumentConverter:
        """Create document converter with options.

        Args:
            **options: Converter options
                - style_map: str - Custom style map
                - include_default_style_map: bool - Include default style map
                - ignore_empty_paragraphs: bool - Ignore empty paragraphs
                - convert_markdown: bool - Convert to Markdown instead of HTML
                - embed_images: bool - Embed images as data URIs
                - image_handler: Callable - Custom image handler function

        Returns:
            Configured document converter
        """
        converter_options = {}

        # Add style map
        style_map = options.get('style_map', self._config.get('style_map'))
        if style_map:
            converter_options['style_map'] = style_map

        # Add default style map option
        include_default = options.get(
            'include_default_style_map',
            self._config.get('include_default_style_map', True),
        )
        if not include_default:
            converter_options['include_default_style_map'] = False

        # Add empty paragraphs option
        ignore_empty = options.get(
            'ignore_empty_paragraphs',
            self._config.get('ignore_empty_paragraphs', True),
        )
        if ignore_empty:
            converter_options['ignore_empty_paragraphs'] = True

        # Add image handling options
        embed_images = options.get(
            'embed_images',
            self._config.get('embed_images', False),
        )
        if embed_images:
            converter_options['embed_images'] = True

        image_handler = options.get(
            'image_handler',
            self._config.get('image_handler'),
        )
        if image_handler:
            converter_options['convert_image'] = image_handler

        # Create converter
        if options.get('convert_markdown', self._config.get('convert_markdown')):
            return mammoth.Converter(
                from_markdown=True,
                **converter_options,
            )
        return mammoth.DocumentConverter(**converter_options)

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using Mammoth.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - style_map: str - Custom style map
                - include_default_style_map: bool - Include default style map
                - ignore_empty_paragraphs: bool - Ignore empty paragraphs
                - convert_markdown: bool - Convert to Markdown instead of HTML
                - embed_images: bool - Embed images as data URIs
                - image_handler: Callable - Custom image handler function
                - extract_raw_text: bool - Extract raw text without formatting
                - extract_messages: bool - Include conversion messages
                - output_format: str - Output format (html, markdown)
                - output_path: str - Path to save converted document

        Returns:
            Processing result with converted document and metadata

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

            # Create converter
            converter = self._create_converter(**options)

            # Initialize metadata
            metadata = {
                'engine': 'mammoth',
                'input_path': str(content_path),
            }

            # Process based on output format
            output_format = options.get('output_format', 'html').lower()
            if output_format == 'html':
                # Convert to HTML
                with open(content_path, 'rb') as docx:
                    result = converter.convert_to_html(docx)
                    metadata['html'] = result.value
                    if options.get('extract_messages'):
                        metadata['messages'] = [str(msg) for msg in result.messages]

            elif output_format == 'markdown':
                # Convert to Markdown
                with open(content_path, 'rb') as docx:
                    result = converter.convert_to_markdown(docx)
                    metadata['markdown'] = result.value
                    if options.get('extract_messages'):
                        metadata['messages'] = [str(msg) for msg in result.messages]

            else:
                raise ContentProcessingError(f"Unsupported output format: {output_format}")

            # Extract raw text if requested
            if options.get('extract_raw_text'):
                with open(content_path, 'rb') as docx:
                    result = converter.extract_raw_text(docx)
                    metadata['text'] = result.value
                    if options.get('extract_messages'):
                        metadata['text_messages'] = [str(msg) for msg in result.messages]

            # Save output if path provided
            output_path = options.get('output_path')
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(metadata[output_format])
                metadata['output_path'] = str(output_path)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with Mammoth: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_html_conversion': True,
            'supports_markdown_conversion': True,
            'supports_raw_text_extraction': True,
            'supports_style_mapping': True,
            'supports_image_embedding': True,
            'supports_custom_image_handlers': True,
            'supported_formats': [
                '.docx',
                '.docm',
            ],
            'supported_output_formats': [
                'html',
                'markdown',
            ],
        } 