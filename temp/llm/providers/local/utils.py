"""Utility functions for the Local provider.

This module provides utility functions specific to the Local provider.
"""

from pathlib import Path
from typing import List

from pepperpy.llm.errors import (
    LLMConfigError,
    LLMError,
)
from pepperpy.llm.providers.local.config import LocalConfig, ModelType
from pepperpy.llm.utils import Message, Prompt
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


def convert_messages_to_prompt_text(messages: List[Message]) -> str:
    """Convert PepperPy messages to a text prompt.

    Args:
        messages: The messages to convert

    Returns:
        The messages as a text prompt
    """
    prompt_text = ""

    for message in messages:
        role = message.role
        content = message.content

        if role == "system":
            prompt_text += f"<|system|>\n{content}\n"
        elif role == "user":
            prompt_text += f"<|user|>\n{content}\n"
        elif role == "assistant":
            prompt_text += f"<|assistant|>\n{content}\n"
        else:
            # Skip unknown roles
            logger.warning(f"Skipping message with unknown role: {role}")
            continue

    # Add the final assistant prompt
    if not prompt_text.endswith("<|assistant|>\n"):
        prompt_text += "<|assistant|>\n"

    return prompt_text


def convert_prompt_to_text(prompt: Prompt) -> str:
    """Convert a PepperPy prompt to text.

    Args:
        prompt: The prompt to convert

    Returns:
        The prompt as text
    """
    return convert_messages_to_prompt_text(prompt.messages)


def ensure_model_downloaded(config: LocalConfig, model_name: str) -> Path:
    """Ensure that a model is downloaded.

    Args:
        config: The Local provider configuration
        model_name: The name of the model to download

    Returns:
        The path to the model

    Raises:
        LLMConfigError: If the model is not configured
        LLMError: If there is an error downloading the model
    """
    # Check if the model is configured
    if model_name not in config.models:
        raise LLMConfigError(
            f"Model '{model_name}' is not configured",
            provider="local",
        )

    model_config = config.models[model_name]

    # Check if the model path is absolute
    model_path = Path(model_config.path)
    if model_path.is_absolute():
        # Check if the model exists
        if not model_path.exists():
            raise LLMError(
                f"Model '{model_name}' not found at '{model_path}'",
                provider="local",
            )

        return model_path

    # Check if the model exists in the models directory
    models_dir = Path(config.models_dir)
    model_path = models_dir / model_path

    if model_path.exists():
        return model_path

    # If the model is a Hugging Face model, download it
    if model_config.type == ModelType.HUGGINGFACE:
        try:
            from huggingface_hub import snapshot_download

            # Create the models directory if it doesn't exist
            models_dir.mkdir(parents=True, exist_ok=True)

            # Download the model
            logger.info(f"Downloading model '{model_name}' from Hugging Face")

            # The path is the model ID on Hugging Face
            model_id = model_config.path

            # Download the model
            local_path = snapshot_download(
                repo_id=model_id,
                cache_dir=config.cache_dir,
                local_dir=str(model_path),
            )

            return Path(local_path)
        except ImportError:
            raise LLMError(
                "The 'huggingface_hub' package is required to download models from Hugging Face",
                provider="local",
            )
        except Exception as e:
            raise LLMError(
                f"Error downloading model '{model_name}' from Hugging Face: {e}",
                provider="local",
            )

    # For other model types, the user must provide the model
    raise LLMError(
        f"Model '{model_name}' not found at '{model_path}'",
        provider="local",
    )


def get_device(config: LocalConfig) -> str:
    """Get the device to use for inference.

    Args:
        config: The Local provider configuration

    Returns:
        The device to use
    """
    # Check if GPU is available and should be used
    if config.use_gpu:
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            logger.warning("PyTorch not available, falling back to CPU")

    return "cpu"


def check_dependencies(model_type: ModelType) -> None:
    """Check if the required dependencies are installed.

    Args:
        model_type: The type of model

    Raises:
        LLMError: If the required dependencies are not installed
    """
    if model_type == ModelType.HUGGINGFACE:
        try:
            import transformers
        except ImportError:
            raise LLMError(
                "The 'transformers' package is required to use Hugging Face models",
                provider="local",
            )
    elif model_type in (ModelType.GGML, ModelType.GGUF):
        try:
            import ctransformers
        except ImportError:
            raise LLMError(
                "The 'ctransformers' package is required to use GGML/GGUF models",
                provider="local",
            )
