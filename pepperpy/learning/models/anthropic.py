"""Anthropic language model implementation for Pepperpy."""

import asyncio
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional, cast

import anthropic
from anthropic import Anthropic
from anthropic.types import Message, MessageParam

from ...common.errors import ModelError, ModelRequestError, ModelResponseError
from ..types import Message as PepperpyMessage
from .base import LLMModel


logger = logging.getLogger(__name__)


class AnthropicModel(LLMModel):
    """Anthropic language model implementation."""
    
    def __init__(
        self,
        name: str,
        model_id: str = "claude-3-opus-20240229",
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize Anthropic model.
        
        Args:
            name: Model name
            model_id: Model identifier (default: claude-3-opus-20240229)
            api_key: Optional API key (default: from environment)
            config: Optional model configuration
        """
        super().__init__(name, model_id, config)
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client: Optional[Anthropic] = None
        
    async def _initialize(self) -> None:
        """Initialize Anthropic client."""
        if not self._api_key:
            raise ModelError("Anthropic API key not provided")
            
        try:
            self._client = Anthropic(api_key=self._api_key)
            logger.debug(f"Initialized Anthropic client for model {self.model_id}")
            
        except Exception as e:
            raise ModelError(f"Failed to initialize Anthropic client: {str(e)}") from e
            
    async def _cleanup(self) -> None:
        """Cleanup Anthropic client."""
        self._client = None
        
    async def generate(
        self,
        messages: List[PepperpyMessage],
        **kwargs: Any,
    ) -> PepperpyMessage:
        """Generate response for messages.
        
        Args:
            messages: Input messages
            **kwargs: Additional generation parameters
            
        Returns:
            Generated message
            
        Raises:
            ModelError: If model is not initialized
            ModelRequestError: If request fails
            ModelResponseError: If response is invalid
        """
        if not self._client:
            raise ModelError("Anthropic client not initialized")
            
        try:
            # Convert messages to Anthropic format
            anthropic_messages = [
                cast(MessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                })
                for msg in messages
            ]
            
            # Merge config with kwargs
            params = {**self._config, **kwargs}
            
            # Generate completion
            response = await self._client.messages.create(
                model=self.model_id,
                messages=anthropic_messages,
                **params,
            )
            
            # Extract response
            if not response.content:
                raise ModelResponseError(
                    "Empty response from Anthropic",
                    model=self.model_id,
                    provider="anthropic",
                    response=response,
                )
                
            content = response.content[0].text
            
            if not content:
                raise ModelResponseError(
                    "Empty text in Anthropic response",
                    model=self.model_id,
                    provider="anthropic",
                    response=response,
                )
                
            # Create response message
            return PepperpyMessage(
                content=content,
                role="assistant",
                metadata={
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else None,
                },
            )
            
        except Exception as e:
            if isinstance(e, ModelError):
                raise
                
            raise ModelRequestError(
                f"Anthropic request failed: {e}",
                model=self.model_id,
                provider="anthropic",
            ) from e
            
    async def generate_stream(
        self,
        messages: List[PepperpyMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming response for messages.
        
        Args:
            messages: Input messages
            **kwargs: Additional generation parameters
            
        Returns:
            Async iterator of generated chunks
            
        Raises:
            ModelError: If model is not initialized
            ModelRequestError: If request fails
            ModelResponseError: If response is invalid
        """
        if not self._client:
            raise ModelError("Anthropic client not initialized")
            
        try:
            # Convert messages to Anthropic format
            anthropic_messages = [
                cast(MessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                })
                for msg in messages
            ]
            
            # Merge config with kwargs
            params = {**self._config, **kwargs}
            
            # Generate streaming completion
            stream = await self._client.messages.create(
                model=self.model_id,
                messages=anthropic_messages,
                stream=True,
                **params,
            )
            
            async for chunk in stream:
                if not chunk.delta or not chunk.delta.text:
                    continue
                    
                yield chunk.delta.text
                
        except Exception as e:
            if isinstance(e, ModelError):
                raise
                
            raise ModelRequestError(
                f"Anthropic request failed: {e}",
                model=self.model_id,
                provider="anthropic",
            ) from e 