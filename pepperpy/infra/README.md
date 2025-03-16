# PepperPy Infrastructure Module

This module provides infrastructure components for the PepperPy framework, including configuration management, telemetry, security, storage, logging, metrics, resilience, caching, connection pooling, data compression, serialization, and core utility functions.

## Components

### Utils (`utils.py`)

The utils module provides foundational utility functions used throughout the PepperPy framework.

Key components:
- ID and hash functions: `generate_id`, `generate_timestamp`, `hash_string`
- File operations: `load_json`, `save_json`, `get_file_extension`, `get_file_mime_type`, `get_file_size`
- String manipulation: `slugify`, `truncate_string`
- Validation: `is_valid_email`, `is_valid_url`
- Retry functionality: `retry`
- Object conversion: `dict_to_object`, `object_to_dict`

Example:
```python
from pepperpy.infra import generate_id, hash_string, load_json, save_json, retry

# Generate a unique ID with prefix
uid = generate_id(prefix="user_")  # e.g., "user_8f7d1a2b3c4d"

# Hash sensitive data
hashed_password = hash_string("my_password", algorithm="sha256")

# Load and save JSON data
config = load_json("config.json")
config["new_setting"] = "value"
save_json(config, "config.json")

# Use retry for unreliable operations
@retry(max_attempts=5, delay=1.0, backoff=2.0)
def fetch_external_api():
    # This function will be retried up to 5 times with exponential backoff
    response = make_external_request()
    return response
```

### Decorators (`decorators.py`)

The decorators module provides common function decorators for enhancing Python functions with cross-cutting concerns.

Key components:
- Retry patterns: `retry`, `async_retry`
- Timing utilities: `timed`, `async_timed`
- Deprecation warnings: `deprecated`
- Memoization: `memoize`, `async_memoize`
- Logging enhancements: `log_exceptions`, `async_log_exceptions`, `log_calls`
- Validation: `validate_arguments`

Example:
```python
from pepperpy.infra import (
    retry, async_retry, timed, async_timed, deprecated, 
    memoize, log_exceptions, log_calls
)

# Add retry logic to a function
@retry(max_retries=3, delay=1.0, backoff=2.0)
def call_external_api():
    # This will be retried up to 3 times with exponential backoff
    return requests.get("https://api.example.com/data")

# Add retry logic to an async function
@async_retry(max_retries=3, delay=1.0, backoff=2.0)
async def call_async_api():
    # This will be retried up to 3 times with exponential backoff
    async with aiohttp.ClientSession() as session:
        return await session.get("https://api.example.com/data")

# Time function execution
@timed()
def process_data(data):
    # This will log execution time
    return transform_data(data)

# Mark function as deprecated
@deprecated("Use new_function() instead")
def old_function():
    # Will issue a warning when called
    return legacy_implementation()

# Cache function results
@memoize
def expensive_computation(arg1, arg2):
    # Results are cached based on arguments
    return perform_complex_calculation(arg1, arg2)

# Log exceptions
@log_exceptions()
def risky_operation():
    # Exceptions will be logged before being raised
    return perform_risky_operation()

# Log function calls with arguments and results
@log_calls(log_args=True, log_result=True)
def important_function(arg1, arg2):
    # Will log call arguments and return value
    return process_inputs(arg1, arg2)
```

### Validation (`validation.py`)

The validation module provides utilities for validating data, including common validation functions, schema validation, and validation result handling.

Key components:
- Validation classes: `ValidationResult`, `ValidationError`, `Validator`, `FunctionValidator`, `SchemaValidator`
- String validation: `is_email`, `is_url`, `matches_pattern`, `min_length`, `max_length`
- Number validation: `is_positive`, `is_integer`, `min_value`, `max_value`, `value_between`
- Collection validation: `min_items`, `max_items`, `contains`, `unique_items`
- Type validation: `is_instance_of`, `is_string`, `is_dict`, `is_list`
- Composite validation: `all_of`, `any_of`, `none_of`, `not_`
- Validation utilities: `validate`, `validate_dict`

