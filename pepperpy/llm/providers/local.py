"""Local LLM provider implementation.

This module provides a local implementation of the LLM provider interface,
using locally installed models for text generation.

Example:
    >>> from pepperpy.llm import LLMProvider
    >>> provider = LLMProvider.from_config({
    ...     "provider": "local",
    ...     "model": "llama2",
    ...     "device": "cuda"
    ... })
    >>> result = await provider.generate("What's the weather?")
    >>> print(result.content)
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.llm.base import (
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
)


class LocalProvider(LLMProvider):
    """Local implementation of the LLM provider interface."""

    name = "local"

    def __init__(
        self,
        model: str = "llama2",
        model_path: Optional[str] = None,
        device: str = "cpu",
        **kwargs: Any,
    ) -> None:
        """Initialize the Local provider.

        Args:
            model: Model identifier (default: llama2)
            model_path: Optional path to model weights
            device: Device to run model on (default: cpu)
            **kwargs: Additional configuration options
        """
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise LLMError(
                "Local provider requires torch and transformers. "
                "Install with: pip install torch transformers"
            )

        super().__init__()
        self.model_id = model
        self.model_path = model_path or model
        self.device = device
        self.kwargs = kwargs

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, device_map=self.device, **kwargs
            )
        except Exception as e:
            raise LLMError(f"Failed to load local model: {e}")

    async def initialize(self) -> None:
        """Initialize the provider.

        Validates that the model is loaded and ready.
        """
        await super().initialize()
        if not hasattr(self, "model") or not hasattr(self, "tokenizer"):
            raise LLMError("Model not properly initialized")

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text using the local model.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Nucleus sampling parameter

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        try:
            import torch

            # Convert messages to text
            if isinstance(messages, str):
                prompt = messages
                message_list = [Message(role="user", content=messages)]
            else:
                prompt = "\n".join(msg.content for msg in messages)
                message_list = messages

            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get("max_tokens", 100),
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.9),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
            )

            return GenerationResult(
                content=response.strip(),
                messages=message_list,
                metadata={
                    "model": self.model_id,
                    "device": self.device,
                },
            )

        except Exception as e:
            raise LLMError(f"Local generation failed: {e}")

    async def stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate text in a streaming fashion.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Nucleus sampling parameter

        Yields:
            Generated text chunks

        Raises:
            LLMError: If generation fails
        """
        try:
            import torch

            # Convert messages to text
            if isinstance(messages, str):
                prompt = messages
            else:
                prompt = "\n".join(msg.content for msg in messages)

            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate with streaming
            with torch.no_grad():
                streamer = self.tokenizer.create_token_stream()
                _ = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get("max_tokens", 100),
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.9),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    streamer=streamer,
                )

                for token in streamer:
                    yield self.tokenizer.decode(token, skip_special_tokens=True)

        except Exception as e:
            raise LLMError(f"Local streaming generation failed: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Local provider capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update(
            {
                "supported_models": ["llama2", "mistral", "phi"],
                "max_tokens": 2048,
                "streaming": True,
            }
        )
        return capabilities
