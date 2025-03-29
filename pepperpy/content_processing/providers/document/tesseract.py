"""Tesseract provider for document processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None


@lazy_provider_class("content_processing.document", "tesseract")
class TesseractProvider:
    """Provider for document processing using Tesseract OCR."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Tesseract provider.

        Args:
            **kwargs: Additional configuration options
                - tesseract_cmd: str - Path to Tesseract executable
                - language: str - OCR language(s) to use
                - config: Dict[str, str] - Additional Tesseract configuration
        """
        self._config = kwargs
        self._initialized = False

        # Set Tesseract executable path if provided
        if 'tesseract_cmd' in kwargs:
            pytesseract.pytesseract.tesseract_cmd = kwargs['tesseract_cmd']

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if pytesseract is None or Image is None:
                raise ContentProcessingError(
                    "Tesseract dependencies not installed. Install with: pip install pytesseract Pillow"
                )

            # Test Tesseract installation
            try:
                pytesseract.get_tesseract_version()
            except Exception as e:
                raise ContentProcessingError(
                    f"Failed to initialize Tesseract. Make sure it's installed: {e}"
                )

            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    def _preprocess_image(
        self,
        image: Image.Image,
        **options: Any,
    ) -> Image.Image:
        """Preprocess image for OCR.

        Args:
            image: PIL Image object
            **options: Preprocessing options
                - grayscale: bool - Convert to grayscale
                - contrast: float - Adjust contrast
                - brightness: float - Adjust brightness
                - deskew: bool - Deskew image
                - denoise: bool - Remove noise
                - threshold: bool - Apply thresholding

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if options.get('grayscale', True):
            image = image.convert('L')

        # Adjust contrast
        if 'contrast' in options:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(options['contrast'])

        # Adjust brightness
        if 'brightness' in options:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(options['brightness'])

        # Apply thresholding
        if options.get('threshold'):
            from PIL import ImageOps
            image = ImageOps.autocontrast(image)

        return image

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document using Tesseract OCR.

        Args:
            content_path: Path to the image/document file
            **options: Additional processing options
                - language: str - OCR language(s) to use
                - config: Dict[str, str] - Additional Tesseract configuration
                - preprocessing: Dict[str, Any] - Image preprocessing options
                - output_format: str - Output format (txt, pdf, hocr)
                - page_segmentation_mode: int - PSM mode (0-13)
                - ocr_engine_mode: int - OCR engine mode (0-3)
                - dpi: int - Image DPI for PDF output
                - extract_metadata: bool - Extract image metadata

        Returns:
            Processing result with extracted text and metadata

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Open image
            image = Image.open(str(content_path))

            # Preprocess image
            preprocessing_options = options.get('preprocessing', {})
            image = self._preprocess_image(image, **preprocessing_options)

            # Prepare OCR options
            ocr_options = {
                'lang': options.get('language', self._config.get('language', 'eng')),
                'config': '',
            }

            # Add page segmentation mode
            if 'page_segmentation_mode' in options:
                ocr_options['config'] += f" --psm {options['page_segmentation_mode']}"

            # Add OCR engine mode
            if 'ocr_engine_mode' in options:
                ocr_options['config'] += f" --oem {options['ocr_engine_mode']}"

            # Add custom config
            custom_config = options.get('config', self._config.get('config', {}))
            for key, value in custom_config.items():
                ocr_options['config'] += f" -{key} {value}"

            # Initialize metadata
            metadata = {
                'engine': 'tesseract',
                'version': pytesseract.get_tesseract_version(),
                'language': ocr_options['lang'],
                'config': ocr_options['config'],
            }

            # Extract image metadata if requested
            if options.get('extract_metadata'):
                metadata['image'] = {
                    'format': image.format,
                    'mode': image.mode,
                    'size': image.size,
                    'dpi': image.info.get('dpi'),
                }

            # Process based on output format
            output_format = options.get('output_format', 'txt')
            if output_format == 'txt':
                # Extract text
                text = pytesseract.image_to_string(image, **ocr_options)
                metadata['text'] = text.strip()

            elif output_format == 'pdf':
                # Convert to searchable PDF
                output_path = Path(str(content_path)).with_suffix('.pdf')
                pdf = pytesseract.image_to_pdf_or_hocr(
                    image,
                    extension='pdf',
                    **ocr_options,
                )
                with open(output_path, 'wb') as f:
                    f.write(pdf)
                metadata['pdf_path'] = str(output_path)

            elif output_format == 'hocr':
                # Generate hOCR output
                output_path = Path(str(content_path)).with_suffix('.hocr')
                hocr = pytesseract.image_to_pdf_or_hocr(
                    image,
                    extension='hocr',
                    **ocr_options,
                )
                with open(output_path, 'wb') as f:
                    f.write(hocr)
                metadata['hocr_path'] = str(output_path)

            else:
                raise ContentProcessingError(f"Unsupported output format: {output_format}")

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document with Tesseract: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_text_extraction': True,
            'supports_pdf_output': True,
            'supports_hocr_output': True,
            'supports_preprocessing': True,
            'supported_formats': [
                '.png',
                '.jpg',
                '.jpeg',
                '.gif',
                '.bmp',
                '.tiff',
                '.webp',
            ],
            'supported_languages': pytesseract.get_languages() if self._initialized else [],
            'supported_output_formats': [
                'txt',
                'pdf',
                'hocr',
            ],
        } 