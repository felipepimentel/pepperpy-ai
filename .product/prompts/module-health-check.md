---
title: Module Health Check
version: "1.0"
scope: "Pepperpy Project"
description: |
  A comprehensive module health assessment guide.
  Use this prompt when:
  - Evaluating module quality
  - Checking module dependencies
  - Assessing code complexity
  - Planning refactoring efforts
  - Preparing for module updates
  
  The prompt helps maintain module quality and identify
  areas needing improvement.
---

Perform a health check on project modules:
1. Run the structure validator:
```bash
./scripts/validate_structure.py
```

2. For each module in `pepperpy/`:
   - Check cyclomatic complexity
   - Verify test coverage
   - Review dependency graph
   - Analyze code duplication
   - Check type annotation coverage
   - Verify documentation completeness

3. Generate a health report including:
   - Module metrics
   - Identified issues
   - Improvement recommendations
   - Priority of fixes

4. Update `/docs/status.md` with findings and create tasks for critical issues. 