# Plugin Services

The PepperPy framework provides a service system that enables plugins to offer well-defined APIs to other plugins. This allows for structured communication while maintaining proper access control and dependency management.

## Overview

The service system allows plugins to:

- Register methods as services with clear access permissions
- Call services from other plugins based on dependency relationships
- Enforce access control through service scopes
- Provide both synchronous and asynchronous services
- Attach metadata to services for additional context

Services are a powerful way to build modular, decoupled plugins that can collaborate while maintaining clear boundaries.

## Service Scopes

Services can be registered with one of three scopes that determine which plugins can access them:

| Scope | Description |
|-------|-------------|
| `ServiceScope.PUBLIC` | Available to all plugins in the system |
| `ServiceScope.DEPENDENT` | Only available to plugins that declare a dependency on the plugin offering the service |
| `ServiceScope.PRIVATE` | Only available to the plugin that registered the service (internal use) |

## Declaring Services

To declare a method as a service, use the `@service` decorator:

```python
from pepperpy.plugin import PepperpyPlugin, service, ServiceScope

class MyPlugin(PepperpyPlugin):
    
    @service("add", scope=ServiceScope.PUBLIC)
    def add_numbers(self, a: int, b: int) -> int:
        """Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of the two numbers
        """
        return a + b
        
    @service("multiply", scope=ServiceScope.DEPENDENT)
    def multiply_numbers(self, a: int, b: int) -> int:
        """Multiply two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Product of the two numbers
        """
        return a * b
        
    @service("internal_calc", scope=ServiceScope.PRIVATE)
    def complex_calculation(self, x: float) -> float:
        """Internal calculation method.
        
        This is only available to this plugin.
        
        Args:
            x: Input value
            
        Returns:
            Calculated result
        """
        return x ** 2 + 3 * x - 1
```

The decorator parameters include:
- `name`: The name of the service (required)
- `scope`: The service scope (defaults to `ServiceScope.PUBLIC` if not specified)
- `metadata`: Optional dictionary with additional information about the service

## Calling Services

To call a service from another plugin, use the `call_service` function:

```python
from pepperpy.plugin import PepperpyPlugin, call_service

class ConsumerPlugin(PepperpyPlugin):
    def calculate(self):
        # Call a service from another plugin
        result = call_service(
            "math_plugin",  # provider plugin ID
            "add",          # service name
            self.plugin_id, # consumer plugin ID
            5, 3            # service parameters
        )
        return result  # Returns 8
```

For async services, use the `await_service` function:

```python
async def process_data(self):
    # Call an async service
    result = await await_service(
        "data_plugin",   # provider plugin ID
        "fetch_data",    # service name
        self.plugin_id,  # consumer plugin ID
        "user123"        # service parameters
    )
    return result
```

## Service Dependencies

Services respect the dependency relationships between plugins. To access a service with `DEPENDENT` scope, the consumer plugin must declare a dependency on the provider plugin:

```python
class ConsumerPlugin(PepperpyPlugin):
    # Declare dependency on the math plugin
    __dependencies__ = {
        "math_plugin": DependencyType.REQUIRED
    }
    
    def calculate(self):
        # Can access DEPENDENT scope services because of the dependency
        result = call_service("math_plugin", "multiply", self.plugin_id, 5, 3)
        return result  # Returns 15
```

If a plugin tries to access a service it doesn't have permission for, a `ServiceAccessError` will be raised.

## Service Errors

The service system defines several error types to handle common failure scenarios:

- `ServiceError`: Base class for all service-related errors
- `ServiceNotFoundError`: Raised when the requested service doesn't exist
- `ServiceAccessError`: Raised when a plugin tries to access a service it doesn't have permission for

## Service Metadata

You can attach metadata to services to provide additional context:

```python
@service("dangerous_operation", scope=ServiceScope.PUBLIC, metadata={"admin_only": True})
def delete_all_data(self):
    # Implementation...
```

Metadata can be used by consumers to make decisions about how to use the service.

## Asynchronous Services

To provide an asynchronous service, simply define the service method as an async function:

```python
@service("fetch_data", scope=ServiceScope.PUBLIC)
async def fetch_external_data(self, user_id: str) -> dict:
    """Fetch data from an external source.
    
    Args:
        user_id: User identifier
        
    Returns:
        User data
    """
    # Simulate async operation
    await asyncio.sleep(1)
    return {"id": user_id, "name": "Example User"}
```

Consumers must use `await_service` to call async services.

## Best Practices

### Service Design

1. **Clear naming**: Choose descriptive service names that reflect their purpose
2. **Appropriate scoping**: Use the most restrictive scope that meets your needs
3. **Comprehensive documentation**: Document each service with clear parameter descriptions and return values
4. **Error handling**: Provide clear error messages when services fail
5. **Versioning**: Consider including version information in service metadata

### Dependency Management

1. **Minimize dependencies**: Only declare dependencies that are truly needed
2. **Fallback mechanisms**: For optional dependencies, implement fallbacks when services aren't available
3. **Proper cleanup**: Ensure services handle cleanup properly when plugins are unloaded

### Performance

1. **Keep services lightweight**: Avoid long-running operations in synchronous services
2. **Use async for I/O**: Make services asynchronous when they perform I/O operations
3. **Cache results**: Consider caching for expensive service calls

## API Reference

### Core Functions

- `service(name, scope=ServiceScope.PUBLIC, metadata=None)`: Decorator to register a method as a service
- `call_service(provider_id, service_name, consumer_id, *args, **kwargs)`: Call a synchronous service
- `await_service(provider_id, service_name, consumer_id, *args, **kwargs)`: Call an asynchronous service

### Service Scopes

- `ServiceScope.PUBLIC`: Available to all plugins
- `ServiceScope.DEPENDENT`: Available only to plugins that declare a dependency
- `ServiceScope.PRIVATE`: Available only to the plugin that defined the service

### Error Classes

- `ServiceError`: Base class for all service-related errors
- `ServiceNotFoundError`: Raised when a service doesn't exist
- `ServiceAccessError`: Raised when a plugin tries to access a service it doesn't have permission for 