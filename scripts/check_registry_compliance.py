#!/usr/bin/env python3
"""Script to check registry compliance in the PepperPy framework.

This script scans the codebase for registry implementations and checks
if they comply with the recommended usage pattern.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import logging
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("check_registry_compliance")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Define the registry files to check
REGISTRY_FILES = [
    "pepperpy/agents/registry.py",
    "pepperpy/workflows/registry.py",
    "pepperpy/rag/registry.py",
    "pepperpy/cli/registry.py",
]

# Define compliance checks
COMPLIANCE_CHECKS = [
    {
        "name": "Import from core registry",
        "pattern": r"from\s+pepperpy\.core\.registry\s+import",
        "required": True,
    },
    {
        "name": "Registry class inheritance",
        "pattern": r"class\s+\w+Registry\(Registry\[",
        "required": True,
    },
    {
        "name": "Get registry function",
        "pattern": r"def\s+get_\w+_registry\(\)",
        "required": True,
    },
    {
        "name": "Register with global registry",
        "pattern": r"registry_manager\s*=\s*get_registry\(\)",
        "required": True,
    },
]


def find_registry_files() -> List[Path]:
    """Find all registry files in the project.

    Returns:
        List of registry file paths

    """
    registry_files = []

    # Add explicitly defined registry files
    for file_path in REGISTRY_FILES:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            registry_files.append(full_path)

    # Find additional registry files
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith("registry.py") and "test" not in file.lower():
                file_path = Path(root) / file
                if file_path not in registry_files:
                    registry_files.append(file_path)

    return registry_files


def check_compliance(file_path: Path) -> Dict[str, bool]:
    """Check if a file complies with the recommended usage pattern.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary of check results

    """
    with open(file_path) as f:
        content = f.read()

    results = {}
    for check in COMPLIANCE_CHECKS:
        pattern = check["pattern"]
        required = check["required"]
        name = check["name"]

        match = re.search(pattern, content)
        results[name] = bool(match) == required

    return results


def main():
    """Run the script."""
    logger.info("Scanning for registry files...")
    registry_files = find_registry_files()
    logger.info(f"Found {len(registry_files)} registry files")

    compliant_files = 0
    non_compliant_files = 0
    compliance_results = {}

    for file_path in registry_files:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        logger.info(f"Checking {rel_path}...")
        results = check_compliance(file_path)

        # Store results
        compliance_results[str(rel_path)] = results

        # Check if file is compliant
        is_compliant = all(results.values())
        if is_compliant:
            logger.info(f"  ✅ {rel_path} is compliant")
            compliant_files += 1
        else:
            logger.info(f"  ❌ {rel_path} is NOT compliant")
            non_compliant_files += 1

            # Show failed checks
            for check, result in results.items():
                if not result:
                    logger.info(f"    - Failed: {check}")

    # Print summary
    logger.info("\nCompliance Summary:")
    logger.info(f"Total registry files: {len(registry_files)}")
    logger.info(f"Compliant files: {compliant_files}")
    logger.info(f"Non-compliant files: {non_compliant_files}")

    if non_compliant_files > 0:
        logger.info(
            "\nPlease update the non-compliant files to follow the recommended pattern.",
        )
        logger.info("See docs/REGISTRY_USAGE_GUIDE.md for more information.")
        sys.exit(1)
    else:
        logger.info("\nAll registry files are compliant with the recommended pattern.")
        sys.exit(0)


if __name__ == "__main__":
    main()

