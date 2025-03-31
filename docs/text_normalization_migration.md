# Text Normalization System Migration Guide

This guide explains how to migrate from the monolithic text normalization implementation to the new plugin-based architecture.

## Overview

The PepperPy text normalization system has been refactored to use a plugin-based architecture, providing several benefits:

1. **Modularity**: Each text normalization implementation can be provided as a plugin
2. **Extensibility**: New normalizers can be added without modifying core code
3. **Dependency management**: Heavy dependencies are isolated in specific plugins
4. **Configuration flexibility**: Each normalizer can have its own configuration options

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from pepperpy.content_processing.processors.text_normalization import TextNormalizer
```

**After:**
```python
from pepperpy.content_processing.processors.text_normalization_base import (
    TextNormalizer, BaseTextNormalizer, TextNormalizerRegistry
)
```

### Step 2: Replace Direct Instantiation with Registry or Plugin Manager

**Before:**
```python
normalizer = TextNormalizer()
normalized_text = normalizer.normalize(text)
```

**After (using registry):**
```python
# Using the registry directly
normalizer = TextNormalizerRegistry.create("base")
normalized_text = normalizer.normalize(text)

# Or using the plugin system
normalizer = plugin_manager.create_provider("text_normalization", "basic")
await normalizer.initialize()
normalized_text = normalizer.normalize(text)
await normalizer.cleanup()
```

### Step 3: Update Custom Normalizers

If you have custom normalizer implementations, convert them to plugins:

1. Create a new plugin directory: `plugins/text_normalization_myservice/`
2. Create the required plugin files:
   - `plugin.yaml`: Plugin metadata and documentation
   - `provider.py`: Implementation of your normalizer
   - `requirements.txt`: Dependencies for your normalizer
   - `__init__.py`: Export the `create_provider` function

Example implementation:

```python
# plugins/text_normalization_myservice/provider.py
from pepperpy.content_processing.processors.text_normalization_base import BaseTextNormalizer

class MyServiceNormalizer(BaseTextNormalizer):
    """Custom text normalizer implementation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Custom initialization
        
    async def initialize(self):
        # Initialize resources
        self.initialized = True
        
    async def cleanup(self):
        # Clean up resources
        self.initialized = False
        
    def normalize(self, text):
        # Custom normalization logic
        # You can also call the base implementation
        text = super().normalize(text)
        # Apply additional transformations
        return text

# Provider factory function
def create_provider(**kwargs):
    return MyServiceNormalizer(**kwargs)
```

### Step 4: Register Custom Normalizers

To make your normalizer available through the registry:

```python
from pepperpy.content_processing.processors.text_normalization_base import TextNormalizerRegistry
from plugins.text_normalization_myservice.provider import MyServiceNormalizer

# Register your normalizer
TextNormalizerRegistry.register("myservice", MyServiceNormalizer)
```

## Available Normalizers

The following normalizers are available:

1. **base**: Provides basic text normalization without external dependencies
2. **basic**: Plugin implementation of the base normalizer
3. **spacy**: Uses the spaCy library for advanced linguistic normalization (optional plugin)
4. **nltk**: Uses NLTK for language-specific normalization (optional plugin)

## Configuration Options

All normalizers support these basic configuration options:

- `transformations`: List of transformation methods to apply
- `custom_patterns`: Custom regex patterns for text cleaning
- `custom_replacements`: Custom character replacements
- `language`: Language code for language-specific processing

Example:

```python
normalizer = TextNormalizerRegistry.create("base", 
    transformations=["strip_whitespace", "normalize_unicode", "lowercase"],
    custom_replacements={"-": "_", ":": ""}
)
```

## Standard Transformations

Available transformation methods:

- `strip_whitespace`: Remove leading and trailing whitespace
- `normalize_unicode`: Normalize Unicode characters
- `normalize_whitespace`: Replace multiple whitespace with single space
- `remove_control_chars`: Remove control characters
- `replace_chars`: Replace special characters with standard ones
- `lowercase`: Convert text to lowercase
- `remove_punctuation`: Remove punctuation
- `remove_numbers`: Remove numbers
- `fix_encoding`: Fix common encoding issues 