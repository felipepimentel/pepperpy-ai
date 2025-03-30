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

    # Development mode: No API keys needed if PEPPERPY_DEV__MODE=true
    # The TTS provider is controlled by PEPPERPY_TTS__PROVIDER (default: elevenlabs)
    # For testing without API keys, set:
    #   export PEPPERPY_DEV__MODE=true
    #   export PEPPERPY_TTS__PROVIDER=mock

    # Create PepperPy instance with TTS support
    print("\nInitializing PepperPy with TTS support...")
    test_mode = os.environ.get("PEPPERPY_DEV__MODE", "").lower() == "true"
    if test_mode:
        print("Running in DEVELOPMENT MODE - using mock TTS provider")
        print("No actual API calls will be made")

    async with PepperPy().with_tts() as pepper:
        # Basic TTS generation
        print("\nGenerating basic speech...")
        audio = await pepper.tts.with_text(
            "Hello! This is a test of PepperPy's TTS capabilities."
        ).generate()

        # Save to output directory
        os.makedirs("examples/output", exist_ok=True)
        output_path = (
            "examples/output/basic.wav" if test_mode else "examples/output/basic.mp3"
        )
        audio.save(output_path)
        print(f"Saved to {output_path}")

        # TTS with voice configuration
        print("\nGenerating speech with custom voice settings...")

        # In test mode, use the available mock voices
        voice_id = "mock-female-en" if test_mode else "en-US-Neural2-F"

        audio = await (
            pepper.tts.with_text("This is an example with custom voice settings.")
            .with_voice(voice_id)
            .with_speed(1.2)
            .with_pitch(0.8)
            .with_volume(1.5)
            .generate()
        )

        output_path = (
            "examples/output/custom_voice.wav"
            if test_mode
            else "examples/output/custom_voice.mp3"
        )
        audio.save(output_path)
        print(f"Saved to {output_path}")

        # List available voices
        print("\nListing available voices:")
        try:
            # Accessing the provider directly to get available voices
            if pepper._tts_provider:
                voices = await pepper._tts_provider.get_available_voices()
                for voice in voices[
                    :5
                ]:  # Show only first 5 voices to keep output manageable
                    print(f"- {voice.name} ({voice.id}): {voice.language}")

                if len(voices) > 5:
                    print(f"... and {len(voices) - 5} more voices")
            else:
                print("TTS provider not available")
        except Exception as e:
            print(f"Error listing voices: {e}")


if __name__ == "__main__":
    # For automated testing, activate development mode:
    # export PEPPERPY_DEV__MODE=true
    # export PEPPERPY_TTS__PROVIDER=mock
    #
    # For production use, configure your TTS API keys in .env:
    # PEPPERPY_TTS__PROVIDER=elevenlabs (or azure, playht, murf)
    # PEPPERPY_TTS__ELEVENLABS__API_KEY=your_api_key
    asyncio.run(main())
