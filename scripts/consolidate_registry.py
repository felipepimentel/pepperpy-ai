#!/usr/bin/env python3
"""Script to consolidate registry systems in the PepperPy framework.

This script automates the consolidation of registry systems by:
1. Fixing imports in registry files
2. Checking compliance with the recommended pattern
3. Providing guidance for manual updates if needed
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import logging
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("consolidate_registry")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(command, cwd=None):
    """Run a shell command and return the output.

    Args:
        command: Command to run
        cwd: Working directory

    Returns:
        Command output
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None


def ensure_docs_directory():
    """Ensure the docs directory exists."""
    docs_dir = PROJECT_ROOT / "docs"
    if not docs_dir.exists():
        logger.info("Creating docs directory...")
        docs_dir.mkdir(parents=True)


def ensure_scripts_executable():
    """Ensure scripts are executable."""
    scripts = [
        "scripts/fix_registry_imports.py",
        "scripts/check_registry_compliance.py",
    ]
    
    for script in scripts:
        script_path = PROJECT_ROOT / script
        if script_path.exists():
            logger.info(f"Making {script} executable...")
            os.chmod(script_path, 0o755)


def main():
    """Run the consolidation script."""
    logger.info("Starting registry consolidation...")

    # Ensure docs directory exists
    ensure_docs_directory()

    # Ensure scripts are executable
    ensure_scripts_executable()

    # Step 1: Fix registry imports
    logger.info("Step 1: Fixing registry imports...")
    fix_imports_script = PROJECT_ROOT / "scripts/fix_registry_imports.py"
    if fix_imports_script.exists():
        output = run_command(["python", str(fix_imports_script)])
        if output:
            logger.info(output)
    else:
        logger.error("fix_registry_imports.py script not found!")
        return

    # Step 2: Check registry compliance
    logger.info("Step 2: Checking registry compliance...")
    check_compliance_script = PROJECT_ROOT / "scripts/check_registry_compliance.py"
    if check_compliance_script.exists():
        output = run_command(["python", str(check_compliance_script)])
        if output:
            logger.info(output)
    else:
        logger.error("check_registry_compliance.py script not found!")
        return

    # Step 3: Provide guidance for manual updates
    logger.info("\nStep 3: Manual updates")
    logger.info("Please review the compliance check results above.")
    logger.info("For any non-compliant registry files, please update them to follow the recommended pattern.")
    logger.info("See docs/REGISTRY_USAGE_GUIDE.md for more information.")

    logger.info("\nRegistry consolidation completed!")
    logger.info("To verify the consolidation, run the check_registry_compliance.py script again.")


if __name__ == "__main__":
    main()

