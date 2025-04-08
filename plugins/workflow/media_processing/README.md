# Media Processing Plugin

The Media Processing plugin offers powerful capabilities for handling, transforming, and analyzing various media types including images, audio, and video.

## Basic CLI Usage

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "transform_image",
  "source": "input.jpg",
  "operations": [
    {"type": "resize", "width": 800, "height": 600},
    {"type": "adjust", "brightness": 1.2, "contrast": 1.1}
  ],
  "output": "output.jpg"
}'
```

## Available Tasks

### Process Image

Transform and manipulate images with various operations.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "process_image",
  "source": "input.jpg",
  "operations": [
    {"type": "resize", "width": 800, "height": 600, "maintain_aspect": true},
    {"type": "crop", "x": 10, "y": 10, "width": 400, "height": 300},
    {"type": "rotate", "angle": 90},
    {"type": "flip", "direction": "horizontal"},
    {"type": "adjust", "brightness": 1.2, "contrast": 1.1, "saturation": 0.9},
    {"type": "filter", "name": "blur", "radius": 2},
    {"type": "convert", "format": "png", "quality": 90}
  ],
  "output": "processed_image.png"
}'
```

### Process Video

Transform and edit video files.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "process_video",
  "source": "input.mp4",
  "operations": [
    {"type": "trim", "start": "00:00:10", "end": "00:01:20"},
    {"type": "resize", "width": 1280, "height": 720},
    {"type": "adjust", "brightness": 1.1, "contrast": 1.2},
    {"type": "speed", "factor": 1.5},
    {"type": "add_audio", "source": "background.mp3", "volume": 0.7},
    {"type": "add_text", "text": "Demo Video", "position": "top_left", "font_size": 24},
    {"type": "convert", "format": "webm", "codec": "vp9", "bitrate": "2M"}
  ],
  "output": "processed_video.webm"
}'
```

### Process Audio

Transform and manipulate audio files.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "process_audio",
  "source": "input.mp3",
  "operations": [
    {"type": "trim", "start": "00:00:05", "end": "00:02:30"},
    {"type": "normalize", "level": -3},
    {"type": "adjust", "volume": 1.2, "bass": 1.3, "treble": 0.9},
    {"type": "filter", "name": "noise_reduction", "amount": 0.5},
    {"type": "effect", "name": "reverb", "room_size": 0.7, "damping": 0.4},
    {"type": "fade", "in": 2, "out": 3},
    {"type": "convert", "format": "ogg", "quality": "high"}
  ],
  "output": "processed_audio.ogg"
}'
```

### Extract Media Information

Extract metadata and technical details from media files.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "extract_info",
  "source": "media_file.mp4",
  "info_type": "all"  # Options: all, basic, metadata, streams, chapters
}'
```

### Extract Media Components

Extract specific components from media files.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "extract_components",
  "source": "video.mp4",
  "components": [
    {"type": "audio", "output": "audio.mp3"},
    {"type": "frames", "output": "frame_%03d.jpg", "fps": 1},
    {"type": "subtitle", "output": "subtitles.srt", "stream_index": 0}
  ]
}'
```

### Media Conversion

Convert media files between formats.

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "convert_media",
  "source": "input.avi",
  "output": "output.mp4",
  "format": "mp4",
  "options": {
    "video_codec": "h264",
    "audio_codec": "aac",
    "video_bitrate": "2M",
    "audio_bitrate": "128k",
    "preset": "medium"
  }
}'
```

## Configuration Options

Customize the media processing behavior with these options:

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "process_video",
  "source": "input.mp4",
  "operations": [...],
  "config": {
    "threads": 4,  # Number of processing threads
    "gpu_acceleration": true,  # Use GPU acceleration when available
    "temp_dir": "/tmp/media_processing",  # Directory for temporary files
    "log_level": "info",  # Logging verbosity (debug, info, warning, error)
    "preserve_metadata": true,  # Preserve original metadata in output files
    "overwrite": true  # Overwrite output files if they exist
  }
}'
```

## Input Format

The CLI accepts input in the following format:

