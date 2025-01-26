"""Google Gemini LLM provider implementation."""
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from ..base.provider import BaseProvider, ProviderConfig

class GeminiProvider(BaseProvider):
    """Provider for Google Gemini language models."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Gemini provider."""
        super().__init__(config)
        self.model = None
        self.model_name = config.parameters.get("model", "gemini-pro")
    
    async def initialize(self) -> None:
        """Initialize the Gemini client."""
        if not self._initialized:
            api_key = self.config.parameters.get("api_key")
            if not api_key:
                raise ValueError("Google API key is required")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.model = None
        self._initialized = False
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> GenerateContentResponse:
        """Generate completion for the given messages."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        # Convert messages to Gemini format
        chat = self.model.start_chat()
        for msg in messages:
            if msg["role"] == "user":
                await chat.send_message_async(msg["content"])
            elif msg["role"] == "assistant":
                # Skip assistant messages as they're responses
                continue
        
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["max_output_tokens"] = max_tokens
        if stop:
            generation_config["stop_sequences"] = stop
        
        response = await chat.send_message_async(
            messages[-1]["content"],
            generation_config=generation_config
        )
        
        return response 