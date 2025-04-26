"""
PepperPy Main Framework Class.

This module provides the main entry point for the PepperPy framework,
coordinating and orchestrating all domain providers.
"""

import sys
import logging
from typing import Any, Protocol, cast, runtime_checkable, Dict, List, Optional, Self, Union
import asyncio
import importlib

# Verificação de versão do Python
if sys.version_info < (3, 12):
    raise RuntimeError("PepperPy requer Python 3.12 ou superior")

# Import domain providers
from pepperpy.agent.base import AgentProvider, BaseAgentProvider
from pepperpy.communication import (
    CommunicationProvider,
    CommunicationProtocol,
    create_provider as create_communication_provider
)
from pepperpy.cache.base import BaseCacheProvider, CacheProvider
from pepperpy.llm.base import BaseLLMProvider, LLMProvider
from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import get_registry, discover_plugins
from pepperpy.storage.provider import StorageProvider
from pepperpy.tool.base import BaseToolProvider, ToolProvider
from pepperpy.tts.base import BaseTTSProvider, TTSProvider
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.core.config import ConfigManager
from pepperpy.rag.processor import create_processor, TextProcessor

logger = logging.getLogger(__name__)

# Extended protocol definitions with initialize method
@runtime_checkable
class InitializableProvider(Protocol):
    """Protocol for providers that can be initialized."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...


class PepperPy:
    """Main PepperPy framework class that orchestrates all domain providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the PepperPy framework.

        Args:
            config: Global configuration for all providers
        """
        self.config = config or {}
        self._agent_provider: AgentProvider | None = None
        self._cache_provider: CacheProvider | None = None
        self._discovery_provider: PluginDiscoveryProvider | None = None
        self._llm_provider: LLMProvider | None = None
        self._storage_provider: StorageProvider | None = None
        self._tts_provider: TTSProvider | None = None
        self._tool_provider: ToolProvider | None = None
        self._workflow_provider: WorkflowProvider | None = None

        # Task configuration
        self._task_config: dict[str, Any] = {}

        # Add topology provider
        self._communication_provider = None

        self.components = {}
        self.rag_processor = None
        self._workflow_task = None

    # Task configuration methods
    def with_task_context(self, **context: Any) -> "PepperPy":
        """Configure task context.

        Args:
            **context: Context key-value pairs

        Returns:
            Self for method chaining
        """
        self._task_config["context"] = {
            **(self._task_config.get("context", {})),
            **context,
        }
        return self

    def with_task_parameters(self, **parameters: Any) -> "PepperPy":
        """Configure task parameters.

        Args:
            **parameters: Parameter key-value pairs

        Returns:
            Self for method chaining
        """
        self._task_config["parameters"] = {
            **(self._task_config.get("parameters", {})),
            **parameters,
        }
        return self

    def with_task_capability(self, capability: str) -> "PepperPy":
        """Set required task capability.

        Args:
            capability: Capability name

        Returns:
            Self for method chaining
        """
        self._task_config["capability"] = capability
        return self

    def with_task_format(self, format_type: str) -> "PepperPy":
        """Set task output format.

        Args:
            format_type: Format type

        Returns:
            Self for method chaining
        """
        self._task_config["format"] = format_type
        return self

    def with_task_schema(self, schema: dict[str, Any]) -> "PepperPy":
        """Set task data schema.

        Args:
            schema: Schema definition

        Returns:
            Self for method chaining
        """
        self._task_config["schema"] = schema
        return self

    # Agent provider methods
    def with_agent(
        self, provider: str | type[BaseAgentProvider] | AgentProvider, **config: Any
    ) -> "PepperPy":
        """Configure the agent provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("agent", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown agent provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance with merged config
            merged_config = {
                **self.config.get("agent", {}),
                **config,
                "task_config": self._task_config,  # Include task config
            }
            self._agent_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseAgentProvider):
            # Create an instance of the provider class
            merged_config = {
                **self.config.get("agent", {}),
                **config,
                "task_config": self._task_config,  # Include task config
            }
            self._agent_provider = provider(config=merged_config)
        else:
            # Use the provided instance
            self._agent_provider = cast(AgentProvider, provider)

        return self

    # Cache provider methods
    def with_cache(
        self, provider: str | type[BaseCacheProvider] | CacheProvider, **config: Any
    ) -> "PepperPy":
        """Configure the cache provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("cache", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown cache provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("cache", {}), **config}
            self._cache_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseCacheProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("cache", {}), **config}
            self._cache_provider = provider(
                namespace="pepperpy", ttl=3600, config=merged_config
            )
        else:
            # Use the provided instance
            self._cache_provider = cast(CacheProvider, provider)

        return self

    # Discovery provider methods
    def with_discovery(
        self,
        provider: str | type[PluginDiscoveryProvider] | PluginDiscoveryProvider,
        **config: Any,
    ) -> "PepperPy":
        """Configure the discovery provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("discovery", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown discovery provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("discovery", {}), **config}
            self._discovery_provider = provider_class(merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(
            provider, PluginDiscoveryProvider
        ):
            # Create an instance of the provider class
            merged_config = {**self.config.get("discovery", {}), **config}
            self._discovery_provider = provider(merged_config)
        else:
            # Use the provided instance
            self._discovery_provider = cast(PluginDiscoveryProvider, provider)

        return self

    # Storage provider methods
    def with_storage(
        self,
        provider: Any,
        **config: Any,
    ) -> "PepperPy":
        """Configure the storage provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("storage", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown storage provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("storage", {}), **config}
            self._storage_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type):
            # Create an instance of the provider class
            merged_config = {**self.config.get("storage", {}), **config}
            self._storage_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._storage_provider = cast(StorageProvider, provider)

        return self

    # TTS provider methods
    def with_tts(
        self, provider: str | type[BaseTTSProvider] | TTSProvider, **config: Any
    ) -> "PepperPy":
        """Configure the TTS provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("tts", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown TTS provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("tts", {}), **config}
            self._tts_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseTTSProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("tts", {}), **config}
            # We use a type ignore here because mypy doesn't recognize that
            # BaseTTSProvider implements TTSProvider
            self._tts_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._tts_provider = cast(TTSProvider, provider)

        return self

    # Tool provider methods
    def with_tool(
        self, provider: str | type[BaseToolProvider] | ToolProvider, **config: Any
    ) -> "PepperPy":
        """Configure the tool provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("tool", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown tool provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("tool", {}), **config}
            self._tool_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseToolProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("tool", {}), **config}
            self._tool_provider = provider(config=merged_config)
        else:
            # Use the provided instance
            self._tool_provider = cast(ToolProvider, provider)

        return self

    # LLM provider methods
    def with_llm(
        self, provider: str | type[BaseLLMProvider] | LLMProvider, **config: Any
    ) -> "PepperPy":
        """Configure the LLM provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("llm", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown LLM provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance
            merged_config = {**self.config.get("llm", {}), **config}
            self._llm_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, BaseLLMProvider):
            # Create an instance of the provider class
            merged_config = {**self.config.get("llm", {}), **config}
            # We use a type ignore here because mypy doesn't recognize that
            # BaseLLMProvider implements LLMProvider
            self._llm_provider = provider(config=merged_config)  # type: ignore
        else:
            # Use the provided instance
            self._llm_provider = cast(LLMProvider, provider)

        return self

    # Workflow configuration methods
    def with_workflow(
        self, provider: str | type[WorkflowProvider] | WorkflowProvider, **config: Any
    ) -> "PepperPy":
        """Configure workflow provider.

        Args:
            provider: Provider name, class, or instance
            **config: Provider-specific configuration

        Returns:
            Self for method chaining
        """
        if isinstance(provider, str):
            # Get provider from registry
            provider_class = get_registry().get_plugin("workflow", provider.lower())
            if not provider_class:
                raise ValueError(
                    f"Unknown workflow provider: {provider}. Make sure the plugin is installed."
                )

            # Create instance with merged config
            merged_config = {
                **self.config.get("workflow", {}),
                **config,
                "task_config": self._task_config,  # Include task config
            }
            self._workflow_provider = provider_class(config=merged_config)  # type: ignore
        elif isinstance(provider, type) and issubclass(provider, WorkflowProvider):
            # Create an instance of the provider class
            merged_config = {
                **self.config.get("workflow", {}),
                **config,
                "task_config": self._task_config,  # Include task config
            }
            self._workflow_provider = provider(config=merged_config)
        else:
            # Use the provided instance
            self._workflow_provider = cast(WorkflowProvider, provider)

        return self

    def with_workflow_input(self, **inputs: Any) -> "PepperPy":
        """Configure workflow input data.

        Args:
            **inputs: Input key-value pairs

        Returns:
            Self for method chaining
        """
        self._task_config["workflow_inputs"] = {
            **(self._task_config.get("workflow_inputs", {})),
            **inputs,
        }
        return self

    def with_workflow_options(self, **options: Any) -> "PepperPy":
        """Configure workflow options.

        Args:
            **options: Option key-value pairs

        Returns:
            Self for method chaining
        """
        self._task_config["workflow_options"] = {
            **(self._task_config.get("workflow_options", {})),
            **options,
        }
        return self

    # Methods to access the domain providers
    @property
    def agent(self) -> AgentProvider:
        """Get the agent provider.

        Returns:
            Agent provider

        Raises:
            ValueError: If no agent provider is configured
        """
        if not self._agent_provider:
            raise ValueError("No agent provider configured. Use with_agent() first.")
        return self._agent_provider

    @property
    def cache(self) -> CacheProvider:
        """Get the cache provider.

        Returns:
            Cache provider

        Raises:
            ValueError: If no cache provider is configured
        """
        if not self._cache_provider:
            raise ValueError("No cache provider configured. Use with_cache() first.")
        return self._cache_provider

    @property
    def discovery(self) -> PluginDiscoveryProvider:
        """Get the discovery provider.

        Returns:
            Discovery provider

        Raises:
            ValueError: If no discovery provider is configured
        """
        if not self._discovery_provider:
            raise ValueError(
                "No discovery provider configured. Use with_discovery() first."
            )
        return self._discovery_provider

    @property
    def storage(self) -> StorageProvider:
        """Get the storage provider.

        Returns:
            Storage provider

        Raises:
            ValueError: If no storage provider is configured
        """
        if not self._storage_provider:
            raise ValueError(
                "No storage provider configured. Use with_storage() first."
            )
        return self._storage_provider

    @property
    def tts(self) -> TTSProvider:
        """Get the TTS provider.

        Returns:
            TTS provider

        Raises:
            ValueError: If no TTS provider is configured
        """
        if not self._tts_provider:
            raise ValueError("No TTS provider configured. Use with_tts() first.")
        return self._tts_provider

    @property
    def tool(self) -> ToolProvider:
        """Get the tool provider.

        Returns:
            Tool provider

        Raises:
            ValueError: If no tool provider is configured
        """
        if not self._tool_provider:
            raise ValueError("No tool provider configured. Use with_tool() first.")
        return self._tool_provider

    @property
    def llm(self) -> LLMProvider:
        """Get the LLM provider.

        Returns:
            LLM provider

        Raises:
            ValueError: If no LLM provider is configured
        """
        if not self._llm_provider:
            raise ValueError("No LLM provider configured. Use with_llm() first.")
        return self._llm_provider

    @property
    def workflow(self) -> WorkflowProvider:
        """Get the workflow provider.

        Returns:
            Workflow provider

        Raises:
            ValueError: If no workflow provider is configured
        """
        if not self._workflow_provider:
            raise ValueError(
                "No workflow provider configured. Use with_workflow() first."
            )
        return self._workflow_provider

    # Global initialization
    async def initialize(self) -> "PepperPy":
        """Initialize all providers and components.

        Returns:
            Self for method chaining
        """
        # Discover plugins first
        await discover_plugins()
        
        # Initialize all providers
        providers: list[InitializableProvider] = []

        if self._agent_provider:
            providers.append(cast(InitializableProvider, self._agent_provider))

        if self._cache_provider:
            providers.append(cast(InitializableProvider, self._cache_provider))

        if self._discovery_provider:
            providers.append(cast(InitializableProvider, self._discovery_provider))

        if self._llm_provider:
            providers.append(cast(InitializableProvider, self._llm_provider))

        if self._storage_provider:
            providers.append(cast(InitializableProvider, self._storage_provider))

        if self._tts_provider:
            providers.append(cast(InitializableProvider, self._tts_provider))

        if self._tool_provider:
            providers.append(cast(InitializableProvider, self._tool_provider))

        if self._workflow_provider:
            providers.append(cast(InitializableProvider, self._workflow_provider))

        if self._communication_provider:
            providers.append(cast(InitializableProvider, self._communication_provider))
            
        # Initialize RAG processor if configured
        if self.rag_processor:
            await self.rag_processor.initialize()

        # Initialize all providers
        for provider in providers:
            await provider.initialize()

        return self

    def with_communication(
        self, communication_type: str | None = None, **config: Any
    ) -> "PepperPy":
        """Configure communication provider.

        Args:
            communication_type: Type of communication to use
            **config: Communication-specific configuration options

        Returns:
            Self for chaining
        """
        # Merge with existing config if present
        merged_config = {**self.config.get("communication", {}), **config}

        # Create the communication provider
        self._communication_provider = create_communication_provider(
            communication_type, **merged_config
        )

        # Store in config for persistence
        self.config["communication"] = merged_config
        if communication_type:
            self.config["communication"]["communication_type"] = communication_type

        return self

    async def execute_communication(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task using the configured communication.

        Args:
            input_data: Input data containing task and other parameters

        Returns:
            Execution results

        Raises:
            ValueError: If no communication provider is configured
        """
        # Ensure we have a communication provider
        if not self._communication_provider:
            raise ValueError("No communication provider configured")

        # Initialize if needed
        if isinstance(self._communication_provider, InitializableProvider):
            await self._communication_provider.initialize()

        # Execute the communication
        return await self._communication_provider.execute(input_data)

    @property
    def communication(self) -> CommunicationProtocol:
        """Get the configured communication provider.

        Returns:
            Configured communication provider

        Raises:
            ValueError: If no communication provider is configured
        """
        if not self._communication_provider:
            raise ValueError("No communication provider configured")
        return self._communication_provider

    async def __aenter__(self) -> "PepperPy":
        """Enter async context manager."""
        # Initialize existing providers

        # Initialize communication provider if configured
        if self._communication_provider:
            await self._communication_provider.initialize()

        return self

    async def __aexit__(
        self, exc_type: Any = None, exc_val: Any = None, exc_tb: Any = None
    ) -> None:
        """Exit async context manager."""
        # Clean up existing providers

        # Clean up communication provider if configured
        if self._communication_provider:
            await self._communication_provider.cleanup()

    @classmethod
    def create(cls) -> "PepperPy":
        """Create a new PepperPy instance."""
        return cls()
    
    def with_rag_processor(
        self, 
        processor_type: Optional[str] = None, 
        **kwargs: Any
    ) -> "PepperPy":
        """Configure RAG text processor.
        
        Args:
            processor_type: Type of processor to use (spacy, nltk, transformers)
            **kwargs: Additional processor configuration
            
        Returns:
            Self for method chaining
        """
        self._rag_processor_type = processor_type
        self._rag_processor_config = kwargs
        return self
    
    def build(self) -> "PepperPy":
        """Build the PepperPy instance.
        
        Returns:
            Fully configured PepperPy instance
        """
        return self

    @property
    def rag(self) -> 'RAGTask':
        """Get RAG task interface.
        
        Returns:
            RAG task interface
        """
        if not hasattr(self, "_rag_task") or not self._rag_task:
            self._rag_task = RAGTask(self)
        return self._rag_task


class RAGTask:
    """RAG task interface."""
    
    def __init__(self, pepper: PepperPy) -> None:
        """Initialize RAG task.
        
        Args:
            pepper: PepperPy instance
        """
        self.pepper = pepper
        
        # Get processor configuration
        if hasattr(pepper, "_rag_processor_type"):
            self._processor_type = getattr(pepper, "_rag_processor_type")
            self._processor_config = getattr(pepper, "_rag_processor_config", {})
        else:
            self._processor_type = None
            self._processor_config = {}
        
        self._processor = None

    async def _ensure_processor(self) -> None:
        """Ensure processor is initialized."""
        if not self._processor:
            self._processor = await create_processor(
                processor_type=self._processor_type,
                **self._processor_config
            )
            await self._processor.initialize()

    async def process_text(self, text: str, **options: Any) -> Dict[str, Any]:
        """Process text using the configured processor.
        
        Args:
            text: Text to process
            **options: Additional processing options
            
        Returns:
            Processed text result
        """
        try:
            await self._ensure_processor()
            result = await self._processor.execute({
                "task": "process_text",
                "text": text,
                "options": options
            })
            
            return result["result"] if result["status"] == "success" else {"error": result["message"]}
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return {"error": str(e)}
    
    async def chunk_text(self, text: str) -> Dict[str, Any]:
        """Chunk text using the configured processor.
        
        Args:
            text: Text to chunk
            
        Returns:
            Chunked text result
        """
        try:
            await self._ensure_processor()
            result = await self._processor.execute({
                "task": "chunk_text",
                "text": text
            })
            
            return result["result"] if result["status"] == "success" else {"error": result["message"]}
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return {"error": str(e)}


class WorkflowTask:
    """Workflow task."""

    def __init__(self, pepper: PepperPy) -> None:
        """Initialize workflow task.
        
        Args:
            pepper: PepperPy instance
        """
        self._pepper = pepper
        self._workflow_config = getattr(pepper, "_workflow_config", {})
        self._initialized_providers = {}
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up any initialized workflow providers
        for provider in self._initialized_providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up workflow provider: {e}")
                
        self._initialized_providers = {}
                
    async def execute(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            input_data: Input data for the workflow
            
        Returns:
            Workflow result
        """
        try:
            # Check if workflow provider is already initialized
            if workflow_name in self._initialized_providers:
                provider = self._initialized_providers[workflow_name]
            else:
                # Import the workflow provider dynamically
                # Expected format: workflow/name -> plugins.workflow.name.provider
                parts = workflow_name.split('/')
                if len(parts) != 2 or parts[0] != "workflow":
                    raise ValueError(f"Invalid workflow name: {workflow_name}. Expected format: workflow/name")
                
                module_name = parts[1]
                module_path = f"plugins.workflow.{module_name}.provider"
                
                try:
                    module = importlib.import_module(module_path)
                    
                    # Find the provider class
                    provider_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name.endswith("Provider"):
                            provider_class = attr
                            break
                            
                    if not provider_class:
                        raise ValueError(f"Could not find provider class in {module_path}")
                    
                    # Create provider instance
                    provider = provider_class()
                    await provider.initialize()
                    
                    # Cache the initialized provider
                    self._initialized_providers[workflow_name] = provider
                    
                except ImportError as e:
                    raise ValueError(f"Could not import workflow {workflow_name}: {e}")
                except Exception as e:
                    raise ValueError(f"Error initializing workflow {workflow_name}: {e}")
            
            # Execute workflow
            return await provider.execute(input_data)
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
