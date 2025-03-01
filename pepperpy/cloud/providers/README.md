# Cloud Providers

This directory contains provider implementations for cloud service capabilities in the PepperPy framework.

## Available Providers

- **AWS Provider**: Implementation for Amazon Web Services
- **GCP Storage Provider**: Implementation for Google Cloud Platform storage
- **Cloud Storage Provider**: Generic interface for cloud storage services

## Usage

```python
from pepperpy.cloud.providers import AWSProvider, GCPStorageProvider

# Use AWS provider
aws = AWSProvider(region="us-west-2", credentials={...})
result = aws.invoke_lambda("my-function", {"key": "value"})

# Use GCP Storage provider
gcp_storage = GCPStorageProvider(bucket_name="my-bucket", project_id="my-project")
gcp_storage.store("file.txt", "Hello, GCP!")
content = gcp_storage.retrieve("file.txt")
```

## Adding New Providers

To add a new provider:

1. Create a new file in this directory
2. Implement the appropriate cloud service interfaces
3. Register your provider in the `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/cloud/`. The move to this domain-specific location improves modularity and maintainability. 