"""OpenAI LLM provider implementation."""

import os
from typing import Any, AsyncIterator, Dict, List, Optional, cast, Iterable, Union

from openai._client import AsyncOpenAI
from openai._types import NotGiven
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as StreamChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.chat.chat_completion_tool_choice_option import ChatCompletionToolChoiceOptionParam
from openai.types.chat.completion_create_params import ResponseFormat

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMConfig,
)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the OpenAI provider.
        
        Args:
            config: Optional configuration dictionary with:
                - api_key: OpenAI API key (optional if set in env)
                - model: Model to use (default: "gpt-3.5-turbo")
                - timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None
        self._model = self.config.get("model", "gpt-3.5-turbo")
        self._timeout = self.config.get("timeout", 30)

    async def initialize(self) -> None:
        """Initialize the provider.
        
        This sets up the OpenAI client with the provided configuration.
        
        Raises:
            ProviderError: If initialization fails.
        """
        try:
            api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ProviderError("OpenAI API key not found")
                
            self._client = AsyncOpenAI(
                api_key=api_key,
                timeout=self._timeout,
            )
            await super().initialize()
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI provider: {str(e)}") from e

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._client:
            await self._client.close()
        await super().shutdown()

    def _create_chat_message(self, prompt: str) -> List[LLMMessage]:
        """Create chat messages from a prompt.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            List containing a single user message.
        """
        return [LLMMessage(role="user", content=prompt)]

    def _convert_choice_to_response(
        self,
        choice: Union[Choice, StreamChoice],
    ) -> LLMResponse:
        """Convert an OpenAI chat choice to LLMResponse.
        
        Args:
            choice: OpenAI chat completion choice.
            
        Returns:
            Converted response.
        """
        if isinstance(choice, StreamChoice):
            # Handle streaming choice
            delta = choice.delta
            tool_calls = None
            if delta.tool_calls:
                tool_calls = [
                    {
                        "id": tool.id,
                        "type": tool.type,
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments,
                        } if tool.function else {},
                    }
                    for tool in delta.tool_calls
                ]
            
            function_call = None
            if delta.function_call:
                function_call = {
                    "name": delta.function_call.name,
                    "arguments": delta.function_call.arguments,
                }
            
            return LLMResponse(
                content=delta.content or "",
                role=delta.role or "assistant",
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
                function_call=function_call,
            )
        else:
            # Handle regular choice
            message = choice.message
            tool_calls = None
            if message.tool_calls:
                tool_calls = [
                    {
                        "id": tool.id,
                        "type": tool.type,
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments,
                        } if tool.function else {},
                    }
                    for tool in message.tool_calls
                ]
            
            function_call = None
            if message.function_call:
                function_call = {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments,
                }
            
            return LLMResponse(
                content=message.content or "",
                role=message.role,
                finish_reason=choice.finish_reason,
                tool_calls=tool_calls,
                function_call=function_call,
            )

    async def generate(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Generate text from a prompt.
        
        Args:
            prompt: Input prompt.
            config: Optional generation configuration.
            
        Returns:
            Generated response.
            
        Raises:
            ProviderError: If generation fails.
        """
        if not self._client:
            raise ProviderError("Provider not initialized")
            
        await self.validate_prompt(prompt)
        messages = self._create_chat_message(prompt)
        return await self.chat(messages, config)

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[LLMResponse]:
        """Generate text from a prompt with streaming.
        
        Args:
            prompt: Input prompt.
            config: Optional generation configuration.
            
        Yields:
            Generated response chunks.
            
        Raises:
            ProviderError: If generation fails.
        """
        if not self._client:
            raise ProviderError("Provider not initialized")
            
        await self.validate_prompt(prompt)
        messages = self._create_chat_message(prompt)
        async for response in self.chat_stream(messages, config):
            yield response

    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Generate response in a chat conversation.
        
        Args:
            messages: Conversation history.
            config: Optional generation configuration.
            
        Returns:
            Generated response.
            
        Raises:
            ProviderError: If generation fails.
        """
        if not self._client:
            raise ProviderError("Provider not initialized")
            
        await self.validate_messages(messages)
        config = config or LLMConfig()
        
        try:
            # Convert messages to OpenAI format
            openai_messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionMessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                })
                for msg in messages
            ]
            
            # Convert tools to OpenAI format if present
            tools: Iterable[ChatCompletionToolParam] | NotGiven = (
                cast(Iterable[ChatCompletionToolParam], config.tools)
                if config.tools else NotGiven()
            )
            tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = (
                cast(ChatCompletionToolChoiceOptionParam, config.tool_choice)
                if config.tool_choice else NotGiven()
            )
            response_format: ResponseFormat | NotGiven = (
                cast(ResponseFormat, config.response_format)
                if config.response_format else NotGiven()
            )
            
            response = await self._client.chat.completions.create(
                model=cast(str, self._model),
                messages=openai_messages,
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
                presence_penalty=config.presence_penalty,
                frequency_penalty=config.frequency_penalty,
                stop=config.stop,
                tools=tools,
                tool_choice=tool_choice,
                response_format=response_format,
                seed=config.seed,
                stream=False,
            )
            
            result = self._convert_choice_to_response(response.choices[0])
            if response.usage:
                result.usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return result
            
        except Exception as e:
            raise ProviderError(f"Failed to generate chat response: {str(e)}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[LLMResponse]:
        """Generate response in a chat conversation with streaming.
        
        Args:
            messages: Conversation history.
            config: Optional generation configuration.
            
        Yields:
            Generated response chunks.
            
        Raises:
            ProviderError: If generation fails.
        """
        if not self._client:
            raise ProviderError("Provider not initialized")
            
        await self.validate_messages(messages)
        config = config or LLMConfig()
        
        try:
            # Convert messages to OpenAI format
            openai_messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionMessageParam, {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                })
                for msg in messages
            ]
            
            # Convert tools to OpenAI format if present
            tools: Iterable[ChatCompletionToolParam] | NotGiven = (
                cast(Iterable[ChatCompletionToolParam], config.tools)
                if config.tools else NotGiven()
            )
            tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = (
                cast(ChatCompletionToolChoiceOptionParam, config.tool_choice)
                if config.tool_choice else NotGiven()
            )
            response_format: ResponseFormat | NotGiven = (
                cast(ResponseFormat, config.response_format)
                if config.response_format else NotGiven()
            )
            
            stream = await self._client.chat.completions.create(
                model=cast(str, self._model),
                messages=openai_messages,
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
                presence_penalty=config.presence_penalty,
                frequency_penalty=config.frequency_penalty,
                stop=config.stop,
                tools=tools,
                tool_choice=tool_choice,
                response_format=response_format,
                seed=config.seed,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices:
                    yield self._convert_choice_to_response(chunk.choices[0])
                    
        except Exception as e:
            raise ProviderError(f"Failed to generate streaming chat response: {str(e)}") from e

    async def get_token_count(self, text: str) -> int:
        """Get the number of tokens in a text.
        
        This is a rough estimate based on word count.
        For accurate token counts, use a proper tokenizer.
        
        Args:
            text: Input text.
            
        Returns:
            Estimated number of tokens.
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4 + 1

    async def get_metadata(self) -> Dict[str, Any]:
        """Get provider metadata.
        
        Returns:
            Dictionary containing provider metadata.
        """
        model_info = {
            "gpt-4": {
                "context_window": 8192,
                "max_tokens": 4096,
            },
            "gpt-4-32k": {
                "context_window": 32768,
                "max_tokens": 4096,
            },
            "gpt-3.5-turbo": {
                "context_window": 4096,
                "max_tokens": 4096,
            },
            "gpt-3.5-turbo-16k": {
                "context_window": 16384,
                "max_tokens": 4096,
            },
        }
        
        info = model_info.get(cast(str, self._model), {
            "context_window": 4096,
            "max_tokens": 4096,
        })
        
        return {
            "model_name": self._model,
            "context_window": info["context_window"],
            "max_tokens": info["max_tokens"],
            "supports_streaming": True,
            "supports_tools": True,
            "provider_name": "openai",
        } 