# Plugin Dependency System

## Overview

The PepperPy plugin dependency system allows plugins to declare dependencies on other plugins, enabling:

- Ordering of plugin initialization
- Validation of required dependencies
- Detection of conflicting plugins
- Dependency-based relationships between plugins

## Dependency Types

The system supports four types of dependencies:

| Type | Description |
|------|-------------|
| `REQUIRED` | Plugin won't function without this dependency |
| `OPTIONAL` | Plugin can function without this dependency, but may have limited features |
| `ENHANCES` | Plugin is enhanced by this dependency, but doesn't require it |
| `CONFLICTS` | Plugin cannot function with this dependency present |

## Declaring Dependencies

Dependencies can be declared in two ways:

### 1. Class-level Declaration

Use the `__dependencies__` class variable:

```python
from pepperpy.plugin import PepperpyPlugin, DependencyType

class MyPlugin(PepperpyPlugin):
    __metadata__ = {
        "name": "my_plugin",
        "version": "1.0.0",
        "provider_type": "utility",
    }
    
    # Declare dependencies
    __dependencies__ = {
        "database": DependencyType.REQUIRED,
        "cache": DependencyType.OPTIONAL,
        "legacy_plugin": DependencyType.CONFLICTS,
    }
```

### 2. Using the `depends_on` Method

```python
from pepperpy.plugin import PepperpyPlugin, DependencyType

class MyPlugin(PepperpyPlugin):
    # Setup basic plugin
    ...

# Declare dependencies
MyPlugin.depends_on("database", DependencyType.REQUIRED)
MyPlugin.depends_on("cache", DependencyType.OPTIONAL)
```

## Validating Dependencies

PepperPy automatically validates dependencies when a plugin is initialized:

```python
# Inside your plugin's initialize method
def initialize(self) -> None:
    # Check dependencies first
    if not self.validate_dependencies():
        self.logger.warning("Initializing with unmet dependencies")
        
    # Continue with initialization
    super().initialize()
```

You can also manually check for missing dependencies and conflicts:

```python
missing_deps = plugin.check_dependencies()  # List of missing required dependencies
conflicts = plugin.check_conflicts()  # List of conflicting dependencies
```

## Resolving Load Order

The system can calculate the correct load order for a set of plugins based on their dependencies:

```python
from pepperpy.plugin import get_load_order

# Get the correct order to load these plugins
plugins_to_load = ["ui", "database", "api", "auth"]
load_order = get_load_order(plugins_to_load)

# Initialize plugins in the correct order
for plugin_id in load_order:
    initialize_plugin(plugin_id)
```

## Handling Circular Dependencies

The system detects circular dependencies and raises a `CircularDependencyError`:

```python
from pepperpy.plugin import get_load_order, CircularDependencyError

try:
    load_order = get_load_order(plugin_ids)
except CircularDependencyError as e:
    print(f"Circular dependency detected: {e.cycle}")
```

## API Reference

### Dependency Types

```python
class DependencyType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    ENHANCES = "enhances"
    CONFLICTS = "conflicts"
```

### Core Functions

| Function | Description |
|----------|-------------|
| `add_dependency(plugin_id, dependency_id, dependency_type)` | Add a dependency between plugins |
| `add_plugin(plugin_id)` | Register a plugin in the dependency system |
| `mark_loaded(plugin_id)` | Mark a plugin as loaded |
| `has_plugin(plugin_id)` | Check if a plugin is registered |
| `is_loaded(plugin_id)` | Check if a plugin is loaded |
| `get_dependencies(plugin_id)` | Get all dependencies for a plugin |
| `get_required_dependencies(plugin_id)` | Get required dependencies for a plugin |
| `get_optional_dependencies(plugin_id)` | Get optional dependencies for a plugin |
| `get_enhances_dependencies(plugin_id)` | Get enhances dependencies for a plugin |
| `get_conflicts_dependencies(plugin_id)` | Get conflicts dependencies for a plugin |
| `get_load_order(plugin_ids)` | Calculate load order for a list of plugins |
| `check_missing_dependencies(plugin_id)` | Check for missing required dependencies |
| `check_conflicts(plugin_id)` | Check for conflicting dependencies |
| `resolve_dependencies(plugin_ids)` | Resolve dependencies for a list of plugins |

### Error Classes

| Error | Description |
|-------|-------------|
| `DependencyError` | Base error for dependency issues |
| `CircularDependencyError` | Error when a circular dependency is detected |
| `MissingDependencyError` | Error when a required dependency is missing |
| `ConflictingDependencyError` | Error when a conflicting dependency is detected |

## Example: Plugin with Dependencies

```python
from pepperpy.plugin import PepperpyPlugin, DependencyType

class DatabasePlugin(PepperpyPlugin):
    __metadata__ = {
        "name": "database",
        "version": "1.0.0",
        "provider_type": "database",
    }
    
    # This plugin has no dependencies
    
class APIPlugin(PepperpyPlugin):
    __metadata__ = {
        "name": "api",
        "version": "1.0.0",
        "provider_type": "api",
    }
    
    # This plugin requires the database plugin
    __dependencies__ = {
        "database": DependencyType.REQUIRED,
    }
    
    def initialize(self) -> None:
        # Validate dependencies first
        if not self.validate_dependencies():
            self.logger.warning("Initializing with unmet dependencies")
            
        # Get the database plugin
        from pepperpy.plugin.registry import get_plugin
        self.db = get_plugin("database")
        
        # Continue with initialization
        super().initialize()
```

## Best Practices

1. **Minimize Required Dependencies**: Use `OPTIONAL` or `ENHANCES` when possible to increase flexibility.

2. **Avoid Deep Dependency Trees**: Keep dependency chains as short as possible.

3. **Use Conflicts Sparingly**: Only mark plugins as `CONFLICTS` when there are genuine incompatibilities.

4. **Validate Early**: Always validate dependencies at the start of the `initialize` method.

5. **Handle Missing Dependencies Gracefully**: When optional dependencies are missing, adjust functionality rather than failing.

6. **Document Dependencies**: Clearly document your plugin's dependencies in your plugin documentation. 