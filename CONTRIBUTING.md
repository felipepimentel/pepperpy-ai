# Contributing to Pepperpy

First off, thank you for considering contributing to Pepperpy! It's people like you that make Pepperpy such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages and stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python style guides
* Include thoughtfully-worded, well-structured tests
* Document new code based on the Documentation Styleguide
* End all files with a newline

## Development Process

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run the test suite
5. Submit a Pull Request

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/pepperpy.git
cd pepperpy

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pepperpy

# Run specific test file
pytest tests/test_specific.py
```

### Code Style

We use several tools to maintain code quality:

* black for code formatting
* isort for import sorting
* mypy for type checking
* flake8 for style guide enforcement
* pylint for code analysis

Run all checks:

```bash
# Format code
black pepperpy/
isort pepperpy/

# Run type checking
mypy pepperpy/

# Run linters
flake8 pepperpy/
pylint pepperpy/
```

## Documentation

We use MkDocs for documentation. To build the docs:

```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
* feat: A new feature
* fix: A bug fix
* docs: Documentation only changes
* style: Changes that do not affect the meaning of the code
* refactor: A code change that neither fixes a bug nor adds a feature
* perf: A code change that improves performance
* test: Adding missing tests or correcting existing tests
* build: Changes that affect the build system or external dependencies
* ci: Changes to our CI configuration files and scripts
* chore: Other changes that don't modify src or test files

## Questions?

Feel free to open an issue with your question or contact the maintainers directly. 