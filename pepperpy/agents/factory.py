"""Agent factory implementation."""
import logging
from typing import Any, Dict, Optional, Type

from ..interfaces import (
    LLMProvider,
    VectorStoreProvider,
    EmbeddingProvider,
)
from ..core.lifecycle import ComponentLifecycleManager
from .base import BaseAgent

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agent instances."""
    
    def __init__(self):
        """Initialize the agent factory."""
        self._llm_provider: Optional[LLMProvider] = None
        self._vector_store: Optional[VectorStoreProvider] = None
        self._embeddings: Optional[EmbeddingProvider] = None
        self._lifecycle = ComponentLifecycleManager()
    
    def with_llm(self, provider: LLMProvider) -> 'AgentFactory':
        """Set the LLM provider.
        
        Args:
            provider: LLM provider instance.
            
        Returns:
            Self for chaining.
        """
        self._llm_provider = provider
        self._lifecycle.register("llm", provider)
        return self
    
    def with_vector_store(self, provider: VectorStoreProvider) -> 'AgentFactory':
        """Set the vector store provider.
        
        Args:
            provider: Vector store provider instance.
            
        Returns:
            Self for chaining.
        """
        self._vector_store = provider
        self._lifecycle.register("vector_store", provider)
        return self
    
    def with_embeddings(self, provider: EmbeddingProvider) -> 'AgentFactory':
        """Set the embeddings provider.
        
        Args:
            provider: Embeddings provider instance.
            
        Returns:
            Self for chaining.
        """
        self._embeddings = provider
        self._lifecycle.register("embeddings", provider, dependencies=["vector_store"])
        return self
    
    async def create(
        self,
        agent_type: str,
        capabilities: Dict[str, Any],
        config: Dict[str, Any]
    ) -> BaseAgent:
        """Create an agent instance.
        
        Args:
            agent_type: Type of agent to create.
            capabilities: Agent capabilities.
            config: Agent configuration.
            
        Returns:
            Agent instance.
            
        Raises:
            ValueError: If required providers are not set.
        """
        if not self._llm_provider:
            raise ValueError("LLM provider not set")
            
        agent_cls = BaseAgent.get_agent(agent_type)
        
        # Create agent with injected dependencies
        agent = agent_cls(
            llm=self._llm_provider,
            capabilities=capabilities,
            config=config,
            vector_store=self._vector_store,
            embeddings=self._embeddings,
        )
        
        # Register agent with lifecycle manager
        self._lifecycle.register(
            "agent",
            agent,
            dependencies=[
                "llm",
                *(["vector_store"] if self._vector_store else []),
                *(["embeddings"] if self._embeddings else []),
            ]
        )
        
        # Initialize all components in optimal order
        await self._lifecycle.initialize()
        
        return agent 