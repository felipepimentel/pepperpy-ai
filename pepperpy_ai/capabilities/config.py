"""Capability configuration module."""

from dataclasses import dataclass


@dataclass
class CapabilityConfig:
    """Base capability configuration."""

    name: str
    version: str
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    metadata: dict[str, str] | None = None
    settings: dict[str, str] | None = None 