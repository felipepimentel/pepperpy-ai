#!/usr/bin/env bash

# Exit on error
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running lightweight tests...${NC}\n"

# Run core tests only
echo -e "${YELLOW}Running pytest...${NC}"
pytest tests/test_types.py \
      tests/test_exceptions.py \
      tests/test_providers.py \
      -v \
      --cov=pepperpy_ai \
      --cov-report=term-missing
echo -e "${GREEN}Pytest passed!${NC}\n"

# Run linting
echo -e "${YELLOW}Running ruff...${NC}"
ruff check pepperpy_ai tests
echo -e "${GREEN}Ruff passed!${NC}\n"

# Run type checking
echo -e "${YELLOW}Running mypy...${NC}"
mypy pepperpy_ai tests
echo -e "${GREEN}Mypy passed!${NC}\n"

echo -e "${GREEN}All tests passed!${NC}" 