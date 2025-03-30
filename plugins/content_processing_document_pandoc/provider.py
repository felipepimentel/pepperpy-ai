"""Pandoc provider for document processing."""

import os
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError


@lazy_provider_class("content_processing.document", "pandoc")
class PandocProvider:
    """Provider for document processing using Pandoc."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Pandoc provider.

        Args:
            **kwargs: Additional configuration options
                - pandoc_path: str - Path to Pandoc executable
                - data_dir: str - Path to Pandoc data directory
                - defaults_file: str - Path to defaults file
        """
        self._config = kwargs
        self._initialized = False
        self._pandoc_path = kwargs.get('pandoc_path', 'pandoc')
        self._data_dir = kwargs.get('data_dir')
        self._defaults_file = kwargs.get('defaults_file')

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            # Test Pandoc installation
            try:
                result = subprocess.run(
                    [self._pandoc_path, '--version'],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise ContentProcessingError(
                        f"Failed to run Pandoc: {result.stderr}"
                    )
                self._version = result.stdout.split('\n')[0].split(' ')[1]
            except FileNotFoundError:
                raise ContentProcessingError(
                    "Pandoc is not installed. Install from: https://pandoc.org/installing.html"
                )
            except Exception as e:
                raise ContentProcessingError(f"Failed to initialize Pandoc: {e}")

            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    def _build_command(
        self,
        input_path: Path,
        output_path: Path,
        **options: Any,
    ) -> List[str]:
        """Build Pandoc command.

        Args:
            input_path: Input file path
            output_path: Output file path
            **options: Additional options
                - from_format: str - Input format
                - to_format: str - Output format
                - standalone: bool - Create standalone document
                - template: str - Template file path
                - reference_doc: str - Reference document path
                - table_of_contents: bool - Include table of contents
                - number_sections: bool - Number sections
                - highlight_style: str - Code highlighting style
                - variables: Dict[str, str] - Template variables
                - metadata: Dict[str, str] - Document metadata
                - filters: List[str] - Pandoc filters to apply
                - lua_filters: List[str] - Lua filters to apply
                - extract_media: bool - Extract embedded media
                - extract_citations: bool - Extract citations
                - bibliography: str - Bibliography file path
                - csl: str - Citation style file path

        Returns:
            List of command arguments
        """
        cmd = [self._pandoc_path]

        # Add data directory if specified
        if self._data_dir:
            cmd.extend(['--data-dir', str(self._data_dir)])

        # Add defaults file if specified
        if self._defaults_file:
            cmd.extend(['--defaults', str(self._defaults_file)])

        # Add input/output formats
        if 'from_format' in options:
            cmd.extend(['--from', options['from_format']])
        if 'to_format' in options:
            cmd.extend(['--to', options['to_format']])

        # Add standalone option
        if options.get('standalone'):
            cmd.append('--standalone')

        # Add template
        if 'template' in options:
            cmd.extend(['--template', str(options['template'])])

        # Add reference doc
        if 'reference_doc' in options:
            cmd.extend(['--reference-doc', str(options['reference_doc'])])

        # Add table of contents
        if options.get('table_of_contents'):
            cmd.append('--table-of-contents')
            if 'toc_depth' in options:
                cmd.extend(['--toc-depth', str(options['toc_depth'])])

        # Add section numbering
        if options.get('number_sections'):
            cmd.append('--number-sections')

        # Add syntax highlighting
        if 'highlight_style' in options:
            cmd.extend(['--highlight-style', options['highlight_style']])

        # Add variables
        for name, value in options.get('variables', {}).items():
            cmd.extend(['--variable', f"{name}:{value}"])

        # Add metadata
        for name, value in options.get('metadata', {}).items():
            cmd.extend(['--metadata', f"{name}:{value}"])

        # Add filters
        for filter_path in options.get('filters', []):
            cmd.extend(['--filter', str(filter_path)])

        # Add Lua filters
        for filter_path in options.get('lua_filters', []):
            cmd.extend(['--lua-filter', str(filter_path)])

        # Add citation processing
        if options.get('extract_citations'):
            if 'bibliography' in options:
                cmd.extend(['--bibliography', str(options['bibliography'])])
            if 'csl' in options:
                cmd.extend(['--csl', str(options['csl'])])

        # Add extract media option
        if options.get('extract_media'):
            media_dir = output_path.parent / f"{output_path.stem}_media"
            cmd.extend(['--extract-media', str(media_dir)])

        # Add input and output paths
        cmd.extend([str(input_path), '-o', str(output_path)])

        return cmd

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using Pandoc.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - from_format: str - Input format
                - to_format: str - Output format
                - standalone: bool - Create standalone document
                - template: str - Template file path
                - reference_doc: str - Reference document path
                - table_of_contents: bool - Include table of contents
                - number_sections: bool - Number sections
                - highlight_style: str - Code highlighting style
                - variables: Dict[str, str] - Template variables
                - metadata: Dict[str, str] - Document metadata
                - filters: List[str] - Pandoc filters to apply
                - lua_filters: List[str] - Lua filters to apply
                - extract_media: bool - Extract embedded media
                - extract_citations: bool - Extract citations
                - bibliography: str - Bibliography file path
                - csl: str - Citation style file path

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

            # Determine output format and path
            output_format = options.get('to_format', 'html')
            output_path = content_path.with_suffix(f".{output_format}")

            # Build command
            cmd = self._build_command(content_path, output_path, **options)

            # Run Pandoc
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise ContentProcessingError(
                    f"Pandoc conversion failed: {result.stderr}"
                )

            # Get document metadata
            metadata_cmd = [
                self._pandoc_path,
                '--standalone',
                '--template={}',
                str(content_path),
            ]
            metadata_result = subprocess.run(
                metadata_cmd,
                capture_output=True,
                text=True,
            )

            # Initialize metadata
            metadata = {
                'engine': 'pandoc',
                'version': self._version,
                'input_format': options.get('from_format'),
                'output_format': output_format,
                'output_path': str(output_path),
                'command': ' '.join(cmd),
            }

            # Add extracted metadata if available
            if metadata_result.returncode == 0:
                try:
                    doc_metadata = json.loads(metadata_result.stdout)
                    metadata['document'] = doc_metadata
                except json.JSONDecodeError:
                    pass

            # Add media directory if extracted
            if options.get('extract_media'):
                media_dir = output_path.parent / f"{output_path.stem}_media"
                if media_dir.exists():
                    metadata['media_dir'] = str(media_dir)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with Pandoc: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_conversion': True,
            'supports_templates': True,
            'supports_filters': True,
            'supports_citations': True,
            'supports_media_extraction': True,
            'supported_input_formats': [
                'commonmark',
                'docbook',
                'docx',
                'epub',
                'html',
                'latex',
                'markdown',
                'odt',
                'org',
                'rst',
                'textile',
                'twiki',
            ],
            'supported_output_formats': [
                'asciidoc',
                'beamer',
                'commonmark',
                'context',
                'docbook',
                'docx',
                'epub',
                'html',
                'latex',
                'man',
                'markdown',
                'mediawiki',
                'odt',
                'opendocument',
                'org',
                'pdf',
                'plain',
                'rst',
                'rtf',
                'texinfo',
                'textile',
            ],
        } 