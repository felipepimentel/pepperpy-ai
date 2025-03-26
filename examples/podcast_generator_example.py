#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast by:
1. Converting text to speech
2. Handling multiple speakers
3. Combining audio segments
"""

import asyncio
from typing import Dict, List

from pepperpy import PepperPy


async def create_podcast(title: str, segments: List[Dict[str, str]]) -> bytes:
    """Create a podcast from text segments.

    Args:
        title: Podcast title
        segments: List of segments with title, content, and speaker

    Returns:
        Combined audio bytes
    """
    async with PepperPy().with_tts() as assistant:
        # Convert each segment to audio
        audio_segments = []
        for segment in segments:
            audio = await assistant.tts.convert_text(
                segment["content"], segment["speaker"]
            )
            audio_segments.append(audio)

        # Combine segments (handled by the library)
        return await assistant.tts.combine_audio(audio_segments)


async def main() -> None:
    """Run the example."""
    print("Podcast Generator Example")
    print("=" * 50)

    # Define podcast segments
    segments = [
        {
            "title": "intro",
            "content": "Welcome to our podcast about Python!",
            "speaker": "host",
        },
        {
            "title": "main",
            "content": "Python is a versatile programming language...",
            "speaker": "expert",
        },
        {
            "title": "outro",
            "content": "Thanks for listening!",
            "speaker": "host",
        },
    ]

    # Generate podcast
    print("\nGenerating podcast...")
    audio = await create_podcast("python_intro", segments)
    print(f"\nGenerated podcast: {len(audio)} bytes")


if __name__ == "__main__":
    asyncio.run(main())
