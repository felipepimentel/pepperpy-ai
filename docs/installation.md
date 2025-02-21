"""Installation Guide

This guide will help you install Pepperpy and its dependencies.

## Requirements

- Python 3.12 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation Methods

### Using pip

The simplest way to install Pepperpy is using pip:

```bash
pip install pepperpy
```

This will install the latest stable version of Pepperpy and its core dependencies.

### Using Poetry (Recommended)

For development or if you prefer using Poetry:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Install dependencies
poetry install
```

### From Source

To install from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Install in editable mode
pip install -e .
```

## Optional Dependencies

Pepperpy supports various optional features through extra dependencies:

```bash
# Install with all extras
pip install pepperpy[all]

# Install specific extras
pip install pepperpy[llm]      # LLM provider support
pip install pepperpy[storage]  # Storage provider support
pip install pepperpy[memory]   # Memory provider support
pip install pepperpy[content]  # Content synthesis support
```

## Provider Dependencies

Different providers may require additional dependencies:

### LLM Providers
```bash
# OpenAI
pip install pepperpy[openai]

# Anthropic
pip install pepperpy[anthropic]

# HuggingFace
pip install pepperpy[huggingface]
```

### Storage Providers
```bash
# Local storage
pip install pepperpy[local]

# Cloud storage (AWS S3, GCS)
pip install pepperpy[cloud]

# Database storage
pip install pepperpy[database]
```

### Memory Providers
```bash
# Redis
pip install pepperpy[redis]

# PostgreSQL
pip install pepperpy[postgres]

# MongoDB
pip install pepperpy[mongodb]
```

## Verification

After installation, verify that Pepperpy is working correctly:

```bash
# Check installation
pepperpy --version

# Run tests
pytest

# Try a simple example
pepperpy example hello-world
```

## Troubleshooting

### Common Issues

1. **Dependency Conflicts**
   ```bash
   # Try forcing reinstall
   pip install --force-reinstall pepperpy
   ```

2. **Version Mismatch**
   ```bash
   # Install specific version
   pip install pepperpy==1.0.0
   ```

3. **Missing Dependencies**
   ```bash
   # Install with verbose output
   pip install -v pepperpy[all]
   ```

### Getting Help

If you encounter any issues:

1. Check the [FAQ](./support/faq.md)
2. Search [known issues](./support/known-issues.md)
3. Visit our [GitHub Issues](https://github.com/yourusername/pepperpy/issues)
4. Join our [Discord community](https://discord.gg/pepperpy)

## Next Steps

- Read the [Quick Start Guide](./quickstart.md)
- Learn about [Basic Concepts](./concepts.md)
- Explore [Examples](./examples/index.md)""" 