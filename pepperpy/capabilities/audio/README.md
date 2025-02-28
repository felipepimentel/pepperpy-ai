# PepperPy Unified Audio Processing System

The PepperPy Unified Audio Processing System provides a comprehensive framework for audio processing, analysis, and synthesis within the PepperPy ecosystem. This system replaces previous fragmented implementations and offers a consistent API for all components.

## Key Components

### Base Components

- **AudioFeatures**: Container for extracted features from audio signals
- **BaseAudioProcessor**: Base class for all audio processors with common functionality

### Input Processing

- **InputProcessor**: Processes audio input for analysis
  - Noise reduction
  - Normalization
  - Segmentation
  - Feature extraction

### Output Processing

- **OutputProcessor**: Processes audio for output and synthesis
  - Normalization
  - Filter application
  - Effect processing
  - Format conversion

### Analysis

- **SpeechTranscriber**: Transcribes speech in audio content
- **AudioClassifier**: Classifies audio content into categories
- **AudioAnalyzer**: High-level interface combining multiple analysis capabilities

### Migration

- **MigrationHelper**: Utilities for migrating from old audio processing systems
- **map_imports**: Function to update import statements in existing code

## Usage Examples

### Processing Audio Input

```python
from pepperpy.audio import InputProcessor

# Create an input processor
processor = InputProcessor(
    name="speech_processor",
    config={
        "denoise": True,
        "normalize": True,
        "noise_threshold": 0.05,
    }
)

# Process audio
import numpy as np
audio_data = np.random.random(44100)  # 1 second of random audio
processed_audio = await processor.process(audio_data)

# Extract features from an audio file
features = await processor.process_audio("speech.wav")
print(f"Sample rate: {features.sample_rate}, Duration: {features.duration}s")
```

### Generating Audio Output

```python
from pepperpy.audio import OutputProcessor

# Create an output processor
processor = OutputProcessor(
    name="music_processor",
    config={
        "normalize": True,
        "filter": "lowpass",
        "effects": {
            "reverb": {"room_size": 0.8, "damping": 0.5},
            "delay": {"time": 0.3, "feedback": 0.4},
        }
    }
)

# Process audio for output
processed_audio = await processor.process(input_audio)

# Export to a specific format
wav_data = await processor.export_audio(processed_audio, format="wav", sample_rate=44100)
with open("output.wav", "wb") as f:
    f.write(wav_data)
```

### Analyzing Audio Content

```python
from pepperpy.audio import AudioAnalyzer, InputProcessor, SpeechTranscriber, AudioClassifier

# Create components
input_processor = InputProcessor(name="analyzer_input")
transcriber = SpeechTranscriber()
classifier = AudioClassifier()

# Create analyzer with components
analyzer = AudioAnalyzer(
    processor=input_processor,
    transcriber=transcriber,
    classifier=classifier
)

# Analyze audio file
result = await analyzer.analyze("recording.wav")

# Access results
if result.features:
    print(f"Features extracted: {result.features.features.shape}")
    
if result.transcriptions:
    for t in result.transcriptions:
        print(f"Transcription: {t.text} ({t.confidence:.2f})")
        
if result.classifications:
    for c in result.classifications:
        print(f"Classification: {c.label} ({c.confidence:.2f})")
```

### Migrating from Old Systems

```python
from pepperpy.audio.migration import MigrationHelper
from pepperpy.multimodal.audio import AudioProcessor as OldProcessor

# Create old processor
old_processor = OldProcessor(name="legacy", config={"sample_rate": 16000})

# Get equivalent new processor
new_processor = MigrationHelper.get_equivalent_processor(old_processor)

# Generate migration code
code = MigrationHelper.generate_migration_code(
    old_processor_var="processor",
    new_processor_type="InputProcessor",
    module_path="my_module"
)
print(code)

# Print migration guide
MigrationHelper.print_migration_guide()
```

## Best Practices

1. **Use async methods** for all I/O operations
2. **Configure processors** with appropriate settings for your use case
3. **Reuse processor instances** when processing multiple files
4. **Handle errors** appropriately during audio processing
5. **Use batch methods** for processing multiple files efficiently

## Integration with Other PepperPy Components

The audio system is designed to integrate seamlessly with other PepperPy components:

- **Formats**: Use the formats module for audio file handling
- **Workflow**: Create audio processing workflows
- **Memory**: Cache processed audio for performance
- **Multimodal**: Combine audio with other modalities

## Dependencies

The system has minimal dependencies:

- **Required**: None (basic functionality works without external libraries)
- **Recommended**: NumPy (for efficient array operations)
- **Optional**: 
  - PyAudio (for real-time audio capture)
  - librosa (for advanced audio analysis)
  - SoundFile (for audio file I/O)

## Error Handling

All audio processing methods include appropriate error handling:

- **File not found**: When audio files don't exist
- **Format errors**: When audio format is not supported
- **Processing errors**: When audio processing fails
- **Resource errors**: When required resources are unavailable 