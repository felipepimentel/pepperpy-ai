"""Embeddings providers."""

PROVIDER_MODULES = {
    "FastAIEmbeddingProvider": ".fastai",
    "LocalProvider": ".local",
    "OpenAIEmbeddingProvider": ".openai",
    "NumpyProvider": ".numpy_provider",
    "HashProvider": ".hash",
    "CohereProvider": ".cohere",
    "HuggingFaceProvider": ".huggingface",
    "OpenRouterProvider": ".openrouter",
}

__all__ = list(PROVIDER_MODULES.keys())
