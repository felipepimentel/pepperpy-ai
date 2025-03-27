#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast by:
1. Converting text to speech
2. Handling multiple speakers
3. Combining audio segments
"""

import asyncio
from typing import Dict, List

import pepperpy


async def create_podcast(title: str, segments: List[Dict[str, str]]) -> bytes:
    """Create a podcast from text segments.

    Args:
        title: Podcast title
        segments: List of segments with title, content, and speaker

    Returns:
        Combined audio bytes
    """
    # Initialize PepperPy with fluent API
    # Configuration comes from environment variables
    pepper = pepperpy.PepperPy().with_tts()

    async with pepper:
        # Convert each segment to audio
        audio_segments = []
        for segment in segments:
            audio = await pepper.text_to_speech(
                text=segment["content"], voice=segment["speaker"]
            )
            audio_segments.append(audio)

        # Combine segments (simplified example)
        # In a real implementation, you might use a library like pydub
        combined_audio = b"".join(audio_segments)
        return combined_audio


async def main() -> None:
    """Run the example."""
    print("Podcast Generator Example")
    print("=" * 50)

    # Define podcast segments
    segments = [
        {
            "title": "intro",
            "content": "Welcome to our podcast about Python!",
            "speaker": "en-US-GuyNeural",
        },
        {
            "title": "main",
            "content": "Python is a versatile programming language...",
            "speaker": "en-US-JennyNeural",
        },
        {
            "title": "outro",
            "content": "Thanks for listening!",
            "speaker": "en-US-GuyNeural",
        },
    ]

    # Generate podcast
    print("\nGenerating podcast...")
    audio = await create_podcast("python_intro", segments)
    print(f"\nGenerated podcast: {len(audio)} bytes")

    # In a real example, you would save the audio to a file
    # with open("podcast.mp3", "wb") as f:
    #     f.write(audio)


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_TTS__PROVIDER=azure
    # PEPPERPY_TTS__AZURE__API_KEY=your-azure-speech-key
    # PEPPERPY_TTS__AZURE__REGION=your-azure-region
    asyncio.run(main())
