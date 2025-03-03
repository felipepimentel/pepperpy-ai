#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}PepperPy Code Analyzer${NC}"
echo -e "${YELLOW}===================${NC}\n"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found${NC}"
    exit 1
fi

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Not in a virtual environment${NC}"
    echo "It's recommended to activate your virtual environment first"
    echo ""
fi

# Parse arguments
ALL=false
CIRCULAR=false
DOMAIN=false
STRUCTURE=false
HEADERS=false
REGISTRY=false
STUBS=false

# If no arguments, show help
if [ $# -eq 0 ]; then
    echo -e "Usage: $0 [options]"
    echo -e ""
    echo -e "Options:"
    echo -e "  --all        Run all checks"
    echo -e "  --circular   Check for circular dependencies"
    echo -e "  --domain     Check domain conventions"
    echo -e "  --structure  Validate project structure"
    echo -e "  --headers    Validate file headers"
    echo -e "  --registry   Check registry compliance"
    echo -e "  --stubs      Check compatibility stubs coverage"
    echo -e ""
    echo -e "If no options are specified, --all is assumed."
    echo -e ""
    ALL=true
fi

# Parse arguments
for arg in "$@"; do
    case $arg in
        --all)
            ALL=true
            ;;
        --circular)
            CIRCULAR=true
            ;;
        --domain)
            DOMAIN=true
            ;;
        --structure)
            STRUCTURE=true
            ;;
        --headers)
            HEADERS=true
            ;;
        --registry)
            REGISTRY=true
            ;;
        --stubs)
            STUBS=true
            ;;
        --help)
            echo -e "Usage: $0 [options]"
            echo -e ""
            echo -e "Options:"
            echo -e "  --all        Run all checks"
            echo -e "  --circular   Check for circular dependencies"
            echo -e "  --domain     Check domain conventions"
            echo -e "  --structure  Validate project structure"
            echo -e "  --headers    Validate file headers"
            echo -e "  --registry   Check registry compliance"
            echo -e "  --stubs      Check compatibility stubs coverage"
            echo -e ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 scripts/code_analyzer.py"

if [ "$ALL" = true ]; then
    CMD="$CMD --all"
else
    if [ "$CIRCULAR" = true ]; then
        CMD="$CMD --circular"
    fi
    if [ "$DOMAIN" = true ]; then
        CMD="$CMD --domain"
    fi
    if [ "$STRUCTURE" = true ]; then
        CMD="$CMD --structure"
    fi
    if [ "$HEADERS" = true ]; then
        CMD="$CMD --headers"
    fi
    if [ "$REGISTRY" = true ]; then
        CMD="$CMD --registry"
    fi
    if [ "$STUBS" = true ]; then
        CMD="$CMD --stubs"
    fi
fi

# Run the command
echo -e "${YELLOW}Running code analysis...${NC}\n"
$CMD

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}Code analysis completed successfully!${NC}"
else
    echo -e "\n${RED}Code analysis completed with errors!${NC}"
fi

exit $EXIT_CODE
