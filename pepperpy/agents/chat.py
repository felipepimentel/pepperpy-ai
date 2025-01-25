"""Chat agent implementation."""
import logging
from typing import Any, Dict, List, Optional

from ..common.errors import PepperpyError
from .base import BaseAgent
from ..providers.llm.base import BaseLLMProvider
from ..providers.memory.base import BaseMemoryProvider, Message
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

class ChatAgentError(PepperpyError):
    """Chat agent error class."""
    pass

@BaseAgent.register("chat")
class ChatAgent(BaseAgent):
    """Chat agent implementation."""
    
    def __init__(
        self,
        name: str,
        llm: Any,
        capabilities: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize chat agent.
        
        Args:
            name: Agent name.
            llm: LLM provider instance.
            capabilities: Agent capabilities.
            config: Optional agent configuration.
            
        Raises:
            ChatAgentError: If initialization fails.
        """
        super().__init__(name, llm, capabilities, config)
        
        # Initialize chat history
        self._history: List[Dict[str, Any]] = []
        
        # Get chat configuration
        self._max_history = config.get("max_history", 100) if config else 100
        self._system_prompt = config.get("system_prompt", "") if config else ""
        
        if self._max_history <= 0:
            raise ChatAgentError("Max history must be positive")
        
        # Chat-specific configuration
        self.temperature = config.get("temperature", 0.7)
        
        # Message history
        self.messages: List[Message] = []
        
        # Memory provider (from base class)
        self.memory: Optional[BaseMemoryProvider] = self.memory
    
    async def _setup(self) -> None:
        """Set up chat agent resources.
        
        Raises:
            ChatAgentError: If setup fails.
        """
        try:
            # Initialize chat history
            self._history = []
            
            # Set up system prompt if provided
            if self._system_prompt:
                self._history.append({
                    "role": "system",
                    "content": self._system_prompt
                })
        except Exception as e:
            raise ChatAgentError(f"Failed to set up chat agent: {e}")
    
    async def _teardown(self) -> None:
        """Clean up chat agent resources.
        
        Raises:
            ChatAgentError: If cleanup fails.
        """
        try:
            # Clear chat history
            self._history = []
        except Exception as e:
            raise ChatAgentError(f"Failed to clean up chat agent: {e}")
    
    async def _validate_impl(self) -> None:
        """Validate chat agent state.
        
        Raises:
            ChatAgentError: If validation fails.
        """
        try:
            if self._max_history <= 0:
                raise ChatAgentError("Max history must be positive")
            
            if not isinstance(self._history, list):
                raise ChatAgentError("History must be a list")
            
            if len(self._history) > self._max_history:
                raise ChatAgentError("History exceeds max size")
        except Exception as e:
            raise ChatAgentError(f"Failed to validate chat agent: {e}")
    
    async def execute(self, input_data: Any) -> Any:
        """Execute chat agent with input data.
        
        Args:
            input_data: Input data for agent execution.
            
        Returns:
            Agent execution result.
            
        Raises:
            ChatAgentError: If execution fails.
        """
        if not isinstance(input_data, str):
            raise ChatAgentError("Input must be a string")
        
        try:
            # Add user message to history
            self._history.append({
                "role": "user",
                "content": input_data
            })
            
            # Truncate history if needed
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            # Generate response
            response = await self.llm.generate(self._history)
            
            # Add assistant response to history
            self._history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except Exception as e:
            raise ChatAgentError(f"Failed to execute chat agent: {e}")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get chat history.
        
        Returns:
            List of chat messages.
        """
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self._history = []
        if self._system_prompt:
            self._history.append({
                "role": "system",
                "content": self._system_prompt
            })
    
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
        if len(self.messages) > self._max_history * 2:  # Keep extra for context
            self.messages = self.messages[-self._max_history * 2:]
        
        # Add to persistent memory if available
        if self.memory:
            await self.memory.add_message(message)
    
    def _build_history(self) -> str:
        """Build conversation history string.
        
        Returns:
            Formatted conversation history.
        """
        # Start with system prompt
        history = [f"System: {self._system_prompt}"]
        
        # Add recent messages
        for msg in self.messages[-self._max_history * 2:]:
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