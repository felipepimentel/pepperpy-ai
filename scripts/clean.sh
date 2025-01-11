#!/usr/bin/env bash

# Exit on error
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cleaning temporary files...${NC}\n"

# Remove Python cache files
echo -e "${YELLOW}Removing Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
echo -e "${GREEN}Python cache files removed!${NC}\n"

# Remove test cache
echo -e "${YELLOW}Removing test cache...${NC}"
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov
rm -rf coverage.xml
echo -e "${GREEN}Test cache removed!${NC}\n"

# Remove mypy cache
echo -e "${YELLOW}Removing mypy cache...${NC}"
rm -rf .mypy_cache
echo -e "${GREEN}Mypy cache removed!${NC}\n"

# Remove ruff cache
echo -e "${YELLOW}Removing ruff cache...${NC}"
rm -rf .ruff_cache
echo -e "${GREEN}Ruff cache removed!${NC}\n"

# Remove build artifacts
echo -e "${YELLOW}Removing build artifacts...${NC}"
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
echo -e "${GREEN}Build artifacts removed!${NC}\n"

# Remove bandit reports
echo -e "${YELLOW}Removing bandit reports...${NC}"
rm -f bandit-report.txt
rm -f bandit-baseline.json
echo -e "${GREEN}Bandit reports removed!${NC}\n"

echo -e "${GREEN}All temporary files cleaned!${NC}" 