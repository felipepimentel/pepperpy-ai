#!/usr/bin/env bash

# Exit on error
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running code quality checks...${NC}\n"

# Format code
echo -e "${YELLOW}Running black...${NC}"
black pepperpy_ai tests
echo -e "${GREEN}Black passed!${NC}\n"

echo -e "${YELLOW}Running isort...${NC}"
isort pepperpy_ai tests
echo -e "${GREEN}Isort passed!${NC}\n"

# Lint code
echo -e "${YELLOW}Running ruff...${NC}"
ruff check pepperpy_ai tests
echo -e "${GREEN}Ruff passed!${NC}\n"

# Type check
echo -e "${YELLOW}Running mypy...${NC}"
mypy pepperpy_ai tests
echo -e "${GREEN}Mypy passed!${NC}\n"

# Security check
echo -e "${YELLOW}Running bandit...${NC}"
bandit -r pepperpy_ai -c .bandit
echo -e "${GREEN}Bandit passed!${NC}\n"

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
pytest tests -v --cov=pepperpy_ai --cov-report=term-missing
echo -e "${GREEN}Tests passed!${NC}\n"

echo -e "${GREEN}All checks passed!${NC}" 