Example:
```python
from pepperpy.infra import (
    validate, validate_dict, ValidationResult, FunctionValidator,
    is_email, min_length, is_positive, all_of, any_of
)

# Validate a single value
email_validator = FunctionValidator(is_email, "Invalid email address")
result = validate("user@example.com", email_validator)
if result.is_valid:
    print("Email is valid")

# Create a complex validator
password_validator = all_of(
    min_length(8),
    lambda s: any(c.isupper() for c in s),
    lambda s: any(c.isdigit() for c in s)
)

# Validate a dictionary against a schema
user_schema = {
    "email": is_email,
    "name": min_length(2),
    "age": all_of(is_positive, lambda n: n < 120)
}

user_data = {
    "email": "user@example.com",
    "name": "John",
    "age": 30
}

result = validate_dict(user_data, user_schema)
if result.is_valid:
    # Use the validated data
    validated_user = result.validated_data
else:
    # Handle validation errors
    for error in result.errors:
        print(f"Error in {error.path}: {error.message}")
```

### Cache (`cache.py`)

The cache module provides advanced caching strategies with TTL and invalidation mechanisms for the PepperPy framework.

Key components:
- `InvalidationStrategy`: Strategies for invalidating cache entries
- `CacheInvalidator`: Invalidator for cache entries
- `AsyncCacheInvalidator`: Asynchronous invalidator for cache entries
- Decorators: `cached`, `async_cached`
- Utility functions: `clear_cache`, `invalidate_cache`, `initialize_cache`

Example:
```python
from pepperpy.infra import cached, async_cached, initialize_cache

# Initialize the cache system
initialize_cache(cache_type="memory")

# Use the cached decorator for synchronous functions
@cached(ttl=60)
def get_user(user_id: str) -> dict:
    # Expensive operation to get user data
    return {"id": user_id, "name": "John Doe"}

# Use the async_cached decorator for asynchronous functions
@async_cached(ttl=60)
async def get_user_async(user_id: str) -> dict:
    # Expensive operation to get user data
    return {"id": user_id, "name": "John Doe"}

# Invalidate a cache entry
from pepperpy.infra import invalidate_cache
invalidate_cache("user:123")

# Clear the cache
from pepperpy.infra import clear_cache
clear_cache()
```

### Compression (`compression.py`)

The compression module provides utilities for compressing and optimizing data, including various compression algorithms, serialization formats, and optimization strategies for large datasets.

Key components:
- `CompressionAlgorithm`: Enum defining compression algorithms (GZIP, ZLIB, LZMA, NONE)
- `SerializationFormat`: Enum defining serialization formats (JSON, MSGPACK, PICKLE, RAW)
- `CompressionLevel`: Enum defining compression levels (NONE, FAST, DEFAULT, BEST)
- `DataCompressor`: Core class for compressing and decompressing data
- `CompressedData`: Container for compressed data with metadata
- Specialized compressors: `JsonCompressor`, `NumpyCompressor`
- `DatasetOptimizer`: Utilities for optimizing large datasets

Example:
```python
from pepperpy.infra import compress_data, decompress_data, CompressionAlgorithm, SerializationFormat

# Compress data
compressed = compress_data(
    data={"key": "value"},
    algorithm=CompressionAlgorithm.GZIP,
    serialization=SerializationFormat.JSON,
)

# Decompress data
decompressed = decompress_data(
    data=compressed,
    algorithm=CompressionAlgorithm.GZIP,
    serialization=SerializationFormat.JSON,
)

# Compress JSON with key optimization
from pepperpy.infra import compress_json, decompress_json
compressed_json = compress_json(
    data={"repeated_key1": "value1", "repeated_key2": "value2"},
    optimize_keys=True,
)
decompressed_json = decompress_json(compressed_json)

# Compress NumPy arrays
import numpy as np
from pepperpy.infra import compress_numpy, decompress_numpy
array = np.array([[1, 2, 3], [4, 5, 6]])
compressed_array = compress_numpy(array)
decompressed_array = decompress_numpy(compressed_array)

# Optimize large datasets
from pepperpy.infra import optimize_dataset
dataset = [{"id": i, "value": f"value_{i}"} for i in range(10000)]
optimized = optimize_dataset(dataset, chunk_size=1000)
```

### Configuration (`config.py`)

The configuration module provides a unified configuration validation framework for PepperPy, allowing modules to define their configuration schemas and validate configuration at runtime.

Key components:
- `BaseConfig`: Base class for configuration models
- `ConfigRegistry`: Registry for configuration models
- Configuration validation utilities

