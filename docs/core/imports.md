# Unified Import System

## Overview

The unified import system provides a centralized way to manage Python imports with features like:
- Efficient caching and lazy loading
- Circular import detection
- Import profiling and metrics
- Dependency tracking

## Components

### Import Manager

The `ImportManager` is the main interface for managing imports:

```python
from pepperpy.core.imports.unified import get_import_manager

# Get the global manager instance
manager = get_import_manager()

# Register and import a module
metadata = manager.register_module("my_module")

# Lazy import a module
module = manager.lazy_import("my_module")

# Get module dependencies
deps = manager.get_dependencies("my_module")

# Check for circular imports
chain = manager.check_circular_imports("my_module")

# Get import statistics
stats = manager.get_import_stats("my_module")
```

### Import Cache

The `ImportCache` provides efficient module caching:

```python
from pepperpy.core.imports.unified import ImportCache

# Create a cache with limits
cache = ImportCache(
    max_size=1024 * 1024 * 100,  # 100MB
    max_entries=1000,
    ttl=3600,  # 1 hour
)

# Cache a module
cache.set("my_module", module, metadata)

# Get cached module
cached = cache.get("my_module")

# Invalidate cache entry
cache.invalidate("my_module")

# Get cache statistics
stats = cache.get_cache_stats()
```

### Import Types

The system supports different import types:

```python
from pepperpy.core.imports.unified import ImportType

# Direct import (loaded immediately)
metadata = manager.register_module("my_module", ImportType.DIRECT)

# Lazy import (loaded on first use)
module = manager.lazy_import("my_module")

# Conditional import (loaded based on conditions)
metadata = manager.register_module("my_module", ImportType.CONDITIONAL)
```

### Error Handling

The system provides specific error types:

```python
from pepperpy.core.imports.unified import (
    ImportError,
    CircularImportError,
    ImportValidationError,
)

try:
    manager.register_module("my_module")
except CircularImportError as e:
    print(f"Circular import detected: {e.chain}")
except ImportValidationError as e:
    print(f"Validation failed: {e}")
except ImportError as e:
    print(f"Import failed: {e}")
```

## Best Practices

1. **Use Lazy Imports**:
   ```python
   # Instead of
   import heavy_module
   
   # Use
   heavy_module = manager.lazy_import("heavy_module")
   ```

2. **Monitor Import Statistics**:
   ```python
   stats = manager.get_all_stats()
   print(f"Total modules: {stats['total_modules']}")
   print(f"Total size: {stats['total_size']} bytes")
   ```

3. **Handle Circular Imports**:
   ```python
   # Check before importing
   if not manager.check_circular_imports("my_module"):
       module = manager.register_module("my_module")
   ```

4. **Use Import Validation**:
   ```python
   # Validate before using
   if manager.validate_imports("my_module"):
       module = manager.register_module("my_module")
   ```

5. **Configure Cache Appropriately**:
   ```python
   # Adjust cache settings based on your needs
   cache = ImportCache(
       max_size=your_size_limit,
       max_entries=your_entry_limit,
       ttl=your_ttl,
   )
   ```

## Migration Guide

### From Direct Imports

```python
# Before
import my_module
from my_package import my_module

# After
from pepperpy.core.imports.unified import get_import_manager

manager = get_import_manager()
my_module = manager.lazy_import("my_module")
```

### From Custom Import Systems

```python
# Before
class MyImportManager:
    def __init__(self):
        self.modules = {}
    
    def import_module(self, name):
        if name not in self.modules:
            self.modules[name] = importlib.import_module(name)
        return self.modules[name]

# After
from pepperpy.core.imports.unified import get_import_manager

manager = get_import_manager()
module = manager.register_module(name)
```

## Performance Considerations

1. **Cache Size**:
   - Set appropriate cache limits based on memory constraints
   - Monitor cache statistics to optimize settings

2. **Lazy Loading**:
   - Use lazy imports for modules not needed at startup
   - Consider startup time vs first-use time tradeoffs

3. **Memory Usage**:
   - Monitor memory usage through import statistics
   - Use cache cleanup to manage memory pressure

4. **Validation**:
   - Validation adds overhead but prevents issues
   - Consider disabling validation in production if needed

## Security Considerations

1. **Input Validation**:
   - Always validate module names
   - Use allowlist/blocklist for module imports

2. **Error Handling**:
   - Catch and handle import errors appropriately
   - Log security-relevant import failures

3. **Resource Limits**:
   - Set appropriate cache size limits
   - Monitor and limit memory usage

4. **Access Control**:
   - Implement module import restrictions
   - Log sensitive module imports

## Troubleshooting

1. **Circular Imports**:
   ```python
   # Check for circular dependencies
   chain = manager.check_circular_imports("my_module")
   if chain:
       print(f"Circular import chain: {' -> '.join(chain)}")
   ```

2. **Cache Issues**:
   ```python
   # Check cache statistics
   stats = cache.get_cache_stats()
   print(f"Cache hit ratio: {stats['hit_ratio']}")
   
   # Clear cache if needed
   cache.invalidate("my_module")
   ```

3. **Memory Issues**:
   ```python
   # Monitor memory usage
   stats = manager.get_all_stats()
   print(f"Total memory used: {stats['total_size']} bytes")
   ```

4. **Import Failures**:
   ```python
   try:
       module = manager.register_module("my_module")
   except ImportError as e:
       print(f"Import failed: {e}")
       print(f"Module stats: {manager.get_import_stats('my_module')}")
   ```
