"""PyMuPDF provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import fitz
except ImportError:
    fitz = None


@lazy_provider_class("content_processing.document", "pymupdf")
class PyMuPDFProvider:
    """Provider for document processing using PyMuPDF."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize PyMuPDF provider.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if fitz is None:
                raise ContentProcessingError(
                    "PyMuPDF is not installed. Install with: pip install PyMuPDF"
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    def _extract_text(self, doc: fitz.Document, page_range: Optional[tuple] = None) -> str:
        """Extract text from document.

        Args:
            doc: PyMuPDF document object
            page_range: Optional tuple of (start, end) page numbers

        Returns:
            Extracted text content
        """
        start, end = page_range or (0, doc.page_count)
        text = []
        for page_num in range(start, end):
            page = doc[page_num]
            text.append(page.get_text())
        return "\n".join(text)

    def _extract_images(
        self,
        doc: fitz.Document,
        output_dir: Optional[Union[str, Path]] = None,
        page_range: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """Extract images from document.

        Args:
            doc: PyMuPDF document object
            output_dir: Optional directory to save extracted images
            page_range: Optional tuple of (start, end) page numbers

        Returns:
            List of dictionaries containing image metadata
        """
        start, end = page_range or (0, doc.page_count)
        images = []
        for page_num in range(start, end):
            page = doc[page_num]
            image_list = page.get_images()
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    image_info = {
                        'page': page_num + 1,
                        'index': img_idx + 1,
                        'width': base_image['width'],
                        'height': base_image['height'],
                        'colorspace': base_image['colorspace'],
                        'bpc': base_image['bpc'],
                        'type': base_image['ext'],
                    }

                    if output_dir:
                        output_dir = Path(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        image_path = output_dir / f"page_{page_num + 1}_image_{img_idx + 1}.{base_image['ext']}"
                        with open(image_path, 'wb') as f:
                            f.write(base_image['image'])
                        image_info['path'] = str(image_path)

                    images.append(image_info)
        return images

    def _extract_toc(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract table of contents.

        Args:
            doc: PyMuPDF document object

        Returns:
            List of dictionaries containing TOC entries
        """
        toc = []
        for item in doc.get_toc():
            level, title, page = item
            toc.append({
                'level': level,
                'title': title,
                'page': page,
            })
        return toc

    def _extract_links(self, doc: fitz.Document, page_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Extract hyperlinks from document.

        Args:
            doc: PyMuPDF document object
            page_range: Optional tuple of (start, end) page numbers

        Returns:
            List of dictionaries containing link information
        """
        start, end = page_range or (0, doc.page_count)
        links = []
        for page_num in range(start, end):
            page = doc[page_num]
            for link in page.get_links():
                link_info = {
                    'page': page_num + 1,
                    'type': link['kind'],
                    'rect': list(link['from']),
                }
                if link['kind'] == fitz.LINK_URI:
                    link_info['uri'] = link['uri']
                elif link['kind'] == fitz.LINK_GOTO:
                    link_info['destination'] = {
                        'page': link['page'] + 1,
                        'at': list(link['to']),
                    }
                links.append(link_info)
        return links

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using PyMuPDF.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - extract_text: bool - Extract text content
                - extract_metadata: bool - Extract document metadata
                - extract_images: bool - Extract embedded images
                - extract_links: bool - Extract hyperlinks
                - extract_toc: bool - Extract table of contents
                - page_range: Tuple[int, int] - Range of pages to process
                - password: str - Password for encrypted documents
                - output_format: str - Format for converted document
                - compress: bool - Compress output document
                - split_pages: bool - Split document into individual pages

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Open document
            password = options.get('password')
            doc = fitz.open(str(content_path), password=password)

            # Initialize metadata
            metadata = {
                'page_count': doc.page_count,
                'format': doc.name,
                'encrypted': doc.is_encrypted,
                'metadata': doc.metadata,
            }

            # Extract text if requested
            if options.get('extract_text', True):
                page_range = options.get('page_range')
                metadata['text'] = self._extract_text(doc, page_range)

            # Extract images if requested
            if options.get('extract_images'):
                output_dir = options.get('image_output_dir')
                page_range = options.get('page_range')
                metadata['images'] = self._extract_images(doc, output_dir, page_range)

            # Extract table of contents if requested
            if options.get('extract_toc'):
                metadata['toc'] = self._extract_toc(doc)

            # Extract links if requested
            if options.get('extract_links'):
                page_range = options.get('page_range')
                metadata['links'] = self._extract_links(doc, page_range)

            # Convert document if requested
            if 'output_format' in options:
                output_format = options['output_format'].lower()
                output_path = Path(str(content_path)).with_suffix(f'.{output_format}')
                doc.save(
                    str(output_path),
                    garbage=options.get('compress', 4),
                    deflate=options.get('compress', True),
                )
                metadata['converted_path'] = str(output_path)

            # Split into pages if requested
            if options.get('split_pages'):
                output_dir = Path(str(content_path)).parent / f"{Path(content_path).stem}_pages"
                output_dir.mkdir(parents=True, exist_ok=True)
                metadata['pages'] = []
                for page_num in range(doc.page_count):
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    output_path = output_dir / f"page_{page_num + 1}.pdf"
                    new_doc.save(str(output_path))
                    new_doc.close()
                    metadata['pages'].append(str(output_path))

            # Close document
            doc.close()

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with PyMuPDF: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_text_extraction': True,
            'supports_image_extraction': True,
            'supports_toc_extraction': True,
            'supports_link_extraction': True,
            'supports_conversion': True,
            'supports_compression': True,
            'supports_encryption': True,
            'supports_page_splitting': True,
            'supported_formats': [
                '.pdf',
                '.xps',
                '.oxps',
                '.epub',
                '.mobi',
                '.fb2',
                '.cbz',
                '.svg',
            ],
            'supported_output_formats': [
                'pdf',
                'html',
            ],
        } 