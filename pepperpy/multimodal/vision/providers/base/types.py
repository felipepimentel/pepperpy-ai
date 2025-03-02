"""Type definitions for vision providers."""

from enum import Enum
from pathlib import Path
from typing import Dict, TypedDict, Union


class VisionTaskType(str, Enum):
    """Types of vision analysis tasks."""

    OBJECT_DETECTION = "object_detection"
    TEXT_EXTRACTION = "text_extraction"
    IMAGE_CLASSIFICATION = "image_classification"
    FACE_DETECTION = "face_detection"
    LANDMARK_DETECTION = "landmark_detection"
    LOGO_DETECTION = "logo_detection"
    LABEL_DETECTION = "label_detection"
    DOCUMENT_TEXT_DETECTION = "document_text_detection"
    SAFE_SEARCH_DETECTION = "safe_search_detection"
    IMAGE_PROPERTIES = "image_properties"
    CROP_HINTS = "crop_hints"
    WEB_DETECTION = "web_detection"
    PRODUCT_SEARCH = "product_search"


class BoundingBox(TypedDict):
    """Bounding box for detected objects."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float


class DetectedObject(TypedDict, total=False):
    """Detected object in an image."""

    label: str
    confidence: float
    bounding_box: BoundingBox
    attributes: Dict[str, Union[str, float, int, bool]]


# Type for image input
ImageInput = Union[str, Path, bytes]
