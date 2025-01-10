"""AI provider factory."""

from typing import Optional, Type, Dict, List, cast, Any
from datetime import datetime
import importlib
import logging
from functools import lru_cache
import pkg_resources

from pepperpy_core.config import ConfigManager
from pepperpy_core.plugins import PluginManager

from ..exceptions import ProviderError, ConfigError
from ..llm.base import LLMClient
from ..llm.config import LLMConfig
from .base import BaseProvider
from .config import ProviderConfig, PROVIDER_SETTINGS
from ..utils.dependencies import (
    check_provider_availability,
    verify_provider_dependencies,
    get_installation_command,
)

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """Provider registry for managing available providers."""
    
    def __init__(self) -> None:
        """Initialize registry."""
        self._providers: Dict[str, Type[BaseProvider[LLMConfig]]] = {}
        self._last_scan: Optional[datetime] = None
        self._plugin_manager = PluginManager()
        self._config_manager = ConfigManager()

    def register(
        self,
        name: str,
        provider_class: Type[BaseProvider[LLMConfig]]
    ) -> None:
        """Register provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        self._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    def unregister(self, name: str) -> None:
        """Unregister provider.
        
        Args:
            name: Provider name
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered provider: {name}")

    def get_provider(
        self,
        name: str
    ) -> Optional[Type[BaseProvider[LLMConfig]]]:
        """Get provider class.
        
        Args:
            name: Provider name
            
        Returns:
            Provider class if found, None otherwise
        """
        return self._providers.get(name)

    def scan_providers(self) -> None:
        """Scan and register available providers."""
        self._last_scan = datetime.now()
        
        # Scan built-in providers
        provider_modules = {
            "anthropic": ".anthropic",
            "openai": ".openai",
            "stackspot": ".stackspot",
            "openrouter": ".openrouter",
        }
        
        for name, module_path in provider_modules.items():
            # Skip if dependencies are not available
            if not check_provider_availability(name):
                logger.debug(f"Provider {name} dependencies not available")
                continue
                
            try:
                module = importlib.import_module(module_path, package=__package__)
                provider_class = getattr(module, f"{name.capitalize()}Provider")
                self.register(name, provider_class)
            except (ImportError, AttributeError) as e:
                logger.debug(f"Provider {name} not available: {e}")

        # Scan for plugin providers
        for entry_point in pkg_resources.iter_entry_points("pepperpy.providers"):
            try:
                provider_class = entry_point.load()
                provider_name = entry_point.name.lower()
                
                # Skip if dependencies are not available
                if not check_provider_availability(provider_name):
                    logger.debug(f"Provider plugin {provider_name} dependencies not available")
                    continue
                    
                self.register(provider_name, provider_class)
            except Exception as e:
                logger.warning(f"Failed to load provider plugin {entry_point.name}: {e}")

    @property
    def providers(self) -> Dict[str, Type[BaseProvider[LLMConfig]]]:
        """Get registered providers."""
        return self._providers.copy()

    @property
    def last_scan(self) -> Optional[datetime]:
        """Get last provider scan timestamp."""
        return self._last_scan

    def load_provider_config(self, provider: str) -> Dict[str, Any]:
        """Load provider configuration.
        
        Args:
            provider: Provider name
            
        Returns:
            Provider configuration
            
        Raises:
            ConfigError: If configuration loading fails
        """
        try:
            config = self._config_manager.load_config(f"provider.{provider}")
            settings_class = PROVIDER_SETTINGS.get(provider)
            if settings_class:
                settings = settings_class(**config.get("settings", {}))
                config["settings"] = settings.__dict__
            return config
        except Exception as e:
            raise ConfigError(
                f"Failed to load provider config: {e}",
                config_path=f"provider.{provider}",
                cause=e
            )

