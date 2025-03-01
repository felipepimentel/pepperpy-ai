#!/usr/bin/env python3
"""
Script to clean up redundant modules after provider consolidation.

This script:
1. Verifies that all providers have been successfully migrated
2. Creates compatibility stubs in original locations
3. Removes redundant modules
"""

import os
import shutil
from pathlib import Path

# Define paths
REPO_ROOT = Path(__file__).parent.parent
PEPPERPY_DIR = REPO_ROOT / "pepperpy"

# Define paths for original and new locations
ORIGINAL_LOCATIONS = {
    "llm": PEPPERPY_DIR / "llm" / "providers",
    "storage": PEPPERPY_DIR / "storage",
    "cloud": PEPPERPY_DIR / "cloud",
}

NEW_LOCATIONS = {
    "llm": PEPPERPY_DIR / "providers" / "llm",
    "storage": PEPPERPY_DIR / "providers" / "storage",
    "cloud": PEPPERPY_DIR / "providers" / "cloud",
}

INTERFACES_DIR = PEPPERPY_DIR / "interfaces"


def create_compatibility_stub(original_module, new_module):
    """Create a compatibility stub that imports from the new location."""
    os.makedirs(os.path.dirname(original_module), exist_ok=True)

    with open(original_module, "w") as f:
        f.write(f"""# This is a compatibility stub that will be removed in a future version
import warnings

warnings.warn(
    "This module is deprecated. Please use '{new_module}' instead.",
    DeprecationWarning,
    stacklevel=2
)

from {new_module} import *
""")
    print(f"Created compatibility stub at {original_module} pointing to {new_module}")


def verify_migration(domain, original_location, new_location):
    """Verify that all providers have been successfully migrated."""
    if not os.path.exists(new_location):
        print(f"ERROR: New location {new_location} does not exist!")
        return False

    if not os.path.exists(original_location):
        print(
            f"Original location {original_location} does not exist, skipping verification"
        )
        return True

    # Check if all original providers exist in the new location
    all_migrated = True
    for root, dirs, files in os.walk(original_location):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                original_file = os.path.join(root, file)
                relative_path = os.path.relpath(original_file, original_location)
                new_file = os.path.join(new_location, relative_path)

                if not os.path.exists(new_file):
                    print(f"ERROR: Provider {relative_path} not migrated to {new_file}")
                    all_migrated = False

    return all_migrated


def create_compatibility_stubs(domain, original_location, new_location):
    """Create compatibility stubs for all providers in the original location."""
    if not os.path.exists(original_location):
        print(
            f"Original location {original_location} does not exist, skipping stub creation"
        )
        return

    # Create stubs for all Python files
    for root, dirs, files in os.walk(original_location):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                original_file = os.path.join(root, file)
                relative_path = os.path.relpath(original_file, PEPPERPY_DIR)
                module_path = relative_path.replace("/", ".").replace(".py", "")
                new_module_path = (
                    f"pepperpy.providers.{domain}" + module_path.split(f"{domain}")[-1]
                )

                # Backup the original file
                backup_file = original_file + ".bak"
                shutil.copy2(original_file, backup_file)

                # Create the stub
                create_compatibility_stub(original_file, new_module_path)


def main():
    """Main function to clean up redundant modules."""
    print("Starting cleanup of redundant modules...")

    # Step 1: Verify that all providers have been successfully migrated
    print("\n=== Verifying Migration ===")
    all_migrated = True
    for domain, original_location in ORIGINAL_LOCATIONS.items():
        new_location = NEW_LOCATIONS[domain]
        if not verify_migration(domain, original_location, new_location):
            all_migrated = False

    if not all_migrated:
        print(
            "\nERROR: Not all providers have been migrated. Please fix the issues before continuing."
        )
        return

    # Step 2: Create compatibility stubs
    print("\n=== Creating Compatibility Stubs ===")
    for domain, original_location in ORIGINAL_LOCATIONS.items():
        new_location = NEW_LOCATIONS[domain]
        create_compatibility_stubs(domain, original_location, new_location)

    print("\nCleanup completed successfully!")
    print("\nNOTE: Original modules have been replaced with compatibility stubs.")
    print("These stubs will be removed in a future version.")


if __name__ == "__main__":
    main()
