# Text-to-Speech Workflow

A workflow plugin for converting text to speech using various TTS providers:

1. Convert text to audio
2. Stream audio for real-time playback
3. Get available voices
4. Customize voice parameters

## Features

- Text to Audio: Convert text to high-quality speech audio
- Voice Selection: Choose from a wide range of voices and languages
- Streaming: Stream audio for real-time playback
- Customization: Adjust voice style, pitch, rate, and other parameters

## Configuration

The workflow can be configured with these options:

- `provider`: TTS provider to use (default: "azure")
- `api_key`: API key for the TTS provider
- `region`: Region for cloud-based TTS providers (default: "eastus")
- `voice_id`: Default voice ID to use (default: "en-US-AriaNeural")
- `voice_style`: Voice style to use (default: "neutral")
- `output_format`: Audio output format (default: "mp3")
- `save_files`: Whether to save audio files (default: true)
- `output_dir`: Directory to save files (default: "./output/tts")

## Usage

### Basic Text to Speech

```python
from pepperpy.workflow import create_provider

# Create the TTS workflow provider
workflow = create_provider("tts", 
                          provider="azure",
                          api_key="your_api_key",
                          region="eastus")

# Convert text to speech
result = await workflow.execute({
    "task": "convert_text",
    "input": {
        "text": "Hello world! This is a test of text-to-speech capabilities.",
        "voice_id": "en-US-AriaNeural",
        "output_file": "hello.mp3"
    }
})

# Print the result
print(f"Generated {result['audio_size']} bytes of audio")
print(f"Saved to: {result['file_path']}")
```

### List Available Voices

```python
# Create TTS workflow
workflow = create_provider("tts", 
                         provider="azure",
                         api_key="your_api_key")

# Get all available voices
result = await workflow.execute({
    "task": "get_voices",
    "input": {
        "language": "en-US"  # Optional filter by language
    }
})

# Print available voices
voices = result["voices"]
print(f"Found {len(voices)} voices")
for voice in voices:
    print(f"- {voice['id']} ({voice['name']}, {voice['gender']})")
```

### Stream Text

```python
# Create workflow with streaming
workflow = create_provider("tts", 
                         provider="azure",
                         api_key="your_api_key")

# Stream text to speech and save to file
result = await workflow.execute({
    "task": "stream_text",
    "input": {
        "text": "This is a streaming test of the text to speech system.",
        "voice_id": "en-US-AriaNeural",
        "voice_style": "cheerful",
        "output_file": "streaming.mp3"
    }
})

print(f"Streamed {result['chunks']} chunks, total {result['total_size']} bytes")
print(f"Saved to: {result['file_path']}")
```

### Via CLI

```bash
# Run TTS workflow via CLI to generate audio
python -m pepperpy.cli workflow run workflow/tts \
  --params "provider=azure" \
  --params "api_key=your_api_key" \
  --params "task=convert_text" \
  --params "text=Hello from the command line interface!" \
  --params "output_file=cli_example.mp3"
```

## Requirements

- pydantic>=2.0.0
- jsonschema>=4.0.0

## Supported Providers

Currently, the TTS workflow supports:

- Azure TTS (Microsoft)

Support for additional providers like ElevenLabs and OpenAI will be added in future updates. 