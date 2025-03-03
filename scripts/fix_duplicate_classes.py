#!/usr/bin/env python3
"""
Script to fix duplicate class definitions in the codebase.
This script specifically targets the workflows/base.py file which has multiple
definitions of the same classes.
"""

import re
from typing import Dict, List, Tuple


def read_file(file_path: str) -> str:
    """Read file content."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_workflows_base() -> None:
    """Fix duplicate class definitions in workflows/base.py."""
    file_path = "pepperpy/workflows/base.py"
    content = read_file(file_path)

    # Identify duplicate class definitions
    class_pattern = r"(?:@dataclass\s+)?class\s+(\w+)(?:\([\w\s,]+\))?:"
    class_matches = re.finditer(class_pattern, content)

    class_positions: Dict[str, List[Tuple[int, int]]] = {}
    for match in class_matches:
        class_name = match.group(1)
        if class_name not in class_positions:
            class_positions[class_name] = []
        class_positions[class_name].append((match.start(), match.end()))

    # Find classes with multiple definitions
    duplicate_classes = {
        name: positions
        for name, positions in class_positions.items()
        if len(positions) > 1
    }

    if not duplicate_classes:
        print("No duplicate classes found in workflows/base.py")
        return

    print(f"Found {len(duplicate_classes)} classes with duplicate definitions:")
    for class_name, positions in duplicate_classes.items():
        print(f"  - {class_name}: {len(positions)} definitions")

    # Create a backup of the original file
    backup_path = f"{file_path}.bak"
    write_file(backup_path, content)
    print(f"Created backup at {backup_path}")

    # Fix WorkflowStep class (most problematic)
    if "WorkflowStep" in duplicate_classes:
        # Rename the first definition to WorkflowStepConfig
        content = re.sub(
            r"@dataclass\s+class\s+WorkflowStep",
            "@dataclass\nclass WorkflowStepConfig",
            content,
            count=1,
        )

        # Rename the abstract base class to AbstractWorkflowStep
        content = re.sub(
            r"class\s+WorkflowStep\(ABC\)",
            "class AbstractWorkflowStep(ABC)",
            content,
            count=1,
        )

        # Update references to the abstract class
        content = re.sub(
            r"def\s+add_step\(self,\s+step:\s+WorkflowStep\)",
            "def add_step(self, step: AbstractWorkflowStep)",
            content,
        )

        content = re.sub(
            r"def\s+get_steps\(self\)\s+->\s+List\[WorkflowStep\]",
            "def get_steps(self) -> List[AbstractWorkflowStep]",
            content,
        )

        content = re.sub(
            r"self\._steps:\s+List\[WorkflowStep\]",
            "self._steps: List[AbstractWorkflowStep]",
            content,
        )

        content = re.sub(
            r"async\s+def\s+_execute_step\(self,\s+step:\s+WorkflowStep",
            "async def _execute_step(self, step: AbstractWorkflowStep",
            content,
        )

        content = re.sub(
            r"async\s+def\s+execute_step\(self,\s+step:\s+WorkflowStep",
            "async def execute_step(self, step: AbstractWorkflowStep",
            content,
        )

    # Fix WorkflowDefinition class
    if "WorkflowDefinition" in duplicate_classes:
        # Rename the abstract base class to AbstractWorkflowDefinition
        content = re.sub(
            r"class\s+WorkflowDefinition\(ABC\)",
            "class AbstractWorkflowDefinition(ABC)",
            content,
            count=1,
        )

    # Write the fixed content
    write_file(file_path, content)
    print(f"Fixed duplicate class definitions in {file_path}")


def main() -> None:
    """Main function."""
    print("Fixing duplicate class definitions...")
    fix_workflows_base()
    print("Done!")


if __name__ == "__main__":
    main()
