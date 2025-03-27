"""Example demonstrating TTS usage in PepperPy."""

import asyncio
from pathlib import Path

import pepperpy


async def main() -> None:
    """Run the TTS example."""
    # Initialize PepperPy with fluent API
    # All configuration comes from environment variables (.env file)
    pepper = (
        pepperpy.PepperPy().with_tts()  # Uses PEPPERPY_TTS__PROVIDER and other env vars
    )

    # Use async context manager for automatic initialization/cleanup
    async with pepper:
        # List available voices
        voices = await pepper.list_voices()
        print("\nAvailable voices:")
        for voice in voices:
            print(f"- {voice['name']} ({voice['id']}, {voice['locale']})")

        # Text to synthesize
        text = "Hello! This is a test of the Text-to-Speech service using PepperPy."

        # Convert text to speech
        print("\nConverting text to speech...")
        audio_data = await pepper.text_to_speech(text, voice="en-US-JennyNeural")

        # Save the audio file
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "tts_output.mp3"

        with open(output_file, "wb") as f:
            f.write(audio_data)

        print(f"Audio saved to: {output_file}")

        # Demonstrate streaming
        print("\nStreaming text to speech...")
        async for chunk in pepper.text_to_speech_stream(
            text,
            voice="en-US-JennyNeural",
        ):
            # In a real application, you would process each chunk
            # (e.g., send it to an audio output device)
            print(f"Received chunk of {len(chunk)} bytes")


if __name__ == "__main__":
    # Run the example
    # Required environment variables should be in .env file:
    # PEPPERPY_TTS__PROVIDER=azure
    # PEPPERPY_TTS__AZURE__API_KEY=your-azure-speech-key
    # PEPPERPY_TTS__AZURE__REGION=your-azure-region
    asyncio.run(main())
