#!/bin/bash

# Exit on error
set -e

echo "Running code quality checks..."

# Format code with black
echo "🎨 Running black formatter..."
poetry run black .

# Sort imports with isort
echo "📦 Running isort..."
poetry run isort .

# Run ruff linter
echo "🔍 Running ruff linter..."
poetry run ruff check . --fix

# Run mypy type checker
echo "🔎 Running mypy type checker..."
poetry run mypy .

# Run pytest with coverage
echo "🧪 Running tests with coverage..."
poetry run pytest

# Validate project structure
echo "🏗️ Validating project structure..."
poetry run python scripts/structure/validate_structure.py

# Print summary
echo "✨ All checks completed!" 