class AIProviderFactory:
    """Factory for creating AI providers.
    
    This class handles provider instantiation and lifecycle management.
    It uses a registry to track available providers and caches provider
    instances for better performance.
    """
    
    def __init__(self) -> None:
        """Initialize factory."""
        self._registry = ProviderRegistry()
        self._registry.scan_providers()
        self._instances: Dict[str, BaseProvider[LLMConfig]] = {}
        self._config_manager = ConfigManager()

    @property
    def registry(self) -> ProviderRegistry:
        """Get provider registry."""
        return self._registry

    def validate_config(self, config: LLMConfig) -> None:
        """Validate provider configuration.
        
        Args:
            config: Provider configuration
            
        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If provider dependencies are not met
        """
        if not config.provider:
            raise ConfigError("Provider type not specified")
        
        # Check if provider is supported
        if config.provider not in self._registry.providers:
            supported = list(self._registry.providers.keys())
            raise ConfigError(
                f"Unsupported provider: {config.provider}",
                invalid_keys=["provider"],
                config_path=str(config),
                metadata={"supported_providers": supported}
            )
            
        # Check provider dependencies
        missing = verify_provider_dependencies(config.provider)
        if missing:
            install_cmd = get_installation_command(missing)
            raise ProviderError(
                f"Provider '{config.provider}' dependencies not met. "
                f"Missing: {', '.join(missing)}. "
                f"Install with: {install_cmd}",
                provider=config.provider,
                operation="validate_config"
            )

    @lru_cache(maxsize=32)
    def get_provider_class(
        self,
        provider_type: str
    ) -> Type[BaseProvider[LLMConfig]]:
        """Get provider class.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Provider class
            
        Raises:
            ProviderError: If provider not found or dependencies not met
        """
        # Check dependencies first
        if not check_provider_availability(provider_type):
            missing = verify_provider_dependencies(provider_type)
            if missing:
                install_cmd = get_installation_command(missing)
                raise ProviderError(
                    f"Provider '{provider_type}' dependencies not met. "
                    f"Missing: {', '.join(missing)}. "
                    f"Install with: {install_cmd}",
                    provider=provider_type,
                    operation="get_class"
                )
        
        provider_class = self._registry.get_provider(provider_type)
        if not provider_class:
            raise ProviderError(
                f"Provider not found: {provider_type}",
                provider=provider_type,
                operation="get_class"
            )
        return provider_class

    async def create_provider(
        self,
        config: LLMConfig,
        *,
        cache: bool = True,
        load_defaults: bool = True
    ) -> BaseProvider[LLMConfig]:
        """Create provider instance.
        
        Args:
            config: Provider configuration
            cache: Whether to cache provider instance
            load_defaults: Whether to load default configuration
            
        Returns:
            Provider instance
            
        Raises:
            ProviderError: If provider creation fails
            ConfigError: If configuration is invalid
        """
        try:
            # Validate configuration and dependencies
            self.validate_config(config)
            
            # Load default configuration if requested
            if load_defaults:
                defaults = self._registry.load_provider_config(config.provider)
                config = self._merge_configs(defaults, config)
            
            # Check cache
            if cache and config.provider in self._instances:
                return self._instances[config.provider]
            
            # Create provider
            provider_class = self.get_provider_class(config.provider)
            provider = provider_class(config)
            
            # Initialize provider
            await provider.initialize()
            
            # Cache instance
            if cache:
                self._instances[config.provider] = provider
            
            return provider

        except (ConfigError, ProviderError):
            raise
        except Exception as e:
            raise ProviderError(
                "Failed to create provider",
                provider=config.provider,
                operation="create",
                cause=e
            )

    def _merge_configs(self, defaults: Dict[str, Any], config: LLMConfig) -> LLMConfig:
        """Merge default configuration with user configuration.
        
        Args:
            defaults: Default configuration
            config: User configuration
            
        Returns:
            Merged configuration
        """
        merged = defaults.copy()
        config_dict = config.__dict__.copy()
        
        # Remove None values from user config
        config_dict = {k: v for k, v in config_dict.items() if v is not None}
        
        # Merge settings separately to preserve defaults
        settings = merged.get("settings", {}).copy()
        settings.update(config_dict.get("settings", {}))
        config_dict["settings"] = settings
        
        # Update with user config
        merged.update(config_dict)
        
        return LLMConfig(**merged)

    async def cleanup(self) -> None:
        """Cleanup provider instances."""
        for provider in self._instances.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup provider: {e}")
        self._instances.clear()

    def get_supported_providers(self) -> List[str]:
        """Get list of supported provider types.
        
        Returns:
            List of provider names
        """
        return list(self._registry.providers.keys())

    def get_provider_info(self, provider_type: str) -> dict:
        """Get provider information.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Provider information
            
        Raises:
            ProviderError: If provider not found
        """
        provider_class = self.get_provider_class(provider_type)
        capabilities = getattr(provider_class, "capabilities", None)
        if capabilities:
            capabilities = capabilities.__dict__
        else:
            capabilities = {}
            
        # Check dependencies
        missing_deps = verify_provider_dependencies(provider_type)
        
        return {
            "name": provider_type,
            "class": provider_class.__name__,
            "module": provider_class.__module__,
            "capabilities": capabilities,
            "settings": PROVIDER_SETTINGS.get(provider_type, {}).__annotations__,
            "config": self._registry.load_provider_config(provider_type),
            "dependencies": {
                "available": missing_deps is None,
                "missing": missing_deps or []
            }
        }
