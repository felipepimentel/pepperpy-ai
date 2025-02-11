---
title: Repository Cleanup
version: "1.0"
scope: "Pepperpy Project"
description: |
  A systematic guide for cleaning up the repository.
  Use this prompt when:
  - Removing unused code
  - Organizing project files
  - Cleaning up dependencies
  - Removing temporary files
  - Preparing for releases
  
  The prompt helps maintain a clean and efficient
  codebase.
---

Perform repository cleanup:
1. Clean Python artifacts:
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
```

2. Review and clean:
   - Temporary files
   - Log files
   - Test artifacts
   - Build directories
   - Cached files

3. Code cleanup:
   - Remove commented-out code
   - Delete unused imports
   - Clean up debug prints
   - Remove dead code
   - Update TODOs

4. Dependencies:
   - Remove unused dependencies
   - Update requirements files
   - Clean virtual environments

5. Documentation:
   - Remove outdated docs
   - Update README
   - Clean up examples

6. Update `.product/status.md` with cleanup summary. 