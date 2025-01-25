#!/usr/bin/env python3
"""Script to update imports for moved profile files."""

import os
import re
from pathlib import Path

def update_imports(file_path: Path) -> None:
    """Update imports in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update imports
    replacements = {
        'from pepperpy.profile': 'from pepperpy.core.profile',
        'import pepperpy.profile': 'import pepperpy.core.profile',
    }
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
    
    if new_content != content:
        print(f"Updating imports in {file_path}")
        with open(file_path, 'w') as f:
            f.write(new_content)

def main():
    """Main function to update imports in all Python files."""
    root = Path('pepperpy')
    for file_path in root.rglob('*.py'):
        update_imports(file_path)

if __name__ == '__main__':
    main() 