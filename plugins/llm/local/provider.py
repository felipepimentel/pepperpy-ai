"""Local provider for LLM tasks.

This module provides a local model implementation for LLM tasks,
using transformers for local text generation.
"""

from collections.abc import AsyncIterator
from typing import Any, List, Optional, Union

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
)

from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.plugins import ProviderPlugin


class LocalProvider(LLMProvider, ProviderPlugin):
    """Local LLM provider using transformers."""

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    model: str = "default-model"
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 1024
    user_id: str
    client: Optional[Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Local LLM provider."""
        super().__init__(**kwargs)
        self.tokenizer: Optional[PreTrainedTokenizer] = None
        self.model_instance: Optional[PreTrainedModel] = None

    async def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        # Use model_path if provided, otherwise use model name
        model_path = self.model_path or self.model

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model_instance = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=self.device,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
        )

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text using the local model."""
        # Ensure model is initialized
        if self.tokenizer is None or self.model_instance is None:
            await self.initialize()
            if self.tokenizer is None or self.model_instance is None:
                raise RuntimeError("Failed to initialize model and tokenizer")

        # Convert messages to text input
        if isinstance(messages, str):
            prompt = messages
            message_list = [Message(role=MessageRole.USER, content=messages)]
        else:
            # Format messages appropriately for the model (simple concatenation)
            prompt = "\n".join(msg.content for msg in messages)
            message_list = messages.copy()

        # Get generation parameters
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        top_p = kwargs.get("top_p", 0.9)

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate response
        with torch.no_grad():
            outputs = self.model_instance.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True if temperature > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode response
        input_length = inputs["input_ids"].shape[1]
        response = self.tokenizer.decode(
            outputs[0][input_length:],
            skip_special_tokens=True,
        )

        # Create response message
        message_list.append(Message(role=MessageRole.ASSISTANT, content=response))

        # Return result
        return GenerationResult(
            content=response,
            messages=message_list,
            metadata={
                "model": self.model,
                "device": self.device,
            },
        )

    async def generate_stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in streaming mode."""
        # Ensure model is initialized
        if self.tokenizer is None or self.model_instance is None:
            await self.initialize()
            if self.tokenizer is None or self.model_instance is None:
                raise RuntimeError("Failed to initialize model and tokenizer")

        # Convert messages to text input
        if isinstance(messages, str):
            prompt = messages
        else:
            # Format messages appropriately
            prompt = "\n".join(msg.content for msg in messages)

        # Get generation parameters
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        top_p = kwargs.get("top_p", 0.9)

        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate with streaming
        with torch.no_grad():
            try:
                # This might not be available in all tokenizers
                streamer = self.tokenizer.create_token_stream()
                _ = self.model_instance.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True if temperature > 0 else False,
                    pad_token_id=self.tokenizer.eos_token_id,
                    streamer=streamer,
                )

                # Stream tokens as they're generated
                for token in streamer:
                    token_text = self.tokenizer.decode(token, skip_special_tokens=True)
                    if token_text:
                        yield GenerationChunk(
                            content=token_text,
                            metadata={"model": self.model},
                        )
            except (AttributeError, NotImplementedError):
                # Fallback if streaming is not supported
                full_response = await self.generate(messages, **kwargs)
                yield GenerationChunk(
                    content=full_response.content,
                    metadata={"model": self.model},
                )

    async def cleanup(self) -> None:
        """Clean up model resources."""
        # Free memory explicitly for large models
        if self.model_instance:
            del self.model_instance
            self.model_instance = None

        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        # Clear CUDA cache if using GPU
        if self.device.startswith("cuda"):
            torch.cuda.empty_cache()
