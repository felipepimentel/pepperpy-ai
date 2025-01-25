"""Base agent implementation for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.utils.lifecycle import Lifecycle
from pepperpy.providers.llm.base import BaseLLMProvider
from pepperpy.providers.vector_store.base import BaseVectorStoreProvider
from pepperpy.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.providers.memory.base import BaseMemoryProvider


class AgentError(PepperpyError):
    """Agent error class."""
    pass


T = TypeVar('T', bound='BaseAgent')


class BaseAgent(Lifecycle, ABC):
    """Base class for all agents in the system.
    
    An agent is a high-level abstraction that combines various providers
    and capabilities to perform specific tasks.
    """
    
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
        name: str,
        llm_provider: BaseLLMProvider,
        vector_store_provider: Optional[BaseVectorStoreProvider] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        memory_provider: Optional[BaseMemoryProvider] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize agent.
        
        Args:
            name: Agent name
            llm_provider: LLM provider instance
            vector_store_provider: Optional vector store provider
            embedding_provider: Optional embedding provider
            memory_provider: Optional memory provider
            config: Optional configuration
        """
        super().__init__(name, config)
        
        self._llm = llm_provider
        self._vector_store = vector_store_provider
        self._embeddings = embedding_provider
        self._memory = memory_provider
        self._capabilities: Dict[str, Any] = {}
        
    @property
    def llm(self) -> BaseLLMProvider:
        """Get LLM provider."""
        return self._llm
        
    @property
    def vector_store(self) -> Optional[BaseVectorStoreProvider]:
        """Get vector store provider."""
        return self._vector_store
        
    @property
    def embeddings(self) -> Optional[BaseEmbeddingProvider]:
        """Get embedding provider."""
        return self._embeddings
        
    @property
    def memory(self) -> Optional[BaseMemoryProvider]:
        """Get memory provider."""
        return self._memory
        
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return self._capabilities.copy()
        
    async def _initialize_impl(self) -> None:
        """Initialize agent implementation.
        
        Raises:
            AgentError: If initialization fails.
        """
        try:
            await self._setup()
        except Exception as e:
            raise AgentError(f"Failed to initialize agent {self.name}: {e}")
    
    async def _cleanup_impl(self) -> None:
        """Clean up agent implementation.
        
        Raises:
            AgentError: If cleanup fails.
        """
        try:
            await self._teardown()
        except Exception as e:
            raise AgentError(f"Failed to clean up agent {self.name}: {e}")
    
    def _validate_impl(self) -> None:
        """Validate agent implementation.
        
        Raises:
            AgentError: If validation fails.
        """
        try:
            self._validate()
        except Exception as e:
            raise AgentError(f"Failed to validate agent {self.name}: {e}")
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up agent resources.
        
        This method should be implemented by subclasses to perform
        any necessary setup when the agent is initialized.
        
        Raises:
            Exception: If setup fails.
        """
        pass
        
    @abstractmethod
    async def _teardown(self) -> None:
        """Clean up agent resources.
        
        This method should be implemented by subclasses to perform
        any necessary cleanup when the agent is no longer needed.
        
        Raises:
            Exception: If cleanup fails.
        """
        pass
        
    @abstractmethod
    def _validate(self) -> None:
        """Validate agent configuration.
        
        This method should be implemented by subclasses to validate
        that the agent is properly configured.
        
        Raises:
            Exception: If validation fails.
        """
        pass
        
    @abstractmethod
    async def process(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Process input and generate output.
        
        Args:
            input: Input to process
            context: Optional processing context
            
        Returns:
            Processing result
            
        Raises:
            AgentError: If processing fails
        """
        pass 