```json
{
  "task": "task_name",  // Required: The specific task to perform
  "source": "media_file",  // Required: Path to the media file
  "task_specific_parameters": {},  // Parameters specific to the task
  "config": {}  // Optional: Configuration options
}
```

## Output Format

The plugin returns a JSON object with the following structure:

```json
{
  "status": "success",  // or "error"
  "result": {
    "output_files": ["output.mp4"],
    "metadata": {
      "duration": "00:02:15",
      "size": "15.8 MB",
      "dimensions": "1280x720",
      "format": "MP4",
      "processing_time": "5.6s"
    }
  },
  "error": null  // Error message if status is "error"
}
```

## Saving Results to File

To save the results to a file, use the `--output` parameter:

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "extract_info",
  "source": "video.mp4"
}' --output "media_info.json"
```

## Advanced Usage

### Batch Processing

Process multiple files in a single command:

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "batch_process",
  "sources": ["image1.jpg", "image2.png", "image3.tiff"],
  "operation": {
    "task": "process_image",
    "operations": [
      {"type": "resize", "width": 800, "height": null, "maintain_aspect": true},
      {"type": "adjust", "brightness": 1.1}
    ],
    "output_dir": "processed/",
    "output_format": "jpg"
  }
}'
```

### Media Pipeline

Create a complex media processing pipeline:

```bash
python -m pepperpy.cli workflow run workflow/media_processing --input '{
  "task": "pipeline",
  "steps": [
    {
      "task": "process_video",
      "source": "input.mp4",
      "operations": [
        {"type": "trim", "start": "00:00:10", "end": "00:01:30"},
        {"type": "resize", "width": 1280, "height": 720}
      ],
      "output": "temp_video.mp4"
    },
    {
      "task": "process_audio",
      "source": "background.mp3",
      "operations": [
        {"type": "trim", "end": "00:01:20"},
        {"type": "normalize", "level": -3}
      ],
      "output": "temp_audio.mp3"
    },
    {
      "task": "process_video",
      "source": "temp_video.mp4",
      "operations": [
        {"type": "add_audio", "source": "temp_audio.mp3", "replace": true},
        {"type": "add_text", "text": "Final Product", "position": "bottom_right"}
      ],
      "output": "final_video.mp4"
    }
  ],
  "cleanup_temp_files": true
}'
```

## Python Usage

You can also use the plugin directly in Python:

```python
import asyncio
from pepperpy.plugin.registry import PluginRegistry
from pepperpy.plugin.discovery import discover_plugins

async def process_media():
    await discover_plugins()
    registry = PluginRegistry()
    
    processor = await registry.create_provider_instance("workflow", "media_processing")
    
    try:
        result = await processor.execute({
            "task": "process_image",
            "source": "input.jpg",
            "operations": [
                {"type": "resize", "width": 800, "height": 600},
                {"type": "adjust", "brightness": 1.2, "contrast": 1.1}
            ],
            "output": "processed_image.jpg"
        })
        
        return result
    finally:
        await processor.cleanup()

if __name__ == "__main__":
    result = asyncio.run(process_media())
    print(f"Media processing completed: {result['status']}")
    if result["status"] == "success":
        print(f"Output: {result['result']['output_files']}")
```

## Troubleshooting

### Missing Dependencies

If you encounter missing dependency errors:

1. Ensure you have the required libraries installed:
   - For image processing: Pillow
   - For video processing: FFmpeg
   - For audio processing: FFmpeg and PyDub

2. Install the necessary system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg libavcodec-extra
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download FFmpeg from https://ffmpeg.org/download.html
   ```

### Performance Issues

For slow processing of large media files:

1. Enable GPU acceleration in the configuration if your system supports it
2. Increase the number of processing threads
3. Process in smaller chunks or at lower resolutions for initial tests

### Format Compatibility

If you encounter format compatibility issues:

1. Check that your input format is supported
2. Try converting to a more universally supported format first (e.g., MP4 for video, MP3 for audio, PNG for images)
3. Specify codecs explicitly in your conversion settings

## Further Documentation

For more detailed documentation, see the [Media Processing Documentation](docs/plugins/media_processing/index.md). 