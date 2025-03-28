"""Mock TTS provider for testing."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..base import TTSProvider, TTSVoice, TTSAudio


class MockTTSProvider(TTSProvider):
    """A mock TTS provider for testing."""

    def __init__(
        self,
        voice_id: str = "default",
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> None:
        """Initialize MockTTSProvider.

        Args:
            voice_id: Voice ID to use
            output_format: Output format (mp3 or wav)
            **kwargs: Additional configuration
        """
        self.voice_id = voice_id
        self.output_format = output_format
        self.initialized = False
        print("Initializing mock TTS provider")

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
        self.initialized = True

    async def cleanup(self) -> None:
        """Cleanup the provider."""
        print("Cleaning up mock TTS provider")

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get a list of available voices.
        
        Returns:
            A list of TTSVoice objects
        """
        return [
            TTSVoice(
                id="mock-male",
                name="Mock Male Voice",
                gender="male",
                language="en-US",
            ),
            TTSVoice(
                id="mock-female",
                name="Mock Female Voice",
                gender="female",
                language="en-US",
            ),
        ]

    async def synthesize(
        self, 
        text: str, 
        voice_id: Optional[str] = None, 
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> TTSAudio:
        """Synthesize speech from text.
        
        Args:
            text: Input text
            voice_id: Voice ID to use (overrides constructor)
            output_path: Optional path to save audio
            **kwargs: Additional synthesis parameters
            
        Returns:
            TTSAudio object containing the synthesized audio
        """
        voice_id = voice_id or self.voice_id
        
        print(f"MOCK: Synthesizing text with voice {voice_id}")
        print(f"MOCK: Text (truncated): {text[:50]}...")
        
        # Create an empty mock audio file
        audio_data = b'MOCK_AUDIO_DATA'
        
        # Save to file if requested
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            print(f"MOCK: Saved audio to {output_path}")
        
        return TTSAudio(
            audio_data=audio_data,
            content_type=f"audio/{self.output_format}",
            duration_seconds=len(text) * 0.05,  # Fake duration based on text length
        )

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.
        
        Returns:
            Provider configuration dictionary
        """
        return {
            "provider": "mock",
            "voice_id": self.voice_id,
            "output_format": self.output_format,
        } 