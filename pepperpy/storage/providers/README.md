# Storage Providers

This directory contains provider implementations for storage capabilities in the PepperPy framework.

## Available Providers

- **Local Storage Provider**: Implementation for local file system storage
- **SQL Storage Provider**: Implementation for SQL database storage
- **Cloud Storage Provider**: Implementation for cloud-based storage

## Usage

```python
from pepperpy.storage.providers import LocalStorageProvider, SQLStorageProvider, CloudStorageProvider

# Use local storage provider
local_storage = LocalStorageProvider(base_path="/path/to/storage")
local_storage.store("file.txt", "Hello, world!")
content = local_storage.retrieve("file.txt")

# Use SQL storage provider
sql_storage = SQLStorageProvider(connection_string="postgresql://user:pass@localhost/db")
sql_storage.store("table_name", {"id": 1, "name": "Example"})
data = sql_storage.retrieve("table_name", {"id": 1})

# Use cloud storage provider
cloud_storage = CloudStorageProvider(bucket="my-bucket", credentials={...})
cloud_storage.store("remote_file.txt", "Hello, cloud!")
cloud_content = cloud_storage.retrieve("remote_file.txt")
```

## Adding New Providers

To add a new provider:

1. Create a new file in this directory
2. Implement the appropriate storage interfaces
3. Register your provider in the `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/storage/`. The move to this domain-specific location improves modularity and maintainability. 