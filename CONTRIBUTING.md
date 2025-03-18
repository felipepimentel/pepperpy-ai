# Contributing to PepperPy

Thank you for your interest in contributing to PepperPy! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Write or update tests
5. Run the test suite
6. Submit a pull request

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/pepperpy.git
   cd pepperpy
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run tests:
   ```bash
   poetry run pytest
   ```

4. Run linters:
   ```bash
   poetry run black .
   poetry run isort .
   poetry run mypy .
   poetry run ruff check .
   ```

## Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the documentation if needed
3. Add tests for new functionality
4. Ensure all tests pass and linters are happy
5. Update the CHANGELOG.md
6. Submit the pull request

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Add type hints to all functions
- Write tests for new functionality
- Keep functions and methods focused and small
- Use descriptive variable names

## Documentation

- Update documentation for any changed functionality
- Add docstrings to all public functions, classes, and methods
- Include examples in docstrings
- Keep documentation up to date with code changes

## Testing

- Write unit tests for new functionality
- Update existing tests when changing functionality
- Aim for high test coverage
- Use pytest fixtures and parametrize when appropriate
- Test edge cases and error conditions

## Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add support for async pipeline stages

- Implement async execution in Pipeline class
- Update FunctionStage to support async functions
- Add tests for async execution
- Update documentation with async examples

Fixes #123
```

## Questions or Problems?

If you have questions or run into problems, please:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/yourusername/pepperpy/issues)
3. Open a new issue if needed

## License

By contributing to PepperPy, you agree that your contributions will be licensed under its MIT License. 