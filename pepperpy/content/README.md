# Content Module (DEPRECATED)

> ⚠️ **DEPRECATED**: This module is deprecated and will be removed in a future version. Please use the `pepperpy.synthesis` module instead.

## Migration Guide

The functionality previously provided by this module has been moved to the `pepperpy.synthesis` module:

| Old Path | New Path |
|----------|----------|
| `pepperpy.content.synthesis.processors` | `pepperpy.synthesis.processors` |
| `pepperpy.content.synthesis.generators` | `pepperpy.synthesis.generators` |
| `pepperpy.content.synthesis.optimizers` | `pepperpy.synthesis.optimizers` |

### Using the Migration Helper

The `MigrationHelper` class in the `pepperpy.synthesis` module can assist with migrating your code:

```python
from pepperpy.synthesis import MigrationHelper

# Analyze code for legacy imports
legacy_imports = MigrationHelper.detect_legacy_imports(your_code)

# Get suggested replacements
replacements = MigrationHelper.suggest_replacements(your_code)

# Apply replacements automatically
updated_code = MigrationHelper.apply_replacements(your_code)
```

### Example Migration

#### Before:

```python
from pepperpy.content.synthesis.processors import TextProcessor
from pepperpy.content import AudioProcessor

processor = TextProcessor()
result = processor.process_text("Hello world")
```

#### After:

```python
from pepperpy.synthesis.processors import TextProcessor
from pepperpy.synthesis import AudioProcessor

processor = TextProcessor()
result = processor.process_text("Hello world")
```

## Features Now Available in Synthesis

The `pepperpy.synthesis` module provides a comprehensive set of tools for content generation and processing:

- **Processors**: `AudioProcessor`, `ImageProcessor`, `TextProcessor`
- **Generators**: `AudioGenerator`, `ImageGenerator`, `TextGenerator`
- **Optimizers**: `AudioOptimizer`, `ImageOptimizer`, `TextOptimizer`

For more information, please refer to the [Synthesis Module Documentation](../synthesis/README.md). 