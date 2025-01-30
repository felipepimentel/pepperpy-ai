# TASK-001: Core Configuration System

## Overview
Implement a centralized configuration system using Pydantic that will handle all configurable aspects of the system, from model parameters to environment settings. This system will be the foundation for all other components.

## Requirements

### Base Configuration
- [ ] Create `common/config.py` with base configuration class
- [ ] Implement environment variable support with Pydantic
- [ ] Add validation for all configuration parameters
- [ ] Support nested configurations for different components

### Configuration Components
- [ ] Agent Configuration
  ```python
  class AgentConfig(BaseSettings):
      model_type: str = "gpt-4"
      temperature: float = 0.7
      max_tokens: int = 1000
      timeout: int = 30
  ```
- [ ] Memory Configuration
  ```python
  class MemoryConfig(BaseSettings):
      vector_store_type: str = "faiss"
      embedding_size: int = 512
      cache_ttl: int = 3600
  ```
- [ ] Provider Configuration
  ```python
  class ProviderConfig(BaseSettings):
      enabled_providers: list[str] = ["openai", "local"]
      rate_limits: dict[str, int] = {"openai": 60}
  ```

### Environment Management
- [ ] Create `.env.example` template
- [ ] Implement configuration loading from files
- [ ] Add environment override capabilities
- [ ] Support different environments (dev, prod, test)

## Technical Notes

### Configuration Structure
```python
from pydantic import BaseSettings, Field

class PepperpyConfig(BaseSettings):
    """Root configuration class."""
    
    # Environment
    env: str = "development"
    debug: bool = False
    
    # Components
    agent: AgentConfig = Field(default_factory=AgentConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    
    class Config:
        env_prefix = "PEPPERPY_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Usage Example
```python
from pepperpy.common.config import config

# Access configuration
model = config.agent.model_type
embedding_size = config.memory.embedding_size

# Override in tests
with config.override({"agent": {"model_type": "test-model"}}):
    assert config.agent.model_type == "test-model"
```

### Environment Variables
```env
PEPPERPY_ENV=development
PEPPERPY_DEBUG=true
PEPPERPY_AGENT__MODEL_TYPE=gpt-4
PEPPERPY_MEMORY__EMBEDDING_SIZE=512
```

## Validation

### Configuration Loading
- Configuration loads successfully from defaults
- Environment variables override defaults
- Invalid configurations raise appropriate errors
- Nested configurations work correctly

### Type Safety
- All configuration values are properly typed
- Type validation works on assignment
- Pydantic validation rules are enforced

### Environment Handling
- `.env` file is properly loaded
- Environment variables take precedence
- Different environments work correctly

## Dependencies
- None (This is a foundational component)

## Notes
- Keep configuration immutable during runtime
- Document all configuration options
- Consider adding configuration schema export
- Plan for future extensibility 