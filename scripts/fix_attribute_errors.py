#!/usr/bin/env python3
"""
Script to fix attribute errors in the codebase.
This script specifically targets the workflows/base.py file which has issues
with unknown attributes like _callback and _metrics.
"""

import re


def read_file(file_path: str) -> str:
    """Read file content."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_base_workflow_attributes() -> None:
    """Fix attribute errors in BaseWorkflow class."""
    file_path = "pepperpy/workflows/base.py"
    content = read_file(file_path)

    # Create a backup of the original file
    backup_path = f"{file_path}.attr.bak"
    write_file(backup_path, content)
    print(f"Created backup at {backup_path}")

    # Find the BaseWorkflow class definition
    base_workflow_match = re.search(r"class\s+BaseWorkflow\(ABC\):", content)
    if not base_workflow_match:
        print("BaseWorkflow class not found in workflows/base.py")
        return

    # Find the __init__ method of BaseWorkflow
    init_match = re.search(
        r"def\s+__init__\s*\(\s*self,\s*definition:\s*WorkflowDefinition,\s*workflow_id:\s*Optional\[WorkflowID\]\s*=\s*None,\s*\)\s*->\s*None:\s*(?:\"\"\"[\s\S]*?\"\"\")?\s*",
        content[base_workflow_match.end() :],
    )

    if not init_match:
        print("__init__ method not found in BaseWorkflow class")
        return

    # Find the end of the __init__ method
    init_end = base_workflow_match.end() + init_match.end()

    # Add missing attributes to __init__
    missing_attributes = """
        self._callback = None
        self._metrics = {}
        self._metrics_manager = None  # Will be initialized later
"""

    # Insert the missing attributes before the end of __init__
    content_lines = content.split("\n")

    # Find the line number of init_end
    line_count = 0
    char_count = 0
    for i, line in enumerate(content_lines):
        char_count += len(line) + 1  # +1 for newline
        if char_count >= init_end:
            line_count = i
            break

    # Find the indentation level
    indentation = ""
    for char in content_lines[line_count]:
        if char.isspace():
            indentation += char
        else:
            break

    # Format the missing attributes with the correct indentation
    formatted_attributes = "\n".join(
        indentation + line for line in missing_attributes.strip().split("\n")
    )

    # Insert the missing attributes
    content_lines.insert(line_count, formatted_attributes)

    # Join the lines back together
    new_content = "\n".join(content_lines)

    # Write the fixed content
    write_file(file_path, new_content)
    print(f"Fixed attribute errors in {file_path}")


def main() -> None:
    """Main function."""
    print("Fixing attribute errors...")
    fix_base_workflow_attributes()
    print("Done!")


if __name__ == "__main__":
    main()
