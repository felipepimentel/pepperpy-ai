---
title: "Repository Cleanup"
version: "1.1"
scope: "Pepperpy Project"
description: |
  A systematic guide for cleaning up the repository without 
  prompting for user confirmation. The cleanup process is 
  performed automatically following these steps:
    - Removing unused code
    - Organizing project files
    - Cleaning up dependencies
    - Removing temporary files
    - Preparing for releases
  
  This prompt ensures a clean and efficient codebase,
  applying best practices without requiring additional
  manual input.
---

Perform the following cleanup tasks automatically, without asking for confirmation:

1. **Remove Python Artifacts**
   ```bash
   find . -type d -name "__pycache__" -exec rm -r {} +
   find . -type f -name "*.pyc" -delete
   find . -type f -name "*.pyo" -delete
   find . -type f -name "*.pyd" -delete
   ```
   - Also remove any `.egg-info` or similar directories.

2. **Delete Temporary and Test Files**
   - Remove known cache directories and test artifacts:
     ```bash
     rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ coverage.xml
     ```
   - Delete any additional temporary or OS-specific files (e.g., `.tmp`, `.swp`) found in the repository.

3. **Clean Up Virtual Environments**
   - If the project uses a dedicated virtual environment (e.g., `.venv/`), remove it to ensure a fresh environment can be created on the next setup:
     ```bash
     rm -rf .venv/
     ```
   - If you need to keep a virtual environment for immediate use, skip this step or rename it for clarity.

4. **Remove or Archive Log Files**
   - Check for log files in `logs/` or elsewhere. 
   - If **active** logs need preservation, archive them (e.g., compress and move to an archive folder). 
   - If logs are disposable or empty, remove them:
     ```bash
     tar -czf logs/archive-$(date +%Y%m%d).tar.gz logs/*.log 2>/dev/null || true
     rm -f logs/*.log
     ```

5. **Review and Remove Unused Dependencies**
   - Examine `pyproject.toml` (or equivalent) for dependencies not used in the codebase.
   - Remove any such dependencies and keep the file tidy.  
   - Ensure that main, dev, and extras remain organized.

6. **Delete Dead or Unused Code**
   - Remove any commented-out sections or "dead code" blocks that no longer serve a purpose.
   - Eliminate repeated or duplicate functions if they are not used anywhere.

7. **Update Documentation**
   - Remove or update any outdated documentation files.
   - Ensure the main `README` reflects the **current project state**.
   - Clean up obsolete examples or references.

8. **Summarize Actions**
   - Update `.product/kanban.md` with a brief summary of all cleanup actions performed (e.g., "Removed __pycache__, removed logs, updated dependencies, etc.").
   - Note any follow-up steps if further cleanup or refactoring is recommended.

9. **Confirm Successful Completion**
   - Conclude with a statement indicating the cleanup has been completed.
   - If any issues arise, **resolve them** automatically and continue until the repository is successfully cleaned.