"""
TTS Provider implementations.

This package contains implementations of various TTS providers.
"""

PROVIDER_MODULES = {
    "ElevenLabsProvider": ".elevenlabs",
    "MurfProvider": ".murf",
    "PlayHTProvider": ".playht",
    "AzureProvider": ".azure",
    "MockTTSProvider": ".mock",
}

__all__ = list(PROVIDER_MODULES.keys())
