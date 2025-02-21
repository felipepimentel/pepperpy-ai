#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${YELLOW}Cleaning temporary files...${NC}\n"

# Function to safely remove files/directories
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo -e "${YELLOW}Removing $path${NC}"
        rm -rf "$path"
    fi
}

# Function to clean Python cache files in a directory
clean_python_cache() {
    local dir="$1"
    echo -e "${YELLOW}Cleaning Python cache in $dir${NC}"
    
    # Remove .pyc files
    find "$dir" -type f -name "*.pyc" -delete
    
    # Remove __pycache__ directories
    find "$dir" -type d -name "__pycache__" -exec rm -rf {} +
    
    # Remove .pytest_cache directories
    find "$dir" -type d -name ".pytest_cache" -exec rm -rf {} +
    
    # Remove .coverage files
    find "$dir" -type f -name ".coverage" -delete
}

# Clean Python cache files
clean_python_cache "pepperpy"
clean_python_cache "tests"

# Clean build artifacts
safe_remove "build/"
safe_remove "dist/"
safe_remove "*.egg-info"
safe_remove ".eggs/"
safe_remove ".tox/"

# Clean documentation builds
safe_remove "docs/_build/"
safe_remove "docs/api/_build/"

# Clean test artifacts
safe_remove ".pytest_cache/"
safe_remove ".coverage"
safe_remove "coverage.xml"
safe_remove "htmlcov/"

# Clean mypy cache
safe_remove ".mypy_cache/"

# Clean IDE artifacts
safe_remove ".idea/"
safe_remove ".vscode/"
safe_remove "*.code-workspace"

# Clean temporary files
safe_remove "tmp/"
safe_remove "temp/"
safe_remove "*.tmp"
safe_remove "*.temp"
safe_remove "*.log"

# Clean virtual environment (optional)
if [ "$1" == "--venv" ]; then
    safe_remove ".venv/"
fi

echo -e "${GREEN}Cleanup complete!${NC}" 