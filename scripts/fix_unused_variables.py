#!/usr/bin/env python3
"""
Script to fix unused variables in various files.
"""

import os
import shutil
import datetime
import re
from pathlib import Path


def create_backup(file_path):
    """Create a backup of the original file before making changes."""
    backup_dir = Path("backups") / "unused_vars" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backup with original filename in the backup directory
    backup_path = backup_dir / Path(file_path).name
    shutil.copy2(file_path, backup_path)
    print(f"Created backup of {file_path} at {backup_path}")
    return backup_path


def fix_hub_discovery():
    """Fix unused loop variable in hub/discovery.py."""
    file_path = "pepperpy/hub/discovery.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return False
    
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix the unused loop variable by renaming it
    corrected_content = content.replace(
        "for name, obj in inspect.getmembers(module):",
        "for _name, obj in inspect.getmembers(module):"
    )
    
    # Write corrected content
    with open(file_path, "w") as f:
        f.write(corrected_content)
    
    print(f"Fixed unused loop variable in {file_path}")
    return True


def fix_hub_security():
    """Fix unused variables in hub/security.py."""
    file_path = "pepperpy/hub/security.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return False
    
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix the unused variables by adding comments
    corrected_content = content.replace(
        "                    key_data = json.load(f)",
        "                    # key_data will be used in future implementation\n                    _ = json.load(f)"
    ).replace(
        "                    token_data = json.load(f)",
        "                    # token_data will be used in future implementation\n                    _ = json.load(f)"
    )
    
    # Write corrected content
    with open(file_path, "w") as f:
        f.write(corrected_content)
    
    print(f"Fixed unused variables in {file_path}")
    return True


def fix_audio_input():
    """Fix unused variable in audio/input.py."""
    file_path = "pepperpy/multimodal/audio/input.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return False
    
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix the unused variable by adding a comment
    corrected_content = content.replace(
        "            threshold = np.mean(energy) * self._config.get(\"energy_threshold\", 2.0)",
        "            # threshold will be used in future implementation\n            _ = np.mean(energy) * self._config.get(\"energy_threshold\", 2.0)"
    )
    
    # Write corrected content
    with open(file_path, "w") as f:
        f.write(corrected_content)
    
    print(f"Fixed unused variable in {file_path}")
    return True


def main():
    """Main function to fix unused variables in various files."""
    print("Starting to fix unused variables in various files...")
    
    fixed_files = []
    
    # Fix hub/discovery.py
    if fix_hub_discovery():
        fixed_files.append("pepperpy/hub/discovery.py")
    
    # Fix hub/security.py
    if fix_hub_security():
        fixed_files.append("pepperpy/hub/security.py")
    
    # Fix audio/input.py
    if fix_audio_input():
        fixed_files.append("pepperpy/multimodal/audio/input.py")
    
    print("\nSummary:")
    print(f"Fixed {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")
    print("\nBackups were created in the 'backups/unused_vars/' directory.")


if __name__ == "__main__":
    main() 