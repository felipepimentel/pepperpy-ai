"""Pillow provider for image processing."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None


@lazy_provider_class("content_processing.image", "pillow")
class PillowProvider:
    """Provider for image processing using Pillow."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Pillow provider.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if Image is None:
                raise ContentProcessingError(
                    "Pillow is not installed. Install with: pip install Pillow"
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
        """Process image using Pillow.

        Args:
            content_path: Path to the image file
            **options: Additional processing options
                - resize: Tuple[int, int] - Target size for resizing
                - format: str - Target format for conversion
                - optimize: bool - Whether to optimize the image
                - quality: int - JPEG/WebP quality (1-100)
                - grayscale: bool - Convert to grayscale
                - auto_orient: bool - Auto-orient image based on EXIF

        Returns:
            Processing result with extracted content

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Open image
            with Image.open(str(content_path)) as img:
                # Auto-orient if requested
                if options.get('auto_orient', True):
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass  # Ignore orientation errors

                # Convert to grayscale if requested
                if options.get('grayscale'):
                    img = img.convert('L')

                # Resize if requested
                if 'resize' in options:
                    width, height = options['resize']
                    img = img.resize((width, height), Image.Resampling.LANCZOS)

                # Extract metadata
                metadata = {
                    'format': img.format,
                    'mode': img.mode,
                    'dimensions': img.size,
                    'width': img.width,
                    'height': img.height,
                    'dpi': img.info.get('dpi'),
                }

                # Add EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata['exif'] = {
                            'make': exif.get(271),
                            'model': exif.get(272),
                            'datetime': exif.get(306),
                            'orientation': exif.get(274),
                        }

                # Process image if requested
                if any(key in options for key in ['format', 'optimize', 'quality']):
                    # Generate output path
                    output_format = options.get('format', img.format).upper()
                    output_path = Path(str(content_path)).with_suffix(f'.{output_format.lower()}')

                    # Save with options
                    save_options = {
                        'format': output_format,
                        'optimize': options.get('optimize', True),
                    }
                    if output_format in ['JPEG', 'WEBP']:
                        save_options['quality'] = options.get('quality', 85)

                    img.save(output_path, **save_options)
                    metadata['processed_path'] = str(output_path)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process image with Pillow: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_exif': True,
            'supports_resize': True,
            'supports_format_conversion': True,
            'supports_optimization': True,
            'supported_formats': [
                '.jpg',
                '.jpeg',
                '.png',
                '.gif',
                '.bmp',
                '.webp',
                '.tiff',
            ],
        } 