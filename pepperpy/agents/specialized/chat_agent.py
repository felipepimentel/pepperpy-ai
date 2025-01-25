"""Chat agent implementation."""

import logging
from typing import Any, Dict, List, Optional, cast

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.llm.base import BaseLLMProvider
from pepperpy.providers.memory.base import BaseMemoryProvider
from pepperpy.agents.base.base_agent import BaseAgent, AgentError


logger = logging.getLogger(__name__)


class ChatAgentError(AgentError):
    """Chat agent error class."""
    pass


@BaseAgent.register("chat")
class ChatAgent(BaseAgent):
    """Chat agent implementation.
    
    This agent provides conversational capabilities with memory
    management for maintaining context across interactions.
    """
    
    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        memory_provider: Optional[BaseMemoryProvider] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize chat agent.
        
        Args:
            name: Agent name
            llm_provider: LLM provider instance
            memory_provider: Optional memory provider instance
            config: Optional configuration
        """
        super().__init__(
            name=name,
            llm_provider=llm_provider,
            memory_provider=memory_provider,
            config=config,
        )
        
        self._max_history = config.get('max_history', 10) if config else 10
        self._system_prompt = config.get('system_prompt', '') if config else ''
        
    async def _setup(self) -> None:
        """Set up chat agent resources."""
        try:
            if self.memory:
                await self.memory.initialize()
        except Exception as e:
            raise ChatAgentError(f"Failed to set up chat agent: {e}")
            
    async def _teardown(self) -> None:
        """Clean up chat agent resources."""
        try:
            if self.memory:
                await self.memory.cleanup()
        except Exception as e:
            raise ChatAgentError(f"Failed to clean up chat agent: {e}")
            
    def _validate(self) -> None:
        """Validate chat agent configuration."""
        if not isinstance(self._max_history, int) or self._max_history < 1:
            raise ChatAgentError("max_history must be a positive integer")
        if not isinstance(self._system_prompt, str):
            raise ChatAgentError("system_prompt must be a string")
            
    async def process(
        self,
        input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process chat input.
        
        Args:
            input: User message
            context: Optional processing context
            
        Returns:
            Dictionary containing:
                - response: Generated response
                - metadata: Processing metadata
                
        Raises:
            ChatAgentError: If processing fails
        """
        try:
            # Get conversation history
            history = []
            if self.memory:
                history = await self.memory.get(
                    key=f"chat_history_{self.name}",
                    limit=self._max_history,
                )
                
            # Build prompt with history
            prompt = self._build_prompt(input, history)
            
            # Generate response
            response = await self.llm.generate(prompt, context)
            
            # Update history
            if self.memory:
                history.append({
                    'role': 'user',
                    'content': input,
                })
                history.append({
                    'role': 'assistant',
                    'content': response,
                })
                await self.memory.set(
                    key=f"chat_history_{self.name}",
                    value=history[-self._max_history:],
                )
                
            return {
                'response': response,
                'metadata': {
                    'history_length': len(history),
                    'has_memory': bool(self.memory),
                },
            }
        except Exception as e:
            raise ChatAgentError(f"Failed to process input: {e}")
            
    def _build_prompt(self, message: str, history: List[Dict[str, str]]) -> str:
        """Build prompt with conversation history.
        
        Args:
            message: Current user message
            history: Conversation history
            
        Returns:
            Formatted prompt
        """
        prompt = []
        
        # Add system prompt if present
        if self._system_prompt:
            prompt.append(f"System: {self._system_prompt}\n")
            
        # Add conversation history
        for entry in history:
            role = entry['role'].capitalize()
            content = entry['content']
            prompt.append(f"{role}: {content}")
            
        # Add current message
        prompt.append(f"User: {message}")
        prompt.append("Assistant:")
        
        return "\n".join(prompt) 