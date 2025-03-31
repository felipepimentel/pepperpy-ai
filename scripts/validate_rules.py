#!/usr/bin/env python3
"""
Validate Cursor rules format and structure.

This script checks all .mdc files in the .cursor/rules directory to ensure they follow
the expected format for Cursor rules.
"""

import re
import sys
from pathlib import Path

import colorama
import yaml
from colorama import Fore, Style

# Initialize colorama
colorama.init()

RULES_DIR = Path(".cursor/rules")
VALID_FIELDS = {"description", "globs", "alwaysApply"}


def print_error(message):
    """Print error message in red."""
    print(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")


def print_warning(message):
    """Print warning message in yellow."""
    print(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")


def print_success(message):
    """Print success message in green."""
    print(f"{Fore.GREEN}SUCCESS: {message}{Style.RESET_ALL}")


def validate_frontmatter(content, filename):
    """Validate the frontmatter of a rule file."""
    errors = []
    warnings = []

    # Check if file has frontmatter
    frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = frontmatter_pattern.match(content)

    if not match:
        errors.append("Missing frontmatter (should be enclosed in ---)")
        return errors, warnings

    # Parse frontmatter
    frontmatter_content = match.group(1)
    try:
        frontmatter = yaml.safe_load(frontmatter_content)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML in frontmatter: {e}")
        return errors, warnings

    if not frontmatter or not isinstance(frontmatter, dict):
        errors.append("Frontmatter is empty or not a dictionary")
        return errors, warnings

    # Check for required fields
    if "description" not in frontmatter:
        errors.append("Missing required field 'description'")
    elif not frontmatter["description"].startswith("USE WHEN"):
        errors.append("Description should start with 'USE WHEN'")

    if "globs" not in frontmatter:
        errors.append("Missing required field 'globs'")
    elif not isinstance(frontmatter["globs"], list):
        errors.append("'globs' should be a list")
    elif not frontmatter["globs"]:
        warnings.append("'globs' is empty - rule may not be triggered automatically")
    elif any(glob == "**/*" for glob in frontmatter["globs"]):
        warnings.append(
            "Using overly generic glob pattern '**/*' - consider using more specific patterns"
        )

    if "alwaysApply" not in frontmatter:
        warnings.append("Missing optional field 'alwaysApply', will default to false")
    elif not isinstance(frontmatter["alwaysApply"], bool):
        errors.append("'alwaysApply' should be a boolean (true/false)")

    # Check for invalid fields
    for field in frontmatter:
        if field not in VALID_FIELDS:
            warnings.append(f"Unknown field '{field}' in frontmatter")

    return errors, warnings


def validate_rules():
    """Validate all rules in the .cursor/rules directory."""
    errors_found = False
    rules_count = 0
    valid_rules = 0

    if not RULES_DIR.exists():
        print_error(f"Rules directory not found: {RULES_DIR}")
        return 1

    for file_path in RULES_DIR.glob("*.mdc"):
        rules_count += 1
        filename = file_path.name

        print(f"\nChecking {filename}...")

        try:
            content = file_path.read_text()
        except Exception as e:
            print_error(f"Failed to read file: {e}")
            errors_found = True
            continue

        file_errors, file_warnings = validate_frontmatter(content, filename)

        if file_errors:
            for error in file_errors:
                print_error(error)
            errors_found = True
        else:
            valid_rules += 1

        for warning in file_warnings:
            print_warning(warning)

    print("\n" + "=" * 50)
    print(f"Validated {rules_count} rules")
    print(f"Valid: {valid_rules}")
    print(f"Invalid: {rules_count - valid_rules}")
    print("=" * 50 + "\n")

    if errors_found:
        print_error("Some rules have validation errors that need to be fixed.")
        return 1
    else:
        print_success("All rules passed validation!")
        return 0


if __name__ == "__main__":
    sys.exit(validate_rules())
