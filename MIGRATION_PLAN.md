# PepperPy Plugin Architecture Migration Plan

## Table of Contents
- [Current Architecture (As-Is)](#current-architecture-as-is)
- [Target Architecture (To-Be)](#target-architecture-to-be)
- [Migration Strategy](#migration-strategy)
- [Detailed Implementation Steps](#detailed-implementation-steps)
- [Testing Strategy](#testing-strategy)
- [Documentation Updates](#documentation-updates)

## Current Architecture (As-Is)

The PepperPy framework currently uses a monolithic approach where provider implementations are included directly in the core package. Each module follows a similar pattern:

```
pepperpy/
├── __init__.py
├── llm/
│   ├── __init__.py
│   ├── base.py             # Contains interfaces and factory functions
│   └── providers/          # Contains provider implementations
│       ├── __init__.py
│       ├── openai.py
│       ├── openrouter.py
│       └── local.py
├── rag/
│   ├── __init__.py
│   ├── base.py
│   └── providers/
│       ├── __init__.py
│       └── ...
├── storage/
│   └── ...
└── ...
```

Key issues with the current architecture:
1. **Dependency Bloat**: The core package requires dependencies for all providers
2. **Complex Maintenance**: Updating one provider requires modifying the core package
3. **Monolithic Growth**: The codebase keeps growing as providers are added
4. **Fixed Provider Set**: Adding new providers requires modifying the core package
5. **All-or-Nothing Installation**: Users install all provider dependencies regardless of need

## Target Architecture (To-Be)

We will transition to a plugin-based architecture where:
1. The core package (`pepperpy/`) contains only interfaces and minimal functionality
2. Provider implementations are moved to separate plugin packages in the `plugins/` directory
3. Plugins are discovered and loaded dynamically at runtime
4. Each plugin manages its own dependencies
5. **The plugin system is completely abstracted from the end user through the PepperPy class**

```
/
├── pepperpy/                  # Core framework (minimal)
│   ├── __init__.py
│   ├── core.py                # Core utilities
│   ├── llm.py                 # LLM interfaces
│   ├── rag.py                 # RAG interfaces
│   ├── storage.py             # Storage interfaces
│   ├── plugin_manager.py      # Plugin management system
│   ├── pepperpy.py            # Main user-facing class (abstracts plugins)
│   └── utils.py               # Common utilities
│
├── plugins/                   # Provider implementations
│   ├── llm_openai_provider/
│   │   ├── __init__.py
│   │   ├── provider.py        # OpenAI provider implementation
│   │   ├── plugin.json        # Plugin metadata
│   │   └── requirements.txt   # Plugin-specific dependencies
│   ├── llm_anthropic_provider/
│   │   └── ...
│   ├── rag_chroma_provider/
│   │   └── ...
│   └── ...
│
├── examples/
├── tests/
└── pyproject.toml             # Core dependencies only
```

## Migration Strategy

Our migration strategy follows these high-level steps:

1. Create the plugin infrastructure (plugin manager)
2. Simplify the core package structure (flatten modules)
3. Update the PepperPy class to abstract the plugin system
4. Move providers to plugins one module at a time
5. Update factory functions to use the plugin system internally
6. Update tests and examples to work with the new architecture
7. Update documentation

The migration will be performed incrementally, starting with one module (LLM) and then applying the same pattern to other modules.

**IMPORTANT**: All generated code and comments MUST be in English.

## Detailed Implementation Steps

### 1. Create Plugin Manager

Create a single file `pepperpy/plugin_manager.py` that handles plugin discovery, loading, and dependency management:

```python
# pepperpy/plugin_manager.py

import os
import json
import importlib.util
import subprocess
import sys
from typing import Dict, Any, Optional, Type

class PluginManager:
    """Plugin manager for PepperPy."""
    
    _instance = None
    
    # Directories where to look for plugins
    PLUGIN_DIRECTORIES = [
        os.path.join(os.getcwd(), "plugins"),
        os.path.join(os.path.expanduser("~"), ".pepperpy", "plugins"),
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._plugins = {}
            cls._instance._provider_cache = {}
        return cls._instance
    
    def discover_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available plugins."""
        plugins = {}
        
        for plugin_dir in self.PLUGIN_DIRECTORIES:
            if not os.path.exists(plugin_dir):
                continue
                
            for item in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, item)
                if not os.path.isdir(plugin_path):
                    continue
                    
                manifest_path = os.path.join(plugin_path, "plugin.json")
                if not os.path.exists(manifest_path):
                    continue
                    
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                        
                    if "name" in manifest and "category" in manifest:
                        manifest["path"] = plugin_path
                        plugins[manifest["name"]] = manifest
                except Exception as e:
                    print(f"Error loading plugin manifest {manifest_path}: {e}")
                    
        self._plugins = plugins
        return plugins
    
    def load_plugin_class(self, plugin_info: Dict[str, Any]) -> Optional[Type]:
        """Load the main plugin class based on entry_point."""
        if "entry_point" not in plugin_info or "path" not in plugin_info:
            return None
            
        try:
            module_name, class_name = plugin_info["entry_point"].split(":")
            full_path = f"{plugin_info['path']}/{module_name}.py"
            
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                f"{plugin_info['name']}.{module_name}", full_path
            )
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Get the class from the module
            return getattr(module, class_name)
        except Exception as e:
            print(f"Error loading plugin class {plugin_info.get('name')}: {e}")
            return None
    
    def install_plugin_dependencies(self, plugin_name: str) -> bool:
        """Install plugin dependencies using uv."""
        if plugin_name not in self._plugins:
            return False
            
        plugin_info = self._plugins[plugin_name]
        req_path = os.path.join(plugin_info["path"], "requirements.txt")
        
        if not os.path.exists(req_path):
            return True  # No dependencies is success
            
        try:
            # Use uv to install dependencies
            result = subprocess.run(
                [sys.executable, "-m", "uv", "pip", "install", "-r", req_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error installing dependencies for {plugin_name}: {result.stderr}")
                return False
                
            return True
        except Exception as e:
            print(f"Error running uv for {plugin_name}: {e}")
            return False
    
    def get_provider_class(self, category: str, provider_name: str) -> Optional[Type]:
        """Get the provider class from a specific plugin."""
        # Discover plugins if not done yet
        if not self._plugins:
            self.discover_plugins()
            
        # Look for plugin with matching category and provider_name
        for name, info in self._plugins.items():
            if (info.get("category") == category and 
                info.get("provider_name") == provider_name):
                
                # Check cache
                cache_key = f"{category}_{provider_name}"
                if cache_key in self._provider_cache:
                    return self._provider_cache[cache_key]
                
                # Install dependencies if needed
                if not self.install_plugin_dependencies(name):
                    continue
                    
                # Load class
                provider_class = self.load_plugin_class(info)
                if provider_class:
                    self._provider_cache[cache_key] = provider_class
                    return provider_class
                    
        return None
    
    def create_provider(self, category: str, provider_name: str, **config: Any) -> Any:
        """Create a provider instance from a plugin."""
        provider_class = self.get_provider_class(category, provider_name)
        
        if not provider_class:
            raise ValueError(f"Provider '{provider_name}' not found for category '{category}'")
            
        try:
            return provider_class(**config)
        except Exception as e:
            raise ValueError(f"Failed to create provider '{provider_name}': {e}")

# Global plugin manager instance
plugin_manager = PluginManager()
```

### 2. Simplify Core Package Structure

For each module (starting with LLM):

1. Create a new simplified interface file:

```python
# pepperpy/llm.py

"""LLM interfaces and types.

This module defines the core interfaces and data types for working with
Language Model providers in PepperPy.
"""

import abc
import enum
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core import BaseProvider, PepperpyError, ValidationError
from pepperpy.plugin_manager import plugin_manager


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation."""

    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Result of a text generation request."""

    content: str
    messages: List[Message]
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationChunk:
    """A chunk of generated text from a streaming response."""

    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(PepperpyError):
    """Base error for the LLM module."""
    pass


class LLMProvider(BaseProvider, abc.ABC):
    """Base class for LLM providers."""

    name: str = "base"

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the LLM provider."""
        self.name = name
        self._config = config or {}
        self._config.update(kwargs)
        self.initialized = False
        self.last_used = None

    @abc.abstractmethod
    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text based on input messages."""
        pass

    @abc.abstractmethod
    async def generate_stream(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in streaming based on input messages."""
        pass

    # ... other abstract methods ...
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass


# Note: This function is for internal use only - users will interact with PepperPy class instead
def create_provider(provider_type: str = "openai", **config: Any) -> LLMProvider:
    """Create an LLM provider based on type (internal use only).

    Args:
        provider_type: Type of provider to create (default: openai)
        **config: Provider configuration

    Returns:
        An instance of the specified LLMProvider

    Raises:
        ValidationError: If provider creation fails
    """
    try:
        # Use plugin manager to create provider
        return plugin_manager.create_provider("llm", provider_type, **config)
    except Exception as e:
        raise ValidationError(f"Failed to create LLM provider '{provider_type}': {e}")
```

2. Update `pepperpy/__init__.py` to import from the new file:

```python
# pepperpy/__init__.py

"""PepperPy framework."""

from pepperpy.llm import (
    LLMProvider,
    Message,
    MessageRole,
    GenerationResult,
    GenerationChunk,
)

from pepperpy.pepperpy import PepperPy

# ... other imports ...

__all__ = [
    # Main class
    "PepperPy",
    
    # LLM
    "LLMProvider",
    "Message",
    "MessageRole",
    "GenerationResult",
    "GenerationChunk",
    # ... other exports ...
]
```

### 3. Update PepperPy Class

The most important change is to update the PepperPy class to handle plugin management internally:

```python
# pepperpy/pepperpy.py

from typing import Any, Dict, List, Optional, Self, Union

from pepperpy.llm import LLMProvider, Message
from pepperpy.plugin_manager import plugin_manager
from pepperpy.rag import RAGProvider
# ... other imports

class PepperPy:
    """Main class for interacting with the PepperPy framework."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}
        self._llm_provider: Optional[LLMProvider] = None
        self._rag_provider: Optional[RAGProvider] = None
        # ... other providers

    def with_llm(
        self, 
        provider_type: str = "openai", 
        **config: Any
    ) -> Self:
        """Configure LLM support using specific provider type.

        Args:
            provider_type: Type of LLM provider (e.g., "openai", "openrouter")
            **config: Provider-specific configuration

        Returns:
            Self for chaining
        """
        # Use plugin manager internally
        self._llm_provider = plugin_manager.create_provider("llm", provider_type, **config)
        return self

    def with_rag(
        self, 
        provider_type: str = "chroma", 
        **config: Any
    ) -> Self:
        """Configure RAG support using specific provider type.

        Args:
            provider_type: Type of RAG provider
            **config: Provider-specific configuration

        Returns:
            Self for chaining
        """
        # Use plugin manager internally
        self._rag_provider = plugin_manager.create_provider("rag", provider_type, **config)
        return self

    # ... other methods and properties ...
    
    @property
    def chat(self) -> ChatBuilder:
        """Get chat builder."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return ChatBuilder(self._llm_provider)
    
    # ... other builder properties ...

    async def __aenter__(self) -> Self:
        """Enter async context.

        Returns:
            Self for use in context
        """
        # Initialize all configured providers
        if self._llm_provider:
            await self._llm_provider.initialize()
        # ... initialize other providers ...
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        # Clean up all configured providers
        if self._llm_provider:
            await self._llm_provider.cleanup()
        # ... clean up other providers ...
```

### 4. Move Providers to Plugins

For each provider in a module:

1. Create plugin directory structure:

```
plugins/llm_openai_provider/
├── __init__.py
├── provider.py
├── plugin.json
└── requirements.txt
```

2. Move the provider implementation:

```python
# plugins/llm_openai_provider/provider.py

"""OpenAI provider implementation for PepperPy."""

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)

class OpenAIProvider(LLMProvider):
    """LLM provider using the OpenAI API."""

    # ... implementation details ...
```

3. Create plugin metadata:

```json
# plugins/llm_openai_provider/plugin.json

{
  "name": "llm_openai_provider",
  "version": "1.0.0",
  "category": "llm",
  "provider_name": "openai",
  "description": "OpenAI provider for PepperPy",
  "entry_point": "provider:OpenAIProvider",
  "author": "PepperPy Team",
  "pepperpy_compatibility": ">=0.1.0"
}
```

4. Create plugin dependencies:

```
# plugins/llm_openai_provider/requirements.txt

openai>=1.14.0
```

5. Repeat for each provider in each module.

### 5. Update pyproject.toml

Remove provider-specific dependencies from core, and add uv for plugin dependency management:

```toml
[tool.poetry.dependencies]
python = ">=3.9,<3.13"
aiohttp = "^3.9.3"
pydantic = "^2.6.3"
python-dotenv = "^1.0.1"
tenacity = "^8.2.3"
loguru = "^0.7.2"
httpx = "^0.28.1"
pyyaml = "^6.0.2"
uv = "^0.1.12"  # For plugin dependency management

# Keep only the most essential dependencies
# Provider-specific dependencies are moved to plugin requirements.txt
```

### 6. Create plugins/ Directory

```bash
mkdir -p plugins
```

### 7. Update Examples to Use PepperPy Class

```python
# examples/llm_example.py

import asyncio
import os
from pepperpy import PepperPy

async def main():
    # Create a PepperPy instance with the desired providers
    async with PepperPy().with_llm(
        provider_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    ) as pepper:
        # Use the fluent API
        result = await (
            pepper.chat
            .with_system("You are a helpful assistant.")
            .with_user("Tell me about Python.")
            .generate()
        )
        
        print(result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

### 8. Create Tests for the Plugin System

```python
# tests/test_pepperpy.py

import os
import pytest
from pepperpy import PepperPy

@pytest.mark.asyncio
async def test_pepperpy_with_llm():
    """Test PepperPy with LLM provider."""
    # This internally uses the plugin system
    pepper = PepperPy().with_llm("openai", api_key="fake_key")
    
    # Check that provider was created correctly
    assert pepper._llm_provider is not None
    assert pepper._llm_provider.name == "openai"

@pytest.mark.asyncio
async def test_pepperpy_chat():
    """Test PepperPy chat builder."""
    pepper = PepperPy().with_llm("openai", api_key="fake_key")
    
    # Access chat builder
    chat = pepper.chat
    assert chat is not None
    
    # Build a chat session
    chat = (
        chat
        .with_system("You are helpful.")
        .with_user("Tell me about Python.")
    )
    
    # No need to test generation here, just ensure builder works
    assert len(chat._messages) == 2
```

## Testing Strategy

1. **Unit Tests**:
   - Test PepperPy class integration with plugin system
   - Test plugin discovery
   - Test plugin loading
   - Test dependency management
   - Test provider creation for each migrated module

2. **Integration Tests**:
   - Test workflows that use multiple providers
   - Test error handling and fallbacks

3. **API Usage Tests**:
   - Test that the PepperPy class properly abstracts the plugin system
   - Ensure users don't need to be aware of the plugin architecture
   - Verify fluent API continues to work as expected

## Documentation Updates

1. Update `README.md` with plugin architecture overview
2. Create developer documentation for plugin development:
   - Plugin structure requirements
   - Plugin documentation requirements
   - How to test plugins
   - How to publish plugins

3. Update user documentation:
   - How to use the PepperPy class with different providers
   - No mention of plugin system in user documentation
   - Focus on the fluent API and capabilities

4. Update Cursor Rules to reflect new architecture:
   - Update file structure rules
   - Create plugin development rules
   - Update dependency management rules

## Conclusion

This migration plan provides a comprehensive roadmap for transitioning from the current monolithic architecture to a plugin-based architecture. By following these steps, we will create a more maintainable, flexible, and extensible framework.

The most important aspect of this migration is that the plugin system remains completely transparent to end users. They will continue to interact with the PepperPy class and its fluent API, without needing to understand or directly use the plugin architecture. Internal factory functions may use the plugin system, but these details are hidden from the user.

The benefits of this migration include:
1. **Reduced Core Size**: The core package contains only essential code
2. **Independent Provider Development**: Providers can evolve independently
3. **On-demand Dependencies**: Only required dependencies are installed
4. **Simplified Maintenance**: Updates to providers don't require core changes
5. **Community Extensions**: Third parties can easily create new providers
6. **Simplified User Experience**: Users interact only with the PepperPy class

By implementing this plan, we'll set PepperPy on a path for sustainable growth and wider adoption.

**IMPORTANT REMINDER**: All code, comments, and documentation MUST be written in English. 