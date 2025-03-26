#!/usr/bin/env python
"""Simplified Podcast Generator Example.

This example demonstrates how to use PepperPy to create a podcast
with minimal code by leveraging the library's built-in capabilities.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List

from pepperpy.tts import TTSFactory
from pepperpy.tts.audio_pipeline import AudioProject, AudioSegment


class AudioPipeline:
    """Audio pipeline for podcast generation."""

    def __init__(self, output_dir: str = ".pepperpy/audio") -> None:
        """Initialize audio pipeline.

        Args:
            output_dir: Directory to store audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_segment(self, title: str, content: str, speaker: str) -> AudioSegment:
        """Create an audio segment.

        Args:
            title: Title of the segment
            content: Text content to convert to speech
            speaker: Speaker identifier

        Returns:
            Audio segment
        """
        return AudioSegment(
            title=title,
            content=content,
            speaker=speaker,
            duration="",  # Duration will be determined after TTS
        )

    def create_project(
        self, title: str, description: str, segments: List[AudioSegment]
    ) -> AudioProject:
        """Create an audio project.

        Args:
            title: Title of the project
            description: Project description
            segments: List of audio segments

        Returns:
            Audio project
        """
        return AudioProject(
            title=title,
            description=description,
            segments=segments,
        )

    def save_project(self, project: AudioProject, path: str) -> None:
        """Save project to JSON file.

        Args:
            project: Project to save
            path: Path to save to
        """
        data = {
            "title": project.title,
            "description": project.description,
            "segments": [
                {
                    "title": segment.title,
                    "content": segment.content,
                    "speaker": segment.speaker,
                }
                for segment in project.segments
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    async def process_project(
        self, project: AudioProject, background_music: str = "none"
    ) -> Path:
        """Process a project to generate audio files.

        Args:
            project: The project to process
            background_music: Background music to use (default: none)

        Returns:
            Path to generated audio file
        """
        # Create TTS provider
        tts = TTSFactory.create_provider(
            "azure",
            **{
                "api_key": os.getenv("AZURE_TTS_KEY"),
                "region": os.getenv("AZURE_TTS_REGION"),
                "voice_config": {
                    "voice_name": "en-US-JennyNeural",
                    "style": "chat",
                    "role": "Girl",
                },
                "audio_config": {"audio_format": "audio-24khz-48kbitrate-mono-mp3"},
            },
        )

        # Process each segment
        for segment in project.segments:
            # Convert text to speech
            audio_bytes = await tts.convert_text(segment.content, segment.speaker)

            # Save segment audio
            segment_path = self.output_dir / f"{project.title}_{segment.title}.mp3"
            with open(segment_path, "wb") as f:
                f.write(audio_bytes)

        # Combine segments into final podcast
        # This is a placeholder - you would need audio processing logic here
        output_path = self.output_dir / f"{project.title}_final.mp3"
        with open(output_path, "wb") as f:
            for segment in project.segments:
                segment_path = self.output_dir / f"{project.title}_{segment.title}.mp3"
                with open(segment_path, "rb") as sf:
                    f.write(sf.read())

        return output_path


async def main() -> None:
    """Run example."""
    # Create pipeline
    pipeline = AudioPipeline()

    # Create segments
    segments = [
        pipeline.create_segment(
            title="intro",
            content="Welcome to our podcast about Python!",
            speaker="host",
        ),
        pipeline.create_segment(
            title="main",
            content="Python is a versatile programming language...",
            speaker="expert",
        ),
        pipeline.create_segment(
            title="outro",
            content="Thanks for listening!",
            speaker="host",
        ),
    ]

    # Create project
    project = pipeline.create_project(
        title="python_intro",
        description="Introduction to Python",
        segments=segments,
    )

    # Save project
    pipeline.save_project(project, "python_intro.json")

    # Process project
    output_path = await pipeline.process_project(project)
    print(f"Generated podcast: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
