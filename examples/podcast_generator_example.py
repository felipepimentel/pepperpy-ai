#!/usr/bin/env python
"""Simplified Podcast Generator Example.

This example demonstrates how to use PepperPy to create a podcast
with minimal code by leveraging the library's built-in capabilities.
"""

import asyncio
from pathlib import Path

from pepperpy.tts import AudioPipeline, VerbosityLevel


async def main():
    """Run the simplified podcast generator example."""
    # Initialize the audio pipeline with verbosity level
    pipeline = AudioPipeline(
        output_dir=Path("examples/output/podcast"),
        voice_mapping={
            "host": "en-US-1",     # Male voice
            "guest1": "en-US-2",   # Female voice
            "guest2": "en-US-3"    # Different male voice
        },
        verbosity=VerbosityLevel.INFO  # Control output verbosity
    )
    
    # Create podcast content using the library's structured API
    project = pipeline.create_project(
        title="AI Technology Podcast",
        description="An example podcast about AI technology advancements",
        segments=[
            pipeline.create_segment(
                title="Introduction",
                duration="3:00",
                content="Welcome to our podcast about AI technology. Today we'll be discussing recent advancements.",
                speaker="host"
            ),
            pipeline.create_segment(
                title="AI Applications",
                duration="10:00",
                content="AI is being used in numerous fields today, from healthcare to finance.",
                speaker="guest1"
            ),
            pipeline.create_segment(
                title="Future Developments",
                duration="8:00",
                content="In the next decade, we expect to see AI become more integrated into daily life.",
                speaker="guest2"
            ),
            pipeline.create_segment(
                title="Conclusion",
                duration="2:00",
                content="Thanks for listening to our discussion about AI technology.",
                speaker="host"
            )
        ]
    )
    
    # Save the project to a file (handled by the library)
    project_file = pipeline.save_project(project)
    
    # Process the entire podcast in one call
    # This will:
    # 1. Convert the text to speech for each segment
    # 2. Add sound effects and background music
    # 3. Compile all segments into a final podcast file
    final_podcast_path = await pipeline.process_project(
        project,  # We can use the project object directly
        background_music="ambient",  # Example parameter
    )
    
    print(f"\nPodcast generated successfully at: {final_podcast_path}")
    print("\nExample completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 