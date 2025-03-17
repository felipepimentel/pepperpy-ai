#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reporting utilities for refactoring progress.

This module provides functions for generating reports about
the status and progress of refactoring tasks.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .common import TASK_MAP, RefactoringContext, logger


def generate_progress_report(output_file: str, context: RefactoringContext) -> None:
    """
    Generate a markdown report of the refactoring progress.

    Args:
        output_file: Path where the report will be saved
        context: Refactoring context
    """
    logger.info(f"Generating progress report at {output_file}")

    # Get basic stats
    total_tasks = len(TASK_MAP)
    phases = set(task_id.split(".")[0] for task_id in TASK_MAP.keys())

    # Summary
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"""# PepperPy Refactoring Progress Report
*Generated on: {now}*

## Summary
- Total Tasks: {total_tasks}
- Phases: {len(phases)}

"""

    # Tasks by phase
    report += "## Tasks by Phase\n\n"
    for phase in sorted(phases):
        phase_tasks = [
            task_id for task_id in TASK_MAP.keys() if task_id.startswith(f"{phase}.")
        ]
        report += f"### Phase {phase}\n"
        report += f"- Tasks: {len(phase_tasks)}\n"
        report += "- IDs: " + ", ".join(sorted(phase_tasks)) + "\n\n"

    # Task details
    report += "## Task Details\n\n"
    for task_id in sorted(TASK_MAP.keys()):
        task_func = TASK_MAP[task_id]
        report += f"### Task {task_id}\n"
        report += f"- Function: {task_func.__name__}\n"
        if task_func.__doc__:
            doc = task_func.__doc__.strip()
            report += f"- Description: {doc}\n"
        report += (
            f'- Command: `python scripts/refactor.py run-task --task "{task_id}"`\n\n'
        )

    # Project structure analysis
    if not context.dry_run:
        report += "## Project Structure Analysis\n\n"

        # Count Python files
        py_files = list(Path("pepperpy").glob("**/*.py"))
        report += f"- Python files: {len(py_files)}\n"

        # Count directories
        dirs = set(f.parent for f in py_files)
        report += f"- Directories: {len(dirs)}\n"

        # Module statistics
        modules_stats = analyze_module_stats()
        report += "- Module statistics:\n"
        for module, count in sorted(
            modules_stats.items(), key=lambda x: x[1], reverse=True
        ):
            report += f"  - {module}: {count} files\n"

    # Write report
    report_path = Path(output_file)
    if not context.dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        logger.info(f"Progress report generated at {output_file}")
    else:
        logger.info(f"Would generate progress report at {output_file}")
        logger.info(f"Report preview:\n{report[:500]}...")


def analyze_module_stats() -> Dict[str, int]:
    """
    Analyze the statistics of Python modules in the project.

    Returns:
        Dictionary mapping top-level modules to file counts
    """
    stats = {}

    # Walk the project directory
    for root, _, files in os.walk("pepperpy"):
        for file in files:
            if file.endswith(".py"):
                # Get the top-level module
                rel_path = os.path.relpath(root, "pepperpy")
                if rel_path == ".":
                    module = "pepperpy"
                else:
                    module = f"pepperpy.{rel_path.split(os.sep)[0]}"

                # Update stats
                stats[module] = stats.get(module, 0) + 1

    return stats


def generate_task_checklist(output_file: str, context: RefactoringContext) -> None:
    """
    Generate a markdown checklist of all refactoring tasks.

    Args:
        output_file: Path where the checklist will be saved
        context: Refactoring context
    """
    logger.info(f"Generating task checklist at {output_file}")

    # Header
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    checklist = f"""# PepperPy Refactoring Task Checklist
*Generated on: {now}*

This checklist contains all refactoring tasks organized by phase.
Mark tasks as complete when they have been successfully executed.

"""

    # Organize tasks by phase and sub-phase
    tasks_by_phase = {}
    for task_id in sorted(TASK_MAP.keys()):
        parts = task_id.split(".")
        phase = parts[0]
        sub_phase = parts[1] if len(parts) > 1 else "0"

        if phase not in tasks_by_phase:
            tasks_by_phase[phase] = {}

        if sub_phase not in tasks_by_phase[phase]:
            tasks_by_phase[phase][sub_phase] = []

        tasks_by_phase[phase][sub_phase].append(task_id)

    # Generate checklist
    for phase in sorted(tasks_by_phase.keys()):
        checklist += f"## Phase {phase}\n\n"

        for sub_phase in sorted(tasks_by_phase[phase].keys()):
            tasks = tasks_by_phase[phase][sub_phase]

            if sub_phase != "0":
                checklist += f"### Sub-phase {sub_phase}\n\n"

            for task_id in sorted(tasks):
                task_func = TASK_MAP[task_id]
                desc = (
                    task_func.__doc__.strip().split("\n")[0]
                    if task_func.__doc__
                    else "No description"
                )

                checklist += f"- [ ] Task {task_id}: {desc}\n"
                checklist += (
                    f'  - `python scripts/refactor.py run-task --task "{task_id}"`\n'
                )

            checklist += "\n"

    # Write checklist
    checklist_path = Path(output_file)
    if not context.dry_run:
        checklist_path.parent.mkdir(parents=True, exist_ok=True)
        checklist_path.write_text(checklist, encoding="utf-8")
        logger.info(f"Task checklist generated at {output_file}")
    else:
        logger.info(f"Would generate task checklist at {output_file}")
        logger.info(f"Checklist preview:\n{checklist[:500]}...")


