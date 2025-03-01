# Audio Providers

This directory contains provider implementations for audio processing capabilities in the PepperPy framework.

## Available Providers

- **Transcription Providers**: Implementations for converting audio to text
- **Synthesis Providers**: Implementations for converting text to audio

## Usage

```python
from pepperpy.multimodal.audio.providers import transcription, synthesis

# Use transcription providers
transcriber = transcription.SomeTranscriptionProvider()
text = transcriber.transcribe("audio_file.mp3")

# Use synthesis providers
synthesizer = synthesis.SomeSynthesisProvider()
audio_data = synthesizer.synthesize("Text to convert to speech")
```

## Adding New Providers

To add a new provider:

1. Create a new file in the appropriate subdirectory
2. Implement the required interfaces
3. Register your provider in the corresponding `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/audio/`. The move to this domain-specific location improves modularity and maintainability. 