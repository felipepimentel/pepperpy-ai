"""OpenAI model implementation."""

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from ...common.errors import ModelError, ModelRequestError, ModelResponseError
from ..types import Message
from .base import LLMModel


logger = logging.getLogger(__name__)


class OpenAIModel(LLMModel):
    """OpenAI model implementation."""
    
    def __init__(
        self,
        name: str,
        model_id: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenAI model.
        
        Args:
            name: Model name
            model_id: Model identifier (default: gpt-3.5-turbo)
            api_key: Optional API key
            config: Optional model configuration
        """
        super().__init__(name, model_id, config)
        self._api_key = api_key
        self._client: Optional[AsyncOpenAI] = None
        
    async def _initialize(self) -> None:
        """Initialize model."""
        try:
            self._client = AsyncOpenAI(api_key=self._api_key)
            await self._client.models.retrieve(self.model_id)
            
        except Exception as e:
            raise ModelError(f"Failed to initialize OpenAI model: {e}") from e
            
    async def _cleanup(self) -> None:
        """Clean up model."""
        if self._client:
            await self._client.close()
            self._client = None
            
    async def generate(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> Message:
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
            raise ModelError("OpenAI model not initialized")
            
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                cast(ChatCompletionMessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                })
                for msg in messages
            ]
            
            # Merge config with kwargs
            params = {**self._config, **kwargs}
            
            # Generate completion
            completion: ChatCompletion = await self._client.chat.completions.create(
                model=self.model_id,
                messages=openai_messages,
                **params,
            )
            
            # Extract response
            choice = completion.choices[0]
            if not choice.message or not choice.message.content:
                raise ModelResponseError(
                    "Empty response from OpenAI",
                    model=self.model_id,
                    provider="openai",
                    response=completion,
                )
                
            # Create response message
            return Message(
                content=choice.message.content,
                role=choice.message.role,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "model": completion.model,
                    "usage": completion.usage.model_dump() if completion.usage else None,
                },
            )
            
        except Exception as e:
            if isinstance(e, ModelError):
                raise
                
            raise ModelRequestError(
                f"OpenAI request failed: {e}",
                model=self.model_id,
                provider="openai",
            ) from e
            
    async def generate_stream(
        self,
        messages: List[Message],
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
            raise ModelError("OpenAI model not initialized")
            
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                cast(ChatCompletionMessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                })
                for msg in messages
            ]
            
            # Merge config with kwargs
            params = {**self._config, **kwargs}
            
            # Generate streaming completion
            stream = await self._client.chat.completions.create(
                model=self.model_id,
                messages=openai_messages,
                stream=True,
                **params,
            )
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                if not delta or not delta.content:
                    continue
                    
                yield delta.content
                
        except Exception as e:
            if isinstance(e, ModelError):
                raise
                
            raise ModelRequestError(
                f"OpenAI request failed: {e}",
                model=self.model_id,
                provider="openai",
            ) from e 