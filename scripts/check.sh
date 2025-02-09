#!/bin/bash

# Exit on error
set -e

echo "Running code quality checks..."

# Run ruff for linting and formatting
echo "🎨🔍 Running ruff for linting and formatting..."
poetry run ruff check . --fix

# Run mypy type checker
echo "🔎 Running mypy type checker..."
poetry run mypy .

# Run pytest with coverage
echo "🧪 Running tests with coverage..."
poetry run pytest

# Validate project structure
echo "🏗️ Validating project structure..."
poetry run python scripts/validate_structure.py

# Print summary
echo "✨ All checks completed!"