Example:
```python
from pepperpy.infra import BaseConfig, register_config, get_config

# Define a configuration model
class MyConfig(BaseConfig):
    api_key: str
    timeout: int = 30
    
# Register the configuration model
register_config("my_component", MyConfig)

# Get the configuration
config = get_config("my_component")
```

### Connection (`connection.py`)

The connection module provides connection pooling functionality for network providers, including HTTP clients, database connections, and other network resources.

Key components:
- `ConnectionPool`: Base class for connection pools
- `ConnectionPoolConfig`: Configuration for connection pools
- `PooledResourceContext`: Context manager for pooled resources
- `pooled_resource`: Decorator for functions that use pooled resources
- Utility functions: `register_pool`, `get_pool`, `initialize_pools`, `close_pools`

Example:
```python
from pepperpy.infra import ConnectionPool, pooled_resource

# Create a custom connection pool
class MyConnectionPool(ConnectionPool):
    async def _create_connection(self):
        # Create a connection
        return my_connection_library.connect()

    async def _close_connection(self, connection):
        # Close a connection
        await connection.close()

    async def _validate_connection(self, connection):
        # Validate a connection
        return await connection.is_valid()

    def _get_default_config(self):
        return ConnectionPoolConfig(min_size=5, max_size=20)

# Register the pool
pool = MyConnectionPool("my_pool")
register_pool(pool)
await initialize_pools()

# Use the pool with a context manager
async with pooled_resource("my_pool") as connection:
    # Use the connection
    result = await connection.execute("SELECT * FROM table")

# Or use the pool with a decorator
@pooled_resource("my_pool")
async def my_function(connection, arg1, arg2):
    # Use the connection
    result = await connection.execute("SELECT * FROM table")
    return result

# Close all pools when done
await close_pools()
```

### Logging (`logging.py`)

The logging module provides utilities for configuring logging, getting loggers, and setting log levels in the PepperPy framework.

Key components:
- `configure_logging`: Configure the logging system
- `get_logger`: Get a logger with the specified name
- `set_log_level`: Set the log level for a logger
- `initialize_logging`: Initialize logging from configuration

Example:
```python
from pepperpy.infra import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO", log_file="app.log")

# Get a logger
logger = get_logger(__name__)

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

### Metrics (`metrics.py`)

The metrics module provides utilities for measuring and tracking performance metrics, including execution time, memory usage, and custom metrics.

Key components:
- `Timer`: Utility for measuring execution time
- `MemoryTracker`: Utility for tracking memory usage
- `PerformanceTracker`: Utility for tracking comprehensive performance metrics
- `benchmark`: Decorator for benchmarking functions
- Context managers: `measure_time`, `measure_memory`, `performance_tracker`

Example:
```python
from pepperpy.infra import measure_time, measure_memory, benchmark

# Measure execution time
with measure_time("operation") as timer:
    # Code to measure
    result = perform_operation()
print(f"Operation took {timer.elapsed_time} seconds")

# Track memory usage
with measure_memory("memory_operation") as tracker:
    # Memory-intensive code
    result = process_large_dataset()
print(f"Operation used {tracker.memory_used} bytes")

# Benchmark a function
@benchmark(iterations=10, track_memory=True)
def my_function(arg1, arg2):
    # Function implementation
    return result
```

### Resilience (`resilience.py`)

The resilience module provides patterns for building resilient systems, including circuit breakers and provider fallback mechanisms.

Key components:
- `CircuitBreaker`: Implementation of the circuit breaker pattern
- `ProviderFallback`: Implementation of the provider fallback pattern
- Decorators: `with_circuit_breaker`, `with_fallback`
- Utility functions: `get_circuit_breaker`, `get_fallback`, `reset_circuit_breaker`

Example:
```python
from pepperpy.infra import CircuitBreaker, with_circuit_breaker, with_fallback

# Use a circuit breaker directly
breaker = CircuitBreaker("my_provider")
try:
    result = breaker.execute(my_function, arg1, arg2)
except CircuitBreakerError:
    # Handle circuit breaker error
    result = fallback_function()

# Use the circuit breaker decorator
@with_circuit_breaker("my_provider")
def call_provider(arg1, arg2):
    # Function implementation
    return result

# Use the fallback decorator
@with_fallback("primary_provider", ["fallback1", "fallback2"])
def call_with_fallback(provider_id, arg1, arg2):
    # Function implementation using provider_id
    return result
