"""Configuration for the Local provider.

This module defines configuration classes and constants for the Local provider.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Supported model types."""

    HUGGINGFACE = "huggingface"
    GGML = "ggml"
    GGUF = "gguf"
    CUSTOM = "custom"


class LocalModelConfig(BaseModel):
    """Configuration for a local model.

    Attributes:
        name: The name of the model
        path: The path to the model, or None to use the Hugging Face model ID
        type: The type of the model
        max_tokens: The maximum number of tokens to generate
        default_temperature: The default temperature to use for generation
    """

    name: str
    path: Optional[str] = None
    type: ModelType = ModelType.HUGGINGFACE
    max_tokens: int = 512
    default_temperature: float = 0.7


class LocalConfig(BaseModel):
    """Configuration for the Local provider.

    Attributes:
        default_model: The default model to use
        models: A dictionary of model configurations
        data_dir: The directory to store model data in
        download_models: Whether to download models automatically
        gpu_layers: The number of layers to put on the GPU
        threads: The number of threads to use
    """

    default_model: Optional[str] = None
    models: Dict[str, LocalModelConfig] = Field(default_factory=dict)
    data_dir: Path = Path.home() / ".pepperpy" / "models"
    download_models: bool = True
    gpu_layers: int = 0
    threads: int = 4


def get_config() -> LocalConfig:
    """Get the default Local provider configuration.

    Returns:
        The default configuration
    """
    return LocalConfig()
