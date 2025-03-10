"""Local provider implementation.

This module provides an implementation of the Local provider for the PepperPy LLM module.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.llm.errors import (
    LLMConfigError,
    LLMError,
)
from pepperpy.llm.providers.base import LLMProvider, Response, StreamingResponse
from pepperpy.llm.providers.local.config import LocalConfig, ModelType, get_config
from pepperpy.llm.providers.local.utils import (
    check_dependencies,
    convert_prompt_to_text,
    ensure_model_downloaded,
    get_device,
)
from pepperpy.llm.utils import Prompt, retry, validate_prompt
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class LocalProvider(LLMProvider):
    """Local provider implementation.

    This provider integrates with local language models, including models from
    Hugging Face and GGML/GGUF formats.
    """

    def __init__(self, config: Optional[LocalConfig] = None):
        """Initialize the Local provider.

        Args:
            config: The provider configuration, or None to use the default
        """
        self.config = config or get_config()

        if not self.config.default_model:
            if not self.config.models:
                raise LLMConfigError(
                    "No models configured for Local provider",
                    provider="local",
                )

            # Use the first model as the default
            self.config.default_model = next(iter(self.config.models))

        # Check if the default model is configured
        if self.config.default_model not in self.config.models:
            raise LLMConfigError(
                f"Default model '{self.config.default_model}' is not configured",
                provider="local",
            )

        # Initialize model cache
        self._models = {}
        self._tokenizers = {}

        # Get the device to use
        self.device = get_device(self.config)

        logger.info(f"Using device: {self.device}")

    async def close(self) -> None:
        """Close the provider and release resources."""
        # Clean up models
        for model_name, model in self._models.items():
            try:
                # Some models have a close method
                if hasattr(model, "close"):
                    model.close()
            except Exception as e:
                logger.warning(f"Error closing model '{model_name}': {e}")

        # Clear the model cache
        self._models.clear()
        self._tokenizers.clear()

    def _get_model(self, model_name: str) -> Any:
        """Get a model.

        Args:
            model_name: The name of the model to get

        Returns:
            The model

        Raises:
            LLMConfigError: If the model is not configured
            LLMError: If there is an error loading the model
        """
        # Check if the model is already loaded
        if model_name in self._models:
            return self._models[model_name]

        # Get the model configuration
        if model_name not in self.config.models:
            raise LLMConfigError(
                f"Model '{model_name}' is not configured",
                provider="local",
            )

        model_config = self.config.models[model_name]

        # Check dependencies
        check_dependencies(model_config.type)

        # Ensure the model is downloaded
        model_path = ensure_model_downloaded(self.config, model_name)

        # Load the model
        try:
            if model_config.type == ModelType.HUGGINGFACE:
                # Load a Hugging Face model
                from transformers import AutoModelForCausalLM, AutoTokenizer

                # Load the tokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    str(model_path),
                    use_fast=True,
                )

                # Load the model
                model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    device_map=self.device,
                    torch_dtype="auto",
                )

                # Store the tokenizer
                self._tokenizers[model_name] = tokenizer

                # Store the model
                self._models[model_name] = model

                return model
            elif model_config.type in (ModelType.GGML, ModelType.GGUF):
                # Load a GGML/GGUF model
                from ctransformers import AutoModelForCausalLM as CTAutoModelForCausalLM

                # Load the model
                model = CTAutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    model_type="llama" if model_config.type == ModelType.GGUF else None,
                    gpu_layers=self.config.gpu_layers if self.device == "cuda" else 0,
                    threads=self.config.threads,
                )

                # Store the model
                self._models[model_name] = model

                return model
            elif model_config.type == ModelType.CUSTOM:
                # Custom model types are not supported yet
                raise LLMError(
                    "Custom model type not supported yet",
                    provider="local",
                )
            else:
                raise LLMError(
                    f"Unknown model type: {model_config.type}",
                    provider="local",
                )
        except Exception as e:
            raise LLMError(
                f"Error loading model '{model_name}': {e}",
                provider="local",
            )

    def _get_tokenizer(self, model_name: str) -> Any:
        """Get a tokenizer.

        Args:
            model_name: The name of the model to get the tokenizer for

        Returns:
            The tokenizer

        Raises:
            LLMConfigError: If the model is not configured
            LLMError: If there is an error loading the tokenizer
        """
        # Check if the tokenizer is already loaded
        if model_name in self._tokenizers:
            return self._tokenizers[model_name]

        # Get the model configuration
        if model_name not in self.config.models:
            raise LLMConfigError(
                f"Model '{model_name}' is not configured",
                provider="local",
            )

        model_config = self.config.models[model_name]

        # Check dependencies
        check_dependencies(model_config.type)

        # Ensure the model is downloaded
        model_path = ensure_model_downloaded(self.config, model_name)

        # Load the tokenizer
        try:
            if model_config.type == ModelType.HUGGINGFACE:
                # Load a Hugging Face tokenizer
                from transformers import AutoTokenizer

                # Load the tokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    str(model_path),
                    use_fast=True,
                )

                # Store the tokenizer
                self._tokenizers[model_name] = tokenizer

                return tokenizer
            elif model_config.type in (ModelType.GGML, ModelType.GGUF):
                # GGML/GGUF models don't have separate tokenizers
                # The model itself can tokenize
                model = self._get_model(model_name)

                # Store the model as the tokenizer
                self._tokenizers[model_name] = model

                return model
            elif model_config.type == ModelType.CUSTOM:
                # Custom model types are not supported yet
                raise LLMError(
                    "Custom model type not supported yet",
                    provider="local",
                )
            else:
                raise LLMError(
                    f"Unknown model type: {model_config.type}",
                    provider="local",
                )
        except Exception as e:
            raise LLMError(
                f"Error loading tokenizer for model '{model_name}': {e}",
                provider="local",
            )

    @retry(max_retries=1)
    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            The generated completion

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Validate and normalize the prompt
        prompt_obj = validate_prompt(prompt)

        # Get the model name
        model_name = self.config.default_model

        # Get the model configuration
        model_config = self.config.models[model_name]

        # Convert the prompt to text
        prompt_text = convert_prompt_to_text(prompt_obj)

        # Get the model and tokenizer
        model = self._get_model(model_name)
        tokenizer = self._get_tokenizer(model_name)

        try:
            # Generate the completion
            if model_config.type == ModelType.HUGGINGFACE:
                # Generate with a Hugging Face model
                import torch

                # Tokenize the prompt
                inputs = tokenizer(prompt_text, return_tensors="pt").to(self.device)

                # Set generation parameters
                generation_config = {
                    "max_new_tokens": prompt_obj.max_tokens or model_config.max_tokens,
                    "temperature": prompt_obj.temperature
                    or model_config.default_temperature,
                    "do_sample": True,
                }

                if prompt_obj.stop:
                    generation_config["stopping_criteria"] = [
                        lambda input_ids, scores: any(
                            tokenizer.decode(
                                input_ids[0, -len(tokenizer.encode(stop)) :]
                            )
                            == stop
                            for stop in prompt_obj.stop
                        )
                    ]

                # Generate the completion
                with torch.no_grad():
                    output_ids = model.generate(
                        **inputs,
                        **generation_config,
                    )

                # Decode the output
                output = tokenizer.decode(output_ids[0], skip_special_tokens=True)

                # Remove the prompt from the output
                completion = output[len(prompt_text) :]

                # Create the response
                return Response(
                    text=completion,
                    usage={
                        "prompt_tokens": len(inputs["input_ids"][0]),
                        "completion_tokens": len(output_ids[0])
                        - len(inputs["input_ids"][0]),
                        "total_tokens": len(output_ids[0]),
                    },
                    metadata={
                        "model": model_name,
                    },
                )
            elif model_config.type in (ModelType.GGML, ModelType.GGUF):
                # Generate with a GGML/GGUF model
                # Set generation parameters
                generation_config = {
                    "max_new_tokens": prompt_obj.max_tokens or model_config.max_tokens,
                    "temperature": prompt_obj.temperature
                    or model_config.default_temperature,
                }

                if prompt_obj.stop:
                    generation_config["stop"] = prompt_obj.stop

                # Generate the completion
                completion = model(
                    prompt_text,
                    **generation_config,
                )

                # Create the response
                return Response(
                    text=completion,
                    usage={
                        "prompt_tokens": model.tokenize(prompt_text).shape[0],
                        "completion_tokens": model.tokenize(completion).shape[0],
                        "total_tokens": model.tokenize(prompt_text + completion).shape[
                            0
                        ],
                    },
                    metadata={
                        "model": model_name,
                    },
                )
            else:
                raise LLMError(
                    f"Unsupported model type: {model_config.type}",
                    provider="local",
                )
        except Exception as e:
            raise LLMError(
                f"Error generating completion: {e}",
                provider="local",
            )

    @retry(max_retries=1)
    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            An async iterator of response chunks

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Validate and normalize the prompt
        prompt_obj = validate_prompt(prompt)

        # Get the model name
        model_name = self.config.default_model

        # Get the model configuration
        model_config = self.config.models[model_name]

        # Convert the prompt to text
        prompt_text = convert_prompt_to_text(prompt_obj)

        # Get the model and tokenizer
        model = self._get_model(model_name)
        tokenizer = self._get_tokenizer(model_name)

        try:
            # Generate the completion
            if model_config.type == ModelType.HUGGINGFACE:
                # Generate with a Hugging Face model
                from transformers import TextIteratorStreamer

                # Tokenize the prompt
                inputs = tokenizer(prompt_text, return_tensors="pt").to(self.device)

                # Set generation parameters
                generation_config = {
                    "max_new_tokens": prompt_obj.max_tokens or model_config.max_tokens,
                    "temperature": prompt_obj.temperature
                    or model_config.default_temperature,
                    "do_sample": True,
                }

                if prompt_obj.stop:
                    generation_config["stopping_criteria"] = [
                        lambda input_ids, scores: any(
                            tokenizer.decode(
                                input_ids[0, -len(tokenizer.encode(stop)) :]
                            )
                            == stop
                            for stop in prompt_obj.stop
                        )
                    ]

                # Create a streamer
                streamer = TextIteratorStreamer(
                    tokenizer,
                    skip_prompt=True,
                    skip_special_tokens=True,
                )

                # Set the streamer
                generation_config["streamer"] = streamer

                # Generate the completion in a separate thread
                generation_task = asyncio.create_task(
                    asyncio.to_thread(
                        model.generate,
                        **inputs,
                        **generation_config,
                    )
                )

                # Stream the completion
                for text in streamer:
                    # Check if the generation is finished
                    is_finished = generation_task.done()

                    # Yield the streaming response
                    yield StreamingResponse(
                        text=text,
                        is_finished=is_finished,
                        metadata={
                            "model": model_name,
                        },
                    )

                # Wait for the generation to finish
                await generation_task
            elif model_config.type in (ModelType.GGML, ModelType.GGUF):
                # Generate with a GGML/GGUF model
                # Set generation parameters
                generation_config = {
                    "max_new_tokens": prompt_obj.max_tokens or model_config.max_tokens,
                    "temperature": prompt_obj.temperature
                    or model_config.default_temperature,
                }

                if prompt_obj.stop:
                    generation_config["stop"] = prompt_obj.stop

                # Generate the completion
                for text in model.generate_iterator(
                    prompt_text,
                    **generation_config,
                ):
                    # Yield the streaming response
                    yield StreamingResponse(
                        text=text,
                        is_finished=False,
                        metadata={
                            "model": model_name,
                        },
                    )

                # Yield the final response
                yield StreamingResponse(
                    text="",
                    is_finished=True,
                    metadata={
                        "model": model_name,
                    },
                )
            else:
                raise LLMError(
                    f"Unsupported model type: {model_config.type}",
                    provider="local",
                )
        except Exception as e:
            raise LLMError(
                f"Error generating streaming completion: {e}",
                provider="local",
            )

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for

        Returns:
            The generated embeddings

        Raises:
            LLMError: If there is an error generating the embeddings
        """
        # Get the model name
        model_name = self.config.default_model

        # Get the model configuration
        model_config = self.config.models[model_name]

        # Check if the model supports embeddings
        if not model_config.supports_embeddings:
            raise LLMError(
                f"Model '{model_name}' does not support embeddings",
                provider="local",
            )

        # Get the model
        model = self._get_model(model_name)

        try:
            # Generate the embeddings
            if model_config.type == ModelType.HUGGINGFACE:
                # Generate with a Hugging Face model
                import torch

                # Get the tokenizer
                tokenizer = self._get_tokenizer(model_name)

                # Tokenize the text
                inputs = tokenizer(text, return_tensors="pt").to(self.device)

                # Generate the embeddings
                with torch.no_grad():
                    outputs = model(**inputs, output_hidden_states=True)

                # Get the embeddings
                embeddings = (
                    outputs.hidden_states[-1]
                    .mean(dim=1)
                    .squeeze()
                    .cpu()
                    .numpy()
                    .tolist()
                )

                return embeddings
            else:
                raise LLMError(
                    f"Embeddings not supported for model type: {model_config.type}",
                    provider="local",
                )
        except Exception as e:
            raise LLMError(
                f"Error generating embeddings: {e}",
                provider="local",
            )

    async def tokenize(self, text: str) -> List[str]:
        """Tokenize the given text.

        Args:
            text: The text to tokenize

        Returns:
            The list of tokens

        Raises:
            LLMError: If there is an error tokenizing the text
        """
        # Get the model name
        model_name = self.config.default_model

        # Get the tokenizer
        tokenizer = self._get_tokenizer(model_name)

        try:
            # Tokenize the text
            if isinstance(tokenizer, dict) and "tokenize" in tokenizer:
                # GGML/GGUF tokenizer
                token_ids = tokenizer.tokenize(text)

                # Convert token IDs to strings
                return [str(token_id) for token_id in token_ids]
            else:
                # Hugging Face tokenizer
                token_ids = tokenizer.encode(text)

                # Convert token IDs to strings
                return [tokenizer.decode([token_id]) for token_id in token_ids]
        except Exception as e:
            raise LLMError(
                f"Error tokenizing text: {e}",
                provider="local",
            )

    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens in

        Returns:
            The number of tokens

        Raises:
            LLMError: If there is an error counting tokens
        """
        # Get the model name
        model_name = self.config.default_model

        # Get the tokenizer
        tokenizer = self._get_tokenizer(model_name)

        try:
            # Count the tokens
            if isinstance(tokenizer, dict) and "tokenize" in tokenizer:
                # GGML/GGUF tokenizer
                return len(tokenizer.tokenize(text))
            else:
                # Hugging Face tokenizer
                return len(tokenizer.encode(text))
        except Exception as e:
            raise LLMError(
                f"Error counting tokens: {e}",
                provider="local",
            )

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
                    "supports_embeddings": model.supports_embeddings,
                }
                for name, model in self.config.models.items()
            },
            "device": self.device,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            The provider capabilities
        """
        return {
            "provider": "local",
            "supports_streaming": True,
            "supports_embeddings": any(
                model.supports_embeddings for model in self.config.models.values()
            ),
            "supports_tokenization": True,
            "supports_token_counting": True,
        }
