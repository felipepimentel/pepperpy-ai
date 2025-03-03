#!/usr/bin/env python3
"""
Script to fix syntax errors in the semver.py file.
"""

import re
from pathlib import Path


def fix_semver_syntax():
    """Fix syntax errors in the semver.py file."""
    file_path = Path("pepperpy/core/versioning/semver.py")

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False

    try:
        content = file_path.read_text()
        original_content = content

        # Fix the syntax errors with 'from None' inside the parentheses
        patterns = [
            (
                r"raise VersionValidationError\(([^)]+), str\(e\) from None\)",
                r"raise VersionValidationError(\1, str(e)) from None",
            ),
        ]

        for pattern, replacement in patterns:
            content = re.sub(
                pattern, replacement, content, flags=re.MULTILINE | re.DOTALL
            )

        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed syntax errors in {file_path}")
            return True
        else:
            print(f"No changes needed in {file_path}")
            return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function."""
    if fix_semver_syntax():
        print("Successfully fixed semver.py syntax errors")
    else:
        print("No changes were made to semver.py")

    return 0


if __name__ == "__main__":
    main()
