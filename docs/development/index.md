# Development Guide

This guide provides information for developers who want to contribute to PepperPy AI.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pepperpy-ai.git
cd pepperpy-ai
```

2. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
```

4. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

## Code Style

PepperPy AI follows strict code style guidelines:

- Black for code formatting (line length: 88)
- Ruff for linting
- MyPy for type checking
- Google-style docstrings
- Type hints for all functions

### Running Style Checks

```bash
# Format code
poetry run black .

# Run linter
poetry run ruff check .

# Run type checker
poetry run mypy .
```

## Testing

We use pytest for testing. All new features should include tests.

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=pepperpy_ai

# Run specific test file
poetry run pytest tests/test_client.py
```

### Writing Tests

```python
import pytest
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

@pytest.mark.asyncio
async def test_chat():
    config = Config()
    client = PepperPyAI(config)
    
    response = await client.chat("Test message")
    assert response is not None
```

## Documentation

- Use Google-style docstrings
- Include type hints in docstrings
- Provide usage examples for complex functions
- Keep documentation up-to-date with code changes

### Example Docstring

```python
def process_message(
    message: str,
    temperature: float = 0.7
) -> str:
    """Process a message using AI.
    
    Args:
        message: The input message to process.
        temperature: The sampling temperature. Defaults to 0.7.
    
    Returns:
        The processed message.
    
    Raises:
        PepperPyError: If processing fails.
    
    Example:
        >>> client.process_message("Hello")
        'Hello! How can I help you?'
    """
```

## Git Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "feat: add new feature"
```

3. Push changes and create PR:
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

Follow the Conventional Commits specification:

- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Maintenance tasks

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a release PR
4. After merge, tag the release:
```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Security

- Never commit sensitive data
- Use environment variables for secrets
- Follow secure coding practices
- Report security issues privately

## Performance

- Profile code for bottlenecks
- Use async operations where appropriate
- Implement caching when beneficial
- Monitor resource usage

## Additional Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Black Code Style](https://black.readthedocs.io/en/stable/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Poetry Documentation](https://python-poetry.org/docs/) 