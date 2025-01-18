"""HuggingFace API integration."""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

from huggingface_hub import AsyncInferenceClient

from pepperpy.llms.base_llm import BaseLLM, LLMConfig, LLMResponse


class HuggingFaceError(Exception):
    """HuggingFace API error."""

    pass


class HuggingFaceLLM(BaseLLM):
    """HuggingFace LLM provider."""

    MODEL_COSTS: ClassVar[dict[str, float]] = {
        "gpt2": 0.0001,
        "gpt2-medium": 0.0002,
        "gpt2-large": 0.0003,
        "gpt2-xl": 0.0004,
    }

    def __init__(self, config: LLMConfig) -> None:
        """Initialize HuggingFace LLM.

        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.client: AsyncInferenceClient | None = None

    async def initialize(self) -> None:
        """Initialize HuggingFace client."""
        api_key = self.config.model_kwargs.get("api_key")
        if not api_key:
            raise HuggingFaceError("HuggingFace API key is required")

        try:
            self.client = AsyncInferenceClient(api_token=api_key)
        except Exception as e:
            msg = f"Failed to initialize HuggingFace client: {e!s}"
            raise HuggingFaceError(msg) from e

    async def generate(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using HuggingFace model.

        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            Generated response

        Raises:
            HuggingFaceError: If generation fails
        """
        if not self.client:
            raise HuggingFaceError("HuggingFace client not initialized")

        try:
            response = await self.client.text_generation(
                prompt,
                model=self.config.model_name,
                **self._prepare_parameters(
                    stop=stop,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            )
            return LLMResponse(
                text=response,
                tokens_used=len(response.split()),  # Approximate
                finish_reason="stop",
                model_name=self.config.model_name
            )

        except Exception as e:
            msg = f"HuggingFace generation failed: {e!s}"
            raise HuggingFaceError(msg) from e

    async def generate_stream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream text generation using HuggingFace model.

        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            Async iterator of generated text chunks

        Raises:
            HuggingFaceError: If streaming fails
        """
        if not self.client:
            raise HuggingFaceError("HuggingFace client not initialized")

        try:
            async for response in self.client.text_generation(
                prompt,
                model=self.config.model_name,
                stream=True,
                **self._prepare_parameters(
                    stop=stop,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            ):
                yield response

        except Exception as e:
            msg = f"HuggingFace streaming failed: {e!s}"
            raise HuggingFaceError(msg) from e

    async def cleanup(self) -> None:
        """Clean up HuggingFace client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (one per text)

        Raises:
            HuggingFaceError: If embedding generation fails
        """
        if not self.client:
            raise HuggingFaceError("HuggingFace client not initialized")

        try:
            model = self.config.model_kwargs.get(
                "embedding_model",
                "sentence-transformers/all-mpnet-base-v2"
            )
            embeddings = await self.client.embeddings(texts, model=model)
            return embeddings

        except Exception as e:
            msg = f"HuggingFace embedding generation failed: {e!s}"
            raise HuggingFaceError(msg) from e

    def _prepare_parameters(
        self,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare parameters for API call.

        Args:
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            Prepared parameters
        """
        # Convert common parameters
        api_params = {
            "max_new_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "top_p": kwargs.get("top_p", 0.9),
            "top_k": kwargs.get("top_k", 50),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.0),
            "stop_sequences": stop or self.config.stop_sequences,
        }

        # Remove None values
        return {k: v for k, v in api_params.items() if v is not None}
