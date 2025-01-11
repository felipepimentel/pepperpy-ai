#!/usr/bin/env bash

# Exit on error
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up development environment...${NC}\n"

# Install poetry if not installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Installing poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    echo -e "${GREEN}Poetry installed!${NC}\n"
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
poetry install --with dev
echo -e "${GREEN}Dependencies installed!${NC}\n"

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
poetry run pre-commit install
echo -e "${GREEN}Pre-commit hooks installed!${NC}\n"

# Create initial baseline for bandit
echo -e "${YELLOW}Creating bandit baseline...${NC}"
poetry run bandit -r pepperpy_ai -c .bandit -f json -o bandit-baseline.json
echo -e "${GREEN}Bandit baseline created!${NC}\n"

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${YELLOW}Run 'poetry shell' to activate the virtual environment${NC}" 