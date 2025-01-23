"""Agent factory implementation."""
import logging
from typing import Any, Dict, Optional, Type

from .base import BaseAgent
from ..providers.llm.base import BaseLLMProvider
from ..providers.memory.base import BaseMemoryProvider
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agents."""
    
    @staticmethod
    def create_agent(
        agent_type: str,
        config: Dict[str, Any]
    ) -> BaseAgent:
        """Create an agent instance.
        
        Args:
            agent_type: Type of agent to create.
            config: Agent configuration dictionary containing:
                - llm: LLM provider configuration
                    - provider: Provider name
                    - config: Provider configuration
                - capabilities: Optional agent capabilities
                    - memory: Optional memory provider configuration
                        - provider: Provider name
                        - config: Provider configuration
                    - vector_store: Optional vector store provider configuration
                        - provider: Provider name
                        - config: Provider configuration
                    - embeddings: Optional embeddings provider configuration
                        - provider: Provider name
                        - config: Provider configuration
                - config: Agent-specific configuration
            
        Returns:
            Agent instance.
            
        Raises:
            ValueError: If agent type is not registered or configuration is invalid.
        """
        # Get agent class
        try:
            agent_cls = BaseAgent.get_agent(agent_type)
        except ValueError as e:
            logger.error(f"Failed to get agent class: {str(e)}")
            raise ValueError(f"Invalid agent type '{agent_type}'")
        
        # Create LLM provider
        try:
            llm_config = config["llm"]
            llm_cls = BaseLLMProvider.get_provider(llm_config["provider"])
            llm = llm_cls(llm_config["config"])
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to create LLM provider: {str(e)}")
            raise ValueError("Invalid LLM provider configuration")
        
        # Initialize capabilities
        capabilities: Dict[str, Any] = {}
        
        # Add memory provider if configured
        if "memory" in config.get("capabilities", {}):
            try:
                memory_config = config["capabilities"]["memory"]
                memory_cls = BaseMemoryProvider.get_provider(memory_config["provider"])
                capabilities["memory"] = {
                    "provider": memory_config["provider"],
                    "config": memory_config["config"]
                }
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to configure memory provider: {str(e)}")
                raise ValueError("Invalid memory provider configuration")
        
        # Add vector store provider if configured
        if "vector_store" in config.get("capabilities", {}):
            try:
                vector_store_config = config["capabilities"]["vector_store"]
                vector_store_cls = BaseVectorStoreProvider.get_provider(vector_store_config["provider"])
                capabilities["vector_store"] = {
                    "provider": vector_store_config["provider"],
                    "config": vector_store_config["config"]
                }
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to configure vector store provider: {str(e)}")
                raise ValueError("Invalid vector store provider configuration")
        
        # Add embeddings provider if configured
        if "embeddings" in config.get("capabilities", {}):
            try:
                embeddings_config = config["capabilities"]["embeddings"]
                embeddings_cls = BaseEmbeddingProvider.get_provider(embeddings_config["provider"])
                capabilities["embeddings"] = {
                    "provider": embeddings_config["provider"],
                    "config": embeddings_config["config"]
                }
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to configure embeddings provider: {str(e)}")
                raise ValueError("Invalid embeddings provider configuration")
        
        # Create agent
        try:
            return agent_cls(
                llm=llm,
                capabilities=capabilities,
                config=config.get("config", {})
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise ValueError(f"Failed to create agent: {str(e)}") 