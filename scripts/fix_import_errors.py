#!/usr/bin/env python3
"""
Script to fix import errors in the codebase.
This script adds missing imports and fixes incorrect imports in various files.
"""

import os
import re
from typing import Dict, List


def read_file(file_path: str) -> str:
    """Read file content."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_imports_in_file(file_path: str, imports_to_add: Dict[str, List[str]]) -> bool:
    """Fix imports in a file.

    Args:
        file_path: Path to the file
        imports_to_add: Dictionary mapping import statements to symbols

    Returns:
        True if file was modified, False otherwise

    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    content = read_file(file_path)
    original_content = content

    # Create a backup of the original file
    backup_path = f"{file_path}.import.bak"
    write_file(backup_path, content)

    # Add missing imports
    for import_stmt, symbols in imports_to_add.items():
        # Check if import already exists
        import_pattern = re.escape(import_stmt)
        import_match = re.search(rf"from\s+{import_pattern}\s+import", content)

        if import_match:
            # Import exists, check if symbols need to be added
            for symbol in symbols:
                symbol_pattern = re.escape(symbol)
                symbol_match = re.search(
                    rf"from\s+{import_pattern}\s+import.*{symbol_pattern}", content,
                )

                if not symbol_match:
                    # Add symbol to existing import
                    content = re.sub(
                        rf"(from\s+{import_pattern}\s+import\s+[^\\]+?)(\n)",
                        rf"\1, {symbol}\2",
                        content,
                    )
        else:
            # Add new import statement
            import_line = f"from {import_stmt} import {', '.join(symbols)}\n"

            # Find the last import statement
            last_import_match = re.search(r"(from|import).*\n", content)
            if last_import_match:
                # Insert after the last import
                last_import_end = last_import_match.end()
                content = (
                    content[:last_import_end] + import_line + content[last_import_end:]
                )
            else:
                # Insert at the beginning of the file
                content = import_line + content

    # Write the modified content if changes were made
    if content != original_content:
        write_file(file_path, content)
        print(f"Fixed imports in {file_path}")
        return True

    print(f"No changes needed in {file_path}")
    return False


def fix_all_import_errors() -> None:
    """Fix import errors in all files."""
    # Define imports to add for each file
    imports_by_file = {
        "pepperpy/multimodal/synthesis/processors/effects.py": {
            "typing": ["Any", "List", "Optional", "Union"],
            "pydantic": ["BaseModel", "Field"],
            "pydantic.dataclasses": ["dataclass"],
            "pepperpy.multimodal.synthesis.base": [
                "AudioData",
                "AudioProcessor",
                "SynthesisError",
            ],
        },
        "pepperpy/observability/logging/formatters.py": {
            "typing": ["Any", "Callable", "Dict", "Optional"],
            "datetime": ["datetime"],
            "logging": ["LogRecord"],
            "pepperpy.core.common.models": ["BaseModel", "Field"],
        },
        "pepperpy/observability/logging/filters.py": {
            "typing": ["Any", "Dict", "Set"],
            "pepperpy.observability.logging.base": ["LogLevel", "LogRecord"],
        },
        "pepperpy/observability/logging/handlers.py": {
            "typing": ["Any", "Dict", "Optional"],
            "asyncio": ["Lock"],
            "os": ["path"],
            "pepperpy.observability.logging.base": ["LogHandler", "LogRecord"],
        },
        "pepperpy/workflows/base.py": {
            "typing": ["Any", "Dict", "List", "Optional", "Set", "Tuple", "Union"],
            "abc": ["ABC", "abstractmethod"],
            "dataclasses": ["dataclass", "field"],
            "datetime": ["datetime"],
            "enum": ["Enum"],
            "uuid": ["UUID"],
            "pepperpy.core.base": [
                "ComponentBase",
                "ComponentCallback",
                "ComponentConfig",
                "ComponentState",
            ],
            "pepperpy.core.types": ["WorkflowID"],
            "pepperpy.monitoring.metrics": ["Counter", "Histogram", "MetricsManager"],
        },
        "pepperpy/rag/retrieval/system.py": {
            "typing": ["Any", "Dict", "List", "Optional", "Union"],
            "abc": ["ABC", "abstractmethod"],
            "pepperpy.core.lifecycle": ["Lifecycle"],
            "pepperpy.rag.embeddings.base": ["Embedder", "TextEmbedder"],
            "pepperpy.rag.indexing.base": ["Indexer", "VectorIndexer"],
        },
        "pepperpy/workflows/execution/scheduler.py": {
            "typing": ["Any", "Dict", "List", "Optional", "Union"],
            "asyncio": ["Lock", "Task"],
            "dataclasses": ["dataclass", "field"],
            "datetime": ["datetime", "timedelta"],
            "logging": ["getLogger"],
            "uuid": ["UUID"],
            "pepperpy.core.base": ["ComponentBase", "ComponentConfig"],
            "pepperpy.core.types": ["WorkflowID"],
            "pepperpy.monitoring.metrics": ["Counter", "Histogram"],
        },
        "pepperpy/workflows/migration.py": {
            "typing": ["Any", "Dict", "List", "Optional", "Tuple"],
            "re": ["Match", "Pattern"],
            "pepperpy.workflows.base": ["WorkflowDefinition"],
        },
    }

    # Fix imports in each file
    for file_path, imports in imports_by_file.items():
        fix_imports_in_file(file_path, imports)


def main() -> None:
    """Main function."""
    print("Fixing import errors...")
    fix_all_import_errors()
    print("Done!")


if __name__ == "__main__":
    main()
