#!/usr/bin/env python3
"""Unified code analyzer for PepperPy.

This script combines multiple code analysis tools into a single unified interface:
- Circular dependency detection
- Domain conventions validation
- Project structure validation
- File header validation
- Registry compliance checking
- Compatibility stubs coverage

Usage:
    python scripts/code_analyzer.py [--all] [--circular] [--domain] [--structure] [--headers] [--registry] [--stubs]
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("code_analyzer")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Add the project root to the Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Constants for domain conventions
REQUIRED_FILES = ["__init__.py", "base.py", "types.py", "factory.py", "registry.py"]
OPTIONAL_FILES = ["config.py", "utils.py", "errors.py", "defaults.py", "pipeline.py"]
COMMON_SUBDIRS = ["providers", "models", "processors"]

# Constants for header validation
REQUIRED_FIELDS = ["file", "purpose", "component", "created"]
OPTIONAL_FIELDS = ["task", "status"]
VALID_STATUSES = ["active", "deprecated", "experimental"]
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
TASK_PATTERN = r"^TASK-\d{3}$"

# Constants for stubs coverage
MOVED_MODULES = {
    # Original location: New location
    "pepperpy/audio": "pepperpy/capabilities/audio",
    "pepperpy/vision": "pepperpy/capabilities/vision",
    "pepperpy/multimodal": "pepperpy/capabilities/multimodal",
    "pepperpy/llm/providers": "pepperpy/providers/llm",
    "pepperpy/rag/providers": "pepperpy/providers/rag",
    "pepperpy/cloud/providers": "pepperpy/providers/cloud",
    "pepperpy/memory/cache.py": "pepperpy/caching/memory_cache.py",
}

# Constants for registry compliance
REGISTRY_FILES = [
    "pepperpy/agents/registry.py",
    "pepperpy/workflows/registry.py",
    "pepperpy/rag/registry.py",
    "pepperpy/cli/registry.py",
]

# Required project structure
REQUIRED_STRUCTURE = {
    "pepperpy": {
        "core": {
            "errors.py": None,
            "extensions.py": None,
            "layers.py": None,
            "types.py": None,
        },
        "agents": {
            "base.py": None,
            "config.py": None,
            "factory.py": None,
        },
        "workflows": {
            "base.py": None,
            "config.py": None,
            "steps.py": None,
        },
        "providers": {
            "base.py": None,
            "llm": {
                "base.py": None,
            },
        },
    },
}

# Type aliases
ErrorList = List[str]
ValidationResult = List[Tuple[Path, ErrorList]]


#
# Circular Dependencies Analysis
#
def extract_imports(file_path: Path) -> List[str]:
    """Extract import statements from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of imported modules
    """
    imports = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Match 'import pepperpy.x.y' patterns
        import_pattern = r"import\s+(pepperpy\.[^\s;]+)"
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))

        # Match 'from pepperpy.x.y import z' patterns
        from_pattern = r"from\s+(pepperpy\.[^\s;]+)\s+import"
        for match in re.finditer(from_pattern, content):
            imports.append(match.group(1))

    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")

    return imports


def build_dependency_graph(root_dir: Path) -> Dict[str, Set[str]]:
    """Build a dependency graph for the project.

    Args:
        root_dir: Root directory of the project

    Returns:
        Dictionary mapping module paths to sets of imported modules
    """
    graph = {}
    pepperpy_dir = root_dir / "pepperpy"

    for file_path in pepperpy_dir.glob("**/*.py"):
        if "__pycache__" in str(file_path):
            continue

        # Convert file path to module path
        rel_path = file_path.relative_to(root_dir)
        module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")

        # Extract imports
        imports = extract_imports(file_path)
        graph[module_path] = set(imports)

    return graph


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find cycles in the dependency graph using DFS.

    Args:
        graph: Dependency graph

    Returns:
        List of cycles found in the graph
    """
    cycles = []
    visited = set()
    path = []
    path_set = set()

    def dfs(node: str) -> None:
        if node in path_set:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)
        path_set.add(node)

        if node in graph:
            for neighbor in graph[node]:
                dfs(neighbor)

        path.pop()
        path_set.remove(node)

    for node in graph:
        dfs(node)

    return cycles


