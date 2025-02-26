"""Multimodal processing package for Pepperpy."""

from .vision import (
    ImageFeatures,
    ImageDescription,
    ImageProcessor,
    ImageCaptioner,
    ObjectDetector,
    ImageAnalyzer,
)
from .audio import (
    AudioFeatures,
    Transcription,
    AudioProcessor,
    SpeechTranscriber,
    AudioClassifier,
    AudioAnalyzer,
)
from .fusion import (
    FusedFeatures,
    FeatureFuser,
    MultimodalContext,
    ContextFuser,
    MultimodalFusion,
)

__all__ = [
    # Vision
    'ImageFeatures',
    'ImageDescription',
    'ImageProcessor',
    'ImageCaptioner',
    'ObjectDetector',
    'ImageAnalyzer',
    
    # Audio
    'AudioFeatures',
    'Transcription',
    'AudioProcessor',
    'SpeechTranscriber',
    'AudioClassifier',
    'AudioAnalyzer',
    
    # Fusion
    'FusedFeatures',
    'FeatureFuser',
    'MultimodalContext',
    'ContextFuser',
    'MultimodalFusion',
]