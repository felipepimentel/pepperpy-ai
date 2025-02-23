# Import Optimization System

The import optimization system provides advanced functionality for managing Python module imports efficiently. It includes features for caching, profiling, and dependency management.

## Features

### Import Profiling

The system tracks import performance metrics:
- Import duration
- Dependencies
- Error tracking
- Performance analysis

```python
from pepperpy.utils.imports_profiler import ImportProfiler

profiler = ImportProfiler()
profiler.start_import("my_module")
# ... import happens ...
profile = profiler.finish_import("my_module")
analysis = profiler.analyze_imports()
```

### Advanced Caching

The caching system includes:
- File modification tracking
- Path-based caching
- Module reloading support
- Dependency tracking

```python
from pepperpy.utils.imports_cache import ImportCache

cache = ImportCache()
cache.set("my_module", module)
cached_module = cache.get("my_module")  # Returns None if file modified
reloaded = cache.reload("my_module")
```

### Import Optimization

The main optimizer combines all features:
- Import hooks
- Circular import detection
- Dependency management
- Performance tracking

```python
from pepperpy.utils.imports_hook import ImportOptimizer
from pepperpy.utils.modules import ModuleManager

manager = ModuleManager()
optimizer = ImportOptimizer(manager)

# Register optimizer
import sys
sys.meta_path.insert(0, optimizer)

# Get import statistics
profiles = optimizer.get_import_profiles()
print(f"Total imports: {profiles['analysis']['total_imports']}")
print(f"Average duration: {profiles['analysis']['average_duration']:.3f}s")
```

## Usage

1. Create a module manager:
```python
from pepperpy.utils.modules import ModuleManager
manager = ModuleManager()
```

2. Create and register the optimizer:
```python
from pepperpy.utils.imports_hook import ImportOptimizer
optimizer = ImportOptimizer(manager)
sys.meta_path.insert(0, optimizer)
```

3. Import modules normally:
```python
import my_module  # Will be handled by optimizer
```

4. Check import performance:
```python
profiles = optimizer.get_import_profiles()
slow_imports = profiles["slow_imports"]
if slow_imports:
    print("Slow imports detected:", [p.module for p in slow_imports])
```

5. Reload modified modules:
```python
optimizer.reload_module("my_module")
# Or reload with dependencies:
reloaded = optimizer.reload_dependencies("my_module")
```

## Best Practices

1. Initialize the optimizer early in your application:
```python
def setup_import_optimization():
    manager = ModuleManager()
    optimizer = ImportOptimizer(manager)
    sys.meta_path.insert(0, optimizer)
    return optimizer
```

2. Monitor import performance:
```python
def check_import_performance(optimizer):
    profiles = optimizer.get_import_profiles()
    analysis = profiles["analysis"]
    if analysis["average_duration"] > 0.1:  # 100ms threshold
        logger.warning("Slow import performance detected")
        for profile in profiles["slow_imports"]:
            logger.warning(f"Slow import: {profile.module} ({profile.duration:.3f}s)")
```

3. Handle file modifications:
```python
def handle_file_change(optimizer, path):
    # Invalidate cached modules
    optimizer.invalidate_path(path)
    # Find dependent modules
    dependents = optimizer.get_dependent_modules(path)
    # Reload if needed
    for module in dependents:
        optimizer.reload_module(module)
```

## Error Handling

The system provides detailed error information:

```python
try:
    import my_module
except ImportError as e:
    profiles = optimizer.get_import_profiles()
    profile = profiles["profiles"].get("my_module")
    if profile and profile.errors:
        print("Import errors:", profile.errors)
```

## Performance Tips

1. Use lazy loading for optional dependencies:
```python
from pepperpy.utils.imports import lazy_import
optional_module = lazy_import("optional_module")
```

2. Monitor slow imports:
```python
def monitor_imports(optimizer):
    while True:
        time.sleep(60)  # Check every minute
        profiles = optimizer.get_import_profiles()
        for profile in profiles["slow_imports"]:
            if profile.duration > 1.0:  # 1 second threshold
                logger.critical(f"Very slow import: {profile.module}")
```

3. Optimize import paths:
```python
def optimize_import_paths():
    # Add commonly used paths to sys.path
    common_paths = ["/path/to/common/modules"]
    sys.path[:0] = common_paths
```

## Testing

The system includes comprehensive tests:

```bash
pytest tests/utils/test_imports.py
```

This will run tests for:
- Import caching
- Import profiling
- Module reloading
- Circular import detection
- Performance tracking 