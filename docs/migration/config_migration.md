# Configuration System Migration Guide

This guide helps you migrate from the old configuration system to the new unified configuration system.

## Overview of Changes

The new unified configuration system provides several improvements:
- Centralized configuration management
- Better type safety and validation
- Simplified configuration sources
- Improved lifecycle hooks
- Cleaner API

## Migration Steps

### 1. Update Imports

Old imports:
```python
from pepperpy.core.config import (
    ConfigurationManager,
    ConfigSource,
    EnvSource,
    FileSource,
    YAMLSource,
    JSONSource,
    CLISource,
    ConfigWatcher,
)
```

New imports:
```python
from pepperpy.core.config import (
    PepperpyConfig,
    UnifiedConfig,
    ConfigSource,
    ConfigState,
    ConfigHook,
    initialize_config,
    update_config,
    add_config_hook,
    remove_config_hook,
)
```

### 2. Configuration Model

Replace custom configuration classes with the new `PepperpyConfig` model:

Old:
```python
class CustomConfig(BaseConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
        
    def validate(self) -> None:
        self._validate_required_fields()
```

New:
```python
from pepperpy.core.config import PepperpyConfig

# Use the standard configuration model
config = await initialize_config()

# Or extend it for custom needs
class CustomConfig(PepperpyConfig):
    extra_setting: str = Field(default="value")
    
config_manager = UnifiedConfig(CustomConfig)
await config_manager.initialize()
```

### 3. Configuration Loading

Old:
```python
# Manual configuration loading
config = AutoConfig.from_env()
config.update_from_file("config.yml")
```

New:
```python
# Automatic configuration loading
config = await initialize_config()

# Or with a specific file
from pathlib import Path
config = await initialize_config(Path("config.yml"))
```

### 4. Configuration Updates

Old:
```python
config_manager = ConfigManager()
config_manager.update({
    "setting": "value"
})
```

New:
```python
await update_config({
    "setting": "value"
})
```

### 5. Lifecycle Hooks

Old:
```python
class ConfigWatcher:
    def on_change(self, config):
        pass

watcher = ConfigWatcher()
config_manager.add_watcher(watcher)
```

New:
```python
def on_update(config: PepperpyConfig) -> None:
    print(f"Config updated: {config}")

add_config_hook("on_update", on_update)

# Source-specific hooks
add_config_hook(
    "on_load",
    lambda c: print("Loaded from env"),
    source=ConfigSource.ENV
)
```

### 6. Environment Variables

The environment variable handling remains similar but is now more consistent:

```python
# All environment variables must start with PEPPERPY_
PEPPERPY_DEBUG=true
PEPPERPY_TIMEOUT=30.0
PEPPERPY_PROVIDER=openai
PEPPERPY_API_KEY=your-key

# Nested configuration uses double underscores
PEPPERPY_PROVIDER_CONFIGS__OPENAI__MODEL=gpt-4
```

### 7. Configuration Files

Configuration files (YAML) remain supported with a consistent structure:

```yaml
# config.yml
debug: true
provider: openai
timeout: 30.0
provider_configs:
  openai:
    model: gpt-4
```

## Breaking Changes

1. Removed Classes:
   - `AutoConfig`
   - `ConfigManager`
   - `ConfigWatcher`
   - Individual source classes (`EnvSource`, `FileSource`, etc.)

2. Changed Behavior:
   - Configuration loading is now asynchronous
   - Configuration is immutable after loading
   - All configuration updates go through the unified manager
   - Stricter type checking and validation

## Best Practices

1. Use the global configuration manager when possible:
   ```python
   from pepperpy.core.config import config_manager
   
   if config_manager.config.debug:
       # Do something
   ```

2. Handle configuration errors explicitly:
   ```python
   from pepperpy.core.config import ConfigurationError
   
   try:
       config = await initialize_config()
   except ConfigurationError as e:
       logger.error(f"Configuration error: {e}")
       sys.exit(1)
   ```

3. Use type hints with configuration:
   ```python
   from pepperpy.core.config import PepperpyConfig
   
   def process_config(config: PepperpyConfig) -> None:
       timeout = config.timeout  # Type-safe access
   ```

4. Prefer environment variables for sensitive data:
   ```python
   # Don't store in config files
   api_key: your-key
   
   # Use environment variables
   PEPPERPY_API_KEY=your-key
   ```

## Deprecation Timeline

1. v1.0.0: Introduce new unified configuration system
2. v1.1.0: Mark old configuration system as deprecated
3. v2.0.0: Remove old configuration system

## Getting Help

If you encounter issues during migration:
1. Check the [Configuration API Reference](../api_reference/config/index.md)
2. File an issue on GitHub
3. Join our Discord community for support 