# Testing Framework

PepperPy AI provides a comprehensive testing framework for ensuring code quality and reliability.

## Overview

The testing framework provides:
- Unit testing
- Integration testing
- Async testing support
- Mocking utilities
- Test fixtures
- Coverage reporting

## Test Structure

### Directory Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_client.py
│   ├── test_agents.py
│   └── test_providers.py
├── integration/          # Integration tests
│   ├── test_api.py
│   └── test_workflow.py
├── fixtures/             # Test fixtures
│   ├── data.py
│   └── mocks.py
└── conftest.py          # Pytest configuration
```

### Test Configuration

Configure pytest in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
addopts = """
    --cov=pepperpy
    --cov-report=term-missing
    --cov-report=xml
    --cov-report=html
    -v
"""
```

## Writing Tests

### Unit Tests

```python
import pytest
from pepperpy.client import PepperPyAI
from pepperpy.config import Config

@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    config = Config()
    client = PepperPyAI(config)
    
    assert client is not None
    assert client.config == config

@pytest.mark.asyncio
async def test_client_process():
    """Test client processing."""
    config = Config()
    client = PepperPyAI(config)
    
    result = await client.process("Test input")
    assert result is not None
```

### Integration Tests

```python
import pytest
from pepperpy.client import PepperPyAI
from pepperpy.config import Config

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_workflow():
    """Test complete API workflow."""
    config = Config()
    client = PepperPyAI(config)
    
    # Test workflow steps
    response = await client.chat("Hello")
    assert response.status == 200
    
    result = await client.process(response.data)
    assert result.is_valid
```

### Test Fixtures

```python
import pytest
from pepperpy.config import Config

@pytest.fixture
async def client_config():
    """Provide test configuration."""
    return Config(
        api_key="test-key",
        provider="test-provider"
    )

@pytest.fixture
async def mock_client(client_config):
    """Provide mock client."""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    client.config = client_config
    return client
```

## Testing Features

### Async Testing

```python
import pytest
from pepperpy.client import PepperPyAI

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operations."""
    client = PepperPyAI()
    
    async with client:
        result = await client.process("Test")
        assert result is not None
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    """Test using mocks."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"status": "success"}
    
    with patch("pepperpy.client.request") as mock_request:
        mock_request.return_value = mock_response
        client = PepperPyAI()
        result = await client.process("Test")
        assert result["status"] == "success"
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3")
])
async def test_multiple_inputs(input, expected):
    """Test multiple input cases."""
    client = PepperPyAI()
    result = await client.process(input)
    assert result == expected
```

## Best Practices

1. **Test Organization**
   - Group related tests
   - Use clear naming
   - Separate test types

2. **Test Coverage**
   - Aim for high coverage
   - Test edge cases
   - Test error conditions

3. **Test Performance**
   - Use test categories
   - Optimize test runs
   - Parallelize when possible

4. **Test Maintenance**
   - Keep tests updated
   - Remove obsolete tests
   - Document test cases

## Running Tests

### Basic Test Run

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_client.py

# Run specific test function
poetry run pytest tests/test_client.py::test_client_initialization
```

### Coverage Testing

```bash
# Run with coverage
poetry run pytest --cov=pepperpy

# Generate HTML coverage report
poetry run pytest --cov=pepperpy --cov-report=html

# Show missing lines
poetry run pytest --cov=pepperpy --cov-report=term-missing
```

### Test Categories

```bash
# Run unit tests only
poetry run pytest tests/unit/

# Run integration tests
poetry run pytest -m integration

# Run specific test categories
poetry run pytest -m "not slow"
```

### Debugging Tests

```bash
# Run with debug info
poetry run pytest -vv

# Stop on first failure
poetry run pytest -x

# Enter PDB on failure
poetry run pytest --pdb

# Show local variables on failure
poetry run pytest -l
``` 