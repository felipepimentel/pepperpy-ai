"""Vision providers for PepperPy multimodal vision processing"""

# Import base classes and types
from pepperpy.multimodal.vision.providers.base import (
    BoundingBox,
    DetectedObject,
    ImageInput,
    VisionError,
    VisionProvider,
    VisionProviderRegistry,
    VisionTaskType,
)

# Import provider implementations
from pepperpy.multimodal.vision.providers.google import GoogleVisionProvider
from pepperpy.multimodal.vision.providers.openai import OpenAIVisionProvider

__all__ = [
    "VisionProvider",
    "VisionError",
    "VisionProviderRegistry",
    "VisionTaskType",
    "BoundingBox",
    "DetectedObject",
    "ImageInput",
    "GoogleVisionProvider",
    "OpenAIVisionProvider",
]
