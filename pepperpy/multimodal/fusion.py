"""Module for multimodal data fusion."""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .audio import AudioClassifier, AudioFeatures, Transcription
from .vision import ImageDescription, ImageFeatures, ObjectDetector


@dataclass
class FusedFeatures:
    """Represents features fused from multiple modalities."""

    features: np.ndarray
    modalities: List[str]
    weights: Dict[str, float]
    metadata: Optional[dict] = None


class FeatureFuser:
    """Base class for fusing features from multiple modalities."""

    async def fuse_features(
        self,
        image_features: Optional[ImageFeatures] = None,
        audio_features: Optional[AudioFeatures] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> FusedFeatures:
        """Fuse features from different modalities."""
        raise NotImplementedError


@dataclass
class MultimodalContext:
    """Represents combined context from multiple modalities."""

    image_context: Optional[ImageDescription] = None
    audio_context: Optional[List[Transcription]] = None
    object_detections: Optional[List[ObjectDetector.Detection]] = None
    audio_classifications: Optional[List[AudioClassifier.Classification]] = None
    metadata: Optional[dict] = None

    def to_text(self) -> str:
        """Convert multimodal context to a textual representation."""
        parts = []

        if self.image_context:
            parts.append(f"Image Description: {self.image_context.text}")

        if self.object_detections:
            objects = [
                f"{d.label} ({d.confidence:.2f})" for d in self.object_detections
            ]
            parts.append(f"Detected Objects: {', '.join(objects)}")

        if self.audio_context:
            transcripts = [t.text for t in self.audio_context]
            parts.append(f"Audio Transcription: {' '.join(transcripts)}")

        if self.audio_classifications:
            classes = [
                f"{c.label} ({c.confidence:.2f})" for c in self.audio_classifications
            ]
            parts.append(f"Audio Classifications: {', '.join(classes)}")

        return "\n".join(parts)


class ContextFuser:
    """Combines contextual information from multiple modalities."""

    def fuse_context(
        self,
        image_desc: Optional[ImageDescription] = None,
        audio_trans: Optional[List[Transcription]] = None,
        detections: Optional[List[ObjectDetector.Detection]] = None,
        classifications: Optional[List[AudioClassifier.Classification]] = None,
    ) -> MultimodalContext:
        """Combine context from different modalities."""
        return MultimodalContext(
            image_context=image_desc,
            audio_context=audio_trans,
            object_detections=detections,
            audio_classifications=classifications,
        )


class MultimodalFusion:
    """High-level interface for multimodal fusion."""

    def __init__(
        self,
        feature_fuser: Optional[FeatureFuser] = None,
        context_fuser: Optional[ContextFuser] = None,
    ):
        self.feature_fuser = feature_fuser or FeatureFuser()
        self.context_fuser = context_fuser or ContextFuser()

    @dataclass
    class FusionResult:
        """Combined results from feature and context fusion."""

        features: Optional[FusedFeatures] = None
        context: Optional[MultimodalContext] = None

    async def fuse(
        self,
        image_features: Optional[ImageFeatures] = None,
        audio_features: Optional[AudioFeatures] = None,
        image_desc: Optional[ImageDescription] = None,
        audio_trans: Optional[List[Transcription]] = None,
        detections: Optional[List[ObjectDetector.Detection]] = None,
        classifications: Optional[List[AudioClassifier.Classification]] = None,
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> FusionResult:
        """Perform comprehensive multimodal fusion."""

        # Fuse features if available
        fused_features = None
        if image_features or audio_features:
            fused_features = await self.feature_fuser.fuse_features(
                image_features=image_features,
                audio_features=audio_features,
                weights=feature_weights,
            )

        # Fuse context
        context = self.context_fuser.fuse_context(
            image_desc=image_desc,
            audio_trans=audio_trans,
            detections=detections,
            classifications=classifications,
        )

        return self.FusionResult(features=fused_features, context=context)
