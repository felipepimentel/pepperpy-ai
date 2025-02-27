# PepperPy Unified Audio Processing System

This module provides a comprehensive audio processing system for all PepperPy components, with specialized implementations for different use cases.

## Overview

The unified audio processing system consolidates previously fragmented audio processing implementations into a single, coherent module with a consistent API. This system replaces:

- `multimodal/audio.py` (input/analysis side)
- `synthesis/processors/audio.py` (output/generation side)

## Components

### Base Functionality (`base.py`)

- `AudioFeatures`: Container for extracted features from audio
- `BaseAudioProcessor`: Base class for all audio processors

### Input Processing (`input.py`)

- `AudioProcessor`: Processor for audio input
  - Noise reduction
  - Normalization
  - Segmentation
  - Feature extraction

### Output Processing (`output.py`)

- `AudioProcessor`: Processor for audio output
  - Normalization
  - Filter application
  - Effect processing
  - Format conversion

### Analysis (`analysis.py`)

- `SpeechTranscriber`: Base class for speech-to-text transcription
- `AudioClassifier`: Base class for audio classification
- `AudioAnalyzer`: High-level interface for comprehensive audio analysis

## Usage Examples

### Input Processing

```python
from pepperpy.audio import InputProcessor
import numpy as np

# Create an input processor
processor = InputProcessor(
    name="input_processor",
    config={
        "denoise": True,
        "normalize": True,
        "noise_threshold": 0.05,
    }
)

# Process audio
audio_data = np.random.random(44100)  # 1 second of random audio
processed = await processor.process(audio_data)

# Extract features from an audio file
features = await processor.process_audio("path/to/audio.wav")
print(f"Sample rate: {features.sample_rate}, Duration: {features.duration}s")
```

### Output Processing

```python
from pepperpy.audio import OutputProcessor
import numpy as np

# Create an output processor
processor = OutputProcessor(
    name="output_processor",
    config={
        "normalize": True,
        "filter": "lowpass",
        "effects": {
            "reverb": {"room_size": 0.8, "damping": 0.5},
            "eq": {"bass": 1.2, "mid": 1.0, "treble": 0.8}
        }
    }
)

# Process audio for output
audio_data = np.random.random(44100)  # 1 second of random audio
processed = await processor.process(audio_data)

# Export to a specific format
wav_data = await processor.export_audio(processed, format="wav", sample_rate=44100)
```

### Audio Analysis

```python
from pepperpy.audio import AudioAnalyzer, SpeechTranscriber, AudioClassifier, InputProcessor

# Create components
processor = InputProcessor(name="analyzer_processor")
transcriber = SpeechTranscriber()
classifier = AudioClassifier()

# Create analyzer
analyzer = AudioAnalyzer(
    processor=processor,
    transcriber=transcriber,
    classifier=classifier
)

# Analyze audio file
result = await analyzer.analyze("path/to/audio.wav")

# Access results
if result.features:
    print(f"Features shape: {result.features.features.shape}")

if result.transcriptions:
    for t in result.transcriptions:
        print(f"Transcription: {t.text} (confidence: {t.confidence})")

if result.classifications:
    for c in result.classifications:
        print(f"Classification: {c.label} (confidence: {c.confidence})")
```

## Best Practices

1. **Choose the right processor** for your use case:
   - `InputProcessor` for capturing and analyzing audio
   - `OutputProcessor` for generating and exporting audio

2. **Configure processors appropriately** for your specific needs:
   ```python
   processor = InputProcessor(
       name="speech_processor",
       config={
           "denoise": True,
           "normalize": True,
           "segment": True,
           "noise_threshold": 0.05,
           "energy_threshold": 1.5,
           "window_size": 512,
       }
   )
   ```

3. **Use the high-level analyzer** for comprehensive analysis:
   ```python
   analyzer = AudioAnalyzer(
       processor=processor,
       transcriber=transcriber,
       classifier=classifier
   )
   ```

4. **Process audio in batches** when working with multiple files:
   ```python
   features_list = await processor.process_batch(["file1.wav", "file2.wav"])
   ```

5. **Handle async operations properly**:
   ```python
   import asyncio
   
   async def process_files(files):
       results = await processor.process_batch(files)
       return results
   
   # Run the async function
   results = asyncio.run(process_files(["file1.wav", "file2.wav"]))
   ``` 