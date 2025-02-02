#!/bin/bash

# Run type checking
echo "Running type checking..."
mypy pepperpy tests

# Run linting
echo -e "\nRunning linting..."
ruff check pepperpy tests

# Run tests
echo -e "\nRunning tests..."
pytest tests -v 