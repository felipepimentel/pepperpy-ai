---
title: Dependency Update
version: "1.0"
scope: "Pepperpy Project"
description: |
  A comprehensive guide for managing project dependencies.
  Use this prompt when:
  - Updating package versions
  - Adding new dependencies
  - Removing unused packages
  - Checking for vulnerabilities
  - Optimizing dependency tree
  
  The prompt helps maintain up-to-date and secure
  project dependencies.
---

Review and update project dependencies:
1. Check for outdated packages:
```bash
pip list --outdated
```

2. Security check:
```bash
pip-audit
```

3. For each dependency in `pyproject.toml`:
   - Check current version
   - Review latest stable release
   - Check for security advisories
   - Review breaking changes
   - Test compatibility

4. Update process:
   - Create backup of dependency files
   - Update packages incrementally
   - Run test suite after each update
   - Document breaking changes
   - Update requirements files

5. Verify project functionality:
   - Run all tests
   - Check import statements
   - Verify build process
   - Test key features

6. Update documentation:
   - Update dependency list
   - Note breaking changes
   - Update setup instructions
   - Update `/docs/status.md` 