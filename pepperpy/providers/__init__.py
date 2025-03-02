"""Provider implementations for PepperPy framework capabilities.

This module contains implementations of various providers that integrate
with external services and APIs. The providers are organized by domain:

- agent: Agent and chain providers
- audio: Audio processing providers (synthesis, transcription)
- cloud: Cloud service providers (AWS, GCP, Azure)
- embedding: Vector embedding providers
- llm: Language model providers
- memory: Memory storage providers
- storage: Data storage providers
- vision: Computer vision providers
"""

# Import submodules
from . import agent, audio, memory, storage

__all__ = [
    "agent",
    "audio",
    "memory",
    "storage",
]
