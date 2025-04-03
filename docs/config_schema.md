# PepperPy Configuration Schema

This document describes the configuration schema for PepperPy, focusing on the plugin system and how to configure different types of plugins.

## Configuration File Structure

The main configuration file (`config.yaml`) is structured into several sections:

```yaml
# Main application configuration
app_name: PepperPy
app_version: 0.1.0
debug: true

# Component configurations (logging, database, etc.)
logging:
  level: DEBUG
  format: console

# Provider configurations (list format)
providers:
  - type: llm
    name: openai
    config:
      model: gpt-4

# Plugin-specific configurations (nested format)
plugins:
  rag:
    sqlite:
      database_path: ./data/rag.db
  
  supabase:
    url: https://your-project.supabase.co

# Community plugins namespace
community_plugins:
  org_name/plugin_name:
    config:
      option1: value1
```

## Provider Configuration

The `providers` section uses a list format to define available providers and their basic configurations:

```yaml
providers:
  - type: llm  # Plugin type
    name: openai  # Provider name
    default: true  # Whether this is the default provider for the type
    key:  # API key configuration
      env_var: OPENAI_API_KEY  # Environment variable to fetch the key from
      required: true  # Whether the key is required
    config:  # Provider-specific configuration
      model: gpt-4  # Configuration values
      temperature: 0.7
```

This section is primarily used for registering providers and their basic configurations. For more detailed provider-specific settings, use the `plugins` section.

## Plugin-Specific Configuration

The `plugins` section uses a nested structure to organize plugin configurations by type and name:

```yaml
plugins:
  # Type-level configuration
  rag:
    # Provider-level configuration
    sqlite:
      database_path: ./data/rag/sqlite.db
      embedding_dim: 384
    
    faiss:
      index_path: ./data/rag/faiss
      dimension: 1536
  
  # Standalone plugin configuration
  supabase:
    url:
      env_var: SUPABASE_URL
    key:
      env_var: SUPABASE_KEY
    options:
      auto_refresh_token: true
```

Key points:
- First level is the plugin type or name (`rag`, `supabase`)
- Second level is the provider name for typed plugins (`sqlite`, `faiss`)
- Configuration options are nested under these levels

### Accessing Plugin Configuration

Providers can access their configuration as follows:

```python
class SQLiteRAGProvider(RAGProvider, ProviderPlugin):
    # Type-annotated config attributes
    database_path: str = "./data/rag/sqlite.db"
    embedding_dim: int = 384
    
    async def initialize(self) -> None:
        # Access configuration through self attributes
        self.conn = sqlite3.connect(self.database_path)
        # Or alternatively
        db_path = self.get_config("database_path")
```

## Community Plugins

The `community_plugins` section provides a namespace for community-developed plugins:

```yaml
community_plugins:
  org_name/plugin_name:
    key:
      env_var: PLUGIN_API_KEY
    config:
      option1: value1
      option2: value2
```

Community plugins should use a namespaced format (`org_name/plugin_name`) to avoid conflicts with core plugins or other community plugins.

## Environment Variables and Secrets

For sensitive information like API keys, use environment variable references:

```yaml
plugins:
  openai:
    api_key:
      env_var: OPENAI_API_KEY
      required: true
```

This will look for the `OPENAI_API_KEY` environment variable and use its value.

## Configuration Hierarchy and Overrides

Configuration is loaded in the following order (later sources override earlier ones):

1. Default values defined in the plugin class
2. Values from `providers` section in config.yaml
3. Values from `plugins` section in config.yaml
4. Values from environment variables
5. Values provided directly when creating a provider instance

This allows for flexible configuration management where defaults can be overridden as needed.

## Dynamic Configuration

Plugins can also be configured dynamically at runtime:

```python
provider = await create_provider_instance(
    "rag", 
    "sqlite",
    database_path="/custom/path/db.sqlite",
    embedding_dim=512
)
```

These values will override any values from the configuration file or environment variables.

## Best Practices

1. **Plugin Namespace**: Always use a unique namespace for community plugins
2. **Configuration Validation**: Define a config schema in your plugin.yaml
3. **Default Values**: Provide sensible defaults for all configuration options
4. **Documentation**: Document all configuration options in your plugin.yaml
5. **Environment Variables**: Use environment variables for sensitive information
6. **Configuration Types**: Use appropriate types for configuration values (str, int, bool)

## Conclusion

The PepperPy configuration system provides a flexible way to configure plugins at multiple levels, from system-wide defaults to plugin-specific settings to runtime overrides. This allows for both simplicity for basic usage and flexibility for advanced use cases. 