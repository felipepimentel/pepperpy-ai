#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}PepperPy Structure Exporter${NC}"
echo -e "${YELLOW}=========================${NC}\n"

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

# Default values
FORMAT="text"
OUTPUT=""
MAX_DEPTH=""
DIR="."

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --format=*)
            FORMAT="${1#*=}"
            shift
            ;;
        --output=*)
            OUTPUT="${1#*=}"
            shift
            ;;
        --max-depth=*)
            MAX_DEPTH="${1#*=}"
            shift
            ;;
        --dir=*)
            DIR="${1#*=}"
            shift
            ;;
        --help)
            echo -e "Usage: $0 [options]"
            echo -e ""
            echo -e "Options:"
            echo -e "  --format=FORMAT    Output format (text, json, markdown, yaml)"
            echo -e "  --output=FILE      Output file path"
            echo -e "  --max-depth=N      Maximum depth to traverse"
            echo -e "  --dir=DIR          Directory to analyze (default: current directory)"
            echo -e "  --help             Show this help message"
            echo -e ""
            echo -e "Examples:"
            echo -e "  $0 --format=markdown --output=structure.md"
            echo -e "  $0 --format=json --max-depth=3"
            echo -e ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo -e "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 scripts/export_structure.py --format=$FORMAT"

if [ -n "$OUTPUT" ]; then
    CMD="$CMD --output=$OUTPUT"
fi

if [ -n "$MAX_DEPTH" ]; then
    CMD="$CMD --max-depth=$MAX_DEPTH"
fi

if [ -n "$DIR" ]; then
    CMD="$CMD --dir=$DIR"
fi

# Run the command
echo -e "${YELLOW}Exporting project structure...${NC}\n"
$CMD

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    if [ -n "$OUTPUT" ]; then
        echo -e "\n${GREEN}Project structure exported successfully to $OUTPUT!${NC}"
    else
        echo -e "\n${GREEN}Project structure exported successfully!${NC}"
    fi
else
    echo -e "\n${RED}Error exporting project structure!${NC}"
fi

exit $EXIT_CODE 