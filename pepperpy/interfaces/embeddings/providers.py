"""
Embedding providers interface.

This module provides the public interface for embedding providers.
"""

from typing import Any, Dict, List, Optional, Union


class EmbeddingProvider:
    """Base class for embedding providers.
    
    This class defines the interface that all embedding providers must implement.
    """
    
    def __init__(self, provider_name: str):
        """Initialize embedding provider.
        
        Args:
            provider_name: Name of the provider
        """
        self.provider_name = provider_name
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Embedding provider must implement embed method")


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider.
    
    This class provides access to OpenAI's text embedding API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
    ):
        """Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Embedding model name
        """
        super().__init__("openai")
        self.api_key = api_key
        self.model = model


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace embedding provider.
    
    This class provides access to HuggingFace's text embedding API.
    """
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
    ):
        """Initialize HuggingFace embedding provider.
        
        Args:
            model_name: Model name or path
            api_key: HuggingFace API key (uses env var if None)
        """
        super().__init__("huggingface")
        self.model_name = model_name
        self.api_key = api_key


class AzureEmbeddingProvider(EmbeddingProvider):
    """Azure embedding provider.
    
    This class provides access to Azure's text embedding API.
    """
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
    ):
        """Initialize Azure embedding provider.
        
        Args:
            api_key: Azure API key
            endpoint: Azure endpoint URL
            deployment_name: Azure deployment name
        """
        super().__init__("azure")
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider.
    
    This class provides access to Cohere's text embedding API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "embed-english-v2.0",
    ):
        """Initialize Cohere embedding provider.
        
        Args:
            api_key: Cohere API key (uses env var if None)
            model: Embedding model name
        """
        super().__init__("cohere")
        self.api_key = api_key
        self.model = model


class ProviderFactory:
    """Factory for embedding providers.
    
    This class provides methods for creating and configuring
    embedding providers from various services.
    """
    
    @classmethod
    def create_openai_provider(
        cls,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
        **kwargs
    ) -> OpenAIEmbeddingProvider:
        """Create an OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Embedding model name
            **kwargs: Additional provider options
            
        Returns:
            OpenAI embedding provider
        """
        return OpenAIEmbeddingProvider(api_key=api_key, model=model)
    
    @classmethod
    def create_huggingface_provider(
        cls,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> HuggingFaceEmbeddingProvider:
        """Create a HuggingFace embedding provider.
        
        Args:
            model_name: Model name or path
            api_key: HuggingFace API key (uses env var if None)
            **kwargs: Additional provider options
            
        Returns:
            HuggingFace embedding provider
        """
        return HuggingFaceEmbeddingProvider(model_name=model_name, api_key=api_key)
    
    @classmethod
    def create_azure_provider(
        cls,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        **kwargs
    ) -> AzureEmbeddingProvider:
        """Create an Azure embedding provider.
        
        Args:
            api_key: Azure API key
            endpoint: Azure endpoint URL
            deployment_name: Azure deployment name
            **kwargs: Additional provider options
            
        Returns:
            Azure embedding provider
        """
        return AzureEmbeddingProvider(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment_name
        )
    
    @classmethod
    def create_cohere_provider(
        cls,
        api_key: Optional[str] = None,
        model: str = "embed-english-v2.0",
        **kwargs
    ) -> CohereEmbeddingProvider:
        """Create a Cohere embedding provider.
        
        Args:
            api_key: Cohere API key (uses env var if None)
            model: Embedding model name
            **kwargs: Additional provider options
            
        Returns:
            Cohere embedding provider
        """
        return CohereEmbeddingProvider(api_key=api_key, model=model)

