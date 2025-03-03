"""Base interfaces and types for vision providers."""

from pepperpy.multimodal.vision.providers.base.base import VisionError, VisionProvider
from pepperpy.multimodal.vision.providers.base.registry import VisionProviderRegistry
from pepperpy.multimodal.vision.providers.base.types import (
    BoundingBox,
    DetectedObject,
    ImageInput,
    VisionTaskType,
)

__all__ = [
    "BoundingBox",
    "DetectedObject",
    "ImageInput",
    "VisionError",
    "VisionProvider",
    "VisionProviderRegistry",
    "VisionTaskType",
]
