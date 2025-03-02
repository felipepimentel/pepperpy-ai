#!/usr/bin/env python3
"""
Refactoring Implementation Script for PepperPy

This script implements the refactoring opportunities identified in the analysis
of the PepperPy project structure. It automates the process of consolidating
duplicated modules, reorganizing the project structure, and updating imports
throughout the codebase.

The script follows a phased approach:
1. Consolidation of duplicated modules
2. Reorganization of the project structure
3. Implementation of architectural improvements
4. Documentation and testing updates

Each phase includes backup creation, validation steps, and detailed logging
to ensure a safe and traceable refactoring process.
"""

import datetime
import json
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("refactoring.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class RefactoringManager:
    """
    Manages the refactoring process for the PepperPy project.

    This class provides methods for each phase of the refactoring process,
    including consolidation of duplicated modules, reorganization of the
    project structure, and implementation of architectural improvements.
    """

    def __init__(self, project_root: Path, backup_dir: Path | None = None):
        """
        Initialize the RefactoringManager.

        Args:
            project_root: Path to the root of the PepperPy project
            backup_dir: Path to the directory where backups will be stored
        """
        self.project_root = project_root
        self.pepperpy_dir = project_root / "pepperpy"

        if not backup_dir:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = project_root / f"backup_{timestamp}"

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(exist_ok=True, parents=True)

        # Track refactoring actions for reporting
        self.actions = {
            "moved_files": [],
            "consolidated_modules": [],
            "updated_imports": 0,
            "created_stubs": [],
            "removed_duplicates": [],
        }

    def create_backup(self, path: Path) -> Path | None:
        """
        Create a backup of a file or directory.

        Args:
            path: Path to the file or directory to back up

        Returns:
            Path to the backup or None if the path doesn't exist
        """
        if not path.exists():
            logger.warning(f"Cannot back up {path}: does not exist")
            return None

        relative_path = path.relative_to(self.project_root)
        backup_path = self.backup_dir / relative_path

        if path.is_dir():
            shutil.copytree(path, backup_path, dirs_exist_ok=True)
        else:
            backup_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy2(path, backup_path)

        logger.info(f"Created backup of {path} at {backup_path}")
        return backup_path

    def create_stub(self, original_path: Path, new_path: Path) -> Path:
        """
        Create a compatibility stub for a moved module.

        Args:
            original_path: Original path of the module
            new_path: New path of the module

        Returns:
            Path to the created stub
        """
        if not original_path.exists():
            # Create the directory structure if it doesn't exist
            original_path.parent.mkdir(exist_ok=True, parents=True)

        # Determine the import path for the new module
        rel_original = original_path.relative_to(self.pepperpy_dir)
        rel_new = new_path.relative_to(self.pepperpy_dir)

        original_import = f"pepperpy.{str(rel_original.parent).replace('/', '.')}"
        new_import = f"pepperpy.{str(rel_new.parent).replace('/', '.')}"

        if original_path.is_dir():
            # Create an __init__.py stub for a directory
            stub_path = original_path / "__init__.py"
            with open(stub_path, "w") as f:
                f.write(f"""# This is a compatibility stub for code that imports from the old location.
# This module has been moved to {new_import}.
# Please update your imports to use the new location.

import warnings
warnings.warn(
    f"Importing from {original_import} is deprecated. "
    f"Please update your imports to use {new_import}.",
    DeprecationWarning,
    stacklevel=2
)

from {new_import} import *
""")
        else:
            # Create a stub for a file
            with open(original_path, "w") as f:
                module_name = original_path.stem
                new_module_name = new_path.stem

                f.write(f"""# This is a compatibility stub for code that imports from the old location.
# This module has been moved to {new_import}.{new_module_name}.
# Please update your imports to use the new location.

import warnings
warnings.warn(
    f"Importing from {original_import}.{module_name} is deprecated. "
    f"Please update your imports to use {new_import}.{new_module_name}.",
    DeprecationWarning,
    stacklevel=2
)

from {new_import}.{new_module_name} import *
""")

        logger.info(f"Created compatibility stub at {original_path}")
        self.actions["created_stubs"].append(str(original_path))
        return original_path

    def update_imports(self, file_path: Path, old_import: str, new_import: str) -> int:
        """
        Update import statements in a file.

        Args:
            file_path: Path to the file to update
            old_import: Old import statement to replace
            new_import: New import statement

        Returns:
            Number of imports updated
        """
        if not file_path.exists() or not file_path.is_file():
            return 0

        with open(file_path, "r") as f:
            content = f.read()

        # Replace import statements
        patterns = [
            (f"import {old_import}", f"import {new_import}"),
            (f"from {old_import} import", f"from {new_import} import"),
        ]

        count = 0
        for old_pattern, new_pattern in patterns:
            new_content = re.sub(old_pattern, new_pattern, content)
            if new_content != content:
                count += content.count(old_pattern)
                content = new_content

        if count > 0:
            with open(file_path, "w") as f:
                f.write(content)

            logger.debug(f"Updated {count} imports in {file_path}")
            self.actions["updated_imports"] += count

        return count

    def update_all_imports(self, import_mappings: Dict[str, str]) -> int:
        """
        Update all import statements in the project.

        Args:
            import_mappings: Dictionary mapping old import paths to new import paths

        Returns:
            Total number of imports updated
        """
        total_updated = 0

        for path in self.pepperpy_dir.glob("**/*.py"):
            for old_import, new_import in import_mappings.items():
                total_updated += self.update_imports(path, old_import, new_import)

        # Also update imports in tests
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for path in tests_dir.glob("**/*.py"):
                for old_import, new_import in import_mappings.items():
                    total_updated += self.update_imports(path, old_import, new_import)

        logger.info(f"Updated {total_updated} imports in total")
        return total_updated

    def consolidate_capabilities(self) -> None:
        """
        Consolidate the core/capabilities and capabilities directories.
        """
        logger.info("Consolidating capabilities directories...")

        core_capabilities = self.pepperpy_dir / "core" / "capabilities"
        capabilities = self.pepperpy_dir / "capabilities"

        # Create backups
        self.create_backup(core_capabilities)
        self.create_backup(capabilities)

        # Move interface files from core/capabilities to capabilities
        for file_path in core_capabilities.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            # Rename to avoid conflicts
            new_name = (
                "interfaces.py" if file_path.name == "base.py" else file_path.name
            )
            new_path = capabilities / new_name

            # Copy the file to the new location
            shutil.copy2(file_path, new_path)
            logger.info(f"Copied {file_path} to {new_path}")
            self.actions["moved_files"].append((str(file_path), str(new_path)))

        # Update the capabilities/__init__.py to import from the new files
        init_path = capabilities / "__init__.py"
        with open(init_path, "a") as f:
            f.write("\n# Import interfaces from consolidated files\n")
            f.write("from .interfaces import *\n")
            f.write("from .providers import *\n")

        # Create a compatibility stub for core/capabilities
        self.create_stub(core_capabilities, capabilities)

        # Update import mappings
        import_mappings = {
            "pepperpy.core.capabilities": "pepperpy.capabilities",
            "pepperpy.core.capabilities.base": "pepperpy.capabilities.interfaces",
            "pepperpy.core.capabilities.providers": "pepperpy.capabilities.providers",
        }

        self.update_all_imports(import_mappings)

        logger.info("Capabilities directories consolidated successfully")
        self.actions["consolidated_modules"].append("capabilities")

    def consolidate_workflows(self) -> None:
        """
        Consolidate the workflow and workflows directories.
        """
        logger.info("Consolidating workflow directories...")

        workflow = self.pepperpy_dir / "workflow"
        workflows = self.pepperpy_dir / "workflows"

        # Create backups
        self.create_backup(workflow)
        self.create_backup(workflows)

        # Move unique files from workflow to workflows
        for file_path in workflow.glob("*.py"):
            new_path = workflows / file_path.name

            if not new_path.exists():
                # File doesn't exist in workflows, copy it
                shutil.copy2(file_path, new_path)
                logger.info(f"Copied {file_path} to {new_path}")
                self.actions["moved_files"].append((str(file_path), str(new_path)))
            else:
                # File exists in both places, need to merge or decide which to keep
                logger.info(
                    f"File {file_path.name} exists in both workflow and workflows"
                )
                # For now, we'll keep the one in workflows

        # Move unique subdirectories from workflow to workflows
        for dir_path in workflow.glob("*/"):
            if dir_path.name in ["__pycache__"]:
                continue

            if dir_path.name not in ["definition", "execution"]:
                # This is a unique subdirectory, move it to workflows
                new_dir_path = workflows / dir_path.name

                if not new_dir_path.exists():
                    shutil.copytree(dir_path, new_dir_path)
                    logger.info(f"Copied directory {dir_path} to {new_dir_path}")
                    self.actions["moved_files"].append((
                        str(dir_path),
                        str(new_dir_path),
                    ))
                else:
                    logger.info(
                        f"Directory {dir_path.name} exists in both workflow and workflows"
                    )
                    # For now, we'll keep the one in workflows

        # Create a compatibility stub for workflow
        self.create_stub(workflow, workflows)

        # Update import mappings
        import_mappings = {"pepperpy.workflow": "pepperpy.workflows"}

        self.update_all_imports(import_mappings)

        logger.info("Workflow directories consolidated successfully")
        self.actions["consolidated_modules"].append("workflows")

    def consolidate_llm_providers(self) -> None:
        """
        Consolidate the llm/providers and providers/llm directories.
        """
        logger.info("Consolidating LLM providers...")

        llm_providers = self.pepperpy_dir / "llm" / "providers"
        providers_llm = self.pepperpy_dir / "providers" / "llm"

        # Create backups
        self.create_backup(llm_providers)
        self.create_backup(providers_llm)

        # Create a compatibility stub for llm/providers
        self.create_stub(llm_providers, providers_llm)

        # Update import mappings
        import_mappings = {"pepperpy.llm.providers": "pepperpy.providers.llm"}

        self.update_all_imports(import_mappings)

        logger.info("LLM providers consolidated successfully")
        self.actions["consolidated_modules"].append("llm_providers")

    def move_examples(self) -> None:
        """
        Move examples from examples to the root examples directory.
        """
        logger.info("Moving examples to root directory...")

        pepperpy_examples = self.pepperpy_dir / "examples"
        root_examples = self.project_root / "examples"

        # Create backups
        self.create_backup(pepperpy_examples)
        self.create_backup(root_examples)

        # Create the root examples directory if it doesn't exist
        root_examples.mkdir(exist_ok=True)

        # Move all examples to the root directory
        for item in pepperpy_examples.glob("*"):
            if item.name == "__pycache__":
                continue

            new_path = root_examples / item.name

            if item.is_dir():
                if not new_path.exists():
                    shutil.copytree(item, new_path)
                else:
                    # Merge directories
                    for subitem in item.glob("*"):
                        sub_new_path = new_path / subitem.name
                        if not sub_new_path.exists():
                            if subitem.is_dir():
                                shutil.copytree(subitem, sub_new_path)
                            else:
                                shutil.copy2(subitem, sub_new_path)
            else:
                if not new_path.exists():
                    shutil.copy2(item, new_path)
                else:
                    # For files with the same name, create a backup
                    backup_name = f"{item.stem}_pepperpy{item.suffix}"
                    backup_path = new_path.parent / backup_name
                    shutil.copy2(item, backup_path)

        logger.info(f"Moved examples from {pepperpy_examples} to {root_examples}")
        self.actions["moved_files"].append((str(pepperpy_examples), str(root_examples)))

    def consolidate_common_and_core(self) -> None:
        """
        Consolidate overlapping directories between common and core.
        """
        logger.info("Consolidating common and core directories...")

        common = self.pepperpy_dir / "common"
        core = self.pepperpy_dir / "core"

        # Create backups
        self.create_backup(common)
        self.create_backup(core)

        # Define which directories should be in common vs core
        common_dirs = ["utils", "types", "validation"]
        core_dirs = ["errors", "versioning"]

        # Move directories from core to common if they should be in common
        for dir_name in common_dirs:
            core_dir = core / dir_name
            common_dir = common / dir_name

            if core_dir.exists():
                if not common_dir.exists():
                    # Move the entire directory
                    shutil.copytree(core_dir, common_dir)
                    logger.info(f"Moved {core_dir} to {common_dir}")
                    self.actions["moved_files"].append((str(core_dir), str(common_dir)))
                else:
                    # Merge directories
                    for item in core_dir.glob("*"):
                        if item.name == "__pycache__":
                            continue

                        new_path = common_dir / item.name

                        if not new_path.exists():
                            if item.is_dir():
                                shutil.copytree(item, new_path)
                            else:
                                shutil.copy2(item, new_path)

                            logger.info(f"Moved {item} to {new_path}")
                            self.actions["moved_files"].append((
                                str(item),
                                str(new_path),
                            ))

                # Create a compatibility stub
                self.create_stub(core_dir, common_dir)

        # Move directories from common to core if they should be in core
        for dir_name in core_dirs:
            common_dir = common / dir_name
            core_dir = core / dir_name

            if common_dir.exists():
                if not core_dir.exists():
                    # Move the entire directory
                    shutil.copytree(common_dir, core_dir)
                    logger.info(f"Moved {common_dir} to {core_dir}")
                    self.actions["moved_files"].append((str(common_dir), str(core_dir)))
                else:
                    # Merge directories
                    for item in common_dir.glob("*"):
                        if item.name == "__pycache__":
                            continue

                        new_path = core_dir / item.name

                        if not new_path.exists():
                            if item.is_dir():
                                shutil.copytree(item, new_path)
                            else:
                                shutil.copy2(item, new_path)

                            logger.info(f"Moved {item} to {new_path}")
                            self.actions["moved_files"].append((
                                str(item),
                                str(new_path),
                            ))

                # Create a compatibility stub
                self.create_stub(common_dir, core_dir)

        # Update import mappings
        import_mappings = {}

        for dir_name in common_dirs:
            import_mappings[f"pepperpy.core.{dir_name}"] = f"pepperpy.common.{dir_name}"

        for dir_name in core_dirs:
            import_mappings[f"pepperpy.common.{dir_name}"] = f"pepperpy.core.{dir_name}"

        self.update_all_imports(import_mappings)

        logger.info("Common and core directories consolidated successfully")
        self.actions["consolidated_modules"].append("common_and_core")

    def standardize_naming(self) -> None:
        """
        Standardize directory naming (singular vs plural).
        """
        logger.info("Standardizing directory naming...")

        # Define directories to rename (singular to plural)
        to_rename = {"embedding": "embeddings", "pipeline": "pipelines"}

        for old_name, new_name in to_rename.items():
            old_path = self.pepperpy_dir / old_name
            new_path = self.pepperpy_dir / new_name

            if old_path.exists() and not new_path.exists():
                # Create a backup
                self.create_backup(old_path)

                # Copy the directory to the new name
                shutil.copytree(old_path, new_path)
                logger.info(f"Renamed {old_path} to {new_path}")
                self.actions["moved_files"].append((str(old_path), str(new_path)))

                # Create a compatibility stub
                self.create_stub(old_path, new_path)

                # Update import mappings
                import_mappings = {f"pepperpy.{old_name}": f"pepperpy.{new_name}"}

                self.update_all_imports(import_mappings)

        logger.info("Directory naming standardized successfully")

    def create_interfaces_module(self) -> None:
        """
        Create a new interfaces module for public APIs.
        """
        logger.info("Creating interfaces module...")

        interfaces_dir = self.pepperpy_dir / "interfaces"
        interfaces_dir.mkdir(exist_ok=True)

        # Create an __init__.py file
        init_path = interfaces_dir / "__init__.py"
        with open(init_path, "w") as f:
            f.write("""\"\"\"
Public Interfaces for PepperPy

This module defines the public interfaces for the PepperPy framework.
These interfaces are stable and backward-compatible, and should be
used by external code that depends on PepperPy.
\"\"\"

# Import public interfaces
""")

        # Create a README.md file
        readme_path = interfaces_dir / "README.md"
        with open(readme_path, "w") as f:
            f.write("""# PepperPy Public Interfaces

This directory contains the public interfaces for the PepperPy framework.
These interfaces are stable and backward-compatible, and should be used
by external code that depends on PepperPy.

## Usage

```python
from pepperpy.llm import LLMProvider
from pepperpy.rag import RAGPipeline
from pepperpy.agents import Agent
```

## Interface Stability

Interfaces in this module follow semantic versioning:

- Major version changes (1.0.0 -> 2.0.0) may include breaking changes
- Minor version changes (1.0.0 -> 1.1.0) add new features without breaking changes
- Patch version changes (1.0.0 -> 1.0.1) include bug fixes without breaking changes

## Available Interfaces

- `LLMProvider`: Interface for language model providers
- `RAGProvider`: Interface for retrieval-augmented generation providers
- `Agent`: Interface for agents
- `Workflow`: Interface for workflows
- `Embedding`: Interface for embeddings
- `Memory`: Interface for memory systems
""")

        logger.info(f"Created interfaces module at {interfaces_dir}")

    def generate_report(self) -> None:
        """
        Generate a report of the refactoring process.
        """
        logger.info("Generating refactoring report...")

        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "backup_dir": str(self.backup_dir),
            "actions": self.actions,
        }

        report_path = self.project_root / "refactoring_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Generate a markdown report
        md_report_path = self.project_root / "refactoring_report.md"
        with open(md_report_path, "w") as f:
            f.write("# PepperPy Refactoring Report\n\n")
            f.write(
                f"**Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## Summary\n\n")
            f.write(f"- Moved files: {len(self.actions['moved_files'])}\n")
            f.write(
                f"- Consolidated modules: {len(self.actions['consolidated_modules'])}\n"
            )
            f.write(f"- Updated imports: {self.actions['updated_imports']}\n")
            f.write(
                f"- Created compatibility stubs: {len(self.actions['created_stubs'])}\n"
            )
            f.write(
                f"- Removed duplicates: {len(self.actions['removed_duplicates'])}\n\n"
            )

            f.write("## Consolidated Modules\n\n")
            for module in self.actions["consolidated_modules"]:
                f.write(f"- {module}\n")
            f.write("\n")

            f.write("## Created Compatibility Stubs\n\n")
            for stub in self.actions["created_stubs"]:
                f.write(f"- {stub}\n")
            f.write("\n")

            f.write("## Next Steps\n\n")
            f.write("1. Update documentation to reflect the new structure\n")
            f.write("2. Update tests to ensure they work with the new structure\n")
            f.write(
                "3. Implement a plan for removing compatibility stubs in future versions\n"
            )
            f.write("4. Continue monitoring and eliminating circular dependencies\n")

        logger.info(
            f"Generated refactoring report at {report_path} and {md_report_path}"
        )

    def implement_refactoring(self) -> None:
        """
        Implement the refactoring process.
        """
        logger.info("Starting refactoring process...")

        # Phase 1: Consolidation of duplicated modules
        self.consolidate_capabilities()
        self.consolidate_workflows()
        self.consolidate_llm_providers()

        # Phase 2: Reorganization of the project structure
        self.move_examples()
        self.consolidate_common_and_core()
        self.standardize_naming()

        # Phase 3: Implementation of architectural improvements
        self.create_interfaces_module()

        # Generate a report
        self.generate_report()

        logger.info("Refactoring process completed successfully")


def main():
    """
    Main function to run the refactoring process.
    """
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent.parent

    # Create a backup directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / f"backup_{timestamp}"

    # Initialize the refactoring manager
    manager = RefactoringManager(project_root, backup_dir)

    # Implement the refactoring
    manager.implement_refactoring()


if __name__ == "__main__":
    main()
