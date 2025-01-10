# Configuration System

PepperPy AI provides a flexible and extensible configuration system for managing settings across all components.

## Overview

The configuration system provides:
- Hierarchical configuration
- Environment variable support
- Type-safe settings
- Configuration validation
- Default values

## Core Components

### Base Configuration

The foundation of all configurations:

```python
from pepperpy_ai.config import Config, BaseConfig

class CustomConfig(BaseConfig):
    """Custom configuration implementation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self) -> None:
        """Validate configuration."""
        self._validate_required_fields()
        self._validate_field_types()
```

### Configuration Types

Different configuration types for different components:

```python
from pepperpy_ai.config import (
    AgentConfig,
    ProviderConfig,
    TeamConfig,
    ClientConfig
)

# Agent configuration
agent_config = AgentConfig(
    agent_type="development",
    temperature=0.7
)

# Provider configuration
provider_config = ProviderConfig(
    provider="openai",
    api_key="your-api-key"
)

# Team configuration
team_config = TeamConfig(
    team_type="autogen",
    max_steps=10
)

# Client configuration
client_config = ClientConfig(
    timeout=30,
    retries=3
)
```

## Configuration Features

### Environment Variables

Load configuration from environment:

```python
from pepperpy_ai.config import EnvConfig

class AppConfig(EnvConfig):
    """Application configuration from environment."""
    
    @classmethod
    def from_env(cls):
        return cls(
            api_key=cls.get_env("PEPPERPY_API_KEY"),
            provider=cls.get_env("PEPPERPY_PROVIDER", default="openai"),
            debug=cls.get_env_bool("PEPPERPY_DEBUG", default=False)
        )
```

### Configuration Validation

```python
from pepperpy_ai.config import ConfigValidator
from pydantic import BaseModel, Field

class ConfigModel(BaseModel):
    """Configuration validation model."""
    
    api_key: str = Field(..., min_length=32)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(100, gt=0)

class ValidatedConfig(Config):
    """Configuration with validation."""
    
    def validate(self):
        model = ConfigModel(**self.__dict__)
        self.__dict__.update(model.dict())
```

### Module Configuration

```python
from pepperpy_ai.config import ModuleConfig

class TextProcessorConfig(ModuleConfig):
    """Text processor module configuration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = kwargs.get("chunk_size", 1000)
        self.overlap = kwargs.get("overlap", 100)
        self.language = kwargs.get("language", "en")
```

## Best Practices

1. **Configuration Management**
   - Use environment variables for sensitive data
   - Provide sensible defaults
   - Validate all settings

2. **Type Safety**
   - Use type hints
   - Validate types at runtime
   - Convert types appropriately

3. **Security**
   - Secure sensitive data
   - Use environment variables
   - Validate input data

4. **Flexibility**
   - Allow runtime changes
   - Support multiple sources
   - Enable overrides

## Environment Variables

Standard environment variables:

```bash
# Core settings
PEPPERPY_API_KEY=your-api-key
PEPPERPY_PROVIDER=openai
PEPPERPY_DEBUG=false

# Agent settings
PEPPERPY_AGENT_TYPE=development
PEPPERPY_AGENT_TEMPERATURE=0.7

# Provider settings
PEPPERPY_OPENAI_API_KEY=your-openai-key
PEPPERPY_ANTHROPIC_API_KEY=your-anthropic-key

# Team settings
PEPPERPY_TEAM_TYPE=autogen
PEPPERPY_TEAM_MAX_STEPS=10
```

## Examples

### Custom Configuration

```python
from pepperpy_ai.config import Config

class AppConfig(Config):
    """Application configuration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Core settings
        self.debug = kwargs.get("debug", False)
        self.log_level = kwargs.get("log_level", "INFO")
        
        # API settings
        self.api_key = kwargs["api_key"]
        self.api_version = kwargs.get("api_version", "v1")
        
        # Validate
        self.validate()
```

### Configuration Loading

```python
from pepperpy_ai.config import ConfigLoader

async def load_config():
    loader = ConfigLoader()
    
    # Load from multiple sources
    config = await loader.load(
        env=True,
        file="config.yaml",
        overrides={
            "debug": True
        }
    )
    
    return config
```

### Configuration Inheritance

```python
from pepperpy_ai.config import BaseConfig

class BaseServiceConfig(BaseConfig):
    """Base service configuration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeout = kwargs.get("timeout", 30)
        self.retries = kwargs.get("retries", 3)

class APIServiceConfig(BaseServiceConfig):
    """API service configuration."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs["api_key"]
        self.base_url = kwargs["base_url"]
``` 