def check_circular_dependencies() -> List[List[str]]:
    """Check for circular dependencies in the project.

    Returns:
        List of circular dependency chains
    """
    logger.info("Checking for circular dependencies...")
    graph = build_dependency_graph(PROJECT_ROOT)
    cycles = find_cycles(graph)

    if cycles:
        logger.warning(f"Found {len(cycles)} circular dependencies")
        for i, cycle in enumerate(cycles, 1):
            logger.warning(f"Cycle {i}: {' -> '.join(cycle)}")
    else:
        logger.info("No circular dependencies found")

    return cycles


#
# Domain Conventions Analysis
#
def check_domain(domain_path: Path) -> Tuple[List[str], List[str]]:
    """Check if a domain follows the conventions.

    Args:
        domain_path: Path to the domain directory

    Returns:
        Tuple of missing required files and existing files
    """
    if not domain_path.exists() or not domain_path.is_dir():
        logger.error(f"Domain directory '{domain_path}' does not exist")
        return [], []

    # List all files in the domain directory
    domain_files = [f.name for f in domain_path.glob("*.py")]

    # Check required files
    missing_files = [f for f in REQUIRED_FILES if f not in domain_files]

    return missing_files, domain_files


def check_all_domains(base_dir: Path) -> Dict[str, Tuple[List[str], List[str]]]:
    """Check all domains in the project.

    Args:
        base_dir: Base directory to search for domains

    Returns:
        Dictionary mapping domain names to tuples of missing files and existing files
    """
    results = {}

    # Find all potential domain directories
    for domain_dir in base_dir.glob("*"):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue

        # Check if this looks like a domain (has __init__.py)
        if (domain_dir / "__init__.py").exists():
            domain_name = domain_dir.name
            missing, existing = check_domain(domain_dir)
            results[domain_name] = (missing, existing)

    return results


def check_domain_conventions() -> Dict[str, Tuple[List[str], List[str]]]:
    """Check domain conventions in the project.

    Returns:
        Dictionary mapping domain names to tuples of missing files and existing files
    """
    logger.info("Checking domain conventions...")
    pepperpy_dir = PROJECT_ROOT / "pepperpy"
    results = check_all_domains(pepperpy_dir)

    for domain, (missing, existing) in results.items():
        if missing:
            logger.warning(
                f"Domain '{domain}' is missing required files: {', '.join(missing)}"
            )
        else:
            logger.info(f"Domain '{domain}' follows conventions")

    return results


#
# Project Structure Validation
#
def validate_path_exists(path: Path, required: Dict) -> List[str]:
    """Validate that a path exists and contains required files/directories.

    Args:
        path: Path to validate
        required: Dictionary of required files/directories

    Returns:
        List of validation errors
    """
    errors = []

    if not path.exists():
        errors.append(f"Missing path: {path}")
        return errors

    for name, sub_required in required.items():
        sub_path = path / name

        if sub_required is None:
            # This is a file
            if not sub_path.exists() or not sub_path.is_file():
                errors.append(f"Missing file: {sub_path}")
        else:
            # This is a directory
            if not sub_path.exists() or not sub_path.is_dir():
                errors.append(f"Missing directory: {sub_path}")
            else:
                # Recursively validate subdirectories
                errors.extend(validate_path_exists(sub_path, sub_required))

    return errors


def validate_naming_conventions(
    path: Path, seen_files: Optional[Set[Path]] = None
) -> List[str]:
    """Validate naming conventions for files and directories.

    Args:
        path: Path to validate
        seen_files: Set of files already seen (to avoid duplicates)

    Returns:
        List of validation errors
    """
    if seen_files is None:
        seen_files = set()

    errors = []

    # Skip hidden directories and __pycache__
    if path.name.startswith(".") or path.name == "__pycache__":
        return errors

    # Check Python files
    if path.is_file() and path.suffix == ".py":
        if path in seen_files:
            return errors

        seen_files.add(path)

        # Check naming convention (snake_case)
        if not re.match(r"^[a-z][a-z0-9_]*\.py$", path.name):
            errors.append(f"Invalid file name (not snake_case): {path}")

    # Recursively check directories
    elif path.is_dir():
        # Check directory naming convention (snake_case)
        if not re.match(r"^[a-z][a-z0-9_]*$", path.name):
            errors.append(f"Invalid directory name (not snake_case): {path}")

        # Check subdirectories and files
        for sub_path in path.iterdir():
            errors.extend(validate_naming_conventions(sub_path, seen_files))

    return errors


