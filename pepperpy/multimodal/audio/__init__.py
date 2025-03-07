"""Unified audio processing system for PepperPy.

This module provides a comprehensive audio processing system for all PepperPy components,
with specialized implementations for different use cases:

- Base functionality (base.py)
  - Common interfaces
  - Data structures
  - Feature extraction

- Input processing (input.py)
  - Audio capture
  - Speech detection
  - Segmentation
  - Filtering

- Output processing (output.py)
  - Audio normalization
  - Filter application
  - Effect processing
  - Output formatting

- Analysis (analysis.py)
  - Feature analysis
  - Classification
  - Transcription
  - ASR integration

This unified system replaces the previous fragmented implementations:
- multimodal/audio.py (input/analysis side)
- synthesis/processors/audio.py (output/generation side)

All components should use this module for audio processing needs, with appropriate
specialization for their specific requirements.
"""

from typing import Dict, List, Optional, Union

from .analysis import AudioAnalyzer, AudioClassifier, SpeechTranscriber
from .base import AudioFeatures, AudioProcessor
from .input import AudioProcessor as InputProcessor
from .output import AudioProcessor as OutputProcessor

__all__ = [
    # Base classes
    "AudioFeatures",
    "AudioProcessor",
    # Input processing
    "InputProcessor",
    # Output processing
    "OutputProcessor",
    # Analysis
    "AudioAnalyzer",
    "AudioClassifier",
    "SpeechTranscriber",
]
