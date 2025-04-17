#!/bin/bash
# Script to validate and test all plugins

set -e  # Exit on error

# Color codes for pretty output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== PepperPy Plugin Validation Suite =====${NC}"
echo ""

# Check if required scripts exist
if [ ! -f "scripts/plugin_validator.py" ]; then
    echo -e "${RED}Error: plugin_validator.py not found!${NC}"
    exit 1
fi

if [ ! -f "scripts/plugin_tester.py" ]; then
    echo -e "${RED}Error: plugin_tester.py not found!${NC}"
    exit 1
fi

# Create results directory
RESULTS_DIR="plugin_validation_results"
mkdir -p "$RESULTS_DIR"

# Get list of plugins
echo -e "${BLUE}Finding plugins...${NC}"
PLUGINS_DIR="plugins"
PLUGIN_COUNT=$(find "$PLUGINS_DIR" -name "plugin.yaml" | wc -l)

echo -e "Found ${GREEN}$PLUGIN_COUNT${NC} plugins to validate"
echo ""

# Step 1: Run plugin validator
echo -e "${BLUE}Step 1: Running plugin validator${NC}"
echo "Checking plugins against architectural requirements..."

# Run validator and capture output
VALIDATOR_OUTPUT="$RESULTS_DIR/validator_output.txt"
python scripts/plugin_validator.py > "$VALIDATOR_OUTPUT" 2>&1
VALIDATOR_EXIT=$?

if [ $VALIDATOR_EXIT -eq 0 ]; then
    echo -e "${GREEN}Validation successful! All plugins meet architectural requirements.${NC}"
else
    echo -e "${RED}Validation failed! $VALIDATOR_EXIT plugins have issues.${NC}"
    echo -e "See ${YELLOW}$VALIDATOR_OUTPUT${NC} for details."
fi
echo ""

# Step 2: Auto-fix issues
echo -e "${BLUE}Step 2: Attempt to auto-fix issues${NC}"
echo "Would you like to attempt to auto-fix validation issues? (y/n)"
read -r AUTOFIX

if [[ $AUTOFIX == "y" || $AUTOFIX == "Y" ]]; then
    echo "Running batch plugin fixer..."
    
    # First run in dry-run mode to see what would be fixed
    FIXER_DRY_OUTPUT="$RESULTS_DIR/fixer_dry_run.txt"
    python scripts/batch_plugin_fixer.py --dry-run > "$FIXER_DRY_OUTPUT" 2>&1
    
    # Ask for confirmation
    echo -e "Dry run complete. See ${YELLOW}$FIXER_DRY_OUTPUT${NC} for planned changes."
    echo "Proceed with applying fixes? (y/n)"
    read -r CONFIRM
    
    if [[ $CONFIRM == "y" || $CONFIRM == "Y" ]]; then
        FIXER_OUTPUT="$RESULTS_DIR/fixer_output.txt"
        python scripts/batch_plugin_fixer.py > "$FIXER_OUTPUT" 2>&1
        FIXER_EXIT=$?
        
        if [ $FIXER_EXIT -eq 0 ]; then
            echo -e "${GREEN}Auto-fixes applied successfully!${NC}"
        else
            echo -e "${RED}Some issues couldn't be fixed automatically.${NC}"
        fi
        echo -e "See ${YELLOW}$FIXER_OUTPUT${NC} for details."
    else
        echo "Skipping auto-fix application."
    fi
else
    echo "Skipping auto-fix step."
fi
echo ""

# Step 3: Run tests
echo -e "${BLUE}Step 3: Running plugin tests${NC}"
echo "Testing plugin functionality based on examples..."

# Run tester and capture output
TESTER_OUTPUT="$RESULTS_DIR/tester_output.txt"
python scripts/plugin_tester.py > "$TESTER_OUTPUT" 2>&1
TESTER_EXIT=$?

if [ $TESTER_EXIT -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "See ${YELLOW}$TESTER_OUTPUT${NC} for details."
fi
echo ""

# Generate summary report
SUMMARY="$RESULTS_DIR/summary.txt"
echo "===== PepperPy Plugin Validation Summary =====" > "$SUMMARY"
echo "Date: $(date)" >> "$SUMMARY"
echo "Total plugins: $PLUGIN_COUNT" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "Validation: $([ $VALIDATOR_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED")" >> "$SUMMARY"
echo "Tests: $([ $TESTER_EXIT -eq 0 ] && echo "PASSED" || echo "FAILED")" >> "$SUMMARY"
echo "" >> "$SUMMARY"
echo "See individual reports for details:" >> "$SUMMARY"
echo "- Validator: $VALIDATOR_OUTPUT" >> "$SUMMARY"
echo "- Tester: $TESTER_OUTPUT" >> "$SUMMARY"

echo -e "${BLUE}Summary report generated:${NC} ${YELLOW}$SUMMARY${NC}"
echo ""

# Final status
if [ $VALIDATOR_EXIT -eq 0 ] && [ $TESTER_EXIT -eq 0 ]; then
    echo -e "${GREEN}All plugins are valid and tests passed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Some plugins have issues or tests failed.${NC}"
    echo -e "Please check the reports in ${YELLOW}$RESULTS_DIR${NC} directory."
    exit 1
fi 