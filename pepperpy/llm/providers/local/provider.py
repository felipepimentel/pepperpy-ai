"""Local provider implementation.

This module provides an implementation of the Local provider for the PepperPy LLM module.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.llm.errors import (
    LLMConfigError,
    LLMError,
)
from pepperpy.llm.providers.base import LLMProvider, LLMResult, Message
from pepperpy.llm.providers.local.config import LocalConfig, ModelType, get_config
from pepperpy.llm.providers.local.utils import (
    check_dependencies,
    ensure_model_downloaded,
    get_device,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class LocalProvider(LLMProvider):
    """Local provider implementation.

    This provider runs LLM inference locally using libraries like transformers.
    """

    def __init__(
        self,
        config: Optional[LocalConfig] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the local provider.

        Args:
            config: Configuration for the local provider
            model_name: Override the model name in the config
            **kwargs: Additional configuration options
        """
        self.config = config or get_config()
        model_name = model_name or self.config.default_model
        super().__init__(provider_name="local", model_name=model_name, **kwargs)

        # Set up the provider
        self._models: Dict[str, Any] = {}
        self._tokenizers: Dict[str, Any] = {}
        self.device = get_device(self.config)

        # Add capabilities
        self.add_capability("local_inference")

        # Check dependencies
        # Make sure we have the dependencies for at least one model type
        if self.config.models and model_name in self.config.models:
            model_type = self.config.models[model_name].type
            check_dependencies(model_type)
        else:
            check_dependencies(ModelType.HUGGINGFACE)

    async def close(self) -> None:
        """Close any open resources."""
        # Clear models and tokenizers to free memory
        self._models.clear()
        self._tokenizers.clear()

    def _get_model(self, model_name: str) -> Any:
        """Get a model instance, loading it if necessary.

        Args:
            model_name: Name of the model to get

        Returns:
            The model instance

        Raises:
            LLMConfigError: If the model is not supported
            LLMError: If there is an error loading the model
        """
        if model_name not in self._models:
            # Check if the model is configured
            if model_name not in self.config.models:
                raise LLMConfigError(
                    f"Model '{model_name}' is not configured for Local provider"
                )

            # Get the model configuration
            model_config = self.config.models[model_name]

            # Load the model
            logger.info(f"Loading model: {model_name}")

            try:
                # Ensure the model is downloaded
                model_path = ensure_model_downloaded(self.config, model_name)

                # Load the model based on its type
                if model_config.type == ModelType.HUGGINGFACE:
                    import torch
                    from transformers import AutoModelForCausalLM

                    # Load the model
                    model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        device_map=self.device,
                        torch_dtype=torch.float16
                        if torch.cuda.is_available()
                        else None,
                    )

                    # Cache the model
                    self._models[model_name] = model
                else:
                    raise LLMConfigError(f"Unsupported model type: {model_config.type}")
            except Exception as e:
                logger.error(f"Error loading model {model_name}: {e}")
                raise LLMError(f"Failed to load model '{model_name}': {e}") from e

        return self._models[model_name]

    def _get_tokenizer(self, model_name: str) -> Any:
        """Get a tokenizer instance, loading it if necessary.

        Args:
            model_name: Name of the model to get

        Returns:
            The tokenizer instance

        Raises:
            LLMConfigError: If the model is not supported
            LLMError: If there is an error loading the tokenizer
        """
        if model_name not in self._tokenizers:
            # Check if the model is configured
            if model_name not in self.config.models:
                raise LLMConfigError(
                    f"Model '{model_name}' is not configured for Local provider"
                )

            # Get the model configuration
            model_config = self.config.models[model_name]

            # Load the tokenizer
            logger.info(f"Loading tokenizer: {model_name}")

            try:
                # Ensure the model is downloaded
                model_path = ensure_model_downloaded(self.config, model_name)

                # Load the tokenizer based on its type
                if model_config.type == ModelType.HUGGINGFACE:
                    from transformers import AutoTokenizer

                    # Load the tokenizer
                    tokenizer = AutoTokenizer.from_pretrained(
                        str(model_path),
                        padding_side="left",
                        truncation_side="left",
                    )

                    # Cache the tokenizer
                    self._tokenizers[model_name] = tokenizer
                else:
                    raise LLMConfigError(f"Unsupported model type: {model_config.type}")
            except Exception as e:
                logger.error(f"Error loading tokenizer {model_name}: {e}")
                raise LLMError(f"Failed to load tokenizer '{model_name}': {e}") from e

        return self._tokenizers[model_name]

    async def generate(self, prompt: Union[str, List[Message]], **options) -> LLMResult:
        """Generate text using the local model.

        Args:
            prompt: The prompt to generate text from (string or list of messages)
            **options: Additional options for generation

        Returns:
            The generated text result

        Raises:
            LLMError: If generation fails
        """
        # Convert prompt to string if it's a list of messages
        if isinstance(prompt, list):
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in prompt])
        else:
            prompt_text = prompt

        model_name = options.get("model_name", self.model_name)
        temperature = options.get("temperature", 0.7)
        max_tokens = options.get("max_tokens", 512)

        try:
            # Get model and tokenizer
            model = self._get_model(model_name)
            tokenizer = self._get_tokenizer(model_name)

            # Tokenize input
            inputs = tokenizer(prompt_text, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate text
            outputs = model.generate(
                **inputs,
                max_length=max_tokens + len(inputs["input_ids"][0]),
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.eos_token_id,
            )

            # Decode and get only the new text after the prompt
            full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = full_text[len(prompt_text) :].strip()

            # Count tokens for usage info
            prompt_tokens = len(inputs["input_ids"][0])
            completion_tokens = len(outputs[0]) - prompt_tokens
            total_tokens = prompt_tokens + completion_tokens

            # Return the result
            return LLMResult(
                text=generated_text,
                model_name=model_name,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                metadata={"temperature": temperature, "max_tokens": max_tokens},
            )
        except Exception as e:
            logger.error(f"Error generating text with local model: {e}")
            raise LLMError(f"Local model generation failed: {e}") from e

    async def generate_stream(
        self, prompt: Union[str, List[Message]], **options
    ) -> AsyncIterator[LLMResult]:
        """Generate text in a streaming fashion using the local model.

        Args:
            prompt: The prompt to generate text from (string or list of messages)
            **options: Additional options for generation

        Yields:
            The generated text chunks

        Raises:
            LLMError: If generation fails
        """
        # This is a simplified implementation that doesn't actually stream
        # A real implementation would generate tokens one by one
        result = await self.generate(prompt, **options)

        # Split the result into chunks and yield them
        chunks = [result.text[i : i + 10] for i in range(0, len(result.text), 10)]

        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            yield LLMResult(
                text=chunk,
                model_name=result.model_name,
                usage=result.usage,
                metadata={"is_finished": is_last, **result.metadata},
            )
            # Simulate streaming delay
            await asyncio.sleep(0.1)

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "provider": "local",
            "default_model": self.config.default_model,
            "models": {
                name: {
                    "name": model.name,
                    "path": model.path,
                    "type": model.type.value,
                    "max_tokens": model.max_tokens,
                }
                for name, model in self.config.models.items()
            },
            "device": self.device,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "provider": "local",
            "supports_streaming": True,
            "capabilities": list(self._capabilities),
        }