def update_task_md(task_file: str, context: RefactoringContext) -> None:
    """
    Update the TASK-012.md file with refactor.py execution commands.

    Args:
        task_file: Path to the TASK-012.md file
        context: Refactoring context
    """
    logger.info(f"Updating task file: {task_file}")

    task_path = Path(task_file)
    if not task_path.exists():
        logger.error(f"Task file {task_file} not found.")
        return

    content = task_path.read_text(encoding="utf-8")
    original_content = content

    # Extract task sections that need commands
    tasks = extract_tasks_from_md(content)

    # Pattern to match task headers in markdown
    task_pattern = r"- \[ \] \*\*`([^`]+)`\*\* - (.*?)(?=\n\s*- \[ \]|\n\s*$|\n\s*\n)"

    # For each task, add execution command
    for task_name, task_desc, pattern_match in tasks:
        command = generate_command_for_task(task_name, task_desc)

        if command:
            # Check if command already exists
            if "`python scripts/refactor.py" not in pattern_match:
                # Replace the task entry with task entry + command
                replacement = f"- [ ] **`{task_name}`** - {task_desc}\n  - `{command}`"
                content = content.replace(pattern_match, replacement)

    # Only write if content changed
    if content != original_content:
        if not context.dry_run:
            # Create a backup
            if context.backup:
                backup_path = task_path.with_suffix(".md.bak")
                backup_path.write_text(original_content, encoding="utf-8")
                logger.info(f"Created backup at {backup_path}")

            # Write updated content
            task_path.write_text(content, encoding="utf-8")
            logger.info(f"Updated {task_file} with execution commands")
        else:
            logger.info(f"Would update {task_file} with execution commands")
    else:
        logger.info(f"No changes needed for {task_file}")


def extract_tasks_from_md(content: str) -> List[Tuple[str, str, str]]:
    """
    Extract task sections from markdown content.

    Args:
        content: Markdown content to parse

    Returns:
        List of tuples (task_name, task_desc, original_match)
    """
    # Pattern to match task headers with backticks around the name
    task_pattern = r"- \[ \] \*\*`([^`]+)`\*\* - (.*?)(?=\n\s*- \[ \]|\n\s*$|\n\s*\n)"

    # Pattern for plain task headers (no backticks)
    plain_pattern = r"- \[ \] \*\*([^*]+)\*\* - (.*?)(?=\n\s*- \[ \]|\n\s*$|\n\s*\n)"

    tasks = []

    # Find tasks with backticks
    for match in re.finditer(task_pattern, content, re.DOTALL):
        task_name = match.group(1)
        task_desc = match.group(2).strip()
        full_match = match.group(0)
        tasks.append((task_name, task_desc, full_match))

    # Find plain tasks
    for match in re.finditer(plain_pattern, content, re.DOTALL):
        task_name = match.group(1)
        task_desc = match.group(2).strip()
        full_match = match.group(0)
        tasks.append((task_name, task_desc, full_match))

    return tasks


