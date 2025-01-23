"""Chat agent implementation."""
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from ..providers.llm.base import BaseLLMProvider
from ..providers.memory.base import BaseMemoryProvider, Message
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

@BaseAgent.register("chat")
class ChatAgent(BaseAgent):
    """Chat agent implementation."""
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        capabilities: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """Initialize the chat agent.
        
        Args:
            llm: LLM provider instance.
            capabilities: Dictionary of agent capabilities.
            config: Agent configuration.
        """
        super().__init__(llm, capabilities, config)
        
        # Chat-specific configuration
        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        self.max_history = config.get("max_history", 10)
        self.temperature = config.get("temperature", 0.7)
        
        # Message history
        self.messages: List[Message] = []
        
        # Memory provider (from base class)
        self.memory: Optional[BaseMemoryProvider] = self.memory
    
    async def process(self, input_data: str) -> str:
        """Process user input and generate a response.
        
        Args:
            input_data: User input text.
            
        Returns:
            Generated response.
            
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        try:
            # Add user message to history
            user_message = Message(content=input_data, role="user")
            await self._add_message(user_message)
            
            # Build conversation history
            history = self._build_history()
            
            # Generate response
            response = await self.llm.generate(
                prompt=history,
                temperature=self.temperature
            )
            
            # Add assistant message to history
            assistant_message = Message(content=response, role="assistant")
            await self._add_message(assistant_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process input: {str(e)}")
            raise RuntimeError(f"Failed to process input: {str(e)}")
    
    async def _add_message(self, message: Message) -> None:
        """Add a message to history and memory.
        
        Args:
            message: Message to add.
        """
        # Add to in-memory history
        self.messages.append(message)
        
        # Trim history if needed
        if len(self.messages) > self.max_history * 2:  # Keep extra for context
            self.messages = self.messages[-self.max_history * 2:]
        
        # Add to persistent memory if available
        if self.memory:
            await self.memory.add_message(message)
    
    def _build_history(self) -> str:
        """Build conversation history string.
        
        Returns:
            Formatted conversation history.
        """
        # Start with system prompt
        history = [f"System: {self.system_prompt}"]
        
        # Add recent messages
        for msg in self.messages[-self.max_history * 2:]:
            role = msg.role.title()
            history.append(f"{role}: {msg.content}")
        
        return "\n\n".join(history)
    
    async def search_history(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Search conversation history.
        
        Args:
            query: Search query.
            limit: Optional limit on number of results.
            
        Returns:
            List of matching messages.
            
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        if not self.memory:
            # Search in-memory history
            messages = []
            for msg in reversed(self.messages):
                if query.lower() in msg.content.lower():
                    messages.append(msg)
                    if limit and len(messages) >= limit:
                        break
            return messages
            
        # Search in persistent memory
        return await self.memory.search_messages(query, limit)
    
    async def clear_history(self) -> None:
        """Clear conversation history.
        
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        # Clear in-memory history
        self.messages.clear()
        
        # Clear persistent memory if available
        if self.memory:
            await self.memory.clear_messages() 