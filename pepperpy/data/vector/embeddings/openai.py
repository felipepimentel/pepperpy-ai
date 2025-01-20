"""OpenAI embedding model implementation for Pepperpy."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
from numpy.typing import NDArray
import openai
from openai import OpenAI

from ....common.errors import ModelError, ModelRequestError, ModelResponseError
from .base import EmbeddingModel


logger = logging.getLogger(__name__)


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI embedding model implementation."""
    
    def __init__(
        self,
        name: str,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpenAI embedding model.
        
        Args:
            name: Model name
            model: Model identifier (default: text-embedding-3-small)
            api_key: Optional API key (default: from environment)
            organization: Optional organization ID
            **kwargs: Additional model parameters
        """
        # Set dimension based on model
        dimension = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }.get(model, 1536)
        
        super().__init__(name, model, dimension, **kwargs)
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._organization = organization or os.getenv("OPENAI_ORG_ID")
        self._client: Optional[OpenAI] = None
        
    async def _initialize(self) -> None:
        """Initialize OpenAI client."""
        if not self._api_key:
            raise ModelError("OpenAI API key not provided")
            
        try:
            self._client = OpenAI(
                api_key=self._api_key,
                organization=self._organization,
            )
            logger.debug(f"Initialized OpenAI client for model {self.model}")
            await super()._initialize()
            
        except Exception as e:
            raise ModelError(f"Failed to initialize OpenAI client: {str(e)}") from e
            
    async def _cleanup(self) -> None:
        """Cleanup OpenAI client."""
        self._client = None
        await super()._cleanup()
        
    async def _embed(self, texts: List[str]) -> NDArray[np.float32]:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            Array of embeddings with shape (N, dimension)
            
        Raises:
            ModelRequestError: If request fails
            ModelResponseError: If response is invalid
        """
        if not self._client:
            raise ModelError("OpenAI client not initialized")
            
        try:
            # Create embeddings
            response = self._client.embeddings.create(
                model=self.model,
                input=texts,
            )
            
            # Extract embeddings
            if not response.data:
                raise ModelResponseError(
                    message="Empty response from OpenAI",
                    model=self.model,
                    provider="openai",
                    response=response,
                )
                
            embeddings = [data.embedding for data in response.data]
            
            if not embeddings:
                raise ModelResponseError(
                    message="Empty embeddings in OpenAI response",
                    model=self.model,
                    provider="openai",
                    response=response,
                )
                
            logger.debug(f"Generated {len(embeddings)} embeddings with model {self.model}")
            
            return np.array(embeddings, dtype=np.float32)
            
        except openai.OpenAIError as e:
            raise ModelRequestError(
                message=f"OpenAI request failed: {str(e)}",
                model=self.model,
                provider="openai",
            ) from e
            
        except Exception as e:
            raise ModelError(f"Unexpected error: {str(e)}") from e 