# Configuration Providers

This directory contains provider implementations for configuration capabilities in the PepperPy framework.

## Available Providers

- **Env Config Provider**: Implementation for environment variable-based configuration
- **File Config Provider**: Implementation for file-based configuration
- **Filesystem Config Provider**: Implementation for filesystem-based configuration
- **Secure Config Provider**: Implementation for secure configuration with encryption

## Usage

```python
from pepperpy.core.config.providers import EnvConfigProvider, FileConfigProvider, SecureConfigProvider

# Use environment variable provider
env_config = EnvConfigProvider(prefix="PEPPERPY_")
api_key = env_config.get("API_KEY")

# Use file-based provider
file_config = FileConfigProvider(file_path="config.yaml")
settings = file_config.get_all()

# Use secure provider
secure_config = SecureConfigProvider(key_path="secret.key")
password = secure_config.get_secure("DATABASE_PASSWORD")
```

## Adding New Providers

To add a new provider:

1. Create a new file in this directory
2. Implement the `ConfigProvider` interface
3. Register your provider in the `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/config/`. The move to this domain-specific location improves modularity and maintainability. 