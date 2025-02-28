#!/usr/bin/env python3
"""Script to fix imports after restructuring.

This script updates import statements in Python files to reflect the new
project structure after the restructuring process.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Pattern, Set

# Define the import mappings
IMPORT_MAPPINGS = {
    # Moved modules to capabilities
    "from pepperpy.audio": "from pepperpy.capabilities.audio",
    "import pepperpy.audio": "import pepperpy.capabilities.audio",
    "from pepperpy.vision": "from pepperpy.capabilities.vision",
    "import pepperpy.vision": "import pepperpy.capabilities.vision",
    "from pepperpy.multimodal": "from pepperpy.capabilities.multimodal",
    "import pepperpy.multimodal": "import pepperpy.capabilities.multimodal",
    # Moved providers
    "from pepperpy.providers.llm": "from pepperpy.providers.llm",
    "import pepperpy.providers.llm": "import pepperpy.providers.llm",
    "from pepperpy.rag.providers": "from pepperpy.providers.rag",
    "import pepperpy.rag.providers": "import pepperpy.providers.rag",
    "from pepperpy.cloud.providers": "from pepperpy.providers.cloud",
    "import pepperpy.cloud.providers": "import pepperpy.providers.cloud",
    # Cache consolidation
    "from pepperpy.memory.cache": "from pepperpy.caching.memory_cache",
    "import pepperpy.memory.cache": "import pepperpy.caching.memory_cache",
}

def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file.
    
    Args:
        file_path: Path to the file to fix
        
    Returns:
        True if changes were made, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        original_lines = lines.copy()
        modified = False
        
        for i, line in enumerate(lines):
            for old_import, new_import in IMPORT_MAPPINGS.items():
                # Check if the line starts with the old import pattern
                if line.strip().startswith(old_import):
                    # Replace only at the beginning of the line or after whitespace
                    new_line = line.replace(old_import, new_import, 1)
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
                        break
        
        # If content changed, write it back
        if modified:
            print(f"Fixing imports in {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        
        return False
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory recursively.
    
    Args:
        directory: Directory to search in
        
    Returns:
        List of paths to Python files
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".md"):
                python_files.append(Path(root) / file)
    return python_files

def main():
    """Main function."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Find all Python files
    python_files = find_python_files(project_root)
    
    # Fix imports in each file
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()
