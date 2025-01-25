"""Agent factory implementation for Pepperpy framework."""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.llm.base import BaseLLMProvider
from pepperpy.providers.vector_store.base import BaseVectorStoreProvider
from pepperpy.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.providers.memory.base import BaseMemoryProvider
from pepperpy.agents.base.base_agent import BaseAgent


class AgentFactoryError(PepperpyError):
    """Agent factory error class."""
    pass


class AgentFactory:
    """Factory class for creating agents.
    
    This class provides a fluent interface for configuring and creating
    agent instances with the necessary providers and capabilities.
    """
    
    def __init__(self) -> None:
        """Initialize agent factory."""
        self._llm_provider: Optional[BaseLLMProvider] = None
        self._vector_store_provider: Optional[BaseVectorStoreProvider] = None
        self._embedding_provider: Optional[BaseEmbeddingProvider] = None
        self._memory_provider: Optional[BaseMemoryProvider] = None
        
    def with_llm(self, provider: BaseLLMProvider) -> 'AgentFactory':
        """Set LLM provider.
        
        Args:
            provider: LLM provider instance
            
        Returns:
            Self for chaining
        """
        self._llm_provider = provider
        return self
        
    def with_vector_store(
        self,
        provider: Optional[BaseVectorStoreProvider],
    ) -> 'AgentFactory':
        """Set vector store provider.
        
        Args:
            provider: Vector store provider instance
            
        Returns:
            Self for chaining
        """
        self._vector_store_provider = provider
        return self
        
    def with_embeddings(
        self,
        provider: Optional[BaseEmbeddingProvider],
    ) -> 'AgentFactory':
        """Set embedding provider.
        
        Args:
            provider: Embedding provider instance
            
        Returns:
            Self for chaining
        """
        self._embedding_provider = provider
        return self
        
    def with_memory(
        self,
        provider: Optional[BaseMemoryProvider],
    ) -> 'AgentFactory':
        """Set memory provider.
        
        Args:
            provider: Memory provider instance
            
        Returns:
            Self for chaining
        """
        self._memory_provider = provider
        return self
        
    async def create(
        self,
        agent_type: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Create an agent instance.
        
        Args:
            agent_type: Type of agent to create
            name: Name for the agent instance
            config: Optional configuration
            
        Returns:
            Agent instance
            
        Raises:
            AgentFactoryError: If agent creation fails
        """
        if not self._llm_provider:
            raise AgentFactoryError("LLM provider is required")
            
        try:
            agent_cls = BaseAgent.get_agent(agent_type)
            agent = agent_cls(
                name=name,
                llm_provider=self._llm_provider,
                vector_store_provider=self._vector_store_provider,
                embedding_provider=self._embedding_provider,
                memory_provider=self._memory_provider,
                config=config,
            )
            await agent.initialize()
            return agent
        except Exception as e:
            raise AgentFactoryError(f"Failed to create agent: {e}")
            
    @classmethod
    def from_config(
        cls,
        config: Dict[str, Any],
    ) -> 'AgentFactory':
        """Create factory from configuration.
        
        Args:
            config: Factory configuration
            
        Returns:
            Agent factory instance
            
        Raises:
            AgentFactoryError: If factory creation fails
        """
        try:
            factory = cls()
            
            # Configure providers from config
            if 'llm_provider' in config:
                provider_cls = BaseLLMProvider.get_provider(
                    config['llm_provider']['type']
                )
                factory.with_llm(provider_cls(
                    name=config['llm_provider']['name'],
                    config=config['llm_provider'].get('config'),
                ))
                
            if 'vector_store_provider' in config:
                provider_cls = BaseVectorStoreProvider.get_provider(
                    config['vector_store_provider']['type']
                )
                factory.with_vector_store(provider_cls(
                    name=config['vector_store_provider']['name'],
                    config=config['vector_store_provider'].get('config'),
                ))
                
            if 'embedding_provider' in config:
                provider_cls = BaseEmbeddingProvider.get_provider(
                    config['embedding_provider']['type']
                )
                factory.with_embeddings(provider_cls(
                    name=config['embedding_provider']['name'],
                    config=config['embedding_provider'].get('config'),
                ))
                
            if 'memory_provider' in config:
                provider_cls = BaseMemoryProvider.get_provider(
                    config['memory_provider']['type']
                )
                factory.with_memory(provider_cls(
                    name=config['memory_provider']['name'],
                    config=config['memory_provider'].get('config'),
                ))
                
            return factory
        except Exception as e:
            raise AgentFactoryError(f"Failed to create factory from config: {e}") 