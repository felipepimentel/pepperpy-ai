#!/usr/bin/env python3
"""
Script to fix syntax errors in various files and B904 errors (raise ... from err).
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Files with syntax errors to fix
FILES_TO_FIX = {
    "pepperpy/cli/registry.py": {
        "patterns": [
            # Fix raise CLIError() with parameters on separate lines
            (
                r'raise CLIError\(\)\s+f"([^"]+)",\s+details=({[^}]+}),\s+\)',
                r'raise CLIError(f"\1", details=\2)',
            ),
            (
                r'raise CLIError\(\s+from\s+e\)\s+f"([^"]+)",\s+details=({[^}]+}),\s+\)',
                r'raise CLIError(f"\1", details=\2) from e',
            ),
        ],
    },
    "pepperpy/cloud/providers/gcp.py": {
        "patterns": [
            # Fix __init__ method
            (r"def __init__\(\)\s+self,", r"def __init__(self,"),
            # Fix raise ImportError with from None
            (
                r'raise ImportError\(\s+from\s+None\)\s+"([^"]+)"\s+"([^"]+)"\s+\)',
                r'raise ImportError("\1\2") from None',
            ),
            # Fix Client initialization
            (
                r"self\.client = storage\.Client\(\)\s+project=([^,]+),\s+credentials=([^,]+),\s+\)",
                r"self.client = storage.Client(project=\1, credentials=\2)",
            ),
            # Fix blob.generate_signed_url
            (
                r'return blob\.generate_signed_url\(\)\s+expiration=([^,]+),\s+method="GET",\s+\)',
                r'return blob.generate_signed_url(expiration=\1, method="GET")',
            ),
        ],
    },
    "pepperpy/core/config/providers/secure.py": {
        "patterns": [
            # Fix raise ImportError with from None
            (
                r'raise ImportError\(\s+from\s+None\)\s+"([^"]+)"\s+"([^"]+)"\s+\)',
                r'raise ImportError("\1\2") from None',
            ),
            # Fix PBKDF2HMAC initialization
            (
                r"kdf = PBKDF2HMAC\(\)\s+algorithm=([^,]+),\s+length=(\d+),\s+salt=([^,]+),\s+iterations=(\d+),\s+\)",
                r"kdf = PBKDF2HMAC(algorithm=\1, length=\2, salt=\3, iterations=\4)",
            ),
            # Fix dictionary comprehension
            (
                r'encrypted_values = {}\s+k: v for k, v in self\._config\.items\(\) if k\.startswith\(f"{([^}]+)}\."\)\s+}',
                r'encrypted_values = {k: v for k, v in self._config.items() if k.startswith(f"{\1}.")}',
            ),
        ],
    },
    "pepperpy/core/lifecycle/base.py": {
        "patterns": [
            # Fix import statement
            (
                r"LifecycleTransition,\s+from,\s+import,\s+typing,\s+\)",
                r"LifecycleTransition\n)",
            ),
        ],
    },
    "pepperpy/core/protocols/base.py": {
        "patterns": [
            # Fix decorator
            (
                r'@runtime_checkable\s+"""Protocol for components with lifecycle management."""',
                r'@runtime_checkable\nclass LifecycleProtocol(Protocol):\n    """Protocol for components with lifecycle management."""',
            ),
        ],
    },
    "pepperpy/core/resources/base.py": {
        "patterns": [
            # Fix import statement
            (r"ResourceType,\s+from,\s+import,\s+typing,\s+\)", r"ResourceType\n)"),
        ],
    },
}

# Files with B904 errors to fix
B904_FILES = [
    "pepperpy/core/config/base.py",
    "pepperpy/core/versioning/semver.py",
    "pepperpy/llm/providers/gemini/gemini_provider.py",
    "pepperpy/llm/providers/openai/openai_provider.py",
    "pepperpy/workflows/base.py",
    "pepperpy/workflows/core/base.py",
]


def fix_syntax_errors(file_path: str, patterns: List[Tuple[str, str]]) -> bool:
    """Fix syntax errors in a file using regex patterns."""
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return False

    try:
        content = path.read_text()
        original_content = content

        for pattern, replacement in patterns:
            content = re.sub(
                pattern, replacement, content, flags=re.MULTILINE | re.DOTALL,
            )

        if content != original_content:
            path.write_text(content)
            print(f"Fixed syntax errors in {file_path}")
            return True
        print(f"No changes needed in {file_path}")
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_b904_errors(file_path: str) -> bool:
    """Fix B904 errors (raise ... from err) in a file."""
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return False

    try:
        content = path.read_text()
        original_content = content

        # Pattern to find raise statements in except blocks without 'from'
        pattern = r"(except\s+([A-Za-z0-9_]+)(?:\s+as\s+([A-Za-z0-9_]+))?\s*:(?:[^\n]*\n)+?\s+)raise\s+([A-Za-z0-9_]+)\(([^)]*)\)(?!\s+from)"

        def replace_raise(match):
            except_block = match.group(1)
            exception_type = match.group(2)
            exception_var = match.group(3)
            raise_type = match.group(4)
            raise_args = match.group(5)

            if exception_var:
                return f"{except_block}raise {raise_type}({raise_args}) from {exception_var}"
            return f"{except_block}raise {raise_type}({raise_args}) from None"

        content = re.sub(
            pattern, replace_raise, content, flags=re.MULTILINE | re.DOTALL,
        )

        if content != original_content:
            path.write_text(content)
            print(f"Fixed B904 errors in {file_path}")
            return True
        print(f"No B904 errors found in {file_path}")
        return False
    except Exception as e:
        print(f"Error fixing B904 errors in {file_path}: {e}")
        return False


def main():
    """Main function to fix syntax errors and B904 errors."""
    syntax_fixed = 0
    b904_fixed = 0

    # Fix syntax errors
    for file_path, config in FILES_TO_FIX.items():
        if fix_syntax_errors(file_path, config["patterns"]):
            syntax_fixed += 1

    # Fix B904 errors
    for file_path in B904_FILES:
        if fix_b904_errors(file_path):
            b904_fixed += 1

    print("\nSummary:")
    print(f"- Fixed syntax errors in {syntax_fixed} files")
    print(f"- Fixed B904 errors in {b904_fixed} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
