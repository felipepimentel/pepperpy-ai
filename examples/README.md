# PepperPy Framework Examples

This directory contains example scripts demonstrating how to use the PepperPy framework.

## Basic Examples

### Basic Test

The `basic_test.py` script demonstrates the basic functionality of the PepperPy framework, including:

- Storage module
- Workflows module
- Configuration handling
- Error handling

To run the basic test:

```bash
python basic_test.py
```

### RAG Example

The `rag_example.py` script demonstrates how to use the Retrieval-Augmented Generation (RAG) capabilities of the PepperPy framework.

To run the RAG example:

```bash
python rag_example.py
```

### Workflow Example

The `workflow_example.py` script demonstrates how to create and execute workflows using the PepperPy framework.

To run the workflow example:

```bash
python workflow_example.py
```

### Storage Example

The `storage_example.py` script demonstrates how to use the storage capabilities of the PepperPy framework.

To run the storage example:

```bash
python storage_example.py
```

### Streaming Example

The `streaming_example.py` script demonstrates how to use the streaming capabilities of the PepperPy framework.

To run the streaming example:

```bash
python streaming_example.py
```

### Security Example

The `security_example.py` script demonstrates how to use the security features of the PepperPy framework.

To run the security example:

```bash
python security_example.py
```

## Memory Examples

The `memory` directory contains examples demonstrating how to use the memory capabilities of the PepperPy framework:

- `simple_memory.py`: Demonstrates basic memory operations
- `memory_example.py`: Demonstrates more advanced memory features

To run the memory examples:

```bash
python memory/simple_memory.py
python memory/memory_example.py
```

## Running All Examples

To run all examples, you can use the following command:

```bash
for example in $(find . -name "*.py" | grep -v "__pycache__"); do
    echo "Running $example..."
    python $example
    echo "------------------------"
done
```

## Requirements

All examples require the PepperPy framework to be installed. You can install it using:

```bash
pip install -e ..
```

or

```bash
poetry install
```

from the root directory of the repository. 