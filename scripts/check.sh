#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${YELLOW}Running code quality checks...${NC}\n"

# Function to run a check
run_check() {
    local cmd="$1"
    local name="$2"
    
    echo -e "${YELLOW}Running $name...${NC}"
    if $cmd; then
        echo -e "${GREEN}✓ $name passed${NC}\n"
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}\n"
        return 1
    fi
}

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Not in a virtual environment${NC}"
    echo "Please activate your virtual environment first"
    exit 1
fi

# Run black check (don't format, just check)
run_check "black --check pepperpy/ tests/" "Black code style check"

# Run isort check
run_check "isort --check-only pepperpy/ tests/" "Import sorting check"

# Run flake8
run_check "flake8 pepperpy/ tests/" "Flake8 linting"

# Run mypy
run_check "mypy pepperpy/ tests/" "Type checking"

# Run pylint
run_check "pylint pepperpy/ tests/" "Pylint code analysis"

# Run bandit security checks
run_check "bandit -r pepperpy/" "Security checks"

# Run pytest with coverage
run_check "pytest --cov=pepperpy tests/ --cov-report=term-missing" "Unit tests"

# Run doctest
run_check "python -m doctest pepperpy/**/*.py" "Doctests"

# Check for outdated dependencies
echo -e "${YELLOW}Checking for outdated dependencies...${NC}"
pip list --outdated

echo -e "${GREEN}All checks completed!${NC}"
