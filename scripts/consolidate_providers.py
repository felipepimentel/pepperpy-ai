#!/usr/bin/env python3
"""
Script to consolidate providers from multimodal directories to the centralized providers directory.

This script:
1. Copies any unique content from multimodal/audio/providers to providers/audio
2. Copies any unique content from multimodal/vision/providers to providers/vision
3. Updates imports in affected files
4. Removes the original multimodal provider directories after migration
"""

import os
import re
import shutil
from pathlib import Path

# Define paths
REPO_ROOT = Path(__file__).parent.parent
MULTIMODAL_AUDIO_PROVIDERS = (
    REPO_ROOT / "pepperpy" / "multimodal" / "audio" / "providers"
)
MULTIMODAL_VISION_PROVIDERS = (
    REPO_ROOT / "pepperpy" / "multimodal" / "vision" / "providers"
)
CENTRAL_AUDIO_PROVIDERS = REPO_ROOT / "pepperpy" / "providers" / "audio"
CENTRAL_VISION_PROVIDERS = REPO_ROOT / "pepperpy" / "providers" / "vision"

# Define import mappings for updating imports
IMPORT_MAPPINGS = {
    r"from pepperpy\.multimodal\.audio\.providers": "from pepperpy.providers.audio",
    r"from pepperpy\.multimodal\.vision\.providers": "from pepperpy.providers.vision",
    r"import pepperpy\.multimodal\.audio\.providers": "import pepperpy.providers.audio",
    r"import pepperpy\.multimodal\.vision\.providers": "import pepperpy.providers.vision",
}


def copy_directory_contents(src_dir, dest_dir):
    """Copy contents from src_dir to dest_dir, overwriting existing files."""
    print(f"Copying contents from {src_dir} to {dest_dir}")

    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    # Copy all files and directories
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dest_item = os.path.join(dest_dir, item)

        if os.path.isdir(src_item):
            # If it's a directory, recursively copy its contents
            copy_directory_contents(src_item, dest_item)
        else:
            # If it's a file, copy it
            print(f"  Copying {src_item} to {dest_item}")
            shutil.copy2(src_item, dest_item)


def update_imports_in_file(file_path):
    """Update imports in a single file according to the mappings."""
    print(f"Updating imports in {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = []

    for pattern, replacement in IMPORT_MAPPINGS.items():
        # Use regex to find and replace imports
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            changes.append(f"Updated {count} occurrences of {pattern} to {replacement}")
            content = new_content

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Made {len(changes)} changes:")
        for change in changes:
            print(f"    - {change}")
    else:
        print("  No changes needed")


def update_imports_in_directory(directory):
    """Update imports in all Python files in the given directory and its subdirectories."""
    print(f"Updating imports in directory: {directory}")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                update_imports_in_file(file_path)


def main():
    """Main function to consolidate providers."""
    print("Starting provider consolidation...")

    # Step 1: Copy multimodal audio providers to central providers
    print("\n=== Consolidating Audio Providers ===")
    copy_directory_contents(MULTIMODAL_AUDIO_PROVIDERS, CENTRAL_AUDIO_PROVIDERS)

    # Step 2: Copy multimodal vision providers to central providers
    print("\n=== Consolidating Vision Providers ===")
    copy_directory_contents(MULTIMODAL_VISION_PROVIDERS, CENTRAL_VISION_PROVIDERS)

    # Step 3: Update imports in the pepperpy directory
    print("\n=== Updating Imports ===")
    update_imports_in_directory(REPO_ROOT / "pepperpy")

    # Step 4: Remove the original multimodal provider directories
    print("\n=== Cleaning Up ===")
    print(f"Removing {MULTIMODAL_AUDIO_PROVIDERS}")
    shutil.rmtree(MULTIMODAL_AUDIO_PROVIDERS)
    print(f"Removing {MULTIMODAL_VISION_PROVIDERS}")
    shutil.rmtree(MULTIMODAL_VISION_PROVIDERS)

    print("\nProvider consolidation completed successfully!")


if __name__ == "__main__":
    main()
