"""Module for audio processing capabilities."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import numpy as np


@dataclass
class AudioFeatures:
    """Represents extracted features from an audio signal."""

    features: np.ndarray
    sample_rate: int
    duration: float
    metadata: Optional[dict] = None


@dataclass
class Transcription:
    """Represents a transcription of audio content."""

    text: str
    confidence: float
    start_time: float
    end_time: float
    metadata: Optional[dict] = None


class AudioProcessor:
    """Base class for audio processing operations."""

    async def process_audio(self, audio_path: Union[str, Path]) -> AudioFeatures:
        """Process an audio file and extract features."""
        raise NotImplementedError

    async def process_batch(
        self, audio_paths: List[Union[str, Path]]
    ) -> List[AudioFeatures]:
        """Process multiple audio files in batch."""
        raise NotImplementedError


class SpeechTranscriber:
    """Base class for speech-to-text transcription."""

    async def transcribe(self, audio_path: Union[str, Path]) -> List[Transcription]:
        """Transcribe speech in an audio file."""
        raise NotImplementedError

    async def transcribe_batch(
        self, audio_paths: List[Union[str, Path]]
    ) -> List[List[Transcription]]:
        """Transcribe speech in multiple audio files."""
        raise NotImplementedError


class AudioClassifier:
    """Base class for audio classification tasks."""

    @dataclass
    class Classification:
        """Represents a classification result."""

        label: str
        confidence: float
        metadata: Optional[dict] = None

    async def classify(self, audio_path: Union[str, Path]) -> List[Classification]:
        """Classify the content of an audio file."""
        raise NotImplementedError

    async def classify_batch(
        self, audio_paths: List[Union[str, Path]]
    ) -> List[List[Classification]]:
        """Classify multiple audio files."""
        raise NotImplementedError


class AudioAnalyzer:
    """High-level interface for audio analysis combining multiple capabilities."""

    def __init__(
        self,
        processor: Optional[AudioProcessor] = None,
        transcriber: Optional[SpeechTranscriber] = None,
        classifier: Optional[AudioClassifier] = None,
    ):
        self.processor = processor
        self.transcriber = transcriber
        self.classifier = classifier

    @dataclass
    class AnalysisResult:
        """Combined results from multiple analysis methods."""

        features: Optional[AudioFeatures] = None
        transcriptions: Optional[List[Transcription]] = None
        classifications: Optional[List[AudioClassifier.Classification]] = None

    async def analyze(self, audio_path: Union[str, Path]) -> AnalysisResult:
        """Perform comprehensive analysis of an audio file."""
        features = (
            await self.processor.process_audio(audio_path) if self.processor else None
        )
        transcriptions = (
            await self.transcriber.transcribe(audio_path) if self.transcriber else None
        )
        classifications = (
            await self.classifier.classify(audio_path) if self.classifier else None
        )

        return self.AnalysisResult(
            features=features,
            transcriptions=transcriptions,
            classifications=classifications,
        )
