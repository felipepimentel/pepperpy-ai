"""Public API for data module.

This module provides the public API for data handling,
including schema validation, data transformation, and persistence.
"""

from pepperpy.data.core import (
    check,
    clear_data,
    list_keys,
    remove,
    retrieve,
    store,
    validate_and_transform,
)
from pepperpy.data.errors import (
    ConnectionError,
    DataError,
    PersistenceError,
    QueryError,
    SchemaError,
    TransformError,
    ValidationError,
)
from pepperpy.data.persistence import (
    FileStorageProvider,
    MemoryStorageProvider,
    StorageProvider,
    StorageProviderRegistry,
    StorageType,
    clear_providers,
    connect,
    delete,
    disconnect,
    exists,
    get,
    get_provider,
    is_connected,
    keys,
    list_providers,
    register_file_provider,
    register_memory_provider,
    register_provider,
    set,
    unregister_provider,
)
from pepperpy.data.persistence import (
    clear as clear_storage,
)
from pepperpy.data.persistence import (
    get_registry as get_provider_registry,
)
from pepperpy.data.persistence import (
    set_registry as set_provider_registry,
)
from pepperpy.data.schema import (
    DataclassSchema,
    JsonSchema,
    PydanticSchema,
    Schema,
    SchemaRegistry,
    SchemaType,
    clear_schemas,
    get_schema,
    list_schemas,
    register_dataclass,
    register_json_schema,
    register_pydantic_model,
    register_schema,
    unregister_schema,
    validate,
)
from pepperpy.data.schema import (
    get_registry as get_schema_registry,
)
from pepperpy.data.schema import (
    set_registry as set_schema_registry,
)
from pepperpy.data.transform import (
    ClassTransform,
    FunctionTransform,
    Transform,
    TransformPipeline,
    TransformRegistry,
    TransformType,
    clear_transforms,
    get_transform,
    list_transforms,
    register_class_transform,
    register_function_transform,
    register_pipeline,
    register_transform,
    transform,
    unregister_transform,
)
from pepperpy.data.transform import (
    get_registry as get_transform_registry,
)
from pepperpy.data.transform import (
    set_registry as set_transform_registry,
)
from pepperpy.data.transform.pipeline import (
    ConditionalStage,
    FunctionStage,
    Pipeline,
    PipelineRegistry,
    PipelineStage,
    TransformStage,
    clear_pipelines,
    create_pipeline,
    execute_pipeline,
    get_pipeline,
    list_pipelines,
    unregister_pipeline,
)
from pepperpy.data.transform.pipeline import (
    get_registry as get_pipeline_registry,
)
from pepperpy.data.transform.pipeline import (
    register_pipeline as register_pipeline_obj,
)
from pepperpy.data.transform.pipeline import (
    set_registry as set_pipeline_registry,
)

__all__ = [
    # Core
    "check",
    "clear_data",
    "list_keys",
    "remove",
    "retrieve",
    "store",
    "validate_and_transform",
    # Errors
    "ConnectionError",
    "DataError",
    "PersistenceError",
    "QueryError",
    "SchemaError",
    "TransformError",
    "ValidationError",
    # Persistence
    "FileStorageProvider",
    "MemoryStorageProvider",
    "StorageProvider",
    "StorageProviderRegistry",
    "StorageType",
    "clear_storage",
    "clear_providers",
    "connect",
    "delete",
    "disconnect",
    "exists",
    "get",
    "get_provider",
    "get_provider_registry",
    "is_connected",
    "keys",
    "list_providers",
    "register_file_provider",
    "register_memory_provider",
    "register_provider",
    "set",
    "set_provider_registry",
    "unregister_provider",
    # Schema
    "DataclassSchema",
    "JsonSchema",
    "PydanticSchema",
    "Schema",
    "SchemaRegistry",
    "SchemaType",
    "clear_schemas",
    "get_schema",
    "get_schema_registry",
    "list_schemas",
    "register_dataclass",
    "register_json_schema",
    "register_pydantic_model",
    "register_schema",
    "set_schema_registry",
    "unregister_schema",
    "validate",
    # Transform
    "ClassTransform",
    "FunctionTransform",
    "Transform",
    "TransformPipeline",
    "TransformRegistry",
    "TransformType",
    "clear_transforms",
    "get_transform",
    "get_transform_registry",
    "list_transforms",
    "register_class_transform",
    "register_function_transform",
    "register_pipeline",
    "register_transform",
    "set_transform_registry",
    "transform",
    "unregister_transform",
    # Pipeline
    "ConditionalStage",
    "FunctionStage",
    "Pipeline",
    "PipelineRegistry",
    "PipelineStage",
    "TransformStage",
    "clear_pipelines",
    "create_pipeline",
    "execute_pipeline",
    "get_pipeline",
    "get_pipeline_registry",
    "list_pipelines",
    "register_pipeline_obj",
    "set_pipeline_registry",
    "unregister_pipeline",
]
