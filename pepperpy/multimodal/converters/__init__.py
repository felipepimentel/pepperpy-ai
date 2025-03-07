"""Conversores multimodais do PepperPy.

Este módulo fornece implementações de conversores entre diferentes
modalidades, como texto para imagem, imagem para texto, etc.
"""

from pepperpy.multimodal.converters.base import (
    convert_between_modalities,
    get_converter,
    register_converter,
)
from pepperpy.multimodal.converters.implementations import (
    ImageToTextConverter,
    TextToImageConverter,
)

__all__ = [
    # Funções
    "convert_between_modalities",
    "get_converter",
    "register_converter",
    # Conversores
    "TextToImageConverter",
    "ImageToTextConverter",
]