def validate_structure() -> List[str]:
    """Validate the project structure.

    Returns:
        List of validation errors
    """
    logger.info("Validating project structure...")
    errors = []

    # Validate required structure
    errors.extend(
        validate_path_exists(PROJECT_ROOT, {"pepperpy": REQUIRED_STRUCTURE["pepperpy"]})
    )

    # Validate naming conventions
    errors.extend(validate_naming_conventions(PROJECT_ROOT / "pepperpy"))

    if errors:
        logger.warning(f"Found {len(errors)} structure validation errors")
        for error in errors:
            logger.warning(error)
    else:
        logger.info("Project structure is valid")

    return errors


#
# File Header Validation
#
def parse_header(content: str) -> Dict[str, str]:
    """Parse file header into fields.

    Args:
        content: File content to parse

    Returns:
        Dictionary of field names to values
    """
    fields = {}
    header_match = re.search(r'"""(.*?)"""', content, re.DOTALL)

    if not header_match:
        return fields

    header = header_match.group(1).strip()

    # Extract fields from header
    current_field = None
    current_value = []

    for line in header.split("\n"):
        line = line.strip()

        if not line:
            continue

        # Check if this line starts a new field
        field_match = re.match(r"^([A-Za-z]+):\s*(.*)$", line)

        if field_match:
            # Save previous field if any
            if current_field:
                fields[current_field.lower()] = "\n".join(current_value).strip()

            # Start new field
            current_field = field_match.group(1)
            current_value = [field_match.group(2)]
        elif current_field:
            # Continue previous field
            current_value.append(line)

    # Save last field
    if current_field:
        fields[current_field.lower()] = "\n".join(current_value).strip()

    # First line is usually the file description
    if not fields and header:
        fields["file"] = header.split("\n")[0].strip()

    return fields


def validate_header(file_path: Path) -> List[str]:
    """Validate a file header.

    Args:
        file_path: Path to the file

    Returns:
        List of validation errors
    """
    errors = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        fields = parse_header(content)

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in fields:
                errors.append(f"Missing required header field: {field}")

        # Validate date format
        if "created" in fields and not re.match(DATE_PATTERN, fields["created"]):
            errors.append(f"Invalid date format: {fields['created']}")

        # Validate status
        if "status" in fields and fields["status"] not in VALID_STATUSES:
            errors.append(f"Invalid status: {fields['status']}")

        # Validate task ID
        if "task" in fields and not re.match(TASK_PATTERN, fields["task"]):
            errors.append(f"Invalid task ID: {fields['task']}")

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return errors


def should_check_file(path: Path) -> bool:
    """Check if a file should be validated.

    Args:
        path: Path to the file

    Returns:
        True if the file should be validated, False otherwise
    """
    # Skip non-Python files
    if path.suffix != ".py":
        return False

    # Skip __pycache__ and hidden directories
    if "__pycache__" in str(path) or any(part.startswith(".") for part in path.parts):
        return False

    # Skip test files
    if "tests" in path.parts:
        return False

    return True


def check_headers() -> List[Tuple[Path, List[str]]]:
    """Check file headers in the project.

    Returns:
        List of tuples of file paths and validation errors
    """
    logger.info("Checking file headers...")
    results = []

    for file_path in (PROJECT_ROOT / "pepperpy").glob("**/*.py"):
        if should_check_file(file_path):
            errors = validate_header(file_path)
            if errors:
                results.append((file_path, errors))

    if results:
        logger.warning(f"Found {len(results)} files with header issues")
        for file_path, errors in results:
            logger.warning(f"Header issues in {file_path}:")
            for error in errors:
                logger.warning(f"  - {error}")
    else:
        logger.info("All file headers are valid")

    return results


#
# Registry Compliance Checking
#
def find_registry_files() -> List[Path]:
    """Find registry files in the project.

    Returns:
        List of registry file paths
    """
    registry_files = []

    for registry_path in REGISTRY_FILES:
        path = PROJECT_ROOT / registry_path
        if path.exists():
            registry_files.append(path)

    return registry_files


