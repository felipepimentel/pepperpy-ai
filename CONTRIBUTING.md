# Contributing to Pepperpy

Thank you for your interest in contributing to Pepperpy! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/pepperpy.git
   cd pepperpy
   ```

3. Set up your development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   pip install -r tests/requirements.txt
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Process

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints for all functions and methods
   - Write Google-style docstrings
   - Format code using `ruff format`
   - Sort imports using `ruff check`

2. **Testing**
   - Write tests for all new features
   - Maintain or improve code coverage
   - Run tests with `pytest`
   - Run type checking with `mypy`

3. **Documentation**
   - Update docstrings for modified code
   - Update README.md if needed
   - Add examples for new features
   - Keep docstrings and comments up to date

4. **Commit Messages**
   Format: `type(scope): description`
   
   Types:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation changes
   - style: Code style changes
   - refactor: Code refactoring
   - test: Test changes
   - chore: Build/maintenance changes

   Example:
   ```
   feat(memory): add Redis memory store implementation
   
   - Add RedisMemoryStore class
   - Implement async key-value operations
   - Add configuration options
   - Write unit tests
   ```

## Pull Request Process

1. **Before Submitting**
   - Run all tests and ensure they pass
   - Run type checking and fix any issues
   - Format code and sort imports
   - Update documentation if needed
   - Add tests for new features

2. **Submitting**
   - Push your changes to your fork
   - Create a pull request from your fork to our main repository
   - Fill out the pull request template
   - Link any related issues

3. **Review Process**
   - Maintainers will review your PR
   - Address any requested changes
   - Once approved, your PR will be merged

## Development Guidelines

### Code Organization

- Keep files focused and modular
- Follow the established project structure
- Use appropriate abstraction levels
- Keep functions and methods small and focused

### Error Handling

- Use custom exception classes
- Provide helpful error messages
- Include context in exceptions
- Handle errors at appropriate levels

### Testing

- Write unit tests for all new code
- Include integration tests where needed
- Test edge cases and error conditions
- Mock external dependencies
- Use appropriate test fixtures

### Documentation

- Write clear and concise docstrings
- Include usage examples
- Document exceptions and edge cases
- Keep comments up to date
- Update README for new features

### Performance

- Consider async/await for I/O operations
- Use appropriate data structures
- Implement caching where beneficial
- Profile code for bottlenecks

## Project Structure

Follow the established project structure:

```
pepperpy/
├── core/               # Core framework components
├── providers/         # Model providers
├── memory/           # Memory management
├── adapters/         # Framework adapters
└── monitoring/      # Observability

tests/
├── core/
├── providers/
├── memory/
├── adapters/
└── monitoring/
```

## Getting Help

- Open an issue for bugs or feature requests
- Join our community discussions
- Read the documentation
- Contact the maintainers

## License

By contributing to Pepperpy, you agree that your contributions will be licensed under the MIT License. 