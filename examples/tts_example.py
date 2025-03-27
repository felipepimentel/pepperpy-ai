"""Example demonstrating TTS usage in PepperPy."""

import asyncio
import os
from pathlib import Path

from pepperpy.tts import AzureTTSProvider, TTSComponent


async def main() -> None:
    """Run the TTS example."""
    # Initialize the Azure TTS provider
    provider = AzureTTSProvider()
    await provider.initialize()

    try:
        # List available voices
        voices = await provider.get_voices()
        print("\nAvailable voices:")
        for voice in voices:
            print(f"- {voice['name']} ({voice['id']}, {voice['locale']})")

        # Create a TTS component
        component = TTSComponent(
            id="tts-1",
            name="Text to Speech",
            provider=provider,
            config={
                "voice": "en-US-JennyNeural",
                "output_format": "audio-16khz-128kbitrate-mono-mp3",
            },
        )

        # Text to synthesize
        text = (
            "Hello! This is a test of the Azure Text-to-Speech service using PepperPy."
        )

        # Convert text to speech
        print("\nConverting text to speech...")
        audio_data = await component.process(text)

        # Save the audio file
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "tts_output.mp3"

        with open(output_file, "wb") as f:
            f.write(audio_data)

        print(f"Audio saved to: {output_file}")

        # Demonstrate streaming
        print("\nStreaming text to speech...")
        async for chunk in provider.convert_text_stream(
            text,
            voice_id="en-US-JennyNeural",
            chunk_size=4096,
        ):
            # In a real application, you would process each chunk
            # (e.g., send it to an audio output device)
            print(f"Received chunk of {len(chunk)} bytes")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        # Clean up resources
        await provider.cleanup()


if __name__ == "__main__":
    # Set Azure credentials (replace with your own)
    os.environ["AZURE_SPEECH_KEY"] = "your-azure-speech-key"
    os.environ["AZURE_SPEECH_REGION"] = "your-azure-region"

    # Run the example
    asyncio.run(main())
