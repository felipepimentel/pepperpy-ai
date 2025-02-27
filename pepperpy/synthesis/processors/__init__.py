"""Processadores para síntese de conteúdo multimodal."""

from .audio import AudioProcessor
from .image import ImageProcessor
from .text import TextProcessor
from .video import VideoProcessor

__all__ = [
    "TextProcessor",
    "ImageProcessor",
    "AudioProcessor",
    "VideoProcessor",
]
