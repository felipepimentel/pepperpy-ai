# Migrating to YAML Configuration

This document provides guidance for migrating from the previous environment variable-based configuration to the new YAML configuration system in PepperPy.

## Overview of Changes

PepperPy has transitioned from using environment variables for all configuration to a YAML-based configuration system with environment variable references for sensitive data. This change provides:

1. Better organization of configuration
2. Support for complex data structures (lists, nested objects)
3. Environment-specific overrides
4. Clearer separation of sensitive credentials and configuration
5. Stronger type validation and defaults

## Migration Steps

### Step 1: Create a config.yaml File

Create a `config.yaml` file in your project root with your configuration:

```yaml
# Application core settings
app_name: PepperPy
app_version: 0.1.0
debug: true

# Component configurations
logging:
  level: DEBUG
  
# Security settings (referencing environment variables)
security:
  secret_key:
    env_var: PEPPERPY_SECRET_KEY
    required: true

# Provider settings
providers:
  - type: llm
    name: openai
    default: true
    key:
      env_var: OPENAI_API_KEY
```

### Step 2: Move API Keys to .env

Your `.env` file should now contain only sensitive credentials:

```
# .env file - ONLY sensitive credentials
PEPPERPY_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-api-key-here
ELEVENLABS_API_KEY=your-tts-api-key-here
```

### Step 3: Update Code to Use New API

If you were directly accessing environment variables, update your code to use the new configuration API:

**Before:**
```python
import os

api_key = os.environ.get("PEPPERPY_LLM__OPENAI_API_KEY")
model = os.environ.get("PEPPERPY_LLM__MODEL", "gpt-3.5-turbo")
```

**After:**
```python
from pepperpy.core.config import get_provider_api_key, get_component_config

api_key = get_provider_api_key("llm", "openai")
llm_config = get_component_config("llm")
model = llm_config.get("model", "gpt-3.5-turbo")
```

## Environment Variable Mapping

Here's how the old environment variables map to the new YAML configuration:

| Old Environment Variable | New YAML Configuration |
|--------------------------|------------------------|
| `PEPPERPY_APP__NAME` | `app_name: PepperPy` |
| `PEPPERPY_APP__VERSION` | `app_version: 0.1.0` |
| `PEPPERPY_APP__DEBUG` | `debug: true` |
| `PEPPERPY_LOGGING__LEVEL` | `logging: { level: DEBUG }` |
| `PEPPERPY_SECURITY__SECRET_KEY` | `security: { secret_key: { env_var: PEPPERPY_SECRET_KEY } }` |
| `PEPPERPY_LLM__PROVIDER` | `llm: { provider: openai }` |
| `PEPPERPY_LLM__OPENAI_API_KEY` | `providers: [{ type: llm, name: openai, key: { env_var: OPENAI_API_KEY } }]` |

## Backward Compatibility

The system maintains backward compatibility with the previous environment variable-based configuration. If a configuration value isn't found in the YAML file, it will fall back to checking the equivalent environment variable.

However, we recommend migrating to the new system for all new development to take advantage of its improved features.

## Testing Your Configuration

PepperPy includes a configuration example file that shows the currently loaded configuration:

```bash
python -m examples.config_example
```

This will display the loaded configuration, including which providers have valid API keys.

## Common Issues

### Missing API Keys

If your providers aren't finding API keys, make sure:
1. The provider is correctly defined in `config.yaml`
2. The API key environment variable is set and correctly referenced
3. You're using the new API to access the configuration

### Configuration Not Loading

If your configuration isn't loading:
1. Make sure your `config.yaml` file is in the current directory
2. Check the file for YAML syntax errors
3. Verify that all required fields have values

### Backward Compatibility Issues

If you're having issues with backward compatibility:
1. Ensure you're using the most recent version of PepperPy
2. Set both the new and old environment variables during the transition period 