def generate_command_for_task(task_name: str, task_desc: str) -> str:
    """
    Generate execution command for a task based on its name and description.

    Args:
        task_name: Name of the task
        task_desc: Description of the task

    Returns:
        Command to execute the task
    """
    # Clean up task_name
    task_name = task_name.strip("`")

    # Specific command mappings based on task name
    if "pepperpy/llm/embedding.py" in task_name:
        return 'python scripts/refactor.py run-task --task "2.1.1"'

    elif "pepperpy/llm/providers/" in task_name:
        return 'python scripts/refactor.py run-task --task "2.1.2"'

    elif "pepperpy/llm/utils.py" in task_name:
        files = "pepperpy/llm/utils.py"
        output = "pepperpy/llm/utils.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nUtilitários para operações de LLM.\\n\\nEste módulo fornece funções auxiliares para processamento de LLM.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/rag/models.py" in task_name:
        return 'python scripts/refactor.py run-task --task "2.2.1"'

    elif "pepperpy/rag/storage.py" in task_name:
        files = "pepperpy/rag/storage/*.py"
        output = "pepperpy/rag/storage.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nArmazenamento para RAG.\\n\\nEste módulo fornece funcionalidades de armazenamento para RAG.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/rag/providers/" in task_name:
        return 'python scripts/refactor.py restructure-files --mapping "rag_providers_mapping.json"'

    elif "pepperpy/rag/utils.py" in task_name:
        files = "pepperpy/rag/utils.py"
        output = "pepperpy/rag/utils.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nUtilitários para operações de RAG.\\n\\nEste módulo fornece funções auxiliares para processamento de RAG.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/data/models.py" in task_name:
        files = "pepperpy/data/models/*.py"
        output = "pepperpy/data/models.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nModelos centrais para operações de dados.\\n\\nEste módulo define os modelos e funcionalidades para gerenciamento de dados.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/data/providers.py" in task_name:
        files = "pepperpy/data/providers/*.py"
        output = "pepperpy/data/providers.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nProvedores de dados para PepperPy.\\n\\nEste módulo fornece acesso a vários provedores de dados.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/data" in task_name and "clean" in task_desc.lower():
        return 'python scripts/refactor.py clean --directory "pepperpy/data"'

    elif "pepperpy/http/" in task_name:
        files = "pepperpy/http/*.py"
        output = "pepperpy/http/client.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nCliente HTTP para PepperPy.\\n\\nEste módulo fornece funcionalidades de cliente HTTP.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/storage/" in task_name:
        files = "pepperpy/storage/*.py"
        output = "pepperpy/storage/base.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nFuncionalidades de armazenamento para PepperPy.\\n\\nEste módulo fornece funcionalidades de armazenamento genéricas.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/memory/" in task_name:
        files = "pepperpy/memory/*.py"
        output = "pepperpy/memory/optimization.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nOtimização de memória para PepperPy.\\n\\nEste módulo fornece funcionalidades de otimização de memória.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/providers/" in task_name:
        files = "pepperpy/providers/*.py"
        output = "pepperpy/providers/base.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nClasses base para provedores.\\n\\nEste módulo define interfaces comuns para todos os provedores.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Protocol, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/cli/" in task_name:
        files = "pepperpy/cli/*/*.py"
        output = "pepperpy/cli/commands.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nComandos CLI para PepperPy.\\n\\nEste módulo fornece comandos de linha de comando para o PepperPy.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/plugins/" in task_name:
        files = "pepperpy/plugins/*.py"
        output = "pepperpy/plugins/base.py"
        header = '#!/usr/bin/env python\\n# -*- coding: utf-8 -*-\\n\\"\\"\\"\\nSistema de plugins para PepperPy.\\n\\nEste módulo fornece funcionalidades para extensão via plugins.\\n\\"\\"\\"\\n\\nfrom typing import Any, Dict, List, Optional, Union\\n'
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}" --header "{header}"'

    elif "pepperpy/__init__.py" in task_name or "__all__" in task_desc:
        return 'python scripts/refactor.py update-imports --directory "pepperpy"'

    elif "public.py" in task_desc.lower():
        return 'python scripts/refactor.py clean --directory "pepperpy"'

    elif "circular" in task_desc.lower():
        return "python scripts/refactor.py validate"

    elif (
        "core.py" in task_desc.lower()
        or "find" in task_desc.lower()
        and "unused" in task_desc.lower()
    ):
        return 'python scripts/refactor.py find-unused --directory "pepperpy"'

    elif "diretórios vazios" in task_desc.lower() or "clean" in task_desc.lower():
        return 'python scripts/refactor.py clean --directory "pepperpy"'

    # Default command for restructure-files
    elif "restructure" in task_desc.lower() or "move" in task_desc.lower():
        return 'python scripts/refactor.py restructure-files --mapping "mapping.json"'

    # Default command for consolidate
    elif (
        "consolidate" in task_desc.lower()
        or "mesclar" in task_desc.lower()
        or "consolidar" in task_desc.lower()
    ):
        files = "path/to/files/*.py"
        output = "path/to/output.py"
        return f'python scripts/refactor.py consolidate --files "{files}" --output "{output}"'

    # Default command for validation
    elif "validate" in task_desc.lower() or "validar" in task_desc.lower():
        return "python scripts/refactor.py validate"

    # Generic task runner for unknown tasks
    else:
        return ""