```

### Serialization (`serialization.py`)

The serialization module provides utilities for serializing and deserializing data in various formats, including JSON, MessagePack, Pickle, YAML, and XML.

Key components:
- `SerializationFormat`: Enum defining serialization formats (JSON, MSGPACK, PICKLE, YAML, XML, RAW)
- `SerializerConfig`: Configuration options for serializers
- `Serializer`: Abstract base class for serializers
- Concrete serializers: `JSONSerializer`, `MessagePackSerializer`, `PickleSerializer`
- `FormatConverter`: Utility for converting between formats
- Convenience functions: `serialize_json`, `deserialize_json`, etc.

Example:
```python
from pepperpy.infra import (
    serialize_json, 
    deserialize_json, 
    JSONSerializer, 
    SerializerConfig
)

# Use convenience functions
data = {"name": "John", "age": 30}
json_bytes = serialize_json(data)
decoded_data = deserialize_json(json_bytes)

# Use serializer with custom configuration
config = SerializerConfig(indent=2, sort_keys=True)
serializer = JSONSerializer(config)
json_bytes = serializer.serialize(data)
decoded_data = serializer.deserialize(json_bytes)

# Convert between formats
from pepperpy.infra import convert_format, SerializationFormat
msgpack_bytes = convert_format(
    data=data,
    source_format=SerializationFormat.JSON,
    target_format=SerializationFormat.MSGPACK
)

# Work with base64 encoding
from pepperpy.infra import to_base64, from_base64
base64_str = to_base64(json_bytes)
original_bytes = from_base64(base64_str)
```

### Telemetry (`telemetry.py`)

The telemetry module provides a system for monitoring and reporting metrics and events in the PepperPy framework.

Key components:
- `MetricType`: Types of metrics that can be collected
- `EventLevel`: Levels for events that can be reported
- `TelemetryManager`: Manager for telemetry handlers
- `ProviderTelemetry`: Telemetry for a specific provider

Example:
```python
from pepperpy.infra import get_provider_telemetry, MetricType

# Get telemetry for a provider
telemetry = get_provider_telemetry("my_provider")

# Report a metric
telemetry.report_metric("request_count", 1, MetricType.COUNTER)

# Report an event
telemetry.info("request_processed", "Request processed successfully")
```

### Security (`security.py`)

The security module provides components for authentication, authorization, and credential management.

Key components:
- `AuthType`: Types of authentication
- `PermissionLevel`: Permission levels for authorization
- `SecurityManager`: Manager for security operations
- `Credential` and `Identity`: Core security data structures

Example:
```python
from pepperpy.infra import create_security_manager, AuthType, PermissionLevel

# Create a security manager
security_manager = create_security_manager()

# Create an identity
identity = security_manager.create_identity("user1")

# Create an API key
credential = security_manager.create_api_key(identity.id)

# Check authorization
is_authorized = security_manager.authorize(
    identity, "documents:read", PermissionLevel.READ
)
```

### Storage (`storage.py`)

The storage module provides components for data persistence and storage.

Key components:
- `StorageType`: Types of storage
- `StorageProvider`: Base class for storage providers
- `MemoryStorageProvider` and `FileStorageProvider`: Concrete storage providers
- Storage utility functions

Example:
```python
from pepperpy.infra import register_memory_provider, connect, set, get

# Register a memory provider
register_memory_provider("cache")

# Connect to the provider
await connect("cache")

# Store data
await set("cache", "key1", {"value": 42})

# Retrieve data
data = await get("cache", "key1")
```

## Usage

Import the components you need from the `pepperpy.infra` module:

```python
from pepperpy.infra import (
    # Cache
    cached, async_cached, initialize_cache, invalidate_cache,
    
    # Compression
    compress_data, decompress_data, compress_json, compress_numpy,
    
    # Config
    BaseConfig, get_config,
    
    # Connection
    ConnectionPool, pooled_resource, register_pool, initialize_pools,
    
    # Logging
    configure_logging, get_logger,
    
    # Metrics
    measure_time, benchmark, get_memory_usage,
    
    # Resilience
    CircuitBreaker, with_circuit_breaker, with_fallback,
    
    # Serialization
    serialize_json, deserialize_json, JSONSerializer, convert_format,
    
    # Telemetry
    get_provider_telemetry, MetricType,
    
    # Security
    create_security_manager, PermissionLevel,
    
    # Storage
    register_memory_provider, connect, get, set
)
``` 