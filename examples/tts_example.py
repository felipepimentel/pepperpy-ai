"""Example demonstrating Text-to-Speech functionality with PepperPy's fluent API.

This example shows how to use PepperPy's TTS builder to generate speech from text
with various voice configurations.
"""

import asyncio
import os

from pepperpy import PepperPy


async def main() -> None:
    """Run the example."""
    print("TTS Example")
    print("=" * 50)

    # Initialize PepperPy with TTS support
    # Provider configuration comes from environment variables
    async with PepperPy().with_tts() as pepper:
        # Basic TTS generation
        print("\nGenerating basic speech...")
        audio = await pepper.tts.with_text(
            "Hello! This is a test of PepperPy's TTS capabilities."
        ).generate()

        # Save to output directory
        os.makedirs("examples/output", exist_ok=True)
        await audio.save("examples/output/basic.mp3")
        print("Saved to examples/output/basic.mp3")

        # TTS with voice configuration
        print("\nGenerating speech with custom voice settings...")
        audio = await (
            pepper.tts.with_text("This is an example with custom voice settings.")
            .with_voice("en-US-Neural2-F")  # Example voice ID
            .with_speed(1.2)
            .with_pitch(0.8)
            .with_volume(1.5)
            .generate()
        )

        await audio.save("examples/output/custom_voice.mp3")
        print("Saved to examples/output/custom_voice.mp3")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_TTS__PROVIDER=azure
    # PEPPERPY_TTS__API_KEY=your_api_key
    # PEPPERPY_TTS__REGION=your_region
    asyncio.run(main())
