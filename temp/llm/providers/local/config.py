"""Configuration for the Local provider.

This module defines configuration classes and constants for the Local provider.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pepperpy.config import ConfigModel


class ModelType(str, Enum):
    """Type of local model.

    Attributes:
        HUGGINGFACE: A model from Hugging Face
        GGML: A model in GGML format
        GGUF: A model in GGUF format
        CUSTOM: A custom model type
    """

    HUGGINGFACE = "huggingface"
    GGML = "ggml"
    GGUF = "gguf"
    CUSTOM = "custom"


@dataclass
class LocalModelConfig:
    """Configuration for a local model.

    Attributes:
        name: The name of the model
        path: The path to the model
        type: The type of the model
        max_tokens: The maximum number of tokens the model can process
        supports_embeddings: Whether the model supports embeddings
        default_temperature: The default temperature to use with this model
        device: The device to run the model on (e.g., "cpu", "cuda:0")
        quantization: The quantization level to use (e.g., "4bit", "8bit")
        context_length: The context length of the model
    """

    name: str
    path: str
    type: ModelType
    max_tokens: int = 2048
    supports_embeddings: bool = False
    default_temperature: float = 0.7
    device: str = "cpu"
    quantization: Optional[str] = None
    context_length: int = 4096


@dataclass
class LocalConfig(ConfigModel):
    """Configuration for the Local provider.

    Attributes:
        models_dir: The directory to store models in
        cache_dir: The directory to cache models in
        default_model: The default model to use
        models: A dictionary of model configurations
        timeout: The timeout for model operations in seconds
        use_gpu: Whether to use GPU acceleration if available
        gpu_layers: The number of layers to offload to GPU
        threads: The number of threads to use for CPU inference
    """

    models_dir: str = str(Path.home() / ".pepperpy" / "models")
    cache_dir: str = str(Path.home() / ".pepperpy" / "cache")
    default_model: str = ""
    models: Dict[str, LocalModelConfig] = field(default_factory=dict)
    timeout: float = 60.0
    use_gpu: bool = True
    gpu_layers: int = -1  # -1 means all layers
    threads: int = 4

    def __post_init__(self):
        """Initialize default models if none are provided."""
        # No default models for local provider
        # Users must specify their own models
        pass


# Default configuration
DEFAULT_CONFIG = LocalConfig()


def get_config() -> LocalConfig:
    """Get the Local configuration.

    Returns:
        The Local configuration
    """
    from pepperpy.config import get_config as get_global_config

    config = get_global_config()
    local_config = config.get("llm.providers.local", DEFAULT_CONFIG)

    if isinstance(local_config, dict):
        return LocalConfig(**local_config)

    return local_config
