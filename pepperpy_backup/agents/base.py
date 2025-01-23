"""Base agent implementation."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar

from ..providers.llm.base import BaseLLMProvider
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseAgent')

class BaseAgent(ABC):
    """Base class for all agents."""
    
    _registry: ClassVar[Dict[str, Type['BaseAgent']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register an agent class.
        
        Args:
            name: Name to register the agent under.
            
        Returns:
            Decorator function.
        """
        def decorator(agent_cls: Type[T]) -> Type[T]:
            cls._registry[name] = agent_cls
            return agent_cls
        return decorator
    
    @classmethod
    def get_agent(cls, name: str) -> Type['BaseAgent']:
        """Get a registered agent class.
        
        Args:
            name: Name of the agent.
            
        Returns:
            Agent class.
            
        Raises:
            ValueError: If agent is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Agent '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        capabilities: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """Initialize the agent.
        
        Args:
            llm: LLM provider instance.
            capabilities: Dictionary of agent capabilities.
            config: Agent configuration.
        """
        self.llm = llm
        self.capabilities = capabilities
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.is_initialized = False
        
        # Optional providers
        self.vector_store: Optional[BaseVectorStoreProvider] = None
        self.embeddings: Optional[BaseEmbeddingProvider] = None
        
        # Initialize providers from capabilities
        if "vector_store" in capabilities:
            provider_name = capabilities["vector_store"]["provider"]
            provider_config = capabilities["vector_store"]["config"]
            provider_cls = BaseVectorStoreProvider.get_provider(provider_name)
            self.vector_store = provider_cls(provider_config)
            
        if "embeddings" in capabilities:
            provider_name = capabilities["embeddings"]["provider"]
            provider_config = capabilities["embeddings"]["config"]
            provider_cls = BaseEmbeddingProvider.get_provider(provider_name)
            self.embeddings = provider_cls(provider_config)
    
    async def initialize(self) -> bool:
        """Initialize the agent and its capabilities.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return True
            
        try:
            # Initialize LLM provider
            await self.llm.initialize()
            
            # Initialize vector store if present
            if self.vector_store:
                await self.vector_store.initialize()
                
            # Initialize embeddings if present
            if self.embeddings:
                await self.embeddings.initialize()
                
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            await self.cleanup()
            raise ValueError(f"Agent initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        # Clean up LLM provider
        await self.llm.cleanup()
        
        # Clean up vector store if present
        if self.vector_store:
            await self.vector_store.cleanup()
            
        # Clean up embeddings if present
        if self.embeddings:
            await self.embeddings.cleanup()
            
        self.is_initialized = False
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input data and generate a response.
        
        Args:
            input_data: Input data to process.
            
        Returns:
            Processed result.
            
        Raises:
            ValueError: If the agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
    
    def has_capability(self, name: str) -> bool:
        """Check if the agent has a specific capability.
        
        Args:
            name: Name of the capability.
            
        Returns:
            True if the agent has the capability.
        """
        return name in self.capabilities
    
    def get_capability_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific capability.
        
        Args:
            name: Name of the capability.
            
        Returns:
            Configuration dictionary if capability exists, None otherwise.
        """
        return self.capabilities.get(name) 