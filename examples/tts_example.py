"""
PepperPy TTS Example.

Example of using the TTS module with the Azure provider.
"""

import asyncio

from pepperpy.tts import AzureTTSProvider


async def main():
    """Run the TTS example."""
    # Create a provider with configuration
    provider = AzureTTSProvider(
        config={
            "api_key": "your-api-key",  # Replace with actual Azure API key
            "region": "eastus",
        }
    )

    # Initialize the provider
    await provider.initialize()

    # Get available voices
    voices = await provider.get_voices()
    print(f"Available voices: {len(voices)}")
    for voice in voices[:2]:  # Print first two voices
        print(f"- {voice['id']} ({voice['name']}, {voice['gender']})")

    # Convert text to speech
    text = (
        "Hello world, this is a test of the Azure Text-to-Speech provider in PepperPy."
    )
    voice_id = "en-US-AriaNeural"

    print(f"\nConverting text to speech with voice {voice_id}...")
    audio_data = await provider.convert_text(
        text=text, voice_id=voice_id, style="cheerful"
    )

    # In a real application, you'd save the audio data
    print(f"Generated {len(audio_data)} bytes of audio data")

    # Stream text (using the default implementation in this example)
    print("\nStreaming text to speech...")
    chunks = []
    async for chunk in provider.convert_text_stream(text=text, voice_id=voice_id):
        chunks.append(chunk)
        print(f"Received chunk of {len(chunk)} bytes")

    print(f"Received {len(chunks)} chunks, total {sum(len(c) for c in chunks)} bytes")


if __name__ == "__main__":
    asyncio.run(main())
