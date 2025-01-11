#!/usr/bin/env bash

# Exit on error
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version is provided
if [ -z "$1" ]; then
    echo -e "${RED}Please provide a version number (e.g. 1.0.0)${NC}"
    exit 1
fi

VERSION=$1

echo -e "${YELLOW}Publishing version ${VERSION}...${NC}\n"

# Run quality checks
echo -e "${YELLOW}Running quality checks...${NC}"
./scripts/check.sh
echo -e "${GREEN}Quality checks passed!${NC}\n"

# Clean build artifacts
echo -e "${YELLOW}Cleaning build artifacts...${NC}"
./scripts/clean.sh
echo -e "${GREEN}Build artifacts cleaned!${NC}\n"

# Update version
echo -e "${YELLOW}Updating version to ${VERSION}...${NC}"
poetry version $VERSION
echo -e "${GREEN}Version updated!${NC}\n"

# Build package
echo -e "${YELLOW}Building package...${NC}"
poetry build
echo -e "${GREEN}Package built!${NC}\n"

# Publish to PyPI
echo -e "${YELLOW}Publishing to PyPI...${NC}"
poetry publish
echo -e "${GREEN}Package published!${NC}\n"

# Create git tag
echo -e "${YELLOW}Creating git tag...${NC}"
git tag -a "v${VERSION}" -m "Release version ${VERSION}"
git push origin "v${VERSION}"
echo -e "${GREEN}Git tag created and pushed!${NC}\n"

echo -e "${GREEN}Version ${VERSION} published successfully!${NC}" 