def check_registry_compliance() -> Dict[Path, Dict[str, bool]]:
    """Check registry compliance in the project.

    Returns:
        Dictionary mapping registry files to compliance results
    """
    logger.info("Checking registry compliance...")
    results = {}

    registry_files = find_registry_files()

    for file_path in registry_files:
        compliance = {}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check for Registry class
            compliance["has_registry_class"] = "class Registry" in content

            # Check for register method
            compliance["has_register_method"] = "def register" in content

            # Check for get method
            compliance["has_get_method"] = "def get" in content

            # Check for list method
            compliance["has_list_method"] = "def list" in content

            results[file_path] = compliance

        except Exception as e:
            logger.error(f"Error checking registry compliance for {file_path}: {e}")

    # Log results
    for file_path, compliance in results.items():
        if all(compliance.values()):
            logger.info(f"Registry {file_path} is compliant")
        else:
            logger.warning(f"Registry {file_path} is not fully compliant:")
            for check, result in compliance.items():
                if not result:
                    logger.warning(f"  - Missing: {check}")

    return results


#
# Compatibility Stubs Coverage
#
def find_stubs(project_root: Path) -> Dict[str, bool]:
    """Find compatibility stubs in the project.

    Args:
        project_root: Path to the project root

    Returns:
        Dictionary mapping module paths to boolean indicating if stub exists
    """
    stubs_status = {path: False for path in MOVED_MODULES}

    for original_path in MOVED_MODULES:
        path = project_root / original_path

        # Check if it's a directory with __init__.py
        if path.is_dir() and (path / "__init__.py").exists():
            with open(path / "__init__.py", encoding="utf-8") as f:
                content = f.read()

            # Check if it's a compatibility stub
            if "This is a compatibility stub" in content:
                stubs_status[original_path] = True

        # Check if it's a file
        elif original_path.endswith(".py") and path.exists():
            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Check if it's a compatibility stub
            if "This is a compatibility stub" in content:
                stubs_status[original_path] = True

    return stubs_status


def check_stubs_coverage() -> Dict[str, bool]:
    """Check compatibility stubs coverage in the project.

    Returns:
        Dictionary mapping module paths to boolean indicating if stub exists
    """
    logger.info("Checking compatibility stubs coverage...")
    stubs_status = find_stubs(PROJECT_ROOT)

    missing_stubs = [path for path, exists in stubs_status.items() if not exists]

    if missing_stubs:
        logger.warning(f"Missing compatibility stubs for {len(missing_stubs)} modules:")
        for path in missing_stubs:
            logger.warning(f"  - {path} -> {MOVED_MODULES[path]}")
    else:
        logger.info("All moved modules have compatibility stubs")

    return stubs_status


#
# Main Function
#
def main() -> int:
    """Main function.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Unified code analyzer for PepperPy")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument(
        "--circular", action="store_true", help="Check for circular dependencies"
    )
    parser.add_argument(
        "--domain", action="store_true", help="Check domain conventions"
    )
    parser.add_argument(
        "--structure", action="store_true", help="Validate project structure"
    )
    parser.add_argument("--headers", action="store_true", help="Validate file headers")
    parser.add_argument(
        "--registry", action="store_true", help="Check registry compliance"
    )
    parser.add_argument(
        "--stubs", action="store_true", help="Check compatibility stubs coverage"
    )

    args = parser.parse_args()

    # If no specific checks are requested, run all checks
    if not any([
        args.circular,
        args.domain,
        args.structure,
        args.headers,
        args.registry,
        args.stubs,
    ]):
        args.all = True

    # Track if any checks failed
    has_errors = False

    # Run requested checks
    if args.all or args.circular:
        cycles = check_circular_dependencies()
        has_errors = has_errors or bool(cycles)

    if args.all or args.domain:
        domain_results = check_domain_conventions()
        has_errors = has_errors or any(
            missing for missing, _ in domain_results.values()
        )

    if args.all or args.structure:
        structure_errors = validate_structure()
        has_errors = has_errors or bool(structure_errors)

    if args.all or args.headers:
        header_results = check_headers()
        has_errors = has_errors or bool(header_results)

    if args.all or args.registry:
        registry_results = check_registry_compliance()
        has_errors = has_errors or any(
            not all(compliance.values()) for compliance in registry_results.values()
        )

    if args.all or args.stubs:
        stubs_results = check_stubs_coverage()
        has_errors = has_errors or not all(stubs_results.values())

    # Return exit code
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
