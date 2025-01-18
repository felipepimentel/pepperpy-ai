"""Embeddings capability configuration module."""

from dataclasses import dataclass
from typing import Any

from .capability_config import CapabilityConfig


@dataclass
class EmbeddingsConfig(CapabilityConfig):
    """Embeddings capability configuration."""

    model: str
    batch_size: int = 32
    normalize: bool = True
    device: str = "cpu"
    timeout: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        base_data = super().to_dict()
        config_data: dict[str, Any] = {
            "model": self.model,
            "batch_size": self.batch_size,
            "normalize": self.normalize,
            "device": self.device,
            "timeout": self.timeout,
        }
        base_data.update(config_data)
        return dict(base_data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingsConfig":
        """Create config from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            version=data.get("version", "1.0.0"),
            enabled=data.get("enabled", True),
            api_key=data.get("api_key"),
            api_base=data.get("api_base"),
            api_version=data.get("api_version"),
            organization_id=data.get("organization_id"),
            settings=data.get("settings", {}),
            model=data["model"],
            batch_size=data.get("batch_size", 32),
            normalize=data.get("normalize", True),
            device=data.get("device", "cpu"),
            timeout=data.get("timeout